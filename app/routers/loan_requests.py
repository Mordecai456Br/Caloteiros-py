from datetime import date
from typing import Literal
import uuid

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.loan_request import LoanRequestStatus
from app.schemas.common import PaginatedResponse
from app.schemas.loan_request import (
    LoanRequestApprovePayload,
    LoanRequestCreate,
    LoanRequestResponse,
    LoanRequestUpdate,
)
from app.services.loan_request_service import LoanRequestService

router = APIRouter(prefix="/loan-requests", tags=["Loan Requests"])


@router.post(
    "", response_model=LoanRequestResponse, status_code=status.HTTP_201_CREATED
)
def create_loan_request(
    payload: LoanRequestCreate, db: Session = Depends(get_db)
):
    service = LoanRequestService(db)
    return service.create_loan_request(payload)


@router.get("", response_model=PaginatedResponse[LoanRequestResponse])
def list_loan_requests(
    status: LoanRequestStatus | None = Query(
        default=None, description="Filtrar por situação da solicitação"
    ),
    user_id: uuid.UUID | None = Query(
        default=None, description="Filtrar por usuário relacionado"
    ),
    start_date: date | None = Query(
        default=None, description="Data inicial da solicitação (inclusiva)"
    ),
    end_date: date | None = Query(
        default=None, description="Data final da solicitação (inclusiva)"
    ),
    sort_by: Literal[
        "created_at", "request_amount", "first_due_date", "status"
    ] = Query(default="created_at", description="Campo de ordenação"),
    order: Literal["asc", "desc"] = Query(
        default="desc", description="Direção da ordenação"
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
    service = LoanRequestService(db)
    return service.list_loan_requests(
        status=status,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        order=order,
        page=page,
        limit=limit,
    )


@router.get("/{request_id}", response_model=LoanRequestResponse)
def get_loan_request(request_id: uuid.UUID, db: Session = Depends(get_db)):
    service = LoanRequestService(db)
    return service.get_loan_request(request_id)


@router.patch("/{request_id}", response_model=LoanRequestResponse)
def update_loan_request(
    request_id: uuid.UUID,
    payload: LoanRequestUpdate,
    db: Session = Depends(get_db),
):
    service = LoanRequestService(db)
    return service.update_loan_request(request_id, payload)


@router.patch("/{request_id}/approve", response_model=LoanRequestResponse)
def approve_loan_request(
    request_id: uuid.UUID,
    payload: LoanRequestApprovePayload | None = Body(default=None),
    db: Session = Depends(get_db),
):
    service = LoanRequestService(db)
    return service.approve_loan_request(request_id, payload)


@router.patch("/{request_id}/deny", response_model=LoanRequestResponse)
def deny_loan_request(request_id: uuid.UUID, db: Session = Depends(get_db)):
    service = LoanRequestService(db)
    return service.deny_loan_request(request_id)
