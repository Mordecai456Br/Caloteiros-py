import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment import Payment


class PaymentRepository:
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
