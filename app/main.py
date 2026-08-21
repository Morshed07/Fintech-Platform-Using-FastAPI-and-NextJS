import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.core.redis import init_redis, close_redis
from app.api.v1.auth import router as auth_router
from app.api.v1.wallets import router as wallets_router
from app.api.v1.transfers import router as transfers_router
from app.api.v1.gateway import router as gateway_router
from app.api.v1.kyc import router as kyc_router
from app.api.v1.health import router as health_router
from app.core.idempotency import IdempotencyMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis connection pool
    await init_redis()
    
    # Ensure DB tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    
    # Shutdown: Close Redis connection pool
    await close_redis()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production Grade FastAPI Auth System with JWT, Redis OTP, and Async Email Queue",
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(IdempotencyMiddleware)

# Ensure uploads folder exists
os.makedirs("uploads/avatars", exist_ok=True)

# Serve files inside "uploads" directory at "/uploads" URL route
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(wallets_router, prefix=settings.API_V1_STR)
app.include_router(transfers_router, prefix=settings.API_V1_STR)
app.include_router(gateway_router, prefix=settings.API_V1_STR)
app.include_router(kyc_router, prefix=settings.API_V1_STR)
app.include_router(health_router)


@app.get('/')
async def root():
    return {
        "message": "FastAPI Auth System API is running",
        "docs": "/docs"
    }
