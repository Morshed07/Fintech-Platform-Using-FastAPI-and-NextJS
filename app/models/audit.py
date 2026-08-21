import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )  # e.g. LOGIN, P2P_TRANSFER, PIN_SET, WITHDRAWAL, DEPOSIT, KYC_SUBMIT

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})"


class UserKYC(Base):
    __tablename__ = "user_kyc"

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

    tier: Mapped[str] = mapped_column(
        String(20),
        default="TIER_0",
        nullable=False
    )  # TIER_0 ($1k/day), TIER_1 ($10k/day), TIER_2 ($100k/day)

    document_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )  # PASSPORT, DRIVERS_LICENSE, NID

    document_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    verification_status: Mapped[str] = mapped_column(
        String(20),
        default="APPROVED",
        nullable=False
    )  # PENDING, APPROVED, REJECTED

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

    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"UserKYC(user_id={self.user_id}, tier={self.tier}, status={self.verification_status})"
