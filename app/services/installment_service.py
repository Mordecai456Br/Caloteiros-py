from datetime import date
from decimal import Decimal
from typing import Literal
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleException,
    NotFoundException,
    ValidationException,
)
from app.models.installment import Installment, InstallmentStatus
from app.repositories.installment_repository import InstallmentRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.installment import (
    InstallmentFilterStatus,
    InstallmentResponse,
    InstallmentUpdate,
)
from app.services.loan_service import LoanService


class InstallmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.installment_repo = InstallmentRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.loan_service = LoanService(db)

    def get_installment(self, installment_id: int) -> Installment:
        installment = self.installment_repo.get_by_id(installment_id)
        if not installment:
            raise NotFoundException("Parcela não encontrada.")
        return installment

    def list_installments(
        self,
        *,
        loan_id: uuid.UUID | None = None,
        status: InstallmentFilterStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        sort_by: str = "due_date",
        order: Literal["asc", "desc"] = "asc",
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[InstallmentResponse]:
        if start_date and end_date and start_date > end_date:
            raise ValidationException(
                "A data inicial (start_date) deve ser anterior ou igual à data final (end_date)."
            )

        items, total = self.installment_repo.list_filtered(
            loan_id=loan_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )
        return PaginatedResponse[InstallmentResponse](
            items=[InstallmentResponse.model_validate(item) for item in items],
            pagination=PaginationMeta.create(page=page, limit=limit, total=total),
        )

    def update_installment(
        self, installment_id: int, payload: InstallmentUpdate
    ) -> Installment:
        installment = self.get_installment(installment_id)

        if payload.amount is not None:
            if payload.amount <= Decimal("0.00"):
                raise BusinessRuleException(
                    "O valor da parcela deve ser maior que zero."
                )

            total_paid = self.payment_repo.get_total_paid_for_installment(
                installment.id
            )
            if payload.amount < total_paid:
                raise BusinessRuleException(
                    "O valor da parcela não pode ser menor que o valor já pago."
                )

            installment.amount = payload.amount
            if total_paid >= installment.amount:
                installment.status = InstallmentStatus.PAID
            elif total_paid > Decimal("0.00"):
                installment.status = InstallmentStatus.PARTIALLY_PAID
            else:
                installment.status = InstallmentStatus.OPEN

        if payload.due_date is not None:
            installment.due_date = payload.due_date

        installment = self.installment_repo.update(installment)
        self.loan_service.recalculate_loan_state(installment.loan_id)
        return installment
