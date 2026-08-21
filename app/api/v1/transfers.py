import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.users import User
from app.schemas.transfer import (
    P2PTransferRequest,
    TransactionResponse,
    TransactionHistoryQuery,
    TransactionListResponse,
)
from app.services.transfer import TransferService
from app.core.rate_limit import RateLimiter

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(max_requests=10, window_seconds=60))]
)
async def execute_p2p_transfer(
    transfer_in: P2PTransferRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Executes atomic peer-to-peer (P2P) fund transfer with double-entry bookkeeping."""
    try:
        transaction = await TransferService.execute_p2p_transfer(
            db=db,
            sender_user_id=current_user.id,
            transfer_in=transfer_in,
            idempotency_key=idempotency_key
        )
        return transaction
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/history", response_model=TransactionListResponse)
async def get_transaction_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    transaction_type: str | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves paginated transaction history & ledger receipts for the user's wallet."""
    query = TransactionHistoryQuery(page=page, size=size, transaction_type=transaction_type)
    items, total = await TransferService.get_transaction_history(db, current_user.id, query)
    return TransactionListResponse(
        items=items,
        total=total,
        page=page,
        size=size
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_details(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetches details & double-entry ledger items for a specific transaction."""
    try:
        return await TransferService.get_transaction_by_id(db, current_user.id, transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
