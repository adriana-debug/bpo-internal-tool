import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

import app.main
from app.main import app
from app.models.user import User
from fastapi.testclient import TestClient
import traceback

# Patch get_current_user directly
def override_get_current_user(request, db):
    print("DEBUG: Mocked get_current_user called")
    # Return a real user from DB to ensure permissions check works
    from app.models.user import User
    user = db.query(User).filter(User.is_active == True).first()
    print(f"DEBUG: Using user {user.full_name if user else 'None'}")
    return user

app.main.get_current_user = override_get_current_user

client = TestClient(app)

try:
    print("Sending GET request to /api/shift-schedule...")
    response = client.get("/api/shift-schedule?week=2026-01-19")
    print(f"Status: {response.status_code}")
    if response.status_code == 500:
        print(f"Detail: {response.text}")
    else:
        print(f"Response: {response.json().get('status')}")
except Exception:
    print("CAUGHT EXCEPTION IN TEST CLIENT:")
    traceback.print_exc()
