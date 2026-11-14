from datetime import date
from decimal import Decimal
from typing import Literal
import uuid

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.installment import Installment
from app.models.payment import Payment


class PaymentRepository:
    SORTABLE_FIELDS = {
        "created_at": Payment.created_at,
        "received_at": Payment.received_at,
        "amount": Payment.amount,
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        stmt = select(Payment).where(Payment.id == payment_id)
        return self.db.scalar(stmt)

    def get_total_paid_for_installment(self, installment_id: int) -> Decimal:
        stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.installment_id == installment_id
        )
        result = self.db.scalar(stmt)
        return Decimal(str(result or 0))

    def get_total_paid_for_loan(self, loan_id: uuid.UUID) -> Decimal:
        stmt = (
            select(func.coalesce(func.sum(Payment.amount), 0))
            .join(Installment, Payment.installment_id == Installment.id)
            .where(Installment.loan_id == loan_id)
        )
        result = self.db.scalar(stmt)
        return Decimal(str(result or 0))

    def list_filtered(
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
    ) -> tuple[list[Payment], int]:
        stmt = select(Payment)

        if installment_id is not None:
            stmt = stmt.where(Payment.installment_id == installment_id)

        if loan_id is not None:
            stmt = stmt.join(
                Installment, Payment.installment_id == Installment.id
            ).where(Installment.loan_id == loan_id)

        effective_date = func.coalesce(
            Payment.received_at, func.date(Payment.created_at)
        )
        if start_date is not None:
            stmt = stmt.where(effective_date >= start_date)

        if end_date is not None:
            stmt = stmt.where(effective_date <= end_date)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        sort_column = self.SORTABLE_FIELDS.get(sort_by, Payment.created_at)
        order_fn = asc if order == "asc" else desc
        stmt = (
            stmt.order_by(order_fn(sort_column))
            .offset((page - 1) * limit)
            .limit(limit)
        )

        items = list(self.db.scalars(stmt).all())
        return items, total

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Payment]:
        stmt = (
            select(Payment)
            .offset(skip)
            .limit(limit)
            .order_by(Payment.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_installment_id(self, installment_id: int) -> list[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.installment_id == installment_id)
            .order_by(Payment.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def update(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def delete(self, payment: Payment) -> None:
        self.db.delete(payment)
        self.db.commit()
