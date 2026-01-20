from pydantic import BaseModel
from typing import Optional
from datetime import date, time


class DTRBase(BaseModel):
    date: date
    scheduled_shift: Optional[str] = None
    time_in: Optional[time] = None
    time_out: Optional[time] = None
    break_in: Optional[time] = None
    break_out: Optional[time] = None
    total_hours: Optional[str] = None
    overtime_hours: Optional[str] = None
    status: str = "Present"
    remarks: Optional[str] = None
    is_manual_entry: bool = False


class DTRCreate(DTRBase):
    user_id: int


class DTRUpdate(BaseModel):
    scheduled_shift: Optional[str] = None
    time_in: Optional[time] = None
    time_out: Optional[time] = None
    break_in: Optional[time] = None
    break_out: Optional[time] = None
    total_hours: Optional[str] = None
    overtime_hours: Optional[str] = None
    status: Optional[str] = None
    remarks: Optional[str] = None


class DTRResponse(DTRBase):
    id: int
    user_id: int
    employee_name: Optional[str] = None
    employee_no: Optional[str] = None
    campaign: Optional[str] = None

    class Config:
        from_attributes = True


class DTRFilter(BaseModel):
    search: Optional[str] = None
    campaign: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    shift: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    limit: int = 50


class DTRStatistics(BaseModel):
    total_records: int
    present_count: int
    late_count: int
    absent_count: int
    incomplete_count: int
    on_leave_count: int
    total_overtime_hours: float
    average_hours_per_day: float


class DTRBulkUpload(BaseModel):
    records: list[DTRCreate]
