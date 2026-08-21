from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.redis import get_redis

router = APIRouter(tags=["Health Check"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """System health check endpoint verifying Database & Redis connection status."""
    health_status = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": "unknown",
            "redis": "unknown"
        }
    }

    # 1. Check PostgreSQL/SQLite Database
    try:
        await db.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["database"] = f"unhealthy: {str(e)}"

    # 2. Check Redis
    try:
        redis_client = get_redis()
        pong = await redis_client.ping()
        if pong:
            health_status["services"]["redis"] = "healthy"
        else:
            health_status["status"] = "degraded"
            health_status["services"]["redis"] = "unhealthy"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"

    http_status = status.HTTP_200_OK if health_status["status"] == "ok" else status.HTTP_530_SITE_IS_FROZEN
    return JSONResponse(status_code=http_status, content=health_status)
