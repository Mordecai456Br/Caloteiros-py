from __future__ import annotations

from datetime import date
from decimal import Decimal
import enum
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Date, Enum as SqlEnum, ForeignKey, Numeric, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.installment import Installment
    from app.models.loan_request import LoanRequest


class LoanStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in progress"
    PAID = "paid"


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    loan_request_id: Mapped[uuid.UUID] = mapped_column(
        "loanRequestId",
        UUID(as_uuid=True),
        ForeignKey("loan_request.id"),
        unique=True,
        nullable=False,
    )
    principal_amount: Mapped[Decimal] = mapped_column(
        "principalAmount",
        Numeric,
        nullable=False,
    )
    total_to_receive: Mapped[Decimal] = mapped_column(
        "totalToReceive",
        Numeric,
        nullable=False,
    )
    amount_received: Mapped[Decimal] = mapped_column(
        "amountReceived",
        Numeric,
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
    )
    load_date: Mapped[date] = mapped_column(
        "loadDate",
        Date,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        "notes",
        Text,
        nullable=True,
    )
    status: Mapped[LoanStatus] = mapped_column(
        "status",
        SqlEnum(
            LoanStatus,
            name="loan_status",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=LoanStatus.OPEN,
        server_default="open",
    )

    loan_request: Mapped[LoanRequest] = relationship(
        "LoanRequest",
        back_populates="loan",
    )
    installments: Mapped[list[Installment]] = relationship(
        "Installment",
        back_populates="loan",
        cascade="all, delete-orphan",
    )
