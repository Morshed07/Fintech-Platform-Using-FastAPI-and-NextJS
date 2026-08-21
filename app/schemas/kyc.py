import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field


class KYCSubmitRequest(BaseModel):
    document_type: str = Field(..., description="Document type: PASSPORT, DRIVERS_LICENSE, NID")
    document_number: str = Field(..., min_length=4, max_length=100, description="Document identification number")


class KYCResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tier: str  # TIER_0, TIER_1, TIER_2
    document_type: str | None
    verification_status: str  # PENDING, APPROVED, REJECTED
    daily_limit: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
