import uuid

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from app.core.database import Base
from app.core.security import utcnow


def _uuid() -> str:
    return str(uuid.uuid4())


class FeeCategory(Base):
    __tablename__ = "fee_categories"
    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_fee_category"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    default_amount = Column(Numeric(10, 2), nullable=False, default=0)
    frequency = Column(String(20), default="monthly", nullable=False)  # monthly/term/annual/one_time
    created_at = Column(DateTime, default=utcnow, nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("school_id", "invoice_number", name="uq_invoice_number"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    invoice_number = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(String(36), primary_key=True, default=_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    description = Column(String(200), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)


class Payment(Base):
    """Append-only ledger entry. Never updated or deleted — corrections are new entries."""

    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    method = Column(String(20), default="cash", nullable=False)  # cash/bank/online
    note = Column(String(200), default="")
    received_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class FinancialAdjustment(Base):
    """Append-only: waivers, discounts and refunds. Never edited or deleted."""

    __tablename__ = "financial_adjustments"

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=True, index=True)
    kind = Column(String(20), nullable=False)  # waiver / discount / refund
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(Text, default="")
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
