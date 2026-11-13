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
from app.models.payment import Payment
from app.repositories.installment_repository import InstallmentRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.loan_service import LoanService


class PaymentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.installment_repo = InstallmentRepository(db)
        self.loan_service = LoanService(db)

    def create_payment(self, payload: PaymentCreate) -> Payment:
        installment = self.installment_repo.get_by_id(payload.installment_id)
        if not installment:
            raise NotFoundException("Parcela não encontrada.")

        if payload.loan_id is not None and installment.loan_id != payload.loan_id:
            raise BusinessRuleException(
                "A parcela informada não pertence ao empréstimo especificado."
            )

        if payload.amount <= Decimal("0.00"):
            raise BusinessRuleException(
                "O valor do pagamento deve ser maior que zero."
            )

        if installment.status == InstallmentStatus.PAID:
            raise BusinessRuleException("Esta parcela já está totalmente paga.")

        already_paid = self.payment_repo.get_total_paid_for_installment(installment.id)
        remaining_balance = installment.amount - already_paid

        if payload.amount > remaining_balance:
            raise BusinessRuleException(
                f"O valor do pagamento ({payload.amount:.2f}) não pode ser maior que o saldo da parcela ({remaining_balance:.2f})."
            )

        payment = Payment(
            installment_id=payload.installment_id,
            amount=payload.amount,
            received_at=payload.received_at or date.today(),
            receipt_key=payload.receipt_key,
            description=payload.description,
            sender_pix_key=payload.sender_pix_key,
        )
        payment = self.payment_repo.create(payment)

        self._sync_installment_and_loan(installment)
        return payment

    def get_payment(self, payment_id: uuid.UUID) -> Payment:
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundException("Pagamento não encontrado.")
        return payment

    def list_payments(
        self,
        *,
        installment_id: int | None = None,
        loan_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        sort_by: str = "created_at",
        order: Literal["asc", "desc"] = "desc",
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[PaymentResponse]:
        if start_date and end_date and start_date > end_date:
            raise ValidationException(
                "A data inicial (start_date) deve ser anterior ou igual à data final (end_date)."
            )

        items, total = self.payment_repo.list_filtered(
            installment_id=installment_id,
            loan_id=loan_id,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )
        return PaginatedResponse[PaymentResponse](
            items=[PaymentResponse.model_validate(item) for item in items],
            pagination=PaginationMeta.create(page=page, limit=limit, total=total),
        )

    def delete_payment(self, payment_id: uuid.UUID) -> None:
        payment = self.get_payment(payment_id)
        installment = self.installment_repo.get_by_id(payment.installment_id)
        self.payment_repo.delete(payment)

        if installment:
            self._sync_installment_and_loan(installment)

    def _sync_installment_and_loan(self, installment: Installment) -> None:
        total_paid_installment = self.payment_repo.get_total_paid_for_installment(
            installment.id
        )
        if total_paid_installment >= installment.amount:
            installment.status = InstallmentStatus.PAID
        elif total_paid_installment > Decimal("0.00"):
            installment.status = InstallmentStatus.PARTIALLY_PAID
        else:
            installment.status = InstallmentStatus.OPEN

        self.installment_repo.update(installment)
        self.loan_service.recalculate_loan_state(installment.loan_id)
