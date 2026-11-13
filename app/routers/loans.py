from datetime import date
from decimal import Decimal
from typing import Literal
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.loan import LoanCreate, LoanFilterStatus, LoanResponse
from app.services.loan_service import LoanService

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post("", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(payload: LoanCreate, db: Session = Depends(get_db)):
    service = LoanService(db)
    return service.create_loan(payload)


@router.get("", response_model=PaginatedResponse[LoanResponse])
def list_loans(
    user_id: uuid.UUID | None = Query(
        default=None, description="Filtrar por pessoa relacionada"
    ),
    status: LoanFilterStatus | None = Query(
        default=None,
        description="Filtrar por status do empréstimo (open, in progress, paid, active)",
    ),
    start_date: date | None = Query(
        default=None, description="Data inicial do empréstimo (inclusiva)"
    ),
    end_date: date | None = Query(
        default=None, description="Data final do empréstimo (inclusiva)"
    ),
    min_amount: Decimal | None = Query(
        default=None, gt=0, description="Valor mínimo do principal"
    ),
    max_amount: Decimal | None = Query(
        default=None, gt=0, description="Valor máximo do principal"
    ),
    sort_by: Literal[
        "load_date",
        "principal_amount",
        "total_to_receive",
        "amount_received",
        "status",
    ] = Query(default="load_date", description="Campo de ordenação"),
    order: Literal["asc", "desc"] = Query(
        default="desc", description="Direção da ordenação"
    ),
    page: int = Query(default=1, ge=1, description="Página atual"),
    limit: int = Query(
        default=20, ge=1, le=100, description="Quantidade de registros por página"
    ),
    db: Session = Depends(get_db),
):
    service = LoanService(db)
    return service.list_loans(
        user_id=user_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        sort_by=sort_by,
        order=order,
        page=page,
        limit=limit,
    )


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan(loan_id: uuid.UUID, db: Session = Depends(get_db)):
    service = LoanService(db)
    return service.get_loan(loan_id)
