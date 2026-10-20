from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class FeeCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    default_amount: float = Field(ge=0)
    frequency: str = "monthly"


class FeeCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    name: str
    default_amount: float
    frequency: str


class InvoiceItemIn(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)


class InvoiceCreate(BaseModel):
    student_id: str
    title: str = Field(min_length=1, max_length=200)
    items: List[InvoiceItemIn] = Field(min_length=1)
    due_date: Optional[date] = None


class InvoiceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    description: str
    amount: float


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    student_id: str
    invoice_number: str
    title: str
    issue_date: date
    due_date: Optional[date]
    items: List[InvoiceItemResponse] = []
    total: float = 0
    paid: float = 0
    waived: float = 0
    balance: float = 0
    status: str = "unpaid"  # unpaid / partial / paid


class PaymentCreate(BaseModel):
    student_id: str
    invoice_id: Optional[str] = None
    amount: float = Field(gt=0)
    method: str = "cash"
    note: str = ""


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    student_id: str
    invoice_id: Optional[str]
    amount: float
    method: str
    note: str
    created_at: datetime


class AdjustmentCreate(BaseModel):
    student_id: str
    invoice_id: Optional[str] = None
    kind: Literal["waiver", "discount", "refund"]
    amount: float = Field(gt=0)
    reason: str = ""


class AdjustmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    student_id: str
    invoice_id: Optional[str]
    kind: str
    amount: float
    reason: str
    created_at: datetime


class StudentBalance(BaseModel):
    student_id: str
    admission_number: str
    student_name: str
    invoiced: float
    paid: float
    waived: float
    refunded: float
    balance: float
