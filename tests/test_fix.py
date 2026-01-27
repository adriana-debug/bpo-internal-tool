import requests

base_url = "http://127.0.0.1:8005"
session = requests.Session()

def test_user_management_fix():
    print("=== Testing User Management 500 Error Fix ===")
    
    # Step 1: Login as admin
    login_data = {
        'email': 'admin@bpo.com',
        'password': 'admin123'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    print(f"Login Status: {login_response.status_code}")
    
    if login_response.status_code in [302, 200]:
        print("✅ Login successful!")
        
        # Step 2: Test admin users page
        users_response = session.get(f"{base_url}/admin/users")
        print(f"Admin Users Page Status: {users_response.status_code}")
        
        if users_response.status_code == 200:
            print("✅ Admin users page loads successfully!")
            print("✅ 500 Internal Server Error FIXED!")
        elif users_response.status_code == 500:
            print("❌ 500 Internal Server Error still exists")
            print(f"Response: {users_response.text[:500]}")
        else:
            print(f"❌ Unexpected status: {users_response.status_code}")
            print(f"Response: {users_response.text[:300]}")
    else:
        print(f"❌ Login failed: {login_response.status_code}")

if __name__ == "__main__":
    test_user_management_fix()