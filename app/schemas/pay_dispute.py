from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class PayDisputeBase(BaseModel):
    dispute_type: str
    pay_period: str
    disputed_amount: Optional[float] = None
    subject: str
    description: str
    supporting_docs: Optional[str] = None
    priority: str = "Medium"


class PayDisputeCreate(PayDisputeBase):
    employee_id: int


class PayDisputeUpdate(BaseModel):
    dispute_type: Optional[str] = None
    pay_period: Optional[str] = None
    disputed_amount: Optional[float] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    supporting_docs: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None
    resolution_notes: Optional[str] = None
    resolution_amount: Optional[float] = None
    resolved_date: Optional[date] = None


class PayDisputeResponse(PayDisputeBase):
    id: int
    ticket_no: str
    employee_id: int
    employee_name: Optional[str] = None
    employee_no: Optional[str] = None
    campaign: Optional[str] = None
    status: str
    assigned_to: Optional[int] = None
    assignee_name: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolution_amount: Optional[float] = None
    resolved_date: Optional[date] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PayDisputeFilter(BaseModel):
    search: Optional[str] = None
    status: Optional[str] = None
    dispute_type: Optional[str] = None
    priority: Optional[str] = None
    campaign: Optional[str] = None
    assigned_to: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = 1
    limit: int = 50


class PayDisputeStatistics(BaseModel):
    total_disputes: int
    open_count: int
    under_review_count: int
    pending_payroll_count: int
    resolved_count: int
    rejected_count: int
    escalated_count: int
    total_disputed_amount: float
    total_resolved_amount: float


class PayDisputeCommentCreate(BaseModel):
    comment: str
    is_internal: bool = False


class PayDisputeCommentResponse(BaseModel):
    id: int
    dispute_id: int
    user_id: int
    user_name: Optional[str] = None
    comment: str
    is_internal: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
