from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AcademicYearCreate(BaseModel):
    name: str = Field(min_length=4, max_length=20)
    start_date: date
    end_date: date


class AcademicYearResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    name: str
    start_date: date
    end_date: date
    is_current: bool


class SchoolClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    capacity: int = Field(default=40, ge=1, le=500)
    academic_year_id: Optional[str] = None


class SchoolClassUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    capacity: Optional[int] = Field(default=None, ge=1, le=500)


class SchoolClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    academic_year_id: str
    name: str
    capacity: int


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = ""


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    name: str
    code: str


class TeacherCreate(BaseModel):
    employee_number: str = Field(min_length=1, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = ""
    email: str = ""
    phone: str = ""
    subject: str = ""


class TeacherUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[str] = None


class TeacherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    employee_number: str
    first_name: str
    last_name: str
    email: str
    phone: str
    subject: str
    status: str
    created_at: datetime


AttendanceStatus = Literal["present", "absent", "late", "excused"]


class AttendanceMark(BaseModel):
    student_id: str
    status: AttendanceStatus
    note: str = Field(default="", max_length=200)


class AttendanceBulkCreate(BaseModel):
    date: date
    records: list[AttendanceMark] = Field(min_length=1, max_length=500)


class AttendanceCorrection(BaseModel):
    status: AttendanceStatus
    note: str = Field(default="", max_length=200)


class AttendanceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    student_id: str
    class_name: str
    date: date
    status: str
    note: str
    created_at: datetime


class AttendanceSummaryResponse(BaseModel):
    date: date
    present: int
    absent: int
    late: int
    excused: int
    total: int
    marked: bool
