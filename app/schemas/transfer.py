import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class P2PTransferRequest(BaseModel):
    recipient_account_number: str = Field(..., description="10-digit recipient account number (e.g. ACC-XXXXXXXXXX)")
    amount: Decimal = Field(..., gt=Decimal("0.0000"), description="Transfer amount (must be > 0)")
    pin: str = Field(..., min_length=6, max_length=6, description="6-digit transaction PIN")
    description: str | None = Field(None, max_length=255, description="Optional description/note")

    @field_validator("recipient_account_number")
    @classmethod
    def validate_account_number(cls, v: str) -> str:
        clean_v = v.strip().upper()
        if not clean_v.startswith("ACC-"):
            raise ValueError("Account number must start with ACC-")
        return clean_v

    @field_validator("pin")
    @classmethod
    def validate_numerical_pin(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("PIN must contain 6 digits only")
        return v


class LedgerEntryResponse(BaseModel):
    id: uuid.UUID
    wallet_id: uuid.UUID
    entry_type: str  # DEBIT or CREDIT
    amount: Decimal
    balance_after: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    id: uuid.UUID
    reference_id: str
    idempotency_key: str | None
    transaction_type: str
    status: str
    amount: Decimal
    currency: str
    description: str | None
    created_at: datetime
    ledger_entries: list[LedgerEntryResponse] = []

    class Config:
        from_attributes = True


class TransactionHistoryQuery(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Items per page")
    transaction_type: str | None = Field(None, description="Filter by type: P2P_TRANSFER, DEPOSIT, WITHDRAWAL")


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    size: int
