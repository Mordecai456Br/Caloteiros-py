import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.installment import Installment, InstallmentStatus


class InstallmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, installment: Installment) -> Installment:
        self.db.add(installment)
        self.db.commit()
        self.db.refresh(installment)
        return installment

    def create_many(self, installments: list[Installment]) -> list[Installment]:
        self.db.add_all(installments)
        self.db.commit()
        for installment in installments:
            self.db.refresh(installment)
        return installments

    def get_by_id(self, installment_id: int) -> Installment | None:
        stmt = select(Installment).where(Installment.id == installment_id)
        return self.db.scalar(stmt)

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
