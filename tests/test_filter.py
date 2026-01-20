#!/usr/bin/env python3
"""Quick test script to debug filter-options directly"""
from app.core.database import SessionLocal
from app.services.employee_service import get_unique_values

db = SessionLocal()
try:
    print("Testing get_unique_values...")
    result = get_unique_values(db)
    print(f"Result: {result}")
    print(f"\nCampaigns ({len(result.get('campaigns', []))}): {result.get('campaigns', [])}")
    print(f"Departments ({len(result.get('departments', []))}): {result.get('departments', [])}")
    print(f"Statuses ({len(result.get('statuses', []))}): {result.get('statuses', [])}")
    print(f"Roles: {result.get('roles', [])}")
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
finally:
    db.close()
