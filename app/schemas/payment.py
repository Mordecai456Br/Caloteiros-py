from datetime import date, datetime
from decimal import Decimal
import uuid

from pydantic import BaseModel, ConfigDict, Field


class PaymentBase(BaseModel):
    installment_id: int
    amount: Decimal = Field(..., gt=0)
    received_at: date | None = None
    receipt_key: str
    description: str | None = None
    sender_pix_key: str


class PaymentCreate(PaymentBase):
    loan_id: uuid.UUID | None = None


class PaymentUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    received_at: date | None = None
    receipt_key: str | None = None
    description: str | None = None
    sender_pix_key: str | None = None


class PaymentResponse(PaymentBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
