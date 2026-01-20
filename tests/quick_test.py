import requests
import time

try:
    BASE_URL = 'http://127.0.0.1:8004'
    session = requests.Session()

    print('Testing user management page...')

    # Login
    login_data = {'username': 'admin', 'password': 'admin123'}
    response = session.post(f'{BASE_URL}/login', data=login_data, allow_redirects=False)
    print(f'Login status: {response.status_code}')

    # Test admin users page
    response = session.get(f'{BASE_URL}/admin/users')
    print(f'User management page status: {response.status_code}')

    if response.status_code == 200:
        print('✅ SUCCESS: User management page loads successfully!')
        print(f'Content length: {len(response.text)} bytes')
        if 'Active' in response.text and 'Stats' in response.text:
            print('✅ Page contains expected content')
        else:
            print('⚠️ Page missing some expected content')
    elif response.status_code == 500:
        print('❌ 500 Internal Server Error still occurring')
        print('First 500 chars of response:')
        print(response.text[:500])
    else:
        print(f'❌ Unexpected status code: {response.status_code}')
except Exception as e:
    print(f'Error: {e}')