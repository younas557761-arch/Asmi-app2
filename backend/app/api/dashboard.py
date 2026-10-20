from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_school
from app.core.database import get_db
from app.core.security import utcnow
from app.models import (
    AttendanceRecord,
    School,
    SchoolClass,
    Student,
    Subject,
    Teacher,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    today = utcnow().date()

    students_active = (
        db.query(Student)
        .filter(Student.school_id == school.id, Student.status == "active")
        .count()
    )
    teachers_active = (
        db.query(Teacher)
        .filter(Teacher.school_id == school.id, Teacher.status == "active")
        .count()
    )
    classes_count = db.query(SchoolClass).filter(SchoolClass.school_id == school.id).count()
    subjects_count = db.query(Subject).filter(Subject.school_id == school.id).count()

    rows = (
        db.query(AttendanceRecord.status, func.count())
        .filter(AttendanceRecord.school_id == school.id, AttendanceRecord.date == today)
        .group_by(AttendanceRecord.status)
        .all()
    )
    counts = {status: n for status, n in rows}
    attendance_total = sum(counts.values())

    return {
        "date": str(today),
        "students_active": students_active,
        "teachers_active": teachers_active,
        "classes_count": classes_count,
        "subjects_count": subjects_count,
        "attendance_today": {
            "marked": attendance_total > 0,
            "present": counts.get("present", 0),
            "absent": counts.get("absent", 0),
            "late": counts.get("late", 0),
            "excused": counts.get("excused", 0),
            "total": attendance_total,
        },
        "setup_checklist": {
            "students_added": students_active > 0,
            "classes_created": classes_count > 0,
            "teachers_added": teachers_active > 0,
            "attendance_marked_today": attendance_total > 0,
        },
    }
