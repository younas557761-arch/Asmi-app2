from typing import List, Optional

from pydantic import BaseModel, Field


class PlanRequest(BaseModel):
    command: str = Field(min_length=3, max_length=500)


class PlanActionDetail(BaseModel):
    action: Optional[str] = None
    params: dict = {}
    confidence: str = "low"
    validation: dict = {}


class PlanResponse(BaseModel):
    id: str
    status: str
    engine: str
    command: str
    plan: PlanActionDetail


class ApproveRequest(BaseModel):
    plan_id: str


class ApproveResponse(BaseModel):
    plan_id: str
    status: str
    result: str


class AssistantAskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)


class AssistantAskResponse(BaseModel):
    text: str
    figures: dict = {}
    engine: str = "rule"


class ModulesResponse(BaseModel):
    items: List[dict]


class OnboardingReview(BaseModel):
    template_key: str
    school_name: str = Field(min_length=2, max_length=200)
    country: str = ""
    city: str = ""
    timezone: str = "UTC"
    currency: str = "PKR"
    language: str = "en"
    academic_year: str = "2026-2027"
    modules: List[str]


class WorkspaceResponse(BaseModel):
    school: dict
    classes_created: int
    subjects_created: int
    fee_categories_created: int
    modules_enabled: int
