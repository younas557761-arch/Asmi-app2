from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_school
from app.core.database import get_db
from app.models import (
    AttendanceRecord,
    FinancialAdjustment,
    Invoice,
    InvoiceItem,
    Payment,
    School,
    Student,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/attendance")
def attendance_report(
    date_from: date = Query(..., alias="from"),
    date_to: date = Query(..., alias="to"),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            AttendanceRecord.date,
            AttendanceRecord.status,
            func.count(),
        )
        .filter(
            AttendanceRecord.school_id == school.id,
            AttendanceRecord.date >= date_from,
            AttendanceRecord.date <= date_to,
        )
        .group_by(AttendanceRecord.date, AttendanceRecord.status)
        .all()
    )
    days: dict[str, dict] = {}
    for day, status, count in rows:
        bucket = days.setdefault(str(day), {"date": str(day), "present": 0, "absent": 0, "late": 0, "excused": 0, "total": 0})
        bucket[status] = count
        bucket["total"] += count
    return {
        "from": str(date_from),
        "to": str(date_to),
        "items": sorted(days.values(), key=lambda d: d["date"]),
        "total": len(days),
    }


@router.get("/fees")
def fees_report(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    invoiced = (
        db.query(func.coalesce(func.sum(InvoiceItem.amount), 0))
        .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
        .filter(Invoice.school_id == school.id)
        .scalar()
    )
    paid = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.school_id == school.id)
        .scalar()
    )
    waived = (
        db.query(func.coalesce(func.sum(FinancialAdjustment.amount), 0))
        .filter(
            FinancialAdjustment.school_id == school.id,
            FinancialAdjustment.kind.in_(["waiver", "discount"]),
        )
        .scalar()
    )
    return {
        "invoiced": float(invoiced),
        "collected": float(paid),
        "waived": float(waived),
        "outstanding": float(invoiced - paid - waived),
    }


@router.get("/enrollment")
def enrollment_report(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    rows = (
        db.query(Student.class_name, func.count())
        .filter(Student.school_id == school.id, Student.status == "active")
        .group_by(Student.class_name)
        .all()
    )
    return {
        "items": [
            {"class_name": class_name or "Unassigned", "students": count}
            for class_name, count in sorted(rows, key=lambda r: r[0] or "")
        ],
        "total": sum(count for _, count in rows),
    }
