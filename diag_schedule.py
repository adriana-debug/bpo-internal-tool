import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from app.services.shift_schedule_service import ShiftScheduleService
from app.core.database import SessionLocal
from datetime import datetime
import traceback

try:
    print("Initializing DB session...")
    db = SessionLocal()
    print("Calling get_weekly_schedule...")
    res = ShiftScheduleService.get_weekly_schedule(db, datetime.fromisoformat('2026-01-19'))
    print(f"Success! Found {len(res)} employees.")
    for r in res[:2]:
        print(f" - {r['employee_name']}: {r['schedules']}")
    db.close()
except Exception:
    print("CAUGHT EXCEPTION:")
    traceback.print_exc()
finally:
    if 'db' in locals():
        db.close()
