from datetime import date
from typing import Literal
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.installment import (
    InstallmentFilterStatus,
    InstallmentResponse,
    InstallmentUpdate,
)
from app.services.installment_service import InstallmentService

router = APIRouter(prefix="/installments", tags=["Installments"])


@router.get("", response_model=PaginatedResponse[InstallmentResponse])
def list_installments(
    loan_id: uuid.UUID | None = Query(
        default=None, description="Filtrar por empréstimo relacionado"
    ),
    status: InstallmentFilterStatus | None = Query(
        default=None,
        description="Status (open, partially_paid, paid, pending, overdue)",
    ),
    start_date: date | None = Query(
        default=None, description="Data inicial de vencimento (inclusiva)"
    ),
    end_date: date | None = Query(
        default=None, description="Data final de vencimento (inclusiva)"
    ),
    sort_by: Literal[
        "due_date", "number", "amount", "created_at", "status"
    ] = Query(default="due_date", description="Campo de ordenação"),
    order: Literal["asc", "desc"] = Query(
        default="asc", description="Direção da ordenação"
    ),
    page: int = Query(default=1, ge=1, description="Página atual"),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Quantidade de registros por página",
    ),
    db: Session = Depends(get_db),
):
    service = InstallmentService(db)
    return service.list_installments(
        loan_id=loan_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        order=order,
        page=page,
        limit=limit,
    )


@router.get("/{installment_id}", response_model=InstallmentResponse)
def get_installment(installment_id: int, db: Session = Depends(get_db)):
    service = InstallmentService(db)
    return service.get_installment(installment_id)


@router.patch("/{installment_id}", response_model=InstallmentResponse)
def update_installment(
    installment_id: int,
    payload: InstallmentUpdate,
    db: Session = Depends(get_db),
):
    service = InstallmentService(db)
    return service.update_installment(installment_id, payload)
