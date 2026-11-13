from datetime import date
from decimal import Decimal
from typing import Literal
import uuid

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.loan import Loan, LoanStatus
from app.models.loan_request import LoanRequest
from app.schemas.loan import LoanFilterStatus


class LoanRepository:
    SORTABLE_FIELDS = {
        "load_date": Loan.load_date,
        "principal_amount": Loan.principal_amount,
        "total_to_receive": Loan.total_to_receive,
        "amount_received": Loan.amount_received,
        "status": Loan.status,
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, loan: Loan) -> Loan:
        self.db.add(loan)
        self.db.commit()
        self.db.refresh(loan)
        return loan

    def get_by_id(self, loan_id: uuid.UUID) -> Loan | None:
        stmt = select(Loan).where(Loan.id == loan_id)
        return self.db.scalar(stmt)

    def get_by_loan_request_id(self, loan_request_id: uuid.UUID) -> Loan | None:
        stmt = select(Loan).where(Loan.loan_request_id == loan_request_id)
        return self.db.scalar(stmt)

    def list_filtered(
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
    ) -> tuple[list[Loan], int]:
        stmt = select(Loan)

        if user_id is not None:
            stmt = stmt.join(LoanRequest, Loan.loan_request_id == LoanRequest.id).where(
                LoanRequest.user_id == user_id
            )

        if status is not None:
            if status == LoanFilterStatus.ACTIVE:
                stmt = stmt.where(
                    Loan.status.in_([LoanStatus.OPEN, LoanStatus.IN_PROGRESS])
                )
            else:
                stmt = stmt.where(Loan.status == LoanStatus(status.value))

        if start_date is not None:
            stmt = stmt.where(Loan.load_date >= start_date)

        if end_date is not None:
            stmt = stmt.where(Loan.load_date <= end_date)

        if min_amount is not None:
            stmt = stmt.where(Loan.principal_amount >= min_amount)

        if max_amount is not None:
            stmt = stmt.where(Loan.principal_amount <= max_amount)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        sort_column = self.SORTABLE_FIELDS.get(sort_by, Loan.load_date)
        order_fn = asc if order == "asc" else desc
        stmt = (
            stmt.order_by(order_fn(sort_column))
            .offset((page - 1) * limit)
            .limit(limit)
        )

        items = list(self.db.scalars(stmt).all())
        return items, total

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Loan]:
        stmt = select(Loan).offset(skip).limit(limit).order_by(Loan.load_date.desc())
        return list(self.db.scalars(stmt).all())

    def update(self, loan: Loan) -> Loan:
        self.db.add(loan)
        self.db.commit()
        self.db.refresh(loan)
        return loan

    def delete(self, loan: Loan) -> None:
        self.db.delete(loan)
        self.db.commit()
