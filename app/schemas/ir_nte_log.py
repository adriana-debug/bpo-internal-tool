from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class IRNTELogBase(BaseModel):
    doc_type: str  # IR or NTE
    filed_date: date
    complaint_violation: str
    received_date: Optional[date] = None
    nte_date: Optional[date] = None
    remarks: Optional[str] = None


class IRNTELogCreate(IRNTELogBase):
    employee_id: int
    attachment_path: Optional[str] = None
    nte_form_path: Optional[str] = None


class IRNTELogUpdate(BaseModel):
    doc_type: Optional[str] = None
    filed_date: Optional[date] = None
    complaint_violation: Optional[str] = None
    received_date: Optional[date] = None
    nte_date: Optional[date] = None
    has_explanation: Optional[bool] = None
    explanation_date: Optional[date] = None
    explanation_summary: Optional[str] = None
    attachment_path: Optional[str] = None
    nte_form_path: Optional[str] = None
    status: Optional[str] = None
    resolution: Optional[str] = None
    resolution_date: Optional[date] = None
    remarks: Optional[str] = None


class IRNTELogResponse(IRNTELogBase):
    id: int
    doc_id: str
    employee_id: int
    employee_name: Optional[str] = None
    employee_no: Optional[str] = None
    campaign: Optional[str] = None
    has_explanation: bool
    explanation_date: Optional[date] = None
    explanation_summary: Optional[str] = None
    attachment_path: Optional[str] = None
    nte_form_path: Optional[str] = None
    status: str
    resolution: Optional[str] = None
    resolution_date: Optional[date] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IRNTELogFilter(BaseModel):
    search: Optional[str] = None
    doc_type: Optional[str] = None
    status: Optional[str] = None
    campaign: Optional[str] = None
    filed_date_from: Optional[date] = None
    filed_date_to: Optional[date] = None
    nte_date_from: Optional[date] = None
    nte_date_to: Optional[date] = None
    has_explanation: Optional[bool] = None
    page: int = 1
    limit: int = 50


class IRNTELogStatistics(BaseModel):
    total_records: int
    open_count: int
    pending_count: int
    under_review_count: int
    resolved_count: int
    escalated_count: int
    ir_count: int
    nte_count: int
