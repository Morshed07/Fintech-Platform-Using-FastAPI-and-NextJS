import uuid
import hmac
import hashlib
import json
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.wallet import Wallet, Transaction, LedgerEntry
from app.schemas.gateway import DepositRequest, WithdrawalRequest, WebhookPayload
from app.schemas.auth import MessageResponse
from app.services.wallet import WalletService
from app.services.transfer import TransferService


class DepositWithdrawalService:
    WEBHOOK_SECRET = getattr(settings, "WEBHOOK_SECRET", "super-secret-webhook-key-2026")

    @classmethod
    async def process_deposit(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        deposit_in: DepositRequest
    ) -> Transaction:
        """Processes deposit into user wallet and creates CREDIT ledger entry."""
        wallet = await WalletService.get_wallet_by_user_id(db, user_id)
        if wallet.status != "ACTIVE":
            raise ValueError("Wallet is inactive or frozen")

        reference_id = TransferService.generate_reference_id()

        # Update wallet balance
        wallet.balance += deposit_in.amount

        # Create Transaction
        transaction = Transaction(
            reference_id=reference_id,
            transaction_type="DEPOSIT",
            status="COMPLETED",
            amount=deposit_in.amount,
            currency=wallet.currency,
            description=deposit_in.description or f"Deposit via {deposit_in.payment_method}"
        )
        db.add(transaction)
        await db.flush()

        # Create CREDIT Ledger Entry
        credit_entry = LedgerEntry(
            transaction_id=transaction.id,
            wallet_id=wallet.id,
            entry_type="CREDIT",
            amount=deposit_in.amount,
            balance_after=wallet.balance
        )
        db.add(credit_entry)

        await db.commit()

        # Re-query transaction with ledger entries
        res = await db.execute(
            select(Transaction)
            .where(Transaction.id == transaction.id)
            .options(selectinload(Transaction.ledger_entries))
        )
        return res.scalar_one()

    @classmethod
    async def process_withdrawal(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        withdraw_in: WithdrawalRequest
    ) -> Transaction:
        """Processes withdrawal from user wallet and creates DEBIT ledger entry."""
        wallet = await WalletService.get_wallet_by_user_id(db, user_id)
        if wallet.status != "ACTIVE":
            raise ValueError("Wallet is inactive or frozen")

        # Verify transaction PIN
        if not WalletService.verify_transaction_pin(wallet, withdraw_in.pin):
            raise ValueError("Invalid 6-digit transaction PIN")

        # Check balance
        if wallet.balance < withdraw_in.amount:
            raise ValueError(f"Insufficient funds for withdrawal. Balance: ${wallet.balance:.2f}")

        reference_id = TransferService.generate_reference_id()

        # Update wallet balance
        wallet.balance -= withdraw_in.amount

        # Create Transaction
        transaction = Transaction(
            reference_id=reference_id,
            transaction_type="WITHDRAWAL",
            status="COMPLETED",
            amount=withdraw_in.amount,
            currency=wallet.currency,
            description=withdraw_in.description or f"Withdrawal to Bank {withdraw_in.bank_account_number} ({withdraw_in.bank_code})"
        )
        db.add(transaction)
        await db.flush()

        # Create DEBIT Ledger Entry (negative amount)
        debit_entry = LedgerEntry(
            transaction_id=transaction.id,
            wallet_id=wallet.id,
            entry_type="DEBIT",
            amount=-withdraw_in.amount,
            balance_after=wallet.balance
        )
        db.add(debit_entry)

        await db.commit()

        # Re-query transaction with ledger entries
        res = await db.execute(
            select(Transaction)
            .where(Transaction.id == transaction.id)
            .options(selectinload(Transaction.ledger_entries))
        )
        return res.scalar_one()

    @classmethod
    def generate_hmac_signature(cls, payload_bytes: bytes, secret: str | None = None) -> str:
        """Computes HMAC-SHA256 signature string for a webhook payload."""
        sec = secret or cls.WEBHOOK_SECRET
        return hmac.new(sec.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    @classmethod
    def verify_hmac_signature(cls, payload_bytes: bytes, signature_header: str, secret: str | None = None) -> bool:
        """Verifies HMAC-SHA256 signature header against computed signature."""
        expected_sig = cls.generate_hmac_signature(payload_bytes, secret)
        return hmac.compare_digest(expected_sig.lower(), signature_header.lower())

    @classmethod
    async def process_gateway_webhook(
        cls,
        db: AsyncSession,
        payload_bytes: bytes,
        signature_header: str
    ) -> MessageResponse:
        """Processes payment gateway webhook callbacks after verifying HMAC-SHA256 signature."""
        if not signature_header or not cls.verify_hmac_signature(payload_bytes, signature_header):
            raise ValueError("Invalid or missing HMAC-SHA256 signature")

        try:
            event_data = json.loads(payload_bytes.decode("utf-8"))
            payload = WebhookPayload(**event_data)
        except Exception:
            raise ValueError("Invalid JSON webhook payload format")

        # Fetch wallet by account_number
        res = await db.execute(select(Wallet).where(Wallet.account_number == payload.account_number))
        wallet = res.scalar_one_or_none()
        if not wallet:
            raise ValueError(f"Target account '{payload.account_number}' not found")

        if payload.event_type == "deposit.succeeded":
            wallet.balance += payload.amount
            txn = Transaction(
                reference_id=payload.reference_id,
                transaction_type="DEPOSIT",
                status="COMPLETED",
                amount=payload.amount,
                currency=wallet.currency,
                description=f"Webhook Deposit Event: {payload.event_id}"
            )
            db.add(txn)
            await db.flush()
            ledger = LedgerEntry(
                transaction_id=txn.id,
                wallet_id=wallet.id,
                entry_type="CREDIT",
                amount=payload.amount,
                balance_after=wallet.balance
            )
            db.add(ledger)
            await db.commit()
            return MessageResponse(message=f"Webhook deposit of ${payload.amount:.2f} processed successfully.")

        return MessageResponse(message=f"Webhook event '{payload.event_type}' received.")
