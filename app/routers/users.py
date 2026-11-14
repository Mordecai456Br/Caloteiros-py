from datetime import date
from typing import Literal
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.create_user(payload)


@router.get("", response_model=PaginatedResponse[UserResponse])
def list_users(
    name: str | None = Query(
        default=None, description="Filtrar pelo nome da pessoa"
    ),
    search: str | None = Query(
        default=None, description="Busca textual em nome, telefone ou e-mail"
    ),
    start_date: date | None = Query(
        default=None, description="Data inicial de cadastro (inclusiva)"
    ),
    end_date: date | None = Query(
        default=None, description="Data final de cadastro (inclusiva)"
    ),
    sort_by: Literal["name", "phone", "email", "created_at"] = Query(
        default="created_at", description="Campo de ordenação"
    ),
    order: Literal["asc", "desc"] = Query(
        default="desc", description="Direção da ordenação"
    ),
    page: int = Query(default=1, ge=1, description="Página atual"),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Quantidade de registros por página",
    ),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    return service.list_users(
        name=name,
        search=search,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        order=order,
        page=page,
        limit=limit,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID, payload: UserUpdate, db: Session = Depends(get_db)
):
    service = UserService(db)
    return service.update_user(user_id, payload)
