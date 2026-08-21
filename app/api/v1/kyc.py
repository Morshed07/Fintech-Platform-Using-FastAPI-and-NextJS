from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.users import User
from app.schemas.kyc import KYCSubmitRequest, KYCResponse
from app.services.kyc import KYCService
from app.services.audit import AuditService

router = APIRouter(prefix="/kyc", tags=["KYC Verification"])


@router.get("/me", response_model=KYCResponse)
async def get_my_kyc(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves current user's KYC verification status, tier, and daily transfer limit."""
    return await KYCService.get_kyc_response(db, current_user.id)


@router.post("/submit", response_model=KYCResponse, status_code=status.HTTP_200_OK)
async def submit_kyc_document(
    kyc_in: KYCSubmitRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Submits identity document for KYC verification and upgrades daily transfer limit to TIER_1 ($10,000/day)."""
    try:
        response = await KYCService.submit_kyc(db, current_user.id, kyc_in)
        await AuditService.log_action(
            db,
            current_user.id,
            "KYC_UPGRADE",
            details=f"Document {kyc_in.document_type} submitted. Upgraded to TIER_1 ($10,000/day)."
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
