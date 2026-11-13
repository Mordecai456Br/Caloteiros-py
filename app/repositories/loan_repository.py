import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.loan import Loan


class LoanRepository:
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
