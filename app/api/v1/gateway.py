from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.users import User
from app.schemas.gateway import DepositRequest, WithdrawalRequest
from app.schemas.transfer import TransactionResponse
from app.schemas.auth import MessageResponse
from app.services.deposit_withdrawal import DepositWithdrawalService
from app.core.rate_limit import RateLimiter

router = APIRouter(prefix="/gateway", tags=["Payment Gateway"])


@router.post(
    "/deposit",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(max_requests=10, window_seconds=60))]
)
async def process_deposit(
    deposit_in: DepositRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Processes simulated fiat deposit into user's wallet."""
    try:
        return await DepositWithdrawalService.process_deposit(db, current_user.id, deposit_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/withdraw",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(max_requests=5, window_seconds=60))]
)
async def process_withdrawal(
    withdraw_in: WithdrawalRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Processes bank withdrawal from user's wallet after verifying 6-digit transaction PIN."""
    try:
        return await DepositWithdrawalService.process_withdrawal(db, current_user.id, withdraw_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/webhook", response_model=MessageResponse)
async def gateway_webhook(
    request: Request,
    x_signature: str | None = Header(None, alias="X-Signature"),
    db: AsyncSession = Depends(get_db)
):
    """Processes external payment gateway webhooks with HMAC-SHA256 signature verification."""
    payload_bytes = await request.body()
    try:
        return await DepositWithdrawalService.process_gateway_webhook(
            db=db,
            payload_bytes=payload_bytes,
            signature_header=x_signature or ""
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
