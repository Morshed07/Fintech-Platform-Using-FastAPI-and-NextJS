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
from app.services.transfer import TransferService
from app.schemas.wallet import SetPinRequest
from app.schemas.transfer import P2PTransferRequest


async def run_tests():
    print("--- Starting Phase 3 P2P Transfer & Double-Entry Bookkeeping Unit Tests ---")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # 1. Create User A (Sender) & User B (Recipient)
        user_a = User(id=uuid.uuid4(), full_name="User Alice", email="alice@fintech.com", password="pwd", is_verified=True)
        user_b = User(id=uuid.uuid4(), full_name="User Bob", email="bob@fintech.com", password="pwd", is_verified=True)
        db.add_all([user_a, user_b])
        await db.commit()

        # 2. Provision Wallets
        wallet_a = await WalletService.create_user_wallet(db, user_a.id)
        wallet_b = await WalletService.create_user_wallet(db, user_b.id)

        # Set initial balances for testing: Alice = $500.00, Bob = $100.00
        wallet_a.balance = Decimal("500.0000")
        wallet_b.balance = Decimal("100.0000")
        await db.commit()

        # Set 6-digit transaction PIN for Alice
        await WalletService.set_transaction_pin(db, user_a.id, SetPinRequest(pin="123456", confirm_pin="123456"))

        print(f"Alice Initial Balance: ${wallet_a.balance:.2f} (Account: {wallet_a.account_number})")
        print(f"Bob Initial Balance:   ${wallet_b.balance:.2f} (Account: {wallet_b.account_number})")

        # 3. Test Invalid PIN Error
        try:
            req_invalid_pin = P2PTransferRequest(recipient_account_number=wallet_b.account_number, amount=Decimal("50.00"), pin="999999")
            await TransferService.execute_p2p_transfer(db, user_a.id, req_invalid_pin)
            assert False, "Should fail with invalid PIN"
        except ValueError as e:
            assert "Invalid 6-digit transaction PIN" in str(e)
            print(f"[SUCCESS] Invalid PIN caught correctly: '{e}'")

        # 4. Test Insufficient Funds Error
        try:
            req_overdraft = P2PTransferRequest(recipient_account_number=wallet_b.account_number, amount=Decimal("1000.00"), pin="123456")
            await TransferService.execute_p2p_transfer(db, user_a.id, req_overdraft)
            assert False, "Should fail with insufficient funds"
        except ValueError as e:
            assert "Insufficient funds" in str(e)
            print(f"[SUCCESS] Insufficient funds caught correctly: '{e}'")

        # 5. Test Successful P2P Transfer ($150.00 from Alice to Bob)
        transfer_req = P2PTransferRequest(
            recipient_account_number=wallet_b.account_number,
            amount=Decimal("150.0000"),
            pin="123456",
            description="Lunch split"
        )

        txn = await TransferService.execute_p2p_transfer(db, user_a.id, transfer_req)
        assert txn is not None
        assert txn.status == "COMPLETED"
        assert txn.amount == Decimal("150.0000")
        assert txn.reference_id.startswith("TXN-")
        print(f"[SUCCESS] Transaction executed with Reference: {txn.reference_id}")

        # 6. Verify Balances
        w_a_updated = await WalletService.get_wallet_by_user_id(db, user_a.id)
        w_b_updated = await WalletService.get_wallet_by_user_id(db, user_b.id)
        assert w_a_updated.balance == Decimal("350.0000")
        assert w_b_updated.balance == Decimal("250.0000")
        print(f"[SUCCESS] Alice New Balance: ${w_a_updated.balance:.2f} (Deducted $150.00)")
        print(f"[SUCCESS] Bob New Balance:   ${w_b_updated.balance:.2f} (Credited $150.00)")

        # 7. Verify Double-Entry Bookkeeping Ledger Integrity
        assert len(txn.ledger_entries) == 2
        debit_entry = next(e for e in txn.ledger_entries if e.entry_type == "DEBIT")
        credit_entry = next(e for e in txn.ledger_entries if e.entry_type == "CREDIT")

        assert debit_entry.amount == Decimal("-150.0000")
        assert debit_entry.balance_after == Decimal("350.0000")

        assert credit_entry.amount == Decimal("150.0000")
        assert credit_entry.balance_after == Decimal("250.0000")

        # Double-entry balance check: Debit + Credit = 0
        assert (debit_entry.amount + credit_entry.amount) == Decimal("0.0000")
        print("[SUCCESS] Double-Entry Ledger Bookkeeping verified (Debit + Credit = $0.00)")

    print("--- Phase 3 Tests Completed Successfully ---")


if __name__ == "__main__":
    asyncio.run(run_tests())
