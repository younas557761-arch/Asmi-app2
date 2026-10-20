from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import utcnow
from app.models import School, SchoolMembership, Session as UserSession, User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    sess = (
        db.query(UserSession)
        .filter(
            UserSession.token == token,
            UserSession.revoked.is_(False),
            UserSession.expires_at > utcnow(),
        )
        .first()
    )
    if not sess:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
    user = db.get(User, sess.user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account disabled")
    request.state.session = sess
    return user


def get_current_school(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> School:
    membership = (
        db.query(SchoolMembership)
        .filter(SchoolMembership.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No school membership")
    request.state.membership = membership
    school = db.get(School, membership.school_id)
    if not school:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "School not found")
    return school
