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


class AcademicYear(Base):
    __tablename__ = "academic_years"
    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_year_name"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    name = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class SchoolClass(Base):
    __tablename__ = "classes"
    __table_args__ = (UniqueConstraint("school_id", "academic_year_id", "name", name="uq_class_name"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    capacity = Column(Integer, default=40, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_subject_name"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), default="")
    created_at = Column(DateTime, default=utcnow, nullable=False)


class Teacher(Base):
    __tablename__ = "teachers"
    __table_args__ = (UniqueConstraint("school_id", "employee_number", name="uq_employee_number"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    employee_number = Column(String(50), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), default="")
    email = Column(String(320), default="")
    phone = Column(String(30), default="")
    subject = Column(String(100), default="")
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("school_id", "student_id", "date", name="uq_attendance_day"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    school_id = Column(String(36), ForeignKey("schools.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    class_name = Column(String(50), default="")
    date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False)
    note = Column(String(200), default="")
    marked_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
