import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    hash_password,
    new_session_token,
    session_expiry,
    utcnow,
    verify_password,
)
from app.models import (
    PasswordResetToken,
    School,
    SchoolMembership,
    Session as UserSession,
    User,
)
from app.schemas import (
    LoginRequest,
    MeResponse,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    SchoolResponse,
)
from app.services.audit import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_session(response: Response, db: Session, user: User, request: Request) -> None:
    token = new_session_token()
    db.add(
        UserSession(
            token=token,
            user_id=user.id,
            user_agent=request.headers.get("user-agent", "")[:300],
            expires_at=session_expiry(settings.session_ttl_hours),
        )
    )
    db.commit()
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.env == "production",
        path="/",
    )


@router.post("/register", response_model=MeResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    if not data.accept_terms:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Terms must be accepted")
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    school = School(
        name=data.school_name,
        country=data.country,
        city=data.city,
        timezone=data.timezone,
        language=data.language,
    )
    db.add_all([user, school])
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    db.add(SchoolMembership(school_id=school.id, user_id=user.id, role="owner"))
    write_audit(db, school.id, user.id, "school.registered", f"school={school.name}")
    db.commit()

    _issue_session(response, db, user, request)
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role="owner",
        school=SchoolResponse.model_validate(school),
    )


@router.post("/login", response_model=MeResponse)
def login(data: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(user.password_hash, data.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    membership = db.query(SchoolMembership).filter(SchoolMembership.user_id == user.id).first()
    if not membership:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No school membership")

    _issue_session(response, db, user, request)
    school = db.get(School, membership.school_id)
    write_audit(db, school.id, user.id, "auth.login")
    db.commit()
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=membership.role,
        school=SchoolResponse.model_validate(school),
    )


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    sess = getattr(request.state, "session", None)
    if sess:
        sess.revoked = True
        db.commit()
    response.delete_cookie(settings.session_cookie_name, path="/")
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=MeResponse)
def me(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = db.query(SchoolMembership).filter(SchoolMembership.user_id == user.id).first()
    school = db.get(School, membership.school_id)
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=membership.role,
        school=SchoolResponse.model_validate(school),
    )


@router.post("/password-reset", response_model=MessageResponse)
def password_reset_request(data: PasswordResetRequest, db: Session = Depends(get_db)):
    """Creates a single-use reset token. Email adapter is pluggable; in development
    the token is returned so the flow is testable end to end."""
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user:
        return MessageResponse(message="If the email exists, a reset link was sent")
    token = new_session_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=session_expiry(1),
        )
    )
    db.commit()
    if settings.env == "development":
        return MessageResponse(message=f"Reset token (dev): {token}")
    return MessageResponse(message="If the email exists, a reset link was sent")


@router.post("/password-reset/confirm", response_model=MessageResponse)
def password_reset_confirm(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(data.token.encode()).hexdigest()
    row = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > utcnow(),
        )
        .first()
    )
    if not row:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired token")
    user = db.get(User, row.user_id)
    user.password_hash = hash_password(data.new_password)
    row.used = True
    db.query(UserSession).filter(UserSession.user_id == user.id).update({"revoked": True})
    db.commit()
    return MessageResponse(message="Password updated")
