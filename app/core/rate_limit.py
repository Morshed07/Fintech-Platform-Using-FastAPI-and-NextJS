from fastapi import Request, HTTPException, status
from app.core.redis import get_redis


class RateLimiter:
    """Redis-backed rate limiter for endpoints."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def __call__(self, request: Request) -> None:
        client = get_redis()
        
        # Identify user by authenticated user_id if available, fallback to IP address
        user_id = None
        if hasattr(request.state, "user") and getattr(request.state, "user"):
            user_id = str(request.state.user.id)
        
        identifier = user_id or (request.client.host if request.client else "anonymous")
        endpoint = request.url.path
        key = f"rate_limit:{identifier}:{endpoint}"

        current_count = await client.incr(key)
        if current_count == 1:
            await client.expire(key, self.window_seconds)

        if current_count > self.max_requests:
            ttl = await client.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds.",
                headers={"Retry-After": str(ttl if ttl > 0 else self.window_seconds)}
            )
