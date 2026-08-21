import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    account_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0.0000"),
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="ACTIVE",
        nullable=False
    )

    pin_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="wallet")

    def __repr__(self) -> str:
        return f"Wallet(id={self.id}, account_number={self.account_number}, balance={self.balance}, currency={self.currency})"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    reference_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True
    )

    transaction_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )  # P2P_TRANSFER, DEPOSIT, WITHDRAWAL, FEE

    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False
    )  # PENDING, COMPLETED, FAILED

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    ledger_entries: Mapped[list["LedgerEntry"]] = relationship("LedgerEntry", back_populates="transaction", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Transaction(id={self.id}, reference_id={self.reference_id}, type={self.transaction_type}, amount={self.amount})"


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    entry_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )  # DEBIT, CREDIT

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )

    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="ledger_entries")
    wallet: Mapped["Wallet"] = relationship("Wallet")

    def __repr__(self) -> str:
        return f"LedgerEntry(id={self.id}, entry_type={self.entry_type}, amount={self.amount}, balance_after={self.balance_after})"
