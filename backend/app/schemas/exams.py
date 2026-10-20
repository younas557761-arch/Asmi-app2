from datetime import date, datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class GradeBandIn(BaseModel):
    grade: str = Field(min_length=1, max_length=10)
    min_percentage: int = Field(ge=0, le=100)


class GradingSchemeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    pass_mark: int = Field(default=40, ge=0, le=100)
    bands: List[GradeBandIn] = Field(default_factory=list)


class GradeBandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    grade: str
    min_percentage: int


class GradingSchemeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    name: str
    pass_mark: int
    bands: List[GradeBandResponse] = []


class ExaminationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date


class ExaminationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    name: str
    start_date: date
    end_date: date
    published: bool
    created_at: datetime


class MarkEntry(BaseModel):
    student_id: str
    subject: str = Field(min_length=1, max_length=100)
    max_marks: int = Field(default=100, gt=0)
    marks_obtained: int = Field(ge=0)


class MarkBulkCreate(BaseModel):
    records: List[MarkEntry] = Field(min_length=1, max_length=1000)


class MarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    subject: str
    max_marks: int
    marks_obtained: int


class StudentResult(BaseModel):
    student_id: str
    admission_number: str
    student_name: str
    total_obtained: int
    total_max: int
    percentage: float
    grade: str = ""
    passed: bool = False
