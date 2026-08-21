from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.users import User
from app.schemas.wallet import WalletResponse, SetPinRequest
from app.schemas.auth import MessageResponse
from app.services.wallet import WalletService
from app.core.rate_limit import RateLimiter

router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.get("/me", response_model=WalletResponse)
async def get_my_wallet(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetches details and balance for the authenticated user's wallet."""
    wallet = await WalletService.get_wallet_by_user_id(db, current_user.id)
    return await WalletService.get_wallet_response(wallet)


@router.post("/pin", response_model=MessageResponse, dependencies=[Depends(RateLimiter(max_requests=5, window_seconds=60))])
async def set_transaction_pin(
    pin_in: SetPinRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Sets or updates the 6-digit numerical security transaction PIN for the user's wallet."""
    try:
        return await WalletService.set_transaction_pin(db, current_user.id, pin_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
