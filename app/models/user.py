from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.loan_request import LoanRequest


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    loan_requests: Mapped[list[LoanRequest]] = relationship(
        "LoanRequest",
        back_populates="user",
    )
