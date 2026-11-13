from datetime import date
from typing import Literal
import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    service = PaymentService(db)
    return service.create_payment(payload)


@router.get("", response_model=PaginatedResponse[PaymentResponse])
def list_payments(
    installment_id: int | None = Query(
        default=None, description="Filtrar por parcela relacionada"
    ),
    loan_id: uuid.UUID | None = Query(
        default=None, description="Filtrar por empréstimo relacionado"
    ),
    start_date: date | None = Query(
        default=None, description="Data inicial do pagamento (inclusiva)"
    ),
    end_date: date | None = Query(
        default=None, description="Data final do pagamento (inclusiva)"
    ),
    sort_by: Literal["created_at", "received_at", "amount"] = Query(
        default="created_at", description="Campo de ordenação"
    ),
    order: Literal["asc", "desc"] = Query(
        default="desc", description="Direção da ordenação"
    ),
    page: int = Query(default=1, ge=1, description="Página atual"),
    limit: int = Query(
        default=20, ge=1, le=100, description="Quantidade de registros por página"
    ),
    db: Session = Depends(get_db),
):
    service = PaymentService(db)
    return service.list_payments(
        installment_id=installment_id,
        loan_id=loan_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        order=order,
        page=page,
        limit=limit,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: uuid.UUID, db: Session = Depends(get_db)):
    service = PaymentService(db)
    return service.get_payment(payment_id)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(payment_id: uuid.UUID, db: Session = Depends(get_db)):
    service = PaymentService(db)
    service.delete_payment(payment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
