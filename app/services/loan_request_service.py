from datetime import date, datetime, timezone
from typing import Literal
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleException,
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.loan_request import LoanRequest, LoanRequestStatus
from app.repositories.loan_repository import LoanRepository
from app.repositories.loan_request_repository import LoanRequestRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.loan import LoanCreate
from app.schemas.loan_request import (
    LoanRequestApprovePayload,
    LoanRequestCreate,
    LoanRequestResponse,
    LoanRequestUpdate,
)
from app.services.loan_service import LoanService


class LoanRequestService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.loan_request_repo = LoanRequestRepository(db)
        self.user_repo = UserRepository(db)
        self.loan_repo = LoanRepository(db)
        self.loan_service = LoanService(db)

    def create_loan_request(self, payload: LoanRequestCreate) -> LoanRequest:
        user = self.user_repo.get_by_id(payload.user_id)
        if not user:
            raise NotFoundException("Usuário não encontrado.")

        if payload.request_amount <= 0:
            raise BusinessRuleException(
                "O valor solicitado deve ser maior que zero."
            )

        loan_request = LoanRequest(
            user_id=payload.user_id,
            request_amount=payload.request_amount,
            pix_key=payload.pix_key,
            installment_count=payload.installment_count,
            first_due_date=payload.first_due_date,
            description=payload.description,
            status=LoanRequestStatus.PENDING,
        )
        return self.loan_request_repo.create(loan_request)

    def get_loan_request(self, request_id: uuid.UUID) -> LoanRequest:
        loan_request = self.loan_request_repo.get_by_id(request_id)
        if not loan_request:
            raise NotFoundException(
                "Solicitação de empréstimo não encontrada."
            )
        return loan_request

    def list_loan_requests(
        self,
        *,
        status: LoanRequestStatus | None = None,
        user_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        sort_by: str = "created_at",
        order: Literal["asc", "desc"] = "desc",
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[LoanRequestResponse]:
        if start_date and end_date and start_date > end_date:
            raise ValidationException(
                "start_date deve ser anterior ou igual a end_date."
            )

        items, total = self.loan_request_repo.list_filtered(
            status=status,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )
        return PaginatedResponse[LoanRequestResponse](
            items=[LoanRequestResponse.model_validate(item) for item in items],
            pagination=PaginationMeta.create(
                page=page, limit=limit, total=total
            ),
        )

    def update_loan_request(
        self, request_id: uuid.UUID, payload: LoanRequestUpdate
    ) -> LoanRequest:
        loan_request = self.get_loan_request(request_id)
        if loan_request.status != LoanRequestStatus.PENDING:
            raise BusinessRuleException(
                "Não é permitido atualizar solicitação já aprovada ou negada."
            )

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(loan_request, field, value)
        return self.loan_request_repo.update(loan_request)

    def approve_loan_request(
        self,
        request_id: uuid.UUID,
        payload: LoanRequestApprovePayload | None = None,
    ) -> LoanRequest:
        loan_request = self.get_loan_request(request_id)

        if loan_request.status == LoanRequestStatus.DENIED:
            raise BusinessRuleException(
                "Não é permitido aprovar uma solicitação já negada."
            )

        if loan_request.status == LoanRequestStatus.APPROVED:
            raise ConflictException("Esta solicitação já foi aprovada.")

        existing_loan = self.loan_repo.get_by_loan_request_id(loan_request.id)
        if existing_loan:
            raise ConflictException(
                "Já existe um empréstimo registrado para esta solicitação."
            )

        if payload and payload.installment_count is not None:
            loan_request.installment_count = payload.installment_count
        if payload and payload.first_due_date is not None:
            loan_request.first_due_date = payload.first_due_date

        loan_request.status = LoanRequestStatus.APPROVED
        loan_request.approved_at = datetime.now(timezone.utc)
        loan_request = self.loan_request_repo.update(loan_request)

        total_to_receive = (
            payload.total_to_receive
            if payload and payload.total_to_receive is not None
            else loan_request.request_amount
        )
        load_date = (
            payload.load_date
            if payload and payload.load_date is not None
            else date.today()
        )
        notes = (
            payload.notes
            if payload and payload.notes is not None
            else loan_request.description
        )

        self.loan_service.create_loan(
            LoanCreate(
                loan_request_id=loan_request.id,
                principal_amount=loan_request.request_amount,
                total_to_receive=total_to_receive,
                load_date=load_date,
                notes=notes,
                installment_count=loan_request.installment_count,
                first_due_date=loan_request.first_due_date,
            )
        )

        return loan_request

    def deny_loan_request(self, request_id: uuid.UUID) -> LoanRequest:
        loan_request = self.get_loan_request(request_id)

        if loan_request.status == LoanRequestStatus.APPROVED:
            raise BusinessRuleException(
                "Não é permitido negar uma solicitação já aprovada."
            )

        if loan_request.status == LoanRequestStatus.DENIED:
            raise ConflictException("Esta solicitação já foi negada.")

        loan_request.status = LoanRequestStatus.DENIED
        loan_request.denied_at = datetime.now(timezone.utc)
        return self.loan_request_repo.update(loan_request)
