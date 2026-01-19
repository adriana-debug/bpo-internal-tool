from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date
from enum import Enum

class EmployeeStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    TERMINATED = "Terminated"
    ON_LEAVE = "On Leave"
    PROBATION = "Probation"
    NEW_HIRE = "New Hire"
    RESIGNATION_PENDING = "Resignation Pending"

class EmployeeBase(BaseModel):
    employee_no: str = Field(..., min_length=1, max_length=50, description="Employee number")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    email: EmailStr = Field(..., description="Work email address")
    campaign: Optional[str] = Field(None, max_length=100, description="Campaign assignment")
    department: Optional[str] = Field(None, max_length=100, description="Department")
    date_of_joining: Optional[date] = Field(None, description="Date of joining")
    last_working_date: Optional[date] = Field(None, description="Last working date")
    phone_no: Optional[str] = Field(None, max_length=20, description="Phone number")
    personal_email: Optional[EmailStr] = Field(None, description="Personal email address")
    client_email: Optional[EmailStr] = Field(None, description="Client email address")
    assessment_due_date: Optional[date] = Field(None, description="Assessment due date")
    regularization_date: Optional[date] = Field(None, description="Regularization date")
    employee_status: EmployeeStatus = Field(EmployeeStatus.ACTIVE, description="Employee status")

class EmployeeCreate(EmployeeBase):
    password: str = Field(..., min_length=6, description="Password")
    role_name: str = Field(..., description="Role name")

class EmployeeUpdate(BaseModel):
    employee_no: Optional[str] = Field(None, min_length=1, max_length=50)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    campaign: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    date_of_joining: Optional[date] = None
    last_working_date: Optional[date] = None
    phone_no: Optional[str] = Field(None, max_length=20)
    personal_email: Optional[EmailStr] = None
    client_email: Optional[EmailStr] = None
    assessment_due_date: Optional[date] = None
    regularization_date: Optional[date] = None
    employee_status: Optional[EmployeeStatus] = None
    role_name: Optional[str] = None
    is_active: Optional[bool] = None

class EmployeeResponse(BaseModel):
    id: int
    employee_no: str
    full_name: str
    email: str
    campaign: Optional[str]
    department: Optional[str]
    date_of_joining: Optional[date]
    last_working_date: Optional[date]
    phone_no: Optional[str]
    personal_email: Optional[str]
    client_email: Optional[str]
    tenure_months: Optional[int]
    assessment_due_date: Optional[date]
    regularization_date: Optional[date]
    employee_status: str
    role_name: Optional[str]
    is_active: bool
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True

class EmployeeFilter(BaseModel):
    search: Optional[str] = Field(None, description="Search term for name, employee_no, email")
    campaign: Optional[str] = Field(None, description="Filter by campaign")
    department: Optional[str] = Field(None, description="Filter by department")
    employee_status: Optional[EmployeeStatus] = Field(None, description="Filter by status")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    role_name: Optional[str] = Field(None, description="Filter by role")
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(50, ge=1, le=10000, description="Records per page")
    
    # Sorting
    sort_by: Optional[str] = Field(None, description="Column to sort by (full_name, campaign, date_of_joining, last_working_date, employee_status, phone_no)")
    sort_order: Optional[str] = Field("asc", description="Sort order: 'asc' or 'desc'")

class EmployeeListResponse(BaseModel):
    employees: list[EmployeeResponse]
    total_count: int
    page: int
    limit: int
    total_pages: int