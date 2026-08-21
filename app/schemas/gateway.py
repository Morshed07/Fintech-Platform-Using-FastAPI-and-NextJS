from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class DepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0.0000"), description="Deposit amount (must be > 0)")
    payment_method: str = Field("CARD", description="Payment method: CARD, BANK_TRANSFER, GATEWAY")
    description: str | None = Field(None, max_length=255, description="Optional note")


class WithdrawalRequest(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0.0000"), description="Withdrawal amount (must be > 0)")
    pin: str = Field(..., min_length=6, max_length=6, description="6-digit security transaction PIN")
    bank_account_number: str = Field(..., min_length=5, max_length=30, description="Recipient bank account number")
    bank_code: str = Field(..., min_length=2, max_length=20, description="Bank routing code/swift code")
    description: str | None = Field(None, max_length=255, description="Optional note")

    @field_validator("pin")
    @classmethod
    def validate_numerical_pin(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("PIN must contain 6 digits only")
        return v


class WebhookPayload(BaseModel):
    event_id: str
    event_type: str  # deposit.succeeded, deposit.failed, withdrawal.succeeded
    reference_id: str
    account_number: str
    amount: Decimal
    currency: str = "USD"
