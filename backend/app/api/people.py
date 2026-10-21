from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_school, get_current_user
from app.core.database import get_db
from app.models import Guardian, School, Student, StudentGuardian, User
from app.schemas import GuardianCreate, GuardianLink, GuardianResponse
from app.services.audit import write_audit

router = APIRouter(prefix="/guardians", tags=["guardians"])


def _guardian_response(db: Session, guardian: Guardian) -> GuardianResponse:
    links = (
        db.query(StudentGuardian)
        .filter(StudentGuardian.guardian_id == guardian.id)
        .all()
    )
    children = []
    for link in links:
        student = db.get(Student, link.student_id)
        if student:
            children.append(
                {
                    "student_id": student.id,
                    "admission_number": student.admission_number,
                    "name": f"{student.first_name} {student.last_name}".strip(),
                    "relation": link.relation,
                }
            )
    return GuardianResponse(
        id=guardian.id,
        school_id=guardian.school_id,
        full_name=guardian.full_name,
        email=guardian.email,
        phone=guardian.phone,
        status=guardian.status,
        children=children,
        created_at=guardian.created_at,
    )


def _verify_students(db: Session, school: School, student_ids: list[str]) -> None:
    if not student_ids:
        return
    owned = (
        db.query(Student)
        .filter(Student.school_id == school.id, Student.id.in_(student_ids))
        .count()
    )
    if owned != len(set(student_ids)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "One or more students not found")


@router.get("", response_model=dict)
def list_guardians(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    items = (
        db.query(Guardian)
        .filter(Guardian.school_id == school.id)
        .order_by(Guardian.created_at.desc())
        .all()
    )
    return {
        "items": [_guardian_response(db, g) for g in items],
        "total": len(items),
    }


@router.post("", response_model=GuardianResponse, status_code=status.HTTP_201_CREATED)
def create_guardian(
    data: GuardianCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _verify_students(db, school, data.student_ids)
    existing = (
        db.query(Guardian)
        .filter(Guardian.school_id == school.id, Guardian.email == data.email.lower())
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "A guardian with this email already exists")
    guardian = Guardian(
        school_id=school.id,
        full_name=data.full_name,
        email=data.email.lower(),
        phone=data.phone[:30],
    )
    db.add(guardian)
    db.flush()
    for sid in set(data.student_ids):
        db.add(
            StudentGuardian(
                school_id=school.id,
                student_id=sid,
                guardian_id=guardian.id,
                relation=data.relation,
            )
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Duplicate guardian link")
    write_audit(db, school.id, user.id, "guardian.created", f"{guardian.full_name} <{guardian.email}>")
    db.commit()
    return _guardian_response(db, guardian)


@router.post("/{guardian_id}/link", response_model=GuardianResponse, status_code=status.HTTP_201_CREATED)
def link_student(
    guardian_id: str,
    data: GuardianLink,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    guardian = db.get(Guardian, guardian_id)
    if not guardian or guardian.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Guardian not found")
    _verify_students(db, school, [data.student_id])
    existing = (
        db.query(StudentGuardian)
        .filter(
            StudentGuardian.guardian_id == guardian.id,
            StudentGuardian.student_id == data.student_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Student is already linked to this guardian")
    db.add(
        StudentGuardian(
            school_id=school.id,
            student_id=data.student_id,
            guardian_id=guardian.id,
            relation=data.relation,
        )
    )
    write_audit(db, school.id, user.id, "guardian.linked", f"guardian={guardian.id} student={data.student_id}")
    db.commit()
    return _guardian_response(db, guardian)


@router.delete("/{guardian_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_guardian(
    guardian_id: str,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    guardian = db.get(Guardian, guardian_id)
    if not guardian or guardian.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Guardian not found")
    db.query(StudentGuardian).filter(StudentGuardian.guardian_id == guardian.id).delete()
    db.delete(guardian)
    write_audit(db, school.id, user.id, "guardian.deleted", guardian.email)
    db.commit()
