"""AI Assistant core: answers school questions with live database
figures. Deterministic rule engine by default — works with no AI provider.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Announcement,
    AttendanceRecord,
    Examination,
    FinancialAdjustment,
    Invoice,
    InvoiceItem,
    Payment,
    School,
    Student,
    Teacher,
)

SUGGESTIONS = [
    "Summarise this month for me",
    "Which classes have outstanding fees?",
    "Explain how to publish examination results",
    "Highlight attendance patterns this month",
]


def _money(x) -> float:
    return round(float(x or 0), 2)


def school_summary(db: Session, school: School) -> dict:
    students = db.query(Student).filter(Student.school_id == school.id, Student.status == "active").count()
    teachers = db.query(Teacher).filter(Teacher.school_id == school.id, Teacher.status == "active").count()
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
    exams = db.query(Examination).filter(Examination.school_id == school.id).count()
    announcements = (
        db.query(Announcement)
        .filter(Announcement.school_id == school.id, Announcement.status == "published")
        .count()
    )
    return {
        "students": students,
        "teachers": teachers,
        "invoiced": _money(invoiced),
        "collected": _money(paid),
        "outstanding": _money(invoiced - paid - waived),
        "exams": exams,
        "published_announcements": announcements,
    }


def outstanding_by_class(db: Session, school: School) -> dict:
    rows = (
        db.query(Student.id, Student.class_name, Student.admission_number, Student.first_name, Student.last_name)
        .filter(Student.school_id == school.id, Student.status == "active")
        .all()
    )
    report = []
    for sid, class_name, adm, first, last in rows:
        invoiced = (
            db.query(func.coalesce(func.sum(InvoiceItem.amount), 0))
            .join(Invoice, InvoiceItem.invoice_id == Invoice.id)
            .filter(Invoice.school_id == school.id, Invoice.student_id == sid)
            .scalar()
        )
        paid = (
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.school_id == school.id, Payment.student_id == sid)
            .scalar()
        )
        waived = (
            db.query(func.coalesce(func.sum(FinancialAdjustment.amount), 0))
            .filter(
                FinancialAdjustment.school_id == school.id,
                FinancialAdjustment.student_id == sid,
                FinancialAdjustment.kind.in_(["waiver", "discount"]),
            )
            .scalar()
        )
        balance = float(invoiced or 0) - float(paid or 0) - float(waived or 0)
        if balance > 0:
            report.append(
                {
                    "class_name": class_name or "Unassigned",
                    "admission_number": adm,
                    "student": f"{first} {last}".strip(),
                    "balance": _money(balance),
                }
            )
    return {"items": sorted(report, key=lambda r: (r["class_name"], -r["balance"]))}


def answer(db: Session, school: School, question: str) -> dict:
    """Return {"text": str, "figures": dict}. Figures are shown to the
    user as the live numbers used for the answer (transparency)."""
    q = question.strip().lower()

    if "summar" in q or "summary" in q:
        s = school_summary(db, school)
        return {
            "text": (
                f"{school.name} snapshot — Students: {s['students']}, Teachers: {s['teachers']}. "
                f"Fees: {s['collected']} collected of {s['invoiced']} invoiced, {s['outstanding']} outstanding. "
                f"Examinations on record: {s['exams']}. Published announcements: {s['published_announcements']}."
            ),
            "figures": s,
        }

    if "outstanding" in q or ("fee" in q and ("class" in q or "balance" in q or "overdue" in q)):
        data = outstanding_by_class(db, school)
        if not data["items"]:
            return {"text": "No outstanding fee balances right now. All caught up.", "figures": data}
        lines = [
            f"{r['class_name']} — {r['admission_number']} {r['student']}: {r['balance']}"
            for r in data["items"][:15]
        ]
        return {
            "text": "Students with outstanding fees:\n" + "\n".join(lines),
            "figures": data,
        }

    if "publish" in q and ("result" in q or "exam" in q):
        return {
            "text": (
                "To publish examination results: open Examinations, select the exam, enter marks, "
                "then click 'Publish results'. Publishing locks marks (they can no longer be edited) "
                "and the action is recorded in the audit log. Parents see results only after publication."
            ),
            "figures": {},
        }

    if "attendance" in q and ("pattern" in q or "trend" in q or "highlight" in q):
        rows = (
            db.query(AttendanceRecord.status, func.count())
            .filter(AttendanceRecord.school_id == school.id)
            .group_by(AttendanceRecord.status)
            .all()
        )
        counts = {status: n for status, n in rows}
        total = sum(counts.values())
        if total == 0:
            return {"text": "No attendance records yet to analyse.", "figures": counts}
        parts = [f"{status}: {counts.get(status, 0)} ({round(counts.get(status, 0) / total * 100)}%)" for status in ["present", "absent", "late", "excused"]]
        return {
            "text": f"Attendance across all recorded days ({total} marks): " + ", ".join(parts) + ".",
            "figures": counts,
        }

    return {
        "text": (
            "I can answer questions about enrollment, fees, attendance patterns and exam workflows "
            "using your live school data. Try one of the suggestions above."
        ),
        "figures": {},
    }
