from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_school, get_current_user
from app.core.database import get_db
from app.models import AcademicYear, School, SchoolClass, Subject, User
from app.schemas import (
    AcademicYearCreate,
    AcademicYearResponse,
    SchoolClassCreate,
    SchoolClassResponse,
    SchoolClassUpdate,
    SubjectCreate,
    SubjectResponse,
)
from app.services.audit import write_audit

router = APIRouter(tags=["academic"])


# ---------------- Academic years ----------------

@router.get("/academic-years", response_model=dict)
def list_years(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    items = (
        db.query(AcademicYear)
        .filter(AcademicYear.school_id == school.id)
        .order_by(AcademicYear.name.desc())
        .all()
    )
    return {"items": [AcademicYearResponse.model_validate(y) for y in items], "total": len(items)}


@router.post("/academic-years", response_model=AcademicYearResponse, status_code=status.HTTP_201_CREATED)
def create_year(
    data: AcademicYearCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(AcademicYear)
        .filter(AcademicYear.school_id == school.id, AcademicYear.name == data.name)
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Academic year already exists")
    year = AcademicYear(school_id=school.id, **data.model_dump())
    db.add(year)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Academic year already exists")
    write_audit(db, school.id, user.id, "academic_year.created", year.name)
    db.commit()
    return year


@router.post("/academic-years/{year_id}/activate", response_model=AcademicYearResponse)
def activate_year(
    year_id: str,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    year = db.get(AcademicYear, year_id)
    if not year or year.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Academic year not found")
    db.query(AcademicYear).filter(
        AcademicYear.school_id == school.id, AcademicYear.is_current.is_(True)
    ).update({"is_current": False})
    year.is_current = True
    write_audit(db, school.id, user.id, "academic_year.activated", year.name)
    db.commit()
    return year


# ---------------- Classes ----------------

@router.get("/classes", response_model=dict)
def list_classes(
    academic_year_id: str = "",
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    query = db.query(SchoolClass).filter(SchoolClass.school_id == school.id)
    if academic_year_id:
        query = query.filter(SchoolClass.academic_year_id == academic_year_id)
    items = query.order_by(SchoolClass.name.asc()).all()
    return {"items": [SchoolClassResponse.model_validate(c) for c in items], "total": len(items)}


@router.post("/classes", response_model=SchoolClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    data: SchoolClassCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    year_id = data.academic_year_id
    if not year_id:
        current = (
            db.query(AcademicYear)
            .filter(AcademicYear.school_id == school.id, AcademicYear.is_current.is_(True))
            .first()
        )
        if not current:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Create an academic year first")
        year_id = current.id
    year = db.get(AcademicYear, year_id)
    if not year or year.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Academic year not found")
    existing = (
        db.query(SchoolClass)
        .filter(
            SchoolClass.school_id == school.id,
            SchoolClass.academic_year_id == year_id,
            SchoolClass.name == data.name,
        )
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Class already exists for this year")
    school_class = SchoolClass(
        school_id=school.id, academic_year_id=year_id, name=data.name, capacity=data.capacity
    )
    db.add(school_class)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Class already exists for this year")
    write_audit(db, school.id, user.id, "class.created", school_class.name)
    db.commit()
    return school_class


def _get_class(class_id: str, school: School, db: Session) -> SchoolClass:
    school_class = db.get(SchoolClass, class_id)
    if not school_class or school_class.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")
    return school_class


@router.patch("/classes/{class_id}", response_model=SchoolClassResponse)
def update_class(
    class_id: str,
    data: SchoolClassUpdate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    school_class = _get_class(class_id, school, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(school_class, field, value)
    write_audit(db, school.id, user.id, "class.updated", school_class.name)
    db.commit()
    return school_class


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: str,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    school_class = _get_class(class_id, school, db)
    db.delete(school_class)
    write_audit(db, school.id, user.id, "class.deleted", school_class.name)
    db.commit()


# ---------------- Subjects ----------------

@router.get("/subjects", response_model=dict)
def list_subjects(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    items = (
        db.query(Subject)
        .filter(Subject.school_id == school.id)
        .order_by(Subject.name.asc())
        .all()
    )
    return {"items": [SubjectResponse.model_validate(s) for s in items], "total": len(items)}


@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    data: SubjectCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Subject).filter(Subject.school_id == school.id, Subject.name == data.name).first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Subject already exists")
    subject = Subject(school_id=school.id, **data.model_dump())
    db.add(subject)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Subject already exists")
    write_audit(db, school.id, user.id, "subject.created", subject.name)
    db.commit()
    return subject


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: str,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subject = db.get(Subject, subject_id)
    if not subject or subject.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subject not found")
    db.delete(subject)
    write_audit(db, school.id, user.id, "subject.deleted", subject.name)
    db.commit()
