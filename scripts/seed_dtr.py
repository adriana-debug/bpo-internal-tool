"""
Seed DTR (Daily Time Record) data for the past 3 months
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, time, timedelta
import random
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, DailyTimeRecord


# Shift configurations
SHIFTS = [
    ("6am to 2pm", time(6, 0), time(14, 0)),
    ("7am to 3pm", time(7, 0), time(15, 0)),
    ("8am to 4pm", time(8, 0), time(16, 0)),
    ("9am to 5pm", time(9, 0), time(17, 0)),
    ("10am to 6pm", time(10, 0), time(18, 0)),
    ("11am to 7pm", time(11, 0), time(19, 0)),
    ("12pm to 8pm", time(12, 0), time(20, 0)),
    ("2pm to 10pm", time(14, 0), time(22, 0)),
    ("3pm to 11pm", time(15, 0), time(23, 0)),
    ("10pm to 6am", time(22, 0), time(6, 0)),
    ("11pm to 7am", time(23, 0), time(7, 0)),
]


def random_time_variation(base_time: time, max_minutes: int = 30) -> time:
    """Add random variation to a time"""
    minutes = base_time.hour * 60 + base_time.minute
    variation = random.randint(-max_minutes, max_minutes)
    new_minutes = max(0, min(23 * 60 + 59, minutes + variation))
    return time(new_minutes // 60, new_minutes % 60)


def calculate_hours(time_in: time, time_out: time, break_minutes: int = 60) -> float:
    """Calculate total working hours"""
    if not time_in or not time_out:
        return 0.0

    in_minutes = time_in.hour * 60 + time_in.minute
    out_minutes = time_out.hour * 60 + time_out.minute

    # Handle overnight shifts
    if out_minutes < in_minutes:
        out_minutes += 24 * 60

    worked_minutes = out_minutes - in_minutes - break_minutes
    return max(0, worked_minutes / 60)


def seed_dtr(db: Session):
    """Seed DTR records for all active employees for the past 3 months"""

    # Check if DTR records already exist
    existing_count = db.query(DailyTimeRecord).count()
    if existing_count > 0:
        print(f"DTR records already exist ({existing_count} records). Skipping seed.")
        return

    # Get all active employees
    employees = db.query(User).filter(
        User.is_active == True,
        User.employee_status == "Active"
    ).all()

    if not employees:
        print("No active employees found")
        return

    print(f"Seeding DTR for {len(employees)} employees...")

    # Generate dates for the past 3 months
    today = date.today()
    start_date = date(today.year, today.month - 3, 1) if today.month > 3 else date(today.year - 1, today.month + 9, 1)

    records_created = 0

    for employee in employees:
        # Assign a random shift to each employee
        shift_name, shift_start, shift_end = random.choice(SHIFTS)

        # Generate DTR for each day
        current_date = start_date
        while current_date <= today:
            # Skip weekends for most employees (80% chance)
            day_of_week = current_date.weekday()
            is_weekend = day_of_week >= 5

            if is_weekend and random.random() < 0.8:
                # Rest day
                dtr = DailyTimeRecord(
                    user_id=employee.id,
                    date=current_date,
                    scheduled_shift=shift_name,
                    status="Rest Day"
                )
                db.add(dtr)
                records_created += 1
                current_date += timedelta(days=1)
                continue

            # Determine status for this day
            rand = random.random()
            if rand < 0.02:  # 2% absent
                status = "Absent"
                time_in = None
                time_out = None
                break_in = None
                break_out = None
                total_hours = "0"
                overtime = "0"
            elif rand < 0.05:  # 3% on leave
                status = "On Leave"
                time_in = None
                time_out = None
                break_in = None
                break_out = None
                total_hours = "0"
                overtime = "0"
            elif rand < 0.10:  # 5% incomplete
                status = "Incomplete"
                time_in = random_time_variation(shift_start, 15)
                time_out = None
                break_in = None
                break_out = None
                total_hours = "0"
                overtime = "0"
            elif rand < 0.25:  # 15% late
                status = "Late"
                # Late by 5-45 minutes
                late_minutes = random.randint(5, 45)
                in_minutes = shift_start.hour * 60 + shift_start.minute + late_minutes
                time_in = time(in_minutes // 60, in_minutes % 60)
                time_out = random_time_variation(shift_end, 30)
                break_start = time(12, 0) if shift_start.hour < 12 else time(18, 0)
                break_in = random_time_variation(break_start, 10)
                break_minutes = break_in.hour * 60 + break_in.minute + random.randint(45, 75)
                break_out = time(break_minutes // 60 % 24, break_minutes % 60)

                hours = calculate_hours(time_in, time_out)
                total_hours = f"{hours:.1f}"
                overtime = "0"
            else:  # 75% present on time
                status = "Present"
                time_in = random_time_variation(shift_start, 10)
                time_out = random_time_variation(shift_end, 30)
                break_start = time(12, 0) if shift_start.hour < 12 else time(18, 0)
                break_in = random_time_variation(break_start, 10)
                break_minutes = break_in.hour * 60 + break_in.minute + random.randint(45, 75)
                break_out = time(break_minutes // 60 % 24, break_minutes % 60)

                hours = calculate_hours(time_in, time_out)
                total_hours = f"{hours:.1f}"

                # 20% chance of overtime (1-3 hours)
                if random.random() < 0.2:
                    ot_hours = random.uniform(0.5, 3.0)
                    overtime = f"{ot_hours:.1f}"
                    hours += ot_hours
                    total_hours = f"{hours:.1f}"
                else:
                    overtime = "0"

            dtr = DailyTimeRecord(
                user_id=employee.id,
                date=current_date,
                scheduled_shift=shift_name,
                time_in=time_in,
                time_out=time_out,
                break_in=break_in,
                break_out=break_out,
                total_hours=total_hours,
                overtime_hours=overtime,
                status=status,
                is_manual_entry=False
            )
            db.add(dtr)
            records_created += 1

            current_date += timedelta(days=1)

        # Commit in batches
        if records_created % 1000 == 0:
            db.commit()
            print(f"  Created {records_created} records...")

    db.commit()
    print(f"DTR seeding complete. Created {records_created} records.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_dtr(db)
    finally:
        db.close()
