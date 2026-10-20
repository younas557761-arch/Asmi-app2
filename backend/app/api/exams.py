from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_school, get_current_user
from app.core.database import get_db
from app.models import (
    Examination,
    GradeBand,
    GradingScheme,
    Mark,
    School,
    Student,
    User,
)
from app.schemas import (
    ExaminationCreate,
    ExaminationResponse,
    GradingSchemeCreate,
    GradingSchemeResponse,
    GradeBandResponse,
    MarkBulkCreate,
    MarkResponse,
    StudentResult,
)
from app.services import exams as exams_service
from app.services.audit import write_audit

router = APIRouter(prefix="/exams", tags=["exams"])


# ---------------- Grading schemes ----------------

def _scheme_response(scheme: GradingScheme, bands: list[GradeBand]) -> GradingSchemeResponse:
    return GradingSchemeResponse(
        id=scheme.id,
        school_id=scheme.school_id,
        name=scheme.name,
        pass_mark=scheme.pass_mark,
        bands=[GradeBandResponse.model_validate(b) for b in bands],
    )


@router.get("/schemes", response_model=dict)
def list_schemes(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    schemes = db.query(GradingScheme).filter(GradingScheme.school_id == school.id).all()
    result = []
    for scheme in schemes:
        bands = db.query(GradeBand).filter(GradeBand.scheme_id == scheme.id).all()
        result.append(_scheme_response(scheme, bands))
    return {"items": result, "total": len(result)}


@router.post("/schemes", response_model=GradingSchemeResponse, status_code=status.HTTP_201_CREATED)
def create_scheme(
    data: GradingSchemeCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(GradingScheme)
        .filter(GradingScheme.school_id == school.id, GradingScheme.name == data.name)
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Grading scheme already exists")
    scheme = GradingScheme(school_id=school.id, name=data.name, pass_mark=data.pass_mark)
    db.add(scheme)
    db.flush()
    for band in data.bands:
        db.add(GradeBand(scheme_id=scheme.id, **band.model_dump()))
    write_audit(db, school.id, user.id, "grading_scheme.created", scheme.name)
    db.commit()
    bands = db.query(GradeBand).filter(GradeBand.scheme_id == scheme.id).all()
    return _scheme_response(scheme, bands)


# ---------------- Examinations ----------------

@router.get("", response_model=dict)
def list_exams(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    items = (
        db.query(Examination)
        .filter(Examination.school_id == school.id)
        .order_by(Examination.start_date.desc())
        .all()
    )
    return {"items": [ExaminationResponse.model_validate(e) for e in items], "total": len(items)}


@router.post("", response_model=ExaminationResponse, status_code=status.HTTP_201_CREATED)
def create_exam(
    data: ExaminationCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Examination)
        .filter(Examination.school_id == school.id, Examination.name == data.name)
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Examination already exists")
    exam = Examination(school_id=school.id, **data.model_dump())
    db.add(exam)
    write_audit(db, school.id, user.id, "examination.created", exam.name)
    db.commit()
    return exam


def _get_exam(exam_id: str, school: School, db: Session) -> Examination:
    exam = db.get(Examination, exam_id)
    if not exam or exam.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Examination not found")
    return exam


# ---------------- Marks ----------------

@router.post("/{exam_id}/marks", response_model=dict, status_code=status.HTTP_201_CREATED)
def enter_marks(
    exam_id: str,
    data: MarkBulkCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exam = _get_exam(exam_id, school, db)
    if exam.published:
        raise HTTPException(status.HTTP_409_CONFLICT, "Results are published; create a new examination to change marks")

    student_ids = list({r.student_id for r in data.records})
    owned = (
        db.query(Student)
        .filter(Student.school_id == school.id, Student.id.in_(student_ids))
        .all()
    )
    if len(owned) != len(student_ids):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "One or more students not found")

    saved = []
    for entry in data.records:
        if entry.marks_obtained > entry.max_marks:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Marks obtained ({entry.marks_obtained}) exceed max marks ({entry.max_marks})",
            )
        mark = (
            db.query(Mark)
            .filter(
                Mark.examination_id == exam.id,
                Mark.student_id == entry.student_id,
                Mark.subject == entry.subject,
            )
            .first()
        )
        if mark:
            mark.marks_obtained = entry.marks_obtained
            mark.max_marks = entry.max_marks
        else:
            mark = Mark(
                school_id=school.id,
                examination_id=exam.id,
                student_id=entry.student_id,
                subject=entry.subject,
                max_marks=entry.max_marks,
                marks_obtained=entry.marks_obtained,
            )
            db.add(mark)
        saved.append(mark)
    write_audit(db, school.id, user.id, "marks.entered", f"exam={exam.name} count={len(data.records)}")
    db.commit()
    return {
        "items": [MarkResponse.model_validate(m) for m in saved],
        "total": len(saved),
    }


@router.get("/{exam_id}/marks", response_model=dict)
def list_marks(exam_id: str, school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    exam = _get_exam(exam_id, school, db)
    items = db.query(Mark).filter(Mark.examination_id == exam.id).all()
    return {"items": [MarkResponse.model_validate(m) for m in items], "total": len(items)}


# ---------------- Results ----------------

@router.get("/{exam_id}/results", response_model=dict)
def exam_results(exam_id: str, school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    exam = _get_exam(exam_id, school, db)
    marks = db.query(Mark).filter(Mark.examination_id == exam.id).all()

    scheme = db.query(GradingScheme).filter(GradingScheme.school_id == school.id).first()
    bands = db.query(GradeBand).filter(GradeBand.scheme_id == scheme.id).all() if scheme else []

    per_student: dict[str, dict] = {}
    for mark in marks:
        bucket = per_student.setdefault(mark.student_id, {"obtained": 0, "max": 0})
        bucket["obtained"] += mark.marks_obtained
        bucket["max"] += mark.max_marks

    results = []
    for student_id, totals in per_student.items():
        student = db.get(Student, student_id)
        if not student:
            continue
        percentage = round(totals["obtained"] / totals["max"] * 100, 2) if totals["max"] else 0
        grade = exams_service.grade_for_percentage(bands, percentage)
        results.append(
            StudentResult(
                student_id=student_id,
                admission_number=student.admission_number,
                student_name=f"{student.first_name} {student.last_name}".strip(),
                total_obtained=totals["obtained"],
                total_max=totals["max"],
                percentage=percentage,
                grade=grade,
                passed=percentage >= (scheme.pass_mark if scheme else 40),
            )
        )
    results.sort(key=lambda r: r.percentage, reverse=True)
    return {"exam": exam.name, "published": exam.published, "items": results, "total": len(results)}


@router.post("/{exam_id}/publish", response_model=ExaminationResponse)
def publish_results(
    exam_id: str,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exam = _get_exam(exam_id, school, db)
    if exam.published:
        return exam
    exam.published = True
    write_audit(db, school.id, user.id, "results.published", exam.name, severity="critical")
    db.commit()
    return exam
