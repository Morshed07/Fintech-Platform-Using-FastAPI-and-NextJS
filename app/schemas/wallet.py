import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class WalletResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    account_number: str
    balance: Decimal
    currency: str
    status: str
    has_pin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SetPinRequest(BaseModel):
    pin: str = Field(..., min_length=6, max_length=6, description="6-digit numerical security PIN")
    confirm_pin: str = Field(..., min_length=6, max_length=6, description="Confirm 6-digit PIN")

    @field_validator("pin", "confirm_pin")
    @classmethod
    def validate_numerical_pin(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("PIN must contain digits only (0-9)")
        return v

    @field_validator("confirm_pin")
    @classmethod
    def validate_pin_match(cls, v: str, info) -> str:
        if "pin" in info.data and v != info.data["pin"]:
            raise ValueError("PIN and confirm PIN do not match")
        return v


class VerifyPinRequest(BaseModel):
    pin: str = Field(..., min_length=6, max_length=6, description="6-digit numerical security PIN")

    @field_validator("pin")
    @classmethod
    def validate_numerical_pin(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("PIN must contain digits only (0-9)")
        return v
