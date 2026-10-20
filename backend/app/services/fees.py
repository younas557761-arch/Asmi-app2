from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import FinancialAdjustment, Invoice, InvoiceItem, Payment


def invoice_total(db: Session, invoice_id: str) -> Decimal:
    return (
        db.query(func.coalesce(func.sum(InvoiceItem.amount), 0))
        .filter(InvoiceItem.invoice_id == invoice_id)
        .scalar()
    )


def invoice_paid(db: Session, invoice_id: str) -> Decimal:
    return (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.invoice_id == invoice_id)
        .scalar()
    )


def invoice_waived(db: Session, invoice_id: str) -> Decimal:
    return (
        db.query(func.coalesce(func.sum(FinancialAdjustment.amount), 0))
        .filter(
            FinancialAdjustment.invoice_id == invoice_id,
            FinancialAdjustment.kind.in_(["waiver", "discount"]),
        )
        .scalar()
    )


def invoice_status(total: Decimal, paid: Decimal, waived: Decimal) -> str:
    balance = total - paid - waived
    if total > 0 and balance <= 0:
        return "paid"
    if paid > 0 or waived > 0:
        return "partial"
    return "unpaid"
