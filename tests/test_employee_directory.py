#!/usr/bin/env python3
"""
EMPLOYEE DIRECTORY FUNCTIONALITY TEST REPORT
============================================

This script tests all major features of the Employee Directory application.
"""

import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:8005'
session = requests.Session()

# Login
session.post(
    f'{BASE_URL}/login',
    data={'email': 'admin@bpo.com', 'password': 'admin123'},
    allow_redirects=False
)

test_results = {
    'timestamp': datetime.now().isoformat(),
    'base_url': BASE_URL,
    'tests': {}
}

print("=" * 70)
print("EMPLOYEE DIRECTORY FUNCTIONALITY TEST REPORT")
print("=" * 70)
print(f"Timestamp: {test_results['timestamp']}")
print(f"Server: {BASE_URL}")
print()

# ===== TEST 1: Filter Options =====
print("1. FILTER OPTIONS ENDPOINT")
print("-" * 70)
resp = session.get(f'{BASE_URL}/api/employees/filter-options')
if resp.status_code == 200:
    data = resp.json()
    test_results['tests']['filter_options'] = 'PASS'
    print(f"Status: PASS (HTTP {resp.status_code})")
    print(f"Campaigns available: {len(data.get('campaigns', []))}")
    print(f"  {data.get('campaigns', [])}")
    print(f"Departments available: {len(data.get('departments', []))}")
    print(f"  {data.get('departments', [])[:5]}...")
    print(f"Statuses available: {len(data.get('statuses', []))}")
    print(f"  {data.get('statuses', [])}")
    print(f"Roles available: {len(data.get('roles', []))}")
else:
    test_results['tests']['filter_options'] = 'FAIL'
    print(f"Status: FAIL (HTTP {resp.status_code})")
print()

# ===== TEST 2: Employee Listing =====
print("2. EMPLOYEE LIST ENDPOINT")
print("-" * 70)
resp = session.get(f'{BASE_URL}/api/employees?page=1&limit=5')
if resp.status_code == 200:
    data = resp.json()
    test_results['tests']['employee_list'] = 'PASS'
    print(f"Status: PASS (HTTP {resp.status_code})")
    print(f"Total employees: {data.get('total_count', 0)}")
    print(f"Total pages: {data.get('total_pages', 0)}")
    print(f"Employees per page: {len(data.get('employees', []))}")
    print(f"First 3 employees:")
    for emp in data.get('employees', [])[:3]:
        print(f"  - {emp['full_name']} ({emp['employee_no']}) - {emp['employee_status']}")
else:
    test_results['tests']['employee_list'] = 'FAIL'
    print(f"Status: FAIL (HTTP {resp.status_code})")
print()

# ===== TEST 3: Campaign Filter =====
print("3. CAMPAIGN FILTER")
print("-" * 70)
resp = session.get(f'{BASE_URL}/api/employees?campaign=Campaign%20A&limit=5')
if resp.status_code == 200:
    data = resp.json()
    test_results['tests']['campaign_filter'] = 'PASS'
    print(f"Status: PASS (HTTP {resp.status_code})")
    print(f"Filter: Campaign A")
    print(f"Total matching: {data.get('total_count', 0)}")
    print(f"Employees returned: {len(data.get('employees', []))}")
    for emp in data.get('employees', [])[:2]:
        print(f"  - {emp['full_name']} - Campaign: {emp.get('campaign', 'N/A')}")
else:
    test_results['tests']['campaign_filter'] = 'FAIL'
    print(f"Status: FAIL (HTTP {resp.status_code})")
print()

# ===== TEST 4: Department Filter =====
print("4. DEPARTMENT FILTER")
print("-" * 70)
resp = session.get(f'{BASE_URL}/api/employees?department=Support&limit=5')
if resp.status_code == 200:
    data = resp.json()
    test_results['tests']['department_filter'] = 'PASS'
    print(f"Status: PASS (HTTP {resp.status_code})")
    print(f"Filter: Support department")
    print(f"Total matching: {data.get('total_count', 0)}")
    print(f"Employees returned: {len(data.get('employees', []))}")
    for emp in data.get('employees', [])[:2]:
        print(f"  - {emp['full_name']} - Dept: {emp.get('department', 'N/A')}")
