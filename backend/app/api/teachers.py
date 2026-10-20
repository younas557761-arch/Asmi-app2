from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_school, get_current_user
from app.core.database import get_db
from app.models import School, Teacher, User
from app.schemas import TeacherCreate, TeacherResponse, TeacherUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("", response_model=dict)
def list_teachers(
    q: str = "",
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    query = db.query(Teacher).filter(Teacher.school_id == school.id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Teacher.first_name.ilike(like))
            | (Teacher.last_name.ilike(like))
            | (Teacher.employee_number.ilike(like))
        )
    total = query.count()
    items = query.order_by(Teacher.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return {
        "items": [TeacherResponse.model_validate(t) for t in items],
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
def create_teacher(
    data: TeacherCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Teacher)
        .filter(Teacher.school_id == school.id, Teacher.employee_number == data.employee_number)
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Employee number already exists")
    teacher = Teacher(school_id=school.id, **data.model_dump())
    db.add(teacher)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Employee number already exists")
    write_audit(db, school.id, user.id, "teacher.created", teacher.employee_number)
    db.commit()
    return teacher


def _get_teacher(teacher_id: str, school: School, db: Session) -> Teacher:
    teacher = db.get(Teacher, teacher_id)
    if not teacher or teacher.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teacher not found")
    return teacher


@router.get("/{teacher_id}", response_model=TeacherResponse)
def get_teacher(teacher_id: str, school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    return _get_teacher(teacher_id, school, db)


@router.patch("/{teacher_id}", response_model=TeacherResponse)
def update_teacher(
    teacher_id: str,
    data: TeacherUpdate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    teacher = _get_teacher(teacher_id, school, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(teacher, field, value)
    write_audit(db, school.id, user.id, "teacher.updated", teacher.id)
    db.commit()
    return teacher


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(
    teacher_id: str,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    teacher = _get_teacher(teacher_id, school, db)
    db.delete(teacher)
    write_audit(db, school.id, user.id, "teacher.deleted", teacher.employee_number)
    db.commit()
