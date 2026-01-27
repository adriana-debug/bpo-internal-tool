#!/usr/bin/env python3
"""Test API endpoints directly"""
import requests

session = requests.Session()

# Login
login_response = session.post(
    'http://127.0.0.1:8005/login',
    data={'email': 'admin@bpo.com', 'password': 'admin123'},
    allow_redirects=False
)
print(f"Login status: {login_response.status_code}")
print(f"Cookies after login: {session.cookies.get_dict()}")

# Test filter-options
try:
    response = session.get('http://127.0.0.1:8005/api/employees/filter-options')
    print(f"\nFilter options status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test statistics (which works)
try:
    response = session.get('http://127.0.0.1:8005/api/employees/statistics')
    print(f"\nStatistics status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