else:
    test_results['tests']['department_filter'] = 'FAIL'
    print(f"Status: FAIL (HTTP {resp.status_code})")
print()

# ===== TEST 5: Status Filter =====
print("5. STATUS FILTER")
print("-" * 70)
resp = session.get(f'{BASE_URL}/api/employees?employee_status=Active&limit=5')
if resp.status_code == 200:
    data = resp.json()
    test_results['tests']['status_filter'] = 'PASS'
    print(f"Status: PASS (HTTP {resp.status_code})")
    print(f"Filter: Active employees")
    print(f"Total matching: {data.get('total_count', 0)}")
    print(f"Employees returned: {len(data.get('employees', []))}")
else:
    test_results['tests']['status_filter'] = 'FAIL'
    print(f"Status: FAIL (HTTP {resp.status_code})")
print()

# ===== TEST 6: Search Functionality =====
print("6. SEARCH FUNCTIONALITY")
print("-" * 70)
searches = [('Amanda', 5), ('E01139', 1), ('Garcia', 7)]
all_search_pass = True
for search_term, expected_min in searches:
    resp = session.get(f'{BASE_URL}/api/employees?search={search_term}&limit=10')
    if resp.status_code == 200:
        data = resp.json()
        total = data.get('total_count', 0)
        status = "PASS" if total >= expected_min else "PARTIAL"
        if status == "PARTIAL":
            all_search_pass = False
        print(f"  {search_term}: Found {total} employees - {status}")
    else:
        print(f"  {search_term}: FAIL (HTTP {resp.status_code})")
        all_search_pass = False
test_results['tests']['search'] = 'PASS' if all_search_pass else 'PARTIAL'
print()

# ===== TEST 7: Pagination =====
print("7. PAGINATION")
print("-" * 70)
pagination_pass = True
for page in [1, 2, 5]:
    resp = session.get(f'{BASE_URL}/api/employees?page={page}&limit=10')
    if resp.status_code == 200:
        data = resp.json()
        emp_count = len(data.get('employees', []))
        if emp_count <= 10:
            print(f"  Page {page}: {emp_count} employees - PASS")
        else:
            print(f"  Page {page}: {emp_count} employees - FAIL (exceeds limit)")
            pagination_pass = False
    else:
        print(f"  Page {page}: FAIL (HTTP {resp.status_code})")
        pagination_pass = False
test_results['tests']['pagination'] = 'PASS' if pagination_pass else 'FAIL'
print()

# ===== TEST 8: Statistics Endpoint =====
print("8. STATISTICS ENDPOINT")
print("-" * 70)
resp = session.get(f'{BASE_URL}/api/employees/statistics')
if resp.status_code == 200:
    data = resp.json()
    test_results['tests']['statistics'] = 'PASS'
    print(f"Status: PASS (HTTP {resp.status_code})")
    for key in ['total_employees', 'active_employees', 'on_leave', 'terminated']:
        if key in data:
            print(f"  {key}: {data[key]}")
else:
    test_results['tests']['statistics'] = 'FAIL'
    print(f"Status: FAIL (HTTP {resp.status_code})")
print()

# ===== SUMMARY =====
print("=" * 70)
print("TEST SUMMARY")
print("=" * 70)
passed = sum(1 for v in test_results['tests'].values() if v == 'PASS')
total = len(test_results['tests'])
print(f"Total Tests: {total}")
print(f"Passed: {passed}")
print(f"Failed: {total - passed}")
print(f"Success Rate: {(passed/total)*100:.1f}%")
print()
print("Test Results:")
for test_name, result in test_results['tests'].items():
    status = "[PASS]" if result == 'PASS' else "[FAIL]" if result == 'FAIL' else "[PARTIAL]"
    print(f"  {status} {test_name.replace('_', ' ').title()}")
print()
print("=" * 70)
