import calendar
from datetime import date
from decimal import Decimal, ROUND_DOWN
from typing import Literal
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BusinessRuleException,
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.installment import Installment, InstallmentStatus
from app.models.loan import Loan, LoanStatus
from app.models.loan_request import LoanRequestStatus
from app.repositories.installment_repository import InstallmentRepository
from app.repositories.loan_repository import LoanRepository
from app.repositories.loan_request_repository import LoanRequestRepository
from app.repositories.payment_repository import PaymentRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.loan import LoanCreate, LoanFilterStatus, LoanResponse


def _add_months(base_date: date, months: int) -> date:
    month_index = base_date.month - 1 + months
    year = base_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(base_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


class LoanService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.loan_repo = LoanRepository(db)
        self.loan_request_repo = LoanRequestRepository(db)
        self.installment_repo = InstallmentRepository(db)
        self.payment_repo = PaymentRepository(db)

    def create_loan(self, payload: LoanCreate) -> Loan:
        loan_request = self.loan_request_repo.get_by_id(
            payload.loan_request_id
        )
        if not loan_request:
            raise NotFoundException(
                "Solicitação de empréstimo não encontrada."
            )

        if loan_request.status == LoanRequestStatus.DENIED:
            raise BusinessRuleException(
                "Não é permitido criar empréstimo para solicitação negada."
            )

        existing = self.loan_repo.get_by_loan_request_id(
            payload.loan_request_id
        )
        if existing:
            raise ConflictException(
                "Já existe um empréstimo registrado para esta solicitação."
            )

        if payload.principal_amount <= 0 or payload.total_to_receive <= 0:
            raise BusinessRuleException(
                "Os valores do empréstimo devem ser maiores que zero."
            )

        initial_status = self._determine_initial_status(
            amount_received=payload.amount_received,
            total_to_receive=payload.total_to_receive,
        )

        loan = Loan(
            loan_request_id=payload.loan_request_id,
            principal_amount=payload.principal_amount,
            total_to_receive=payload.total_to_receive,
            amount_received=payload.amount_received,
            load_date=payload.load_date,
            notes=payload.notes,
            status=initial_status,
        )
        loan = self.loan_repo.create(loan)

        inst_count = (
            payload.installment_count or loan_request.installment_count
        )
        first_due_date = payload.first_due_date or loan_request.first_due_date
        if inst_count and inst_count >= 1:
            self.generate_installments(
                loan=loan,
                installment_count=int(inst_count),
                first_due_date=first_due_date,
            )

        return loan

    def generate_installments(
        self,
        *,
        loan: Loan,
        installment_count: int,
        first_due_date: date | None = None,
    ) -> list[Installment]:
        if installment_count < 1:
            raise BusinessRuleException(
                "A quantidade de parcelas deve ser maior ou igual a 1."
            )

        start_due_date = first_due_date or _add_months(loan.load_date, 1)
        count_dec = Decimal(installment_count)
        base_amount = (loan.total_to_receive / count_dec).quantize(
            Decimal("0.01"), rounding=ROUND_DOWN
        )
        if base_amount <= 0:
            raise BusinessRuleException(
                "O valor das parcelas não pode ser menor ou igual a zero."
            )

        remainder = loan.total_to_receive - (base_amount * count_dec)
        installments: list[Installment] = []

        for idx in range(installment_count):
            amount = (
                base_amount + remainder
                if idx == installment_count - 1
                else base_amount
            )
            due_date = _add_months(start_due_date, idx)
            installments.append(
                Installment(
                    loan_id=loan.id,
                    number=idx + 1,
                    amount=amount,
                    due_date=due_date,
                    status=InstallmentStatus.OPEN,
                )
            )

        return self.installment_repo.create_many(installments)

    def recalculate_loan_state(self, loan_id: uuid.UUID) -> Loan:
        loan = self.get_loan(loan_id)
        installments = self.installment_repo.list_by_loan_id(loan_id)
        total_paid = self.payment_repo.get_total_paid_for_loan(loan_id)

        loan.amount_received = total_paid
        if installments:
            loan.total_to_receive = sum(
                (inst.amount for inst in installments), Decimal("0.00")
            )
            all_paid = all(
                inst.status == InstallmentStatus.PAID for inst in installments
            )
            any_paid = any(
                inst.status
                in (InstallmentStatus.PARTIALLY_PAID, InstallmentStatus.PAID)
                for inst in installments
            )
            if all_paid or loan.amount_received >= loan.total_to_receive:
                loan.status = LoanStatus.PAID
            elif any_paid or loan.amount_received > Decimal("0.00"):
                loan.status = LoanStatus.IN_PROGRESS
            else:
                loan.status = LoanStatus.OPEN
        else:
            loan.status = self._determine_initial_status(
                amount_received=loan.amount_received,
                total_to_receive=loan.total_to_receive,
            )

        return self.loan_repo.update(loan)

    @staticmethod
    def _determine_initial_status(
        *, amount_received: Decimal, total_to_receive: Decimal
    ) -> LoanStatus:
        if (
            amount_received >= total_to_receive
            and total_to_receive > Decimal("0.00")
        ):
            return LoanStatus.PAID
        if amount_received > Decimal("0.00"):
            return LoanStatus.IN_PROGRESS
        return LoanStatus.OPEN

    def get_loan(self, loan_id: uuid.UUID) -> Loan:
        loan = self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise NotFoundException("Empréstimo não encontrado.")
        return loan

    def list_loans(
        self,
        *,
        user_id: uuid.UUID | None = None,
        status: LoanFilterStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        sort_by: str = "load_date",
        order: Literal["asc", "desc"] = "desc",
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedResponse[LoanResponse]:
        if start_date and end_date and start_date > end_date:
            raise ValidationException(
                "start_date deve ser anterior ou igual a end_date."
            )

        if (
            min_amount is not None
            and max_amount is not None
            and min_amount > max_amount
        ):
            raise ValidationException(
                "min_amount deve ser menor ou igual a max_amount."
            )

        items, total = self.loan_repo.list_filtered(
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
        return PaginatedResponse[LoanResponse](
            items=[LoanResponse.model_validate(item) for item in items],
            pagination=PaginationMeta.create(
                page=page, limit=limit, total=total
            ),
        )
