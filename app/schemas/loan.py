from datetime import date
from decimal import Decimal
import enum
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.loan import LoanStatus


class LoanFilterStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in progress"
    PAID = "paid"
    ACTIVE = "active"


class LoanBase(BaseModel):
    loan_request_id: uuid.UUID
    principal_amount: Decimal = Field(..., gt=0)
    total_to_receive: Decimal = Field(..., gt=0)
    amount_received: Decimal = Field(default=Decimal("0.00"), ge=0)
    load_date: date
    notes: str | None = None


class LoanCreate(LoanBase):
    installment_count: int | None = Field(default=None, ge=1)
    first_due_date: date | None = None


class LoanUpdate(BaseModel):
    principal_amount: Decimal | None = Field(default=None, gt=0)
    total_to_receive: Decimal | None = Field(default=None, gt=0)
    amount_received: Decimal | None = Field(default=None, ge=0)
    load_date: date | None = None
    notes: str | None = None
    status: LoanStatus | None = None


class LoanResponse(LoanBase):
    id: uuid.UUID
    status: LoanStatus

    model_config = ConfigDict(from_attributes=True)
