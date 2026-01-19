from pydantic import BaseModel
from datetime import date, time
from typing import Optional, List

class ShiftScheduleBase(BaseModel):
    schedule_date: date
    day_of_week: str
    shift_time: str
    campaign: str
    notes: Optional[str] = None

class ShiftScheduleSave(BaseModel):
    user_id: int
    schedule_date: date
    shift_time: str
    campaign: str
    notes: Optional[str] = None

class ShiftScheduleResponse(ShiftScheduleBase):
    id: int
    user_id: int
    shift_start: int
    shift_end: int
    is_published: bool
    
    class Config:
        from_attributes = True

class ShiftScheduleUpload(BaseModel):
    employee_no: str
    date: str
    shift_time: str
    campaign: str
    notes: Optional[str] = None

class WeeklyScheduleResponse(BaseModel):
    employee_id: int
    employee_name: str
    employee_no: str
    campaign: str
    schedules: dict  # {day_name: shift_time, ...}

class ScheduleFilterOptions(BaseModel):
    campaigns: List[str]
    shifts: List[str]
    employees: List[dict]
