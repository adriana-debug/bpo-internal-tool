#!/usr/bin/env python3
"""
Test script to diagnose login 500 error and database connection issues.
"""

import requests
import json
from sqlalchemy import inspect
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.rbac import Role

def test_database_connection():
    """Test if database connection is working"""
    print("=" * 60)
    print("1️⃣  TESTING DATABASE CONNECTION")
    print("=" * 60)
    try:
        db = SessionLocal()
        # Test simple query
        user_count = db.query(User).count()
        print(f"✅ Database connection OK")
        print(f"   Total users in database: {user_count}")
        
        # Test if admin user exists
        admin = db.query(User).filter(User.employee_no == "E001").first()
        if admin:
            print(f"✅ Admin user found: {admin.email}")
        else:
            print(f"⚠️  Admin user (E001) NOT found")
        
        # Test if roles table has data
        role_count = db.query(Role).count()
        print(f"✅ Roles in database: {role_count}")
        if role_count == 0:
            print(f"   ⚠️  WARNING: No roles found!")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def test_login_endpoint():
    """Test login endpoint with admin credentials"""
    print("\n" + "=" * 60)
    print("2️⃣  TESTING LOGIN ENDPOINT")
    print("=" * 60)
    
    db = SessionLocal()
    admin = db.query(User).filter(User.employee_no == "E001").first()
    db.close()
    
    if not admin:
        print("❌ Cannot test login - admin user not found")
        return False
    
    url = "http://localhost:8001/login"
    
    # Try with admin credentials (password: admin123)
    data = {
        "email": admin.email,
        "password": "admin123"
    }
    
    print(f"🔐 Testing login with:")
    print(f"   Email: {admin.email}")
    print(f"   Password: admin123")
    
    try:
        response = requests.post(url, data=data, allow_redirects=False)
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 500:
            print(f"\n❌ Login returned 500 Error")
            print(f"Response content: {response.text[:500]}")
            return False
        elif response.status_code == 302:
            print(f"\n✅ Login successful (redirected to {response.headers.get('location')})")
            return True
        else:
            print(f"\n⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing login: {str(e)}")
        return False

def test_database_schema():
    """Test if database tables exist and are properly configured"""
    print("\n" + "=" * 60)
    print("3️⃣  TESTING DATABASE SCHEMA")
    print("=" * 60)
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"✅ Database tables found: {len(tables)}")
        for table in sorted(tables):
            columns = inspector.get_columns(table)
            print(f"   • {table}: {len(columns)} columns")
        
        # Check critical tables
        critical_tables = ['user', 'rbac_role']
        for table in critical_tables:
            if table in tables:
                print(f"   ✅ {table} table exists")
            else:
                print(f"   ❌ {table} table MISSING")
        
        return True
    except Exception as e:
        print(f"❌ Schema inspection failed: {str(e)}")
        return False

def test_admin_user():
    """Check if admin user exists and has correct data"""
    print("\n" + "=" * 60)
    print("4️⃣  TESTING ADMIN USER")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        admin = db.query(User).filter(User.employee_no == "E001").first()
        
        if not admin:
            print("❌ Admin user (E001) not found in database")
            print("   You may need to run reset_db.py to initialize the database")
            return False
        
        print(f"✅ Admin user found:")
        print(f"   Employee No: {admin.employee_no}")
        print(f"   Email: {admin.email}")
        print(f"   Full Name: {admin.full_name}")
        print(f"   Has hashed_password: {admin.hashed_password is not None}")
        print(f"   Is Active: {admin.is_active}")
        
        # Check if password hash looks valid
        if admin.hashed_password and len(admin.hashed_password) > 10:
            print(f"   ✅ Password hash looks valid")
        else:
            print(f"   ❌ Password hash is missing or invalid!")
            return False
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Error checking admin user: {str(e)}")
        return False

def main():
    print("\n" + "🔍 BPO INTERNAL PLATFORM - LOGIN DIAGNOSTICS 🔍".center(60))
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Database Connection", test_database_connection()))
    results.append(("Database Schema", test_database_schema()))
    results.append(("Admin User", test_admin_user()))
    results.append(("Login Endpoint", test_login_endpoint()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✨ All tests passed! Login should be working.")
    else:
        print("\n⚠️  Some tests failed. See details above.")
        print("\n💡 SUGGESTIONS:")
        print("   1. If database not found, run: python reset_db.py")
        print("   2. If admin user missing, check seed process")
        print("   3. Ensure port 8001 is accessible")
        print("   4. Check that app/database.db exists")
    
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
