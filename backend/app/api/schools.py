from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_school, get_current_user
from app.core.database import get_db
from app.models import School, User
from app.schemas import SchoolResponse, SchoolUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/schools", tags=["schools"])


@router.get("/current", response_model=SchoolResponse)
def get_current(school: School = Depends(get_current_school)):
    return school


@router.patch("/current", response_model=SchoolResponse)
def update_current(
    data: SchoolUpdate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(school, field, value)
    write_audit(db, school.id, user.id, "school.updated", data.model_dump_json(exclude_unset=True))
    db.commit()
    return school
