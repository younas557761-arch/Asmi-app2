from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import get_current_school
from app.core.database import get_db
from app.models import AuditLog, School

router = APIRouter(prefix="/audit-logs", tags=["audit"])


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    user_id: Optional[str]
    action: str
    detail: str
    severity: str
    source: str
    created_at: datetime


@router.get("", response_model=dict)
def list_audit_logs(
    q: str = "",
    severity: str = "",
    source: str = "",
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog).filter(AuditLog.school_id == school.id)
    if q:
        like = f"%{q}%"
        query = query.filter((AuditLog.action.ilike(like)) | (AuditLog.detail.ilike(like)))
    if severity:
        query = query.filter(AuditLog.severity == severity)
    if source:
        query = query.filter(AuditLog.source == source)
    total = query.count()
    items = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return {
        "items": [AuditLogResponse.model_validate(a) for a in items],
        "total": total,
        "page": page,
        "size": size,
    }
