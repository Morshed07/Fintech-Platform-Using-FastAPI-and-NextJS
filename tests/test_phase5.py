import sys
import os
sys.path.insert(0, os.path.abspath("."))

import asyncio
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base
from app.models import User
from app.services.wallet import WalletService
from app.services.transfer import TransferService
from app.services.kyc import KYCService
from app.services.audit import AuditService
from app.schemas.wallet import SetPinRequest
from app.schemas.transfer import P2PTransferRequest
from app.schemas.kyc import KYCSubmitRequest


async def run_tests():
    print("--- Starting Phase 5 KYC Tiers, Audit Logs & System Health Unit Tests ---")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # 1. Create User A & User B
        user_a = User(id=uuid.uuid4(), full_name="User KYC Alice", email="kycalice@fintech.com", password="pwd", is_verified=True)
        user_b = User(id=uuid.uuid4(), full_name="User KYC Bob", email="kycbob@fintech.com", password="pwd", is_verified=True)
        db.add_all([user_a, user_b])
        await db.commit()

        # Provision wallets with $5,000 balance each
        wallet_a = await WalletService.create_user_wallet(db, user_a.id)
        wallet_b = await WalletService.create_user_wallet(db, user_b.id)
        wallet_a.balance = Decimal("5000.0000")
        wallet_b.balance = Decimal("5000.0000")
        await db.commit()

        await WalletService.set_transaction_pin(db, user_a.id, SetPinRequest(pin="111111", confirm_pin="111111"))

        # 2. Check Default TIER_0 ($1,000/day limit)
        kyc_a = await KYCService.get_or_create_kyc(db, user_a.id)
        assert kyc_a.tier == "TIER_0"
        assert KYCService.get_daily_limit_for_tier(kyc_a.tier) == Decimal("1000.0000")
        print("[SUCCESS] Initial KYC Tier: TIER_0 ($1,000.00 / day limit)")

        # 3. Test Transfer exceeding TIER_0 limit ($1,500 > $1,000)
        try:
            exceed_req = P2PTransferRequest(recipient_account_number=wallet_b.account_number, amount=Decimal("1500.0000"), pin="111111")
            await TransferService.execute_p2p_transfer(db, user_a.id, exceed_req)
            assert False, "Should fail due to KYC TIER_0 daily limit"
        except ValueError as e:
            assert "Daily limit exceeded for your KYC TIER_0" in str(e)
            print(f"[SUCCESS] TIER_0 daily limit enforced correctly: '{e}'")

        # 4. Upgrade KYC to TIER_1 ($10,000/day limit)
        kyc_sub = KYCSubmitRequest(document_type="PASSPORT", document_number="A12345678")
        kyc_res = await KYCService.submit_kyc(db, user_a.id, kyc_sub)
        assert kyc_res.tier == "TIER_1"
        assert kyc_res.daily_limit == Decimal("10000.0000")
        print("[SUCCESS] KYC document submitted. Upgraded to TIER_1 ($10,000.00 / day limit)")

        # 5. Execute $1,500 Transfer under TIER_1 (Should now succeed)
        valid_req = P2PTransferRequest(recipient_account_number=wallet_b.account_number, amount=Decimal("1500.0000"), pin="111111")
        txn = await TransferService.execute_p2p_transfer(db, user_a.id, valid_req)
        assert txn.status == "COMPLETED"
        print(f"[SUCCESS] $1,500 transfer succeeded under TIER_1. Reference: {txn.reference_id}")

        # 6. Verify Audit Log Recording
        await AuditService.log_action(db, user_a.id, "KYC_UPGRADE", details="Upgraded to TIER_1")
        logs = await AuditService.get_user_logs(db, user_a.id)
        assert len(logs) > 0
        assert logs[0].action == "KYC_UPGRADE"
        print(f"[SUCCESS] Audit log recorded and retrieved successfully ({len(logs)} logs found)")

    print("--- Phase 5 Tests Completed Successfully ---")


if __name__ == "__main__":
    asyncio.run(run_tests())
