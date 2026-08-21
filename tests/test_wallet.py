import sys
import os
sys.path.insert(0, os.path.abspath("."))

import asyncio
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base
from app.models import User, Wallet, Transaction, LedgerEntry
from app.services.wallet import WalletService
from app.schemas.wallet import SetPinRequest


async def run_tests():
    print("--- Starting Phase 1 Wallet Unit Tests ---")
    
    # In-memory SQLite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as db:
        # 1. Create dummy verified user
        user = User(
            id=uuid.uuid4(),
            full_name="Test User",
            email="testuser@fintech.com",
            password="hashedpassword123",
            is_verified=True,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # 2. Provision Wallet automatically
        wallet = await WalletService.create_user_wallet(db, user.id, currency="USD")
        assert wallet is not None
        assert wallet.user_id == user.id
        assert wallet.balance == Decimal("0.0000")
        assert wallet.account_number.startswith("ACC-")
        assert len(wallet.account_number) == 14
        print(f"[SUCCESS] Wallet created with Account Number: {wallet.account_number}")
        
        # 3. Retrieve Wallet by User ID
        fetched_wallet = await WalletService.get_wallet_by_user_id(db, user.id)
        assert fetched_wallet.id == wallet.id
        print(f"[SUCCESS] Wallet fetched successfully by user ID")
        
        # 4. Set Transaction PIN
        pin_req = SetPinRequest(pin="123456", confirm_pin="123456")
        pin_res = await WalletService.set_transaction_pin(db, user.id, pin_req)
        assert "successfully" in pin_res.message
        
        # Re-fetch wallet and verify PIN
        updated_wallet = await WalletService.get_wallet_by_user_id(db, user.id)
        assert WalletService.verify_transaction_pin(updated_wallet, "123456") is True
        assert WalletService.verify_transaction_pin(updated_wallet, "654321") is False
        print(f"[SUCCESS] 6-digit transaction PIN set and verified successfully")

    print("--- Phase 1 Tests Completed Successfully ---")


if __name__ == "__main__":
    asyncio.run(run_tests())
