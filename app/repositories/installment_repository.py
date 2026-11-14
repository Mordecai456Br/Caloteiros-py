from datetime import date
from typing import Literal
import uuid

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.installment import Installment, InstallmentStatus
from app.schemas.installment import InstallmentFilterStatus


class InstallmentRepository:
    SORTABLE_FIELDS = {
        "due_date": Installment.due_date,
        "number": Installment.number,
        "amount": Installment.amount,
        "created_at": Installment.created_at,
        "status": Installment.status,
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, installment: Installment) -> Installment:
        self.db.add(installment)
        self.db.commit()
        self.db.refresh(installment)
        return installment

    def create_many(
        self, installments: list[Installment]
    ) -> list[Installment]:
        self.db.add_all(installments)
        self.db.commit()
        for installment in installments:
            self.db.refresh(installment)
        return installments

    def get_by_id(self, installment_id: int) -> Installment | None:
        stmt = select(Installment).where(Installment.id == installment_id)
        return self.db.scalar(stmt)

    def list_filtered(
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
    ) -> tuple[list[Installment], int]:
        stmt = select(Installment)

        if loan_id is not None:
            stmt = stmt.where(Installment.loan_id == loan_id)

        if status is not None:
            pending_statuses = [
                InstallmentStatus.OPEN,
                InstallmentStatus.PARTIALLY_PAID,
            ]
            if status == InstallmentFilterStatus.PENDING:
                stmt = stmt.where(Installment.status.in_(pending_statuses))
            elif status == InstallmentFilterStatus.OVERDUE:
                stmt = stmt.where(
                    Installment.status.in_(pending_statuses),
                    Installment.due_date < date.today(),
                )
            else:
                stmt = stmt.where(
                    Installment.status == InstallmentStatus(status.value)
                )

        if start_date is not None:
            stmt = stmt.where(Installment.due_date >= start_date)

        if end_date is not None:
            stmt = stmt.where(Installment.due_date <= end_date)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        sort_column = self.SORTABLE_FIELDS.get(sort_by, Installment.due_date)
        order_fn = asc if order == "asc" else desc
        stmt = (
            stmt.order_by(order_fn(sort_column))
            .offset((page - 1) * limit)
            .limit(limit)
        )

        items = list(self.db.scalars(stmt).all())
        return items, total

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Installment]:
        stmt = (
            select(Installment)
            .offset(skip)
            .limit(limit)
            .order_by(Installment.due_date.asc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_loan_id(self, loan_id: uuid.UUID) -> list[Installment]:
        stmt = (
            select(Installment)
            .where(Installment.loan_id == loan_id)
            .order_by(Installment.number.asc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_status(self, status: InstallmentStatus) -> list[Installment]:
        stmt = (
            select(Installment)
            .where(Installment.status == status)
            .order_by(Installment.due_date.asc())
        )
        return list(self.db.scalars(stmt).all())

    def update(self, installment: Installment) -> Installment:
        self.db.add(installment)
        self.db.commit()
        self.db.refresh(installment)
        return installment

    def delete(self, installment: Installment) -> None:
        self.db.delete(installment)
        self.db.commit()
