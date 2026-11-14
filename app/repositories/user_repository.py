from datetime import date
from typing import Literal
import uuid

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    SORTABLE_FIELDS = {
        "name": User.name,
        "phone": User.phone,
        "email": User.email,
        "created_at": User.created_at,
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.scalar(stmt)

    def get_by_phone(self, phone: str) -> User | None:
        stmt = select(User).where(User.phone == phone)
        return self.db.scalar(stmt)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def list_filtered(
        self,
        *,
        name: str | None = None,
        search: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        sort_by: str = "created_at",
        order: Literal["asc", "desc"] = "desc",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        stmt = select(User)

        if name:
            stmt = stmt.where(User.name.ilike(f"%{name}%"))

        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    User.name.ilike(pattern),
                    User.phone.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )

        if start_date:
            stmt = stmt.where(func.date(User.created_at) >= start_date)

        if end_date:
            stmt = stmt.where(func.date(User.created_at) <= end_date)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        sort_column = self.SORTABLE_FIELDS.get(sort_by, User.created_at)
        order_fn = asc if order == "asc" else desc
        stmt = (
            stmt.order_by(order_fn(sort_column))
            .offset((page - 1) * limit)
            .limit(limit)
        )

        items = list(self.db.scalars(stmt).all())
        return items, total

    def list_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        stmt = (
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def update(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
