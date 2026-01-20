"""
Test script to verify filter functionality for KPI cards
"""
import requests
import json

BASE_URL = "http://localhost:8005/api"
HEADERS = {"Accept": "application/json"}

# Test credentials
login_url = "http://localhost:8005/login"
session = requests.Session()

# Login first
print("🔐 Logging in...")
login_data = {"email": "admin@bpo.com", "password": "admin123"}
response = session.post(login_url, data=login_data)
print(f"Login status: {response.status_code}")

print("\n" + "="*70)
print("TEST 1: Get all employees (no filters)")
print("="*70)
response = session.get(f"{BASE_URL}/employees?limit=10000")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Total employees: {data['total_count']}")
    print(f"   Employees in response: {len(data['employees'])}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)

print("\n" + "="*70)
print("TEST 2: Search filter (search='john')")
print("="*70)
response = session.get(f"{BASE_URL}/employees?search=john&limit=10000")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Employees with 'john': {data['total_count']}")
    if data['employees']:
        print(f"   First result: {data['employees'][0]['full_name']} ({data['employees'][0]['email']})")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)

print("\n" + "="*70)
print("TEST 3: Department filter")
print("="*70)
# First get available departments
response = session.get(f"{BASE_URL}/employees/filter-options")
if response.status_code == 200:
    data = response.json()
    if data.get('departments'):
        dept = data['departments'][0]
        print(f"Testing with department: {dept}")
        
        response = session.get(f"{BASE_URL}/employees?department={dept}&limit=10000")
        if response.status_code == 200:
            filter_data = response.json()
            print(f"✅ Employees in {dept}: {filter_data['total_count']}")
        else:
            print(f"❌ Error: {response.status_code}")
else:
    print(f"❌ Could not get filter options: {response.status_code}")

print("\n" + "="*70)
print("TEST 4: Status filter (employee_status='Active')")
print("="*70)
response = session.get(f"{BASE_URL}/employees?employee_status=Active&limit=10000")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Active employees: {data['total_count']}")
    if data['employees']:
        statuses = set(emp['employee_status'] for emp in data['employees'])
        print(f"   Statuses in results: {statuses}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)

print("\n" + "="*70)
print("TEST 5: Campaign filter")
print("="*70)
response = session.get(f"{BASE_URL}/employees/filter-options")
if response.status_code == 200:
    data = response.json()
    if data.get('campaigns'):
        campaign = data['campaigns'][0]
        print(f"Testing with campaign: {campaign}")
        
        response = session.get(f"{BASE_URL}/employees?campaign={campaign}&limit=10000")
        if response.status_code == 200:
            filter_data = response.json()
            print(f"✅ Employees in {campaign}: {filter_data['total_count']}")
        else:
            print(f"❌ Error: {response.status_code}")
else:
    print(f"❌ Could not get filter options: {response.status_code}")

print("\n" + "="*70)
print("TEST 6: Combined filters (department + status)")
print("="*70)
response = session.get(f"{BASE_URL}/employees/filter-options")
if response.status_code == 200:
    data = response.json()
    if data.get('departments'):
        dept = data['departments'][0]
        
        response = session.get(f"{BASE_URL}/employees?department={dept}&employee_status=Active&limit=10000")
        if response.status_code == 200:
            filter_data = response.json()
            print(f"✅ Employees in {dept} with Active status: {filter_data['total_count']}")
            
            # Verify all results match filters
            all_match = all(
                emp['department'] == dept and emp['employee_status'] == 'Active'
                for emp in filter_data['employees']
            )
            if all_match:
                print(f"   ✅ All results match the filters")
            else:
                print(f"   ❌ Some results don't match the filters!")
        else:
            print(f"❌ Error: {response.status_code}")

print("\n" + "="*70)
print("✅ All filter tests completed!")
print("="*70)
