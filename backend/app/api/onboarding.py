from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_school, get_current_user
from app.core.database import get_db
from app.models import (
    AcademicYear,
    FeeCategory,
    School,
    SchoolClass,
    Subject,
    User,
)
from app.schemas.ai import ModulesResponse, OnboardingReview, WorkspaceResponse
from app.services import templates as templates_service
from app.services.audit import write_audit

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/templates", response_model=dict)
def list_templates():
    items = [
        {
            "key": t["key"],
            "name": t["name"],
            "desc": t["desc"],
            "grades": t["grades"],
            "modules": t["modules"],
        }
        for t in templates_service.list_templates()
    ]
    return {"items": items, "total": len(items)}


@router.get("/modules", response_model=ModulesResponse)
def list_modules():
    return ModulesResponse(items=templates_service.MODULES)


@router.post("/create-workspace", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    data: OnboardingReview,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Apply a reviewed onboarding configuration: seeds classes, subjects and
    fee categories from the chosen template. Runs inside one transaction."""
    template = templates_service.get_template(data.template_key)
    if not template:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

    # 1. School profile
    school.name = data.school_name
    school.country = data.country
    school.city = data.city
    school.timezone = data.timezone
    school.language = data.language

    # 2. Academic year (current)
    existing_year = (
        db.query(AcademicYear)
        .filter(AcademicYear.school_id == school.id, AcademicYear.name == data.academic_year)
        .first()
    )
    if existing_year:
        year = existing_year
    else:
        try:
            start_year = int(data.academic_year.split("-")[0])
        except (ValueError, IndexError):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "academic_year must look like 2026-2027")
        year = AcademicYear(
            school_id=school.id,
            name=data.academic_year,
            start_date=f"{start_year}-04-01",
            end_date=f"{start_year + 1}-03-31",
            is_current=False,
        )
        db.add(year)
        db.flush()
    db.query(AcademicYear).filter(
        AcademicYear.school_id == school.id, AcademicYear.is_current.is_(True)
    ).update({"is_current": False})
    year.is_current = True

    # 3. Seed classes from template
    classes_created = 0
    for grade in template["grades"]:
        exists = (
            db.query(SchoolClass)
            .filter(
                SchoolClass.school_id == school.id,
                SchoolClass.academic_year_id == year.id,
                SchoolClass.name == grade,
            )
            .first()
        )
        if not exists:
            db.add(SchoolClass(school_id=school.id, academic_year_id=year.id, name=grade))
            classes_created += 1

    # 4. Seed subjects
    subjects_created = 0
    for subject_name in templates_service.DEFAULT_SUBJECTS:
        if data.modules and "classes" not in data.modules:
            break
        exists = (
            db.query(Subject)
            .filter(Subject.school_id == school.id, Subject.name == subject_name)
            .first()
        )
        if not exists:
            db.add(Subject(school_id=school.id, name=subject_name))
            subjects_created += 1

    # 5. Seed fee categories
    fee_categories_created = 0
    if "fees" in data.modules:
        for fee in template["fee_categories"]:
            exists = (
                db.query(FeeCategory)
                .filter(FeeCategory.school_id == school.id, FeeCategory.name == fee["name"])
                .first()
            )
            if not exists:
                db.add(
                    FeeCategory(
                        school_id=school.id,
                        name=fee["name"],
                        default_amount=fee["amount"],
                        frequency=fee["frequency"],
                    )
                )
                fee_categories_created += 1

    write_audit(
        db, school.id, user.id, "workspace.onboarding_applied",
        f"template={data.template_key} year={data.academic_year} modules={len(data.modules)}",
        severity="warning", source="system",
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Workspace conflict — some records already exist")

    return WorkspaceResponse(
        school={"id": school.id, "name": school.name, "language": school.language, "timezone": school.timezone},
        classes_created=classes_created,
        subjects_created=subjects_created,
        fee_categories_created=fee_categories_created,
        modules_enabled=len(data.modules),
    )
