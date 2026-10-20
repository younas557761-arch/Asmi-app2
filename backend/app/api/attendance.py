from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_school, get_current_user
from app.core.database import get_db
from app.models import AttendanceRecord, School, Student, User
from app.schemas import (
    AttendanceBulkCreate,
    AttendanceCorrection,
    AttendanceRecordResponse,
    AttendanceSummaryResponse,
)
from app.services.audit import write_audit

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("", status_code=status.HTTP_201_CREATED)
def mark_attendance(
    data: AttendanceBulkCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student_ids = list({r.student_id for r in data.records})
    owned = (
        db.query(Student)
        .filter(Student.school_id == school.id, Student.id.in_(student_ids))
        .all()
    )
    if len(owned) != len(student_ids):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "One or more students not found")

    duplicate = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.school_id == school.id,
            AttendanceRecord.date == data.date,
            AttendanceRecord.student_id.in_(student_ids),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Attendance already marked for this date (use correction endpoint to change)",
        )

    by_id = {s.id: s for s in owned}
    for r in data.records:
        db.add(
            AttendanceRecord(
                school_id=school.id,
                student_id=r.student_id,
                class_name=by_id[r.student_id].class_name,
                date=data.date,
                status=r.status,
                note=r.note[:200],
                marked_by=user.id,
            )
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Duplicate attendance submission blocked")

    write_audit(db, school.id, user.id, "attendance.marked", f"date={data.date} count={len(data.records)}")
    db.commit()
    return {"marked": len(data.records), "date": str(data.date)}


@router.get("", response_model=dict)
def list_attendance(
    date: date = Query(...),
    class_name: str = "",
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    query = db.query(AttendanceRecord).filter(
        AttendanceRecord.school_id == school.id, AttendanceRecord.date == date
    )
    if class_name:
        query = query.filter(AttendanceRecord.class_name == class_name)
    total = query.count()
    items = query.order_by(AttendanceRecord.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return {
        "items": [AttendanceRecordResponse.model_validate(r) for r in items],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/summary", response_model=AttendanceSummaryResponse)
def attendance_summary(
    date: date = Query(...),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(AttendanceRecord.status, func.count())
        .filter(AttendanceRecord.school_id == school.id, AttendanceRecord.date == date)
        .group_by(AttendanceRecord.status)
        .all()
    )
    counts = {status: n for status, n in rows}
    total = sum(counts.values())
    return AttendanceSummaryResponse(
        date=date,
        present=counts.get("present", 0),
        absent=counts.get("absent", 0),
        late=counts.get("late", 0),
        excused=counts.get("excused", 0),
        total=total,
        marked=total > 0,
    )


@router.patch("/{record_id}", response_model=AttendanceRecordResponse)
def correct_attendance(
    record_id: str,
    data: AttendanceCorrection,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.get(AttendanceRecord, record_id)
    if not record or record.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Attendance record not found")
    previous = record.status
    record.status = data.status
    if data.note:
        record.note = data.note[:200]
    write_audit(
        db,
        school.id,
        user.id,
        "attendance.corrected",
        f"record={record.id} {previous}->{data.status} date={record.date}",
    )
    db.commit()
    return record
