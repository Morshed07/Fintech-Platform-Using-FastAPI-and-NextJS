import uuid
import secrets
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.wallet import Wallet, Transaction, LedgerEntry
from app.schemas.transfer import P2PTransferRequest, TransactionHistoryQuery
from app.services.wallet import WalletService
from app.services.kyc import KYCService
from app.services.audit import AuditService


class TransferService:

    @staticmethod
    def generate_reference_id() -> str:
        """Generates a unique transaction reference code (e.g. TXN-20260821-9X82F4A1)."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_suffix = "".join(secrets.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(8))
        return f"TXN-{date_str}-{random_suffix}"

    @classmethod
    async def execute_p2p_transfer(
        cls,
        db: AsyncSession,
        sender_user_id: uuid.UUID,
        transfer_in: P2PTransferRequest,
        idempotency_key: str | None = None
    ) -> Transaction:
        """Executes atomic P2P transfer with row locking and double-entry bookkeeping."""
        
        # 1. Fetch sender wallet
        sender_wallet = await WalletService.get_wallet_by_user_id(db, sender_user_id)
        if sender_wallet.status != "ACTIVE":
            raise ValueError("Sender wallet is inactive or frozen")

        # 2. Verify transaction PIN
        if not WalletService.verify_transaction_pin(sender_wallet, transfer_in.pin):
            raise ValueError("Invalid 6-digit transaction PIN")

        # 3. Fetch recipient wallet
        res = await db.execute(select(Wallet).where(Wallet.account_number == transfer_in.recipient_account_number))
        recipient_wallet = res.scalar_one_or_none()
        if not recipient_wallet:
            raise ValueError(f"Recipient account '{transfer_in.recipient_account_number}' not found")

        if recipient_wallet.status != "ACTIVE":
            raise ValueError("Recipient account is currently inactive or frozen")

        # 4. Check transfer to self
        if sender_wallet.id == recipient_wallet.id:
            raise ValueError("Cannot transfer funds to your own wallet account")

        # 5. Row-level locking for concurrency protection (dialect-aware)
        dialect_name = db.bind.dialect.name if db.bind else "sqlite"
        if dialect_name != "sqlite":
            # Apply row-level locking on PostgreSQL / MySQL
            sender_stmt = select(Wallet).where(Wallet.id == sender_wallet.id).with_for_update()
            recipient_stmt = select(Wallet).where(Wallet.id == recipient_wallet.id).with_for_update()
            await db.execute(sender_stmt)
            await db.execute(recipient_stmt)

        # 6. Check sender balance & KYC daily transfer limits
        if sender_wallet.balance < transfer_in.amount:
            raise ValueError(f"Insufficient funds. Wallet balance: ${sender_wallet.balance:.2f}")

        await KYCService.validate_daily_transfer_limit(db, sender_user_id, transfer_in.amount)

        # 7. Generate reference ID
        reference_id = cls.generate_reference_id()
        while True:
            ref_check = await db.execute(select(Transaction).where(Transaction.reference_id == reference_id))
            if ref_check.scalar_one_or_none() is None:
                break
            reference_id = cls.generate_reference_id()

        # 8. Perform Double-Entry Ledger Operations
        sender_wallet.balance -= transfer_in.amount
        recipient_wallet.balance += transfer_in.amount

        # Create Transaction
        transaction = Transaction(
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            transaction_type="P2P_TRANSFER",
            status="COMPLETED",
            amount=transfer_in.amount,
            currency=sender_wallet.currency,
            description=transfer_in.description or f"P2P Transfer to {recipient_wallet.account_number}"
        )
        db.add(transaction)
        await db.flush()

        # Create DEBIT Ledger Entry for Sender (negative amount)
        debit_entry = LedgerEntry(
            transaction_id=transaction.id,
            wallet_id=sender_wallet.id,
            entry_type="DEBIT",
            amount=-transfer_in.amount,
            balance_after=sender_wallet.balance
        )

        # Create CREDIT Ledger Entry for Recipient (positive amount)
        credit_entry = LedgerEntry(
            transaction_id=transaction.id,
            wallet_id=recipient_wallet.id,
            entry_type="CREDIT",
            amount=transfer_in.amount,
            balance_after=recipient_wallet.balance
        )

        db.add(debit_entry)
        db.add(credit_entry)

        # Verify Double-Entry Accounting Constraint
        assert (debit_entry.amount + credit_entry.amount) == Decimal("0.0000"), "Ledger entries are not balanced!"

        await db.commit()

        # Re-query transaction with ledger entries
        res = await db.execute(
            select(Transaction)
            .where(Transaction.id == transaction.id)
            .options(selectinload(Transaction.ledger_entries))
        )
        return res.scalar_one()

    @classmethod
    async def get_transaction_history(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        query: TransactionHistoryQuery
    ) -> tuple[list[Transaction], int]:
        """Fetches paginated transaction history for a user's wallet."""
        wallet = await WalletService.get_wallet_by_user_id(db, user_id)

        # Subquery finding transaction IDs linked to user's wallet via ledger entries
        ledger_subq = select(LedgerEntry.transaction_id).where(LedgerEntry.wallet_id == wallet.id)

        stmt = select(Transaction).where(Transaction.id.in_(ledger_subq)).options(selectinload(Transaction.ledger_entries))

        if query.transaction_type:
            stmt = stmt.where(Transaction.transaction_type == query.transaction_type)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        # Apply ordering and pagination
        stmt = stmt.order_by(Transaction.created_at.desc())
        offset = (query.page - 1) * query.size
        stmt = stmt.offset(offset).limit(query.size)

        result = await db.execute(stmt)
        transactions = list(result.scalars().all())

        return transactions, total

    @classmethod
    async def get_transaction_by_id(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        transaction_id: uuid.UUID
    ) -> Transaction:
        """Retrieves single transaction receipt if user is authorized."""
        wallet = await WalletService.get_wallet_by_user_id(db, user_id)

        # Check user wallet is part of transaction
        stmt = (
            select(Transaction)
            .join(LedgerEntry)
            .where(Transaction.id == transaction_id, LedgerEntry.wallet_id == wallet.id)
            .options(selectinload(Transaction.ledger_entries))
        )
        res = await db.execute(stmt)
        transaction = res.scalar_one_or_none()
        if not transaction:
            raise ValueError("Transaction receipt not found or access denied")
        return transaction
