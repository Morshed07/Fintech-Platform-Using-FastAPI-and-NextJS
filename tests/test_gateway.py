import sys
import os
sys.path.insert(0, os.path.abspath("."))

import asyncio
import json
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base
from app.models import User
from app.services.wallet import WalletService
from app.services.deposit_withdrawal import DepositWithdrawalService
from app.schemas.wallet import SetPinRequest
from app.schemas.gateway import DepositRequest, WithdrawalRequest


async def run_tests():
    print("--- Starting Phase 4 Deposits, Withdrawals & Webhooks Unit Tests ---")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # 1. Create user and provision wallet
        user = User(id=uuid.uuid4(), full_name="Charlie Gateway", email="charlie@fintech.com", password="pwd", is_verified=True)
        db.add(user)
        await db.commit()

        wallet = await WalletService.create_user_wallet(db, user.id)
        assert wallet.balance == Decimal("0.0000")

        # Set 6-digit transaction PIN
        await WalletService.set_transaction_pin(db, user.id, SetPinRequest(pin="654321", confirm_pin="654321"))

        # 2. Test Deposit ($300.00)
        dep_req = DepositRequest(amount=Decimal("300.0000"), payment_method="CARD", description="Test Deposit")
        dep_txn = await DepositWithdrawalService.process_deposit(db, user.id, dep_req)
        assert dep_txn.status == "COMPLETED"
        assert dep_txn.amount == Decimal("300.0000")

        wallet = await WalletService.get_wallet_by_user_id(db, user.id)
        assert wallet.balance == Decimal("300.0000")
        print(f"[SUCCESS] Deposit processed. New Balance: ${wallet.balance:.2f}")

        # 3. Test Withdrawal ($100.00)
        with_req = WithdrawalRequest(
            amount=Decimal("100.0000"),
            pin="654321",
            bank_account_number="9876543210",
            bank_code="CHASE-NY"
        )
        with_txn = await DepositWithdrawalService.process_withdrawal(db, user.id, with_req)
        assert with_txn.status == "COMPLETED"

        wallet = await WalletService.get_wallet_by_user_id(db, user.id)
        assert wallet.balance == Decimal("200.0000")
        print(f"[SUCCESS] Withdrawal processed. New Balance: ${wallet.balance:.2f}")

        # 4. Test HMAC-SHA256 Webhook Verification
        secret = "super-secret-webhook-key-2026"
        webhook_data = {
            "event_id": "evt_1001",
            "event_type": "deposit.succeeded",
            "reference_id": "TXN-WEBHOOK-001",
            "account_number": wallet.account_number,
            "amount": "50.0000",
            "currency": "USD"
        }
        payload_bytes = json.dumps(webhook_data).encode("utf-8")
        signature = DepositWithdrawalService.generate_hmac_signature(payload_bytes, secret)

        # Process valid webhook
        wh_res = await DepositWithdrawalService.process_gateway_webhook(db, payload_bytes, signature)
        assert "processed successfully" in wh_res.message

        wallet = await WalletService.get_wallet_by_user_id(db, user.id)
        assert wallet.balance == Decimal("250.0000")
        print(f"[SUCCESS] Webhook deposit processed with valid HMAC signature. New Balance: ${wallet.balance:.2f}")

        # Test invalid HMAC signature rejection
        try:
            await DepositWithdrawalService.process_gateway_webhook(db, payload_bytes, "invalid-signature-hash")
            assert False, "Should fail with invalid signature"
        except ValueError as e:
            assert "Invalid or missing HMAC-SHA256 signature" in str(e)
            print(f"[SUCCESS] Invalid HMAC signature correctly rejected: '{e}'")

    print("--- Phase 4 Tests Completed Successfully ---")


if __name__ == "__main__":
    asyncio.run(run_tests())
