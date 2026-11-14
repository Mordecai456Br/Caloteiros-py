from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.installment import Installment


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    installment_id: Mapped[int] = mapped_column(
        "installmentId",
        BigInteger,
        ForeignKey("installments.id"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        "amount",
        Numeric,
        nullable=False,
    )
    received_at: Mapped[date | None] = mapped_column(
        "receivedAt",
        Date,
        nullable=True,
    )
    receipt_key: Mapped[str] = mapped_column(
        "receiptKey",
        Text,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        "description",
        Text,
        nullable=True,
    )
    sender_pix_key: Mapped[str] = mapped_column(
        "senderPixKey",
        Text,
        nullable=False,
    )

    installment: Mapped[Installment] = relationship(
        "Installment",
        back_populates="payments",
    )
