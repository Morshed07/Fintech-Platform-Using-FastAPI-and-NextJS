import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import UserKYC
from app.models.wallet import Wallet, LedgerEntry, Transaction
from app.schemas.kyc import KYCSubmitRequest, KYCResponse
from app.services.wallet import WalletService


class KYCService:
    TIER_LIMITS = {
        "TIER_0": Decimal("1000.0000"),    # $1,000 / day
        "TIER_1": Decimal("10000.0000"),   # $10,000 / day
        "TIER_2": Decimal("100000.0000"),  # $100,000 / day
    }

    @classmethod
    async def get_or_create_kyc(cls, db: AsyncSession, user_id: uuid.UUID) -> UserKYC:
        """Retrieves user's KYC profile or provisions default TIER_0."""
        res = await db.execute(select(UserKYC).where(UserKYC.user_id == user_id))
        kyc = res.scalar_one_or_none()
        if not kyc:
            kyc = UserKYC(
                user_id=user_id,
                tier="TIER_0",
                verification_status="APPROVED"
            )
            db.add(kyc)
            await db.commit()
            await db.refresh(kyc)
        return kyc

    @classmethod
    def get_daily_limit_for_tier(cls, tier: str) -> Decimal:
        """Returns daily transfer limit for a given tier."""
        return cls.TIER_LIMITS.get(tier, Decimal("1000.0000"))

    @classmethod
    async def get_todays_transfer_total(cls, db: AsyncSession, user_id: uuid.UUID) -> Decimal:
        """Calculates total outbound transfers & withdrawals executed today (UTC)."""
        wallet = await WalletService.get_wallet_by_user_id(db, user_id)
        now_utc = datetime.now(timezone.utc)
        today_start = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)

        stmt = (
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .join(LedgerEntry, LedgerEntry.transaction_id == Transaction.id)
            .where(
                LedgerEntry.wallet_id == wallet.id,
                LedgerEntry.entry_type == "DEBIT",
                Transaction.created_at >= today_start,
                Transaction.status == "COMPLETED"
            )
        )
        res = await db.execute(stmt)
        return Decimal(str(res.scalar_one()))

    @classmethod
    async def validate_daily_transfer_limit(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        requested_amount: Decimal
    ) -> None:
        """Enforces daily transfer limit according to user's KYC tier."""
        kyc = await cls.get_or_create_kyc(db, user_id)
        daily_limit = cls.get_daily_limit_for_tier(kyc.tier)
        todays_total = await cls.get_todays_transfer_total(db, user_id)

        if todays_total + requested_amount > daily_limit:
            remaining = max(daily_limit - todays_total, Decimal("0.0000"))
            raise ValueError(
                f"Daily limit exceeded for your KYC {kyc.tier}. "
                f"Daily limit: ${daily_limit:.2f}, Used today: ${todays_total:.2f}, "
                f"Remaining limit: ${remaining:.2f}. Submit KYC verification to upgrade your limit."
            )

    @classmethod
    async def submit_kyc(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        kyc_in: KYCSubmitRequest
    ) -> KYCResponse:
        """Submits document verification and upgrades user to TIER_1 limit ($10,000/day)."""
        kyc = await cls.get_or_create_kyc(db, user_id)
        kyc.document_type = kyc_in.document_type.upper()
        kyc.document_number = kyc_in.document_number
        kyc.tier = "TIER_1"
        kyc.verification_status = "APPROVED"

        await db.commit()
        await db.refresh(kyc)

        return KYCResponse(
            id=kyc.id,
            user_id=kyc.user_id,
            tier=kyc.tier,
            document_type=kyc.document_type,
            verification_status=kyc.verification_status,
            daily_limit=cls.get_daily_limit_for_tier(kyc.tier),
            created_at=kyc.created_at,
            updated_at=kyc.updated_at
        )

    @classmethod
    async def get_kyc_response(cls, db: AsyncSession, user_id: uuid.UUID) -> KYCResponse:
        """Converts UserKYC model to KYCResponse schema."""
        kyc = await cls.get_or_create_kyc(db, user_id)
        return KYCResponse(
            id=kyc.id,
            user_id=kyc.user_id,
            tier=kyc.tier,
            document_type=kyc.document_type,
            verification_status=kyc.verification_status,
            daily_limit=cls.get_daily_limit_for_tier(kyc.tier),
            created_at=kyc.created_at,
            updated_at=kyc.updated_at
        )
