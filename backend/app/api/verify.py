import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import session_expiry, utcnow
from app.models import EmailVerificationCode, User
from app.schemas import MessageResponse

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_ATTEMPTS = 5
CODE_TTL_HOURS = 1  # codes expire after 1 hour


class VerifyEmailConfirm(BaseModel):
    code: str = Field(min_length=6, max_length=6)


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


@router.post("/verify-email/request", response_model=MessageResponse)
def request_code(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.email_verified:
        return MessageResponse(message="Email already verified")
    code = f"{secrets.randbelow(900000) + 100000}"
    db.add(
        EmailVerificationCode(
            user_id=user.id,
            code_hash=_hash(code),
            expires_at=session_expiry(CODE_TTL_HOURS),
        )
    )
    db.commit()
    if settings.env == "development":
        return MessageResponse(message=f"Verification code (dev): {code}")
    return MessageResponse(message="If your email is correct, a 6-digit code was sent")


@router.post("/verify-email/confirm", response_model=MessageResponse)
def confirm_code(
    data: VerifyEmailConfirm,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(EmailVerificationCode)
        .filter(
            EmailVerificationCode.user_id == user.id,
            EmailVerificationCode.used.is_(False),
            EmailVerificationCode.expires_at > utcnow(),
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .first()
    )
    if not row:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired code. Request a new one.")
    if row.attempts >= MAX_ATTEMPTS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Request a new code.")
    if row.code_hash != _hash(data.code):
        row.attempts += 1
        db.commit()
        remaining = MAX_ATTEMPTS - row.attempts
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Invalid verification code. {remaining} attempts remaining.",
        )
    user.email_verified = True
    row.used = True
    db.commit()
    return MessageResponse(message="Email verified")
