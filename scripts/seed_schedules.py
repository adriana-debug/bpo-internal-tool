#!/usr/bin/env python3
"""
Seed database with shift schedules for all active employees.

Creates schedules for the current week (Monday to Friday)
with different shift times and campaigns matching employee data.

Shift Types:
- 9am to 5pm (Morning)
- 11pm to 7am (Night) 
- 12pm to 8pm (Afternoon)
- 6am to 2pm (Early Morning)

Distribution: Random assignment per employee
"""

import random
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import SessionLocal
from app.models.user import User
from app.models.user import ShiftSchedule

# Shift time options
SHIFT_TIMES = [
    "9am to 5pm",
    "11pm to 7am",
    "12pm to 8pm",
    "6am to 2pm"
]

# Shift start/end times mapping
SHIFT_TIMES_MAP = {
    "9am to 5pm": (time(9, 0), time(17, 0)),
    "11pm to 7am": (time(23, 0), time(7, 0)),
    "12pm to 8pm": (time(12, 0), time(20, 0)),
    "6am to 2pm": (time(6, 0), time(14, 0))
}

def seed_schedules(db: Session):
    """
    Seed shift schedules for all active employees.
    
    - Creates schedules for current week (Mon-Fri)
    - Random shift assignment per employee
    - No duplicates (checks existing schedules first)
    """
    print("Starting shift schedule seed process...")
    
    # Get all active employees (excluding admin)
    active_employees = db.query(User).filter(
        and_(
            User.is_active == True,
            User.employee_no != "E001"
        )
    ).all()
    
    if not active_employees:
        print("No active employees found. Skipping seed...")
        return
    
    print(f"Found {len(active_employees)} active employees")
    
    # Get current week's Monday
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Working days (Mon-Fri)
    working_days = []
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    for i in range(5):  # Monday to Friday
        day_date = monday + timedelta(days=i)
        working_days.append({
            'date': day_date,
            'day_name': day_names[i]
        })
    
    print(f"Creating schedules for week starting: {monday.date()}")
    
    schedules_created = 0
    schedules_skipped = 0
    
    # Create schedules for each employee for each working day
    for employee in active_employees:
        for day in working_days:
            # Check if schedule already exists for this employee and date
            existing = db.query(ShiftSchedule).filter(
                and_(
                    ShiftSchedule.user_id == employee.id,
                    ShiftSchedule.schedule_date == day['date'].date()
                )
            ).first()
            
            if existing:
                schedules_skipped += 1
                continue
            
            # Random shift assignment
            shift_time = random.choice(SHIFT_TIMES)
            shift_start, shift_end = SHIFT_TIMES_MAP[shift_time]
            
            # Create schedule
            schedule = ShiftSchedule(
                user_id=employee.id,
                schedule_date=day['date'].date(),
                day_of_week=day['day_name'],
                shift_time=shift_time,
                shift_start=shift_start,
                shift_end=shift_end,
                campaign=employee.campaign,  # Use employee's assigned campaign
                notes=None,
                is_published=False
            )
            
            db.add(schedule)
            schedules_created += 1
    
    # Commit all changes
    try:
        db.commit()
        print(f"Shift schedules created: {schedules_created}")
        if schedules_skipped > 0:
            print(f"Schedules skipped (duplicates): {schedules_skipped}")
        print(f"Total records: {schedules_created + schedules_skipped}")
    except Exception as e:
        db.rollback()
        print(f"Error creating schedules: {e}")
        raise

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_schedules(db)
    finally:
        db.close()
