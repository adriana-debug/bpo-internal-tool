#!/usr/bin/env python3
"""
Test script to verify that the user management page loads without 500 errors
"""

import requests
import time

# Configuration
BASE_URL = "http://127.0.0.1:8002"
LOGIN_URL = f"{BASE_URL}/"
ADMIN_USERS_URL = f"{BASE_URL}/admin/users"

def test_user_management():
    """Test that admin user can access user management page without 500 error"""
    session = requests.Session()
    
    print("🧪 Testing User Management Page Fix")
    print("=" * 50)
    
    try:
        # Step 1: Get login page
        print("📋 Step 1: Getting login page...")
        response = session.get(LOGIN_URL)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed to get login page: {response.status_code}")
            return False
            
        # Step 2: Login as admin
        print("🔐 Step 2: Logging in as admin...")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
        print(f"   Status: {response.status_code}")
        print(f"   Redirect: {response.headers.get('location', 'No redirect')}")
        
        if response.status_code not in [302, 303]:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
        # Check if we have authentication cookie
        auth_cookie = None
        for cookie in session.cookies:
            if cookie.name == "access_token":
                auth_cookie = cookie.value
                break
                
        if not auth_cookie:
            print("❌ No authentication cookie received")
            return False
            
        print(f"✅ Login successful! Auth cookie: {auth_cookie[:20]}...")
        
        # Step 3: Access user management page
        print("👥 Step 3: Accessing user management page...")
        response = session.get(ADMIN_USERS_URL)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"   Content-Length: {len(response.text)} bytes")
        
        if response.status_code == 500:
            print("❌ 500 Internal Server Error still occurring!")
            print("   First 500 chars of response:")
            print(response.text[:500])
            return False
        elif response.status_code == 200:
            print("✅ User management page loaded successfully!")
            
            # Check for key elements that should be present
            content = response.text
            checks = [
                ("User Management title", "User Management" in content),
                ("Stats section", "Stats" in content),
                ("Active users count", "Active" in content),
                ("Inactive users count", "Inactive" in content),
                ("Users table", "table" in content or "tbody" in content),
            ]
            
            print("\n🔍 Content validation:")
            all_passed = True
            for check_name, passed in checks:
                status = "✅" if passed else "❌"
                print(f"   {status} {check_name}")
                if not passed:
                    all_passed = False
                    
            if all_passed:
                print("\n🎉 All tests passed! The 500 error has been resolved.")
                return True
            else:
                print("\n⚠️  Page loads but some content may be missing.")
                return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting user management page test...\n")
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    success = test_user_management()
    
    if success:
        print("\n🎯 SUCCESS: User management page is working correctly!")
    else:
        print("\n💥 FAILURE: Issues found with user management page.")
    
    print("\nTest completed.")