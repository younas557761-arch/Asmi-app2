from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class GuardianCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    phone: str = ""
    student_ids: List[str] = Field(default_factory=list)
    relation: str = "guardian"


class GuardianLink(BaseModel):
    student_id: str
    relation: str = "guardian"


class GuardianResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    full_name: str
    email: str
    phone: str
    status: str
    children: List[dict] = []
    created_at: datetime


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    audience: Literal["all", "parents", "class"] = "all"
    class_name: str = ""


class AnnouncementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    title: str
    body: str
    audience: str
    class_name: str
    status: str
    published_at: Optional[datetime] = None
    created_at: datetime
