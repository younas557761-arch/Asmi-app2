import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from app.core.database import Base
from app.core.security import utcnow


def _uuid() -> str:
    return str(uuid.uuid4())


class Examination(Base):
    __tablename__ = "examinations"
    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_exam_name"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    published = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class Mark(Base):
    __tablename__ = "marks"
    __table_args__ = (UniqueConstraint("examination_id", "student_id", "subject", name="uq_mark"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    examination_id = Column(String(36), ForeignKey("examinations.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    subject = Column(String(100), nullable=False)
    max_marks = Column(Integer, nullable=False, default=100)
    marks_obtained = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class GradingScheme(Base):
    __tablename__ = "grading_schemes"
    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_scheme_name"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    pass_mark = Column(Integer, default=40, nullable=False)  # percentage
    created_at = Column(DateTime, default=utcnow, nullable=False)


class GradeBand(Base):
    __tablename__ = "grade_bands"
    __table_args__ = (UniqueConstraint("scheme_id", "grade", name="uq_band_grade"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    scheme_id = Column(String(36), ForeignKey("grading_schemes.id"), nullable=False, index=True)
    grade = Column(String(10), nullable=False)
    min_percentage = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
