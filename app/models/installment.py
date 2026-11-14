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
    Identity,
    Integer,
    Numeric,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.loan import Loan
    from app.models.payment import Payment


class InstallmentStatus(str, enum.Enum):
    OPEN = "open"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"


class Installment(Base):
    __tablename__ = "installments"

    id: Mapped[int] = mapped_column(
        "id",
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(always=True),
        primary_key=True,
        autoincrement=True,
    )
    loan_id: Mapped[uuid.UUID] = mapped_column(
        "loanId",
        UUID(as_uuid=True),
        ForeignKey("loans.id"),
        nullable=False,
    )
    number: Mapped[int] = mapped_column(
        "number",
        Integer,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        "amount",
        Numeric,
        nullable=False,
    )
    due_date: Mapped[date] = mapped_column(
        "dueDate",
        Date,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    status: Mapped[InstallmentStatus] = mapped_column(
        "status",
        SqlEnum(
            InstallmentStatus,
            name="installments_status",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=InstallmentStatus.OPEN,
        server_default="open",
    )

    loan: Mapped[Loan] = relationship("Loan", back_populates="installments")
    payments: Mapped[list[Payment]] = relationship(
        "Payment",
        back_populates="installment",
        cascade="all, delete-orphan",
    )
