from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_school, get_current_user
from app.core.database import get_db
from app.models import School, Student, User
from app.schemas import StudentCreate, StudentResponse, StudentUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=dict)
def list_students(
    q: str = "",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    query = db.query(Student).filter(Student.school_id == school.id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Student.first_name.ilike(like))
            | (Student.last_name.ilike(like))
            | (Student.admission_number.ilike(like))
        )
    total = query.count()
    items = (
        query.order_by(Student.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return {
        "items": [StudentResponse.model_validate(s) for s in items],
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    data: StudentCreate,
    request: Request,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Student)
        .filter(
            Student.school_id == school.id,
            Student.admission_number == data.admission_number,
        )
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Admission number already exists")
    student = Student(school_id=school.id, **data.model_dump())
    db.add(student)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Admission number already exists")
    write_audit(db, school.id, user.id, "student.created", student.admission_number)
    db.commit()
    return student


def _get_owned(student_id: str, school: School, db: Session) -> Student:
    student = db.get(Student, student_id)
    if not student or student.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return student


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: str, school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    return _get_owned(student_id, school, db)


@router.patch("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: str,
    data: StudentUpdate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = _get_owned(student_id, school, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    write_audit(db, school.id, user.id, "student.updated", student.id)
    db.commit()
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: str,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    student = _get_owned(student_id, school, db)
    db.delete(student)
    write_audit(db, school.id, user.id, "student.deleted", student.admission_number)
    db.commit()
