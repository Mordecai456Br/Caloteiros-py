from datetime import date
from typing import Literal
import uuid

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.loan_request import LoanRequest, LoanRequestStatus


class LoanRequestRepository:
    SORTABLE_FIELDS = {
        "created_at": LoanRequest.created_at,
        "request_amount": LoanRequest.request_amount,
        "first_due_date": LoanRequest.first_due_date,
        "status": LoanRequest.status,
    }

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

    def list_filtered(
        self,
        *,
        status: LoanRequestStatus | None = None,
        user_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        sort_by: str = "created_at",
        order: Literal["asc", "desc"] = "desc",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[LoanRequest], int]:
        stmt = select(LoanRequest)

        if status is not None:
            stmt = stmt.where(LoanRequest.status == status)

        if user_id is not None:
            stmt = stmt.where(LoanRequest.user_id == user_id)

        if start_date is not None:
            stmt = stmt.where(func.date(LoanRequest.created_at) >= start_date)

        if end_date is not None:
            stmt = stmt.where(func.date(LoanRequest.created_at) <= end_date)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        sort_column = self.SORTABLE_FIELDS.get(sort_by, LoanRequest.created_at)
        order_fn = asc if order == "asc" else desc
        stmt = (
            stmt.order_by(order_fn(sort_column))
            .offset((page - 1) * limit)
            .limit(limit)
        )

        items = list(self.db.scalars(stmt).all())
        return items, total

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

    def list_by_status(self, status: LoanRequestStatus) -> list[LoanRequest]:
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
