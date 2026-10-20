import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.security import utcnow


def _uuid() -> str:
    return str(uuid.uuid4())


class School(Base):
    __tablename__ = "schools"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(200), nullable=False)
    country = Column(String(100), default="")
    city = Column(String(100), default="")
    timezone = Column(String(64), default="UTC")
    language = Column(String(16), default="en")
    created_at = Column(DateTime, default=utcnow, nullable=False)

    members = relationship("SchoolMembership", back_populates="school")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid)
    email = Column(String(320), unique=True, nullable=False, index=True)
    password_hash = Column(String(512), nullable=False)
    full_name = Column(String(200), default="")
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class SchoolMembership(Base):
    __tablename__ = "school_memberships"
    __table_args__ = (UniqueConstraint("school_id", "user_id", name="uq_membership"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(50), default="owner", nullable=False)

    school = relationship("School", back_populates="members")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=_uuid)
    token = Column(String(128), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user_agent = Column(String(300), default="")
    created_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (UniqueConstraint("school_id", "admission_number", name="uq_admission"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    admission_number = Column(String(50), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), default="")
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(20), default="")
    class_name = Column(String(50), default="")
    section = Column(String(20), default="")
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    detail = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow, nullable=False)


class EmailVerificationCode(Base):
    __tablename__ = "email_verification_codes"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    code_hash = Column(String(128), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
