import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.loan_request import LoanRequest, LoanStatus


class LoanRequestRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, loan_request: LoanRequest) -> LoanRequest:
        self.db.add(loan_request)
        self.db.commit()
        self.db.refresh(loan_request)
        return loan_request

    def get_by_id(self, loan_request_id: uuid.UUID) -> LoanRequest | None:
        stmt = select(LoanRequest).where(LoanRequest.id == loan_request_id)
        return self.db.scalar(stmt)

    def list_all(self, skip: int = 0, limit: int = 100) -> list[LoanRequest]:
        stmt = (
            select(LoanRequest)
            .offset(skip)
            .limit(limit)
            .order_by(LoanRequest.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_user_id(self, user_id: uuid.UUID) -> list[LoanRequest]:
        stmt = (
            select(LoanRequest)
            .where(LoanRequest.user_id == user_id)
            .order_by(LoanRequest.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_status(self, status: LoanStatus) -> list[LoanRequest]:
        stmt = (
            select(LoanRequest)
            .where(LoanRequest.status == status)
            .order_by(LoanRequest.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def update(self, loan_request: LoanRequest) -> LoanRequest:
        self.db.add(loan_request)
        self.db.commit()
        self.db.refresh(loan_request)
        return loan_request

    def delete(self, loan_request: LoanRequest) -> None:
        self.db.delete(loan_request)
        self.db.commit()
