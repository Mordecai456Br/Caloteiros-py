from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import enum
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.loan import Loan
    from app.models.user import User


class LoanRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class LoanRequest(Base):
    __tablename__ = "loan_request"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        "userId",
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    request_amount: Mapped[Decimal] = mapped_column(
        "requestAmount",
        Numeric,
        nullable=False,
    )
    pix_key: Mapped[str] = mapped_column(
        "pixKey",
        String,
        nullable=False,
    )
    installment_count: Mapped[int | None] = mapped_column(
        "installmentCount",
        BigInteger,
        nullable=True,
    )
    first_due_date: Mapped[date | None] = mapped_column(
        "firstDueDate",
        Date,
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        "description",
        Text,
        nullable=True,
    )
    status: Mapped[LoanRequestStatus] = mapped_column(
        "status",
        SqlEnum(
            LoanRequestStatus,
            name="loan_request_status",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=LoanRequestStatus.PENDING,
        server_default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        "approvedAt",
        DateTime(timezone=True),
        nullable=True,
    )
    denied_at: Mapped[datetime | None] = mapped_column(
        "deniedAt",
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship("User", back_populates="loan_requests")
    loan: Mapped[Loan | None] = relationship(
        "Loan",
        back_populates="loan_request",
        uselist=False,
    )
