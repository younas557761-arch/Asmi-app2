from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    school_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=200)
    country: str = ""
    city: str = ""
    timezone: str = "UTC"
    language: str = "en"
    accept_terms: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class SchoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    country: str
    city: str
    timezone: str
    language: str


class SchoolUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    country: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


class StudentCreate(BaseModel):
    admission_number: str = Field(min_length=1, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = ""
    gender: str = ""
    class_name: str = ""
    section: str = ""


class StudentUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = None
    gender: Optional[str] = None
    class_name: Optional[str] = None
    section: Optional[str] = None
    status: Optional[str] = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    admission_number: str
    first_name: str
    last_name: str
    gender: str
    class_name: str
    section: str
    status: str
    created_at: datetime


class MeResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    school: SchoolResponse


class MessageResponse(BaseModel):
    message: str
