import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)

from app.core.database import Base
from app.core.security import utcnow


def _uuid() -> str:
    return str(uuid.uuid4())


class Guardian(Base):
    __tablename__ = "guardians"
    __table_args__ = (UniqueConstraint("school_id", "email", name="uq_guardian_email"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    email = Column(String(320), nullable=False)
    phone = Column(String(30), default="")
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class StudentGuardian(Base):
    __tablename__ = "student_guardians"
    __table_args__ = (UniqueConstraint("student_id", "guardian_id", name="uq_student_guardian"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    guardian_id = Column(String(36), ForeignKey("guardians.id"), nullable=False, index=True)
    relation = Column(String(30), default="guardian", nullable=False)  # father/mother/guardian
    created_at = Column(DateTime, default=utcnow, nullable=False)


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    audience = Column(String(20), default="all", nullable=False)  # all / parents / class
    class_name = Column(String(50), default="")
    status = Column(String(20), default="draft", nullable=False)  # draft / published
    published_at = Column(DateTime, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
