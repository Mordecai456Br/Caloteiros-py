from datetime import date
from typing import Literal
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, ValidationException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    def create_user(self, payload: UserCreate) -> User:
        user = User(
            name=payload.name,
            phone=payload.phone,
            email=payload.email,
            notes=payload.notes,
        )
        return self.user_repo.create(user)

    def get_user(self, user_id: uuid.UUID) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Usuário não encontrado.")
        return user

    def list_users(
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
    ) -> PaginatedResponse[UserResponse]:
        if start_date and end_date and start_date > end_date:
            raise ValidationException(
                "start_date deve ser anterior ou igual a end_date."
            )

        items, total = self.user_repo.list_filtered(
            name=name,
            search=search,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )
        return PaginatedResponse[UserResponse](
            items=[UserResponse.model_validate(item) for item in items],
            pagination=PaginationMeta.create(
                page=page, limit=limit, total=total
            ),
        )

    def update_user(self, user_id: uuid.UUID, payload: UserUpdate) -> User:
        user = self.get_user(user_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        return self.user_repo.update(user)
