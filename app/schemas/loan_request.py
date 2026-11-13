from datetime import date, datetime
from decimal import Decimal
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.loan_request import LoanRequestStatus


class LoanRequestBase(BaseModel):
    user_id: uuid.UUID
    request_amount: Decimal = Field(..., gt=0)
    pix_key: str
    installment_count: int | None = Field(default=None, ge=1)
    first_due_date: date | None = None
    description: str | None = None


class LoanRequestCreate(LoanRequestBase):
    pass


class LoanRequestUpdate(BaseModel):
    """Atualização dos dados da solicitação (status é alterado apenas via /approve ou /deny)."""

    request_amount: Decimal | None = Field(default=None, gt=0)
    pix_key: str | None = None
    installment_count: int | None = Field(default=None, ge=1)
    first_due_date: date | None = None
    description: str | None = None


class LoanRequestApprovePayload(BaseModel):
    """Parâmetros opcionais para personalizar o Loan criado no momento da aprovação."""

    total_to_receive: Decimal | None = Field(default=None, gt=0)
    load_date: date | None = None
    installment_count: int | None = Field(default=None, ge=1)
    first_due_date: date | None = None
    notes: str | None = None


class LoanRequestResponse(LoanRequestBase):
    id: uuid.UUID
    status: LoanRequestStatus
    created_at: datetime
    approved_at: datetime | None = None
    denied_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
