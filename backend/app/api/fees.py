from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_school, get_current_user
from app.core.database import get_db
from app.models import (
    FeeCategory,
    FinancialAdjustment,
    Invoice,
    InvoiceItem,
    Payment,
    School,
    Student,
    User,
)
from app.schemas import (
    AdjustmentCreate,
    AdjustmentResponse,
    FeeCategoryCreate,
    FeeCategoryResponse,
    InvoiceCreate,
    InvoiceItemResponse,
    InvoiceResponse,
    PaymentCreate,
    PaymentResponse,
    StudentBalance,
)
from app.services import fees as fees_service
from app.services.audit import write_audit

router = APIRouter(prefix="/fees", tags=["fees"])


# ---------------- Categories ----------------

@router.get("/categories", response_model=dict)
def list_categories(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    items = (
        db.query(FeeCategory)
        .filter(FeeCategory.school_id == school.id)
        .order_by(FeeCategory.name.asc())
        .all()
    )
    return {"items": [FeeCategoryResponse.model_validate(c) for c in items], "total": len(items)}


@router.post("/categories", response_model=FeeCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: FeeCategoryCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(FeeCategory)
        .filter(FeeCategory.school_id == school.id, FeeCategory.name == data.name)
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Fee category already exists")
    category = FeeCategory(school_id=school.id, **data.model_dump())
    db.add(category)
    db.commit()
    write_audit(db, school.id, user.id, "fee_category.created", category.name)
    db.commit()
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category = db.get(FeeCategory, category_id)
    if not category or category.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fee category not found")
    db.delete(category)
    write_audit(db, school.id, user.id, "fee_category.deleted", category.name)
    db.commit()


# ---------------- Invoices ----------------

def _invoice_response(db: Session, invoice: Invoice) -> InvoiceResponse:
    items = (
        db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).all()
    )
    total = fees_service.invoice_total(db, invoice.id)
    paid = fees_service.invoice_paid(db, invoice.id)
    waived = fees_service.invoice_waived(db, invoice.id)
    return InvoiceResponse(
        id=invoice.id,
        school_id=invoice.school_id,
        student_id=invoice.student_id,
        invoice_number=invoice.invoice_number,
        title=invoice.title,
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        items=[InvoiceItemResponse.model_validate(i) for i in items],
        total=float(total),
        paid=float(paid),
        waived=float(waived),
        balance=float(total - paid - waived),
        status=fees_service.invoice_status(total, paid, waived),
    )


@router.get("/invoices", response_model=dict)
def list_invoices(
    student_id: str = "",
    status_filter: str = Query("", alias="status"),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    invoices = (
        db.query(Invoice).filter(Invoice.school_id == school.id)
        .order_by(Invoice.created_at.desc())
        .all()
    )
    responses = [_invoice_response(db, inv) for inv in invoices]
    if student_id:
        responses = [r for r in responses if r.student_id == student_id]
    if status_filter:
        responses = [r for r in responses if r.status == status_filter]
    return {"items": responses, "total": len(responses)}


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    data: InvoiceCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.get(Student, data.student_id)
    if not student or student.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    count = db.query(Invoice).filter(Invoice.school_id == school.id).count()
    invoice = Invoice(
        school_id=school.id,
        student_id=data.student_id,
        invoice_number=f"INV-{count + 1:04d}",
        title=data.title,
        issue_date=date.today(),
        due_date=data.due_date,
        created_by=user.id,
    )
    db.add(invoice)
    db.flush()
    for item in data.items:
        db.add(InvoiceItem(invoice_id=invoice.id, **item.model_dump()))
    write_audit(db, school.id, user.id, "invoice.created", f"{invoice.invoice_number} student={data.student_id}")
    db.commit()
    return _invoice_response(db, invoice)


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: str, school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice or invoice.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invoice not found")
    return _invoice_response(db, invoice)


# ---------------- Payments (append-only) ----------------

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def record_payment(
    data: PaymentCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.get(Student, data.student_id)
    if not student or student.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    if data.invoice_id:
        invoice = db.get(Invoice, data.invoice_id)
        if not invoice or invoice.school_id != school.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Invoice not found")
        balance = fees_service.invoice_total(db, invoice.id) - fees_service.invoice_paid(db, invoice.id)
        if data.amount > balance:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Amount exceeds invoice balance ({balance})")
    payment = Payment(
        school_id=school.id,
        student_id=data.student_id,
        invoice_id=data.invoice_id,
        amount=data.amount,
        method=data.method,
        note=data.note[:200],
        received_by=user.id,
    )
    db.add(payment)
    write_audit(
        db, school.id, user.id, "payment.recorded",
        f"student={data.student_id} amount={data.amount} method={data.method}",
        severity="warning",
    )
    db.commit()
    return payment


@router.get("/payments", response_model=dict)
def list_payments(
    student_id: str = "",
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    query = db.query(Payment).filter(Payment.school_id == school.id)
    if student_id:
        query = query.filter(Payment.student_id == student_id)
    items = query.order_by(Payment.created_at.desc()).limit(200).all()
    return {
        "items": [PaymentResponse.model_validate(p) for p in items],
        "total": len(items),
    }


# ---------------- Adjustments (append-only) ----------------

@router.post("/adjustments", response_model=AdjustmentResponse, status_code=status.HTTP_201_CREATED)
def create_adjustment(
    data: AdjustmentCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = db.get(Student, data.student_id)
    if not student or student.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    adjustment = FinancialAdjustment(
        school_id=school.id,
        student_id=data.student_id,
        invoice_id=data.invoice_id,
        kind=data.kind,
        amount=data.amount,
        reason=data.reason[:500],
        created_by=user.id,
    )
    db.add(adjustment)
    write_audit(
        db, school.id, user.id, "financial_adjustment.created",
        f"kind={data.kind} amount={data.amount} student={data.student_id}",
        severity="critical",
    )
    db.commit()
    return adjustment


@router.get("/adjustments", response_model=dict)
def list_adjustments(
    student_id: str = "",
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    query = db.query(FinancialAdjustment).filter(FinancialAdjustment.school_id == school.id)
    if student_id:
        query = query.filter(FinancialAdjustment.student_id == student_id)
    items = query.order_by(FinancialAdjustment.created_at.desc()).limit(200).all()
    return {
        "items": [AdjustmentResponse.model_validate(a) for a in items],
        "total": len(items),
    }


# ---------------- Balances ----------------

@router.get("/balances", response_model=dict)
def student_balances(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    students = (
        db.query(Student)
        .filter(Student.school_id == school.id, Student.status == "active")
        .order_by(Student.admission_number.asc())
        .all()
    )
    rows = []
    for student in students:
        invoiced = (
            db.query(func.coalesce(func.sum(InvoiceItem.amount), 0))
            .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
            .filter(Invoice.school_id == school.id, Invoice.student_id == student.id)
            .scalar()
        )
        paid = (
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.school_id == school.id, Payment.student_id == student.id)
            .scalar()
        )
        waived = (
            db.query(func.coalesce(func.sum(FinancialAdjustment.amount), 0))
            .filter(
                FinancialAdjustment.school_id == school.id,
                FinancialAdjustment.student_id == student.id,
                FinancialAdjustment.kind.in_(["waiver", "discount"]),
            )
            .scalar()
        )
        refunded = (
            db.query(func.coalesce(func.sum(FinancialAdjustment.amount), 0))
            .filter(
                FinancialAdjustment.school_id == school.id,
                FinancialAdjustment.student_id == student.id,
                FinancialAdjustment.kind == "refund",
            )
            .scalar()
        )
        rows.append(
            StudentBalance(
                student_id=student.id,
                admission_number=student.admission_number,
                student_name=f"{student.first_name} {student.last_name}".strip(),
                invoiced=float(invoiced),
                paid=float(paid),
                waived=float(waived),
                refunded=float(refunded),
                balance=float(invoiced - paid - waived),
            )
        )
    return {"items": rows, "total": len(rows)}
