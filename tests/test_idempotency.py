import sys
import os
sys.path.insert(0, os.path.abspath("."))

import asyncio
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from app.core.idempotency import IdempotencyService
from app.core.rate_limit import RateLimiter


class MockRedis:
    def __init__(self):
        self.store = {}
        self.ttl_store = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int = None, nx: bool = False):
        if nx and key in self.store:
            return None
        self.store[key] = value
        if ex:
            self.ttl_store[key] = ex
        return True

    async def delete(self, key: str):
        self.store.pop(key, None)
        self.ttl_store.pop(key, None)

    async def incr(self, key: str):
        val = int(self.store.get(key, 0)) + 1
        self.store[key] = str(val)
        return val

    async def expire(self, key: str, seconds: int):
        self.ttl_store[key] = seconds
        return True

    async def ttl(self, key: str):
        return self.ttl_store.get(key, 60)


async def run_tests():
    print("--- Starting Phase 2 Idempotency & Rate Limiter Unit Tests ---")
    mock_redis = MockRedis()

    with patch("app.core.idempotency.get_redis", return_value=mock_redis), \
         patch("app.core.rate_limit.get_redis", return_value=mock_redis):

        # 1. Test Idempotency Lock
        key = "test-idempotency-key-001"
        locked = await IdempotencyService.lock_processing(key)
        assert locked is True, "First lock attempt should succeed"

        duplicate_lock = await IdempotencyService.lock_processing(key)
        assert duplicate_lock is False, "Second lock attempt on same key should fail"
        print("[SUCCESS] Idempotency lock & duplicate prevention verified")

        # 2. Test Saving Response and Retrieval
        response_payload = {"message": "Transfer processed successfully", "reference": "TXN-999"}
        await IdempotencyService.save_response(key, status_code=200, response_body=response_payload)

        record = await IdempotencyService.get_record(key)
        assert record is not None
        assert record["status"] == "COMPLETED"
        assert record["status_code"] == 200
        assert record["response_body"] == response_payload
        print("[SUCCESS] Idempotency response caching and replay retrieval verified")

        # 3. Test Rate Limiter
        rate_limiter = RateLimiter(max_requests=3, window_seconds=60)
        mock_request = AsyncMock()
        mock_request.state = AsyncMock()
        mock_request.state.user = None
        mock_request.client.host = "127.0.0.1"
        mock_request.url.path = "/api/v1/wallets/pin"

        # First 3 requests should pass
        for i in range(3):
            await rate_limiter(mock_request)
        print("[SUCCESS] Rate limiter permitted requests under threshold (3/3)")

        # 4th request should raise HTTP 429
        try:
            await rate_limiter(mock_request)
            assert False, "Rate limiter should have raised HTTP 429"
        except HTTPException as exc:
            assert exc.status_code == 429
            assert "Rate limit exceeded" in exc.detail
            print(f"[SUCCESS] Rate limiter blocked 4th request with HTTP 429: '{exc.detail}'")

    print("--- Phase 2 Tests Completed Successfully ---")


if __name__ == "__main__":
    asyncio.run(run_tests())
