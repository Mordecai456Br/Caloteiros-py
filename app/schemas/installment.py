from datetime import date, datetime
from decimal import Decimal
import enum
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.installment import InstallmentStatus


class InstallmentFilterStatus(str, enum.Enum):
    OPEN = "open"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    PENDING = "pending"
    OVERDUE = "overdue"


class InstallmentBase(BaseModel):
    loan_id: uuid.UUID
    number: int = Field(..., ge=1)
    amount: Decimal = Field(..., gt=0)
    due_date: date
    status: InstallmentStatus = InstallmentStatus.OPEN


class InstallmentCreate(InstallmentBase):
    pass


class InstallmentUpdate(BaseModel):
    """Permite atualizar vencimento ou valor da parcela."""

    amount: Decimal | None = Field(default=None, gt=0)
    due_date: date | None = None


class InstallmentResponse(InstallmentBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
