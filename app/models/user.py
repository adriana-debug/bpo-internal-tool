from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    employee_no = Column(String(50), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    full_name = Column(String(255))
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=True)
    campaign = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    
    # Employee Directory specific fields
    date_of_joining = Column(Date, nullable=True)
    last_working_date = Column(Date, nullable=True)
    phone_no = Column(String(20), nullable=True)
    personal_email = Column(String(255), nullable=True)
    client_email = Column(String(255), nullable=True)
    tenure_months = Column(Integer, nullable=True)  # Calculated field in months
    assessment_due_date = Column(Date, nullable=True)
    regularization_date = Column(Date, nullable=True)
    employee_status = Column(String(50), default="Active")  # Active, Inactive, Terminated, On Leave, etc.
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    role = relationship("Role", back_populates="users")
    custom_permissions = relationship("UserModulePermission", foreign_keys="UserModulePermission.user_id", back_populates="user", cascade="all, delete-orphan")
    shift_schedules = relationship("ShiftSchedule", back_populates="user", cascade="all, delete-orphan")
    dtr_records = relationship("DailyTimeRecord", back_populates="user", cascade="all, delete-orphan")


class ShiftSchedule(Base):
    __tablename__ = "shift_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    schedule_date = Column(Date, index=True)  # Date of the shift
    day_of_week = Column(String(10))  # Monday, Tuesday, etc.
    shift_time = Column(String(50))  # "11pm to 7am", "9am to 5pm", etc.
    shift_start = Column(Time, nullable=True)  # 23:00
    shift_end = Column(Time, nullable=True)  # 07:00
    campaign = Column(String(100), nullable=True)
    notes = Column(String(500), nullable=True)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="shift_schedules")


class DailyTimeRecord(Base):
    __tablename__ = "daily_time_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    date = Column(Date, index=True)
    scheduled_shift = Column(String(50), nullable=True)  # "9am to 5pm"
    time_in = Column(Time, nullable=True)
    time_out = Column(Time, nullable=True)
    break_in = Column(Time, nullable=True)
    break_out = Column(Time, nullable=True)
    total_hours = Column(String(10), nullable=True)  # "8.5" hours
    overtime_hours = Column(String(10), nullable=True)  # "1.5" hours
    status = Column(String(20), default="Present")  # Present, Late, Absent, Incomplete, On Leave, Rest Day
    remarks = Column(String(500), nullable=True)
    is_manual_entry = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="dtr_records")
