import requests
import json

base_url = "http://127.0.0.1:8002"
session = requests.Session()

def test_login_and_user_management():
    print("=== Testing Login and User Management ===")
    
    # Step 1: Test login
    print("\n1. Testing Login...")
    login_data = {
        'email': 'admin@bpo.com',
        'password': 'admin123'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    print(f"Login Response Status: {login_response.status_code}")
    print(f"Login Response Headers: {dict(login_response.headers)}")
    
    if login_response.status_code in [302, 200]:
        print("✅ Login successful!")
        
        # Step 2: Test accessing admin users page
        print("\n2. Testing Admin Users Page Access...")
        users_response = session.get(f"{base_url}/admin/users")
        print(f"Users Page Status: {users_response.status_code}")
        
        if users_response.status_code == 200:
            print("✅ Admin users page accessible!")
        else:
            print(f"❌ Admin users page failed: {users_response.text[:300]}")
            
        # Step 3: Test API endpoints
        print("\n3. Testing User API Endpoints...")
        
        # Test getting user by ID
        user_response = session.get(f"{base_url}/api/users/1")
        print(f"Get User API Status: {user_response.status_code}")
        if user_response.status_code == 200:
            print(f"User Data: {user_response.json()}")
        else:
            print(f"Get User API Error: {user_response.text}")
            
        # Test creating a new user
        print("\n4. Testing Create User API...")
        new_user_data = {
            'email': 'test.user@bpo.com',
            'password': 'password123',
            'full_name': 'Test User',
            'employee_no': 'E003',
            'role_name': 'agent',
            'department': 'Customer Service',
            'campaign': 'Client A'
        }
        
        create_response = session.post(f"{base_url}/api/users", data=new_user_data)
        print(f"Create User Status: {create_response.status_code}")
        if create_response.status_code == 200:
            print(f"Create User Response: {create_response.json()}")
        else:
            print(f"Create User Error: {create_response.text}")
            
    else:
        print(f"❌ Login failed: {login_response.text}")

if __name__ == "__main__":
    test_login_and_user_management()