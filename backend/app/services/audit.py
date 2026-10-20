from sqlalchemy.orm import Session

from app.models import AuditLog


def write_audit(db: Session, school_id: str, user_id: str | None, action: str, detail: str = "") -> None:
    db.add(AuditLog(school_id=school_id, user_id=user_id, action=action, detail=detail))
