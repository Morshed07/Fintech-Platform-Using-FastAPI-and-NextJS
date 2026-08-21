import json
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.redis import get_redis


class IdempotencyService:
    REDIS_PREFIX = "idempotency"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    PROCESSING_TTL_SECONDS = 60  # 1 minute lock

    @classmethod
    def _make_key(cls, idempotency_key: str) -> str:
        return f"{cls.REDIS_PREFIX}:{idempotency_key}"

    @classmethod
    async def get_record(cls, idempotency_key: str) -> dict | None:
        """Retrieves cached idempotency record from Redis."""
        client = get_redis()
        raw_data = await client.get(cls._make_key(idempotency_key))
        if raw_data:
            try:
                return json.loads(raw_data)
            except json.JSONDecodeError:
                return None
        return None

    @classmethod
    async def lock_processing(cls, idempotency_key: str) -> bool:
        """Acquires lock for key with status PROCESSING. Returns True if lock acquired."""
        client = get_redis()
        key = cls._make_key(idempotency_key)
        payload = json.dumps({"status": "PROCESSING"})
        # set nx=True returns True if set succeeded, None if key already exists
        result = await client.set(key, payload, ex=cls.PROCESSING_TTL_SECONDS, nx=True)
        return result is True

    @classmethod
    async def save_response(
        cls,
        idempotency_key: str,
        status_code: int,
        response_body: dict | list,
        ttl: int = DEFAULT_TTL_SECONDS
    ) -> None:
        """Saves completed API response payload in Redis with 24-hour TTL."""
        client = get_redis()
        key = cls._make_key(idempotency_key)
        payload = json.dumps({
            "status": "COMPLETED",
            "status_code": status_code,
            "response_body": response_body
        })
        await client.set(key, payload, ex=ttl)

    @classmethod
    async def unlock_processing(cls, idempotency_key: str) -> None:
        """Removes lock if request execution fails before completing."""
        client = get_redis()
        key = cls._make_key(idempotency_key)
        await client.delete(key)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware to intercept requests with Idempotency-Key header."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only check Idempotency-Key for mutating HTTP methods (POST, PUT, PATCH, DELETE)
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key") or request.headers.get("X-Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        # 1. Check existing record in Redis
        record = await IdempotencyService.get_record(idempotency_key)
        if record:
            if record.get("status") == "COMPLETED":
                return JSONResponse(
                    status_code=record.get("status_code", 200),
                    content=record.get("response_body"),
                    headers={
                        "X-Cache-Lookup": "HIT",
                        "X-Idempotency-Key": idempotency_key
                    }
                )
            elif record.get("status") == "PROCESSING":
                return JSONResponse(
                    status_code=409,
                    content={"detail": "A request with this Idempotency-Key is currently being processed."}
                )

        # 2. Acquire lock
        acquired = await IdempotencyService.lock_processing(idempotency_key)
        if not acquired:
            return JSONResponse(
                status_code=409,
                content={"detail": "Concurrent request detected for this Idempotency-Key."}
            )

        # 3. Process actual request
        try:
            response = await call_next(request)
        except Exception:
            await IdempotencyService.unlock_processing(idempotency_key)
            raise

        # 4. Stream response body and cache if successful
        if response.status_code < 500:
            response_body = [chunk async for chunk in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(response_body))
            
            try:
                body_bytes = b"".join(response_body)
                json_data = json.loads(body_bytes.decode("utf-8"))
                await IdempotencyService.save_response(
                    idempotency_key=idempotency_key,
                    status_code=response.status_code,
                    response_body=json_data
                )
            except Exception:
                # If response is non-JSON or streaming, do not cache
                pass

        return response


async def iterate_in_threadpool(iterator):
    for item in iterator:
        yield item
