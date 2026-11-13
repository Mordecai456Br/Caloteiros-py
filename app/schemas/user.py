from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    name: str | None = None
    phone: str
    email: str | None = None
    notes: str | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None


class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
