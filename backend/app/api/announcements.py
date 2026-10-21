from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_school, get_current_user
from app.core.database import get_db
from app.core.security import utcnow
from app.models import Announcement, School, User
from app.schemas import AnnouncementCreate, AnnouncementResponse
from app.services.audit import write_audit

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("", response_model=dict)
def list_announcements(
    status_filter: str = Query("", alias="status"),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    query = db.query(Announcement).filter(Announcement.school_id == school.id)
    if status_filter:
        query = query.filter(Announcement.status == status_filter)
    items = query.order_by(Announcement.created_at.desc()).limit(200).all()
    return {
        "items": [AnnouncementResponse.model_validate(a) for a in items],
        "total": len(items),
    }


@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    data: AnnouncementCreate,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.audience == "class" and not data.class_name:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "class_name is required for class audience")
    announcement = Announcement(
        school_id=school.id,
        title=data.title,
        body=data.body,
        audience=data.audience,
        class_name=data.class_name,
        status="draft",
        created_by=user.id,
    )
    db.add(announcement)
    write_audit(db, school.id, user.id, "announcement.drafted", announcement.title)
    db.commit()
    return announcement


def _get_owned(announcement_id: str, school: School, db: Session) -> Announcement:
    announcement = db.get(Announcement, announcement_id)
    if not announcement or announcement.school_id != school.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Announcement not found")
    return announcement


@router.post("/{announcement_id}/publish", response_model=AnnouncementResponse)
def publish_announcement(
    announcement_id: str,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    announcement = _get_owned(announcement_id, school, db)
    if announcement.status == "published":
        return announcement
    announcement.status = "published"
    announcement.published_at = utcnow()
    write_audit(
        db, school.id, user.id, "announcement.published",
        f"{announcement.title} audience={announcement.audience}",
        severity="critical",
    )
    db.commit()
    return announcement


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: str,
    school: School = Depends(get_current_school),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    announcement = _get_owned(announcement_id, school, db)
    if announcement.status == "published":
        raise HTTPException(status.HTTP_409_CONFLICT, "Published announcements cannot be deleted")
    db.delete(announcement)
    write_audit(db, school.id, user.id, "announcement.deleted", announcement.title)
    db.commit()
