import uuid
import secrets
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.wallet import Wallet
from app.schemas.wallet import WalletResponse, SetPinRequest
from app.schemas.auth import MessageResponse
from app.core.security import hash_password, verify_password


class WalletService:

    @staticmethod
    def generate_account_number() -> str:
        """Generates a unique 10-digit account number prefixed with ACC-."""
        digits = "".join([str(secrets.randbelow(10)) for _ in range(10)])
        return f"ACC-{digits}"

    @classmethod
    async def create_user_wallet(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        currency: str = "USD"
    ) -> Wallet:
        """Creates a primary wallet for a user if one does not already exist."""
        result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
        existing_wallet = result.scalar_one_or_none()

        if existing_wallet:
            return existing_wallet

        # Ensure account number uniqueness
        account_number = cls.generate_account_number()
        while True:
            check_res = await db.execute(select(Wallet).where(Wallet.account_number == account_number))
            if check_res.scalar_one_or_none() is None:
                break
            account_number = cls.generate_account_number()

        wallet = Wallet(
            user_id=user_id,
            account_number=account_number,
            balance=Decimal("0.0000"),
            currency=currency,
            status="ACTIVE"
        )
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
        return wallet

    @classmethod
    async def get_wallet_by_user_id(cls, db: AsyncSession, user_id: uuid.UUID) -> Wallet:
        """Retrieves wallet for the given user ID."""
        result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
        wallet = result.scalar_one_or_none()
        if not wallet:
            # Auto-provision wallet if missing for verified user
            wallet = await cls.create_user_wallet(db, user_id)
        return wallet

    @classmethod
    async def get_wallet_response(cls, wallet: Wallet) -> WalletResponse:
        """Converts Wallet model to WalletResponse schema."""
        return WalletResponse(
            id=wallet.id,
            user_id=wallet.user_id,
            account_number=wallet.account_number,
            balance=wallet.balance,
            currency=wallet.currency,
            status=wallet.status,
            has_pin=wallet.pin_hash is not None,
            created_at=wallet.created_at,
            updated_at=wallet.updated_at
        )

    @classmethod
    async def set_transaction_pin(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        pin_in: SetPinRequest
    ) -> MessageResponse:
        """Hashes and sets 6-digit numerical security transaction PIN for the wallet."""
        wallet = await cls.get_wallet_by_user_id(db, user_id)
        wallet.pin_hash = hash_password(pin_in.pin)
        await db.commit()
        return MessageResponse(message="Transaction PIN has been set successfully.")

    @staticmethod
    def verify_transaction_pin(wallet: Wallet, pin: str) -> bool:
        """Validates plain text PIN against stored hash."""
        if not wallet.pin_hash:
            return False
        return verify_password(pin, wallet.pin_hash)
