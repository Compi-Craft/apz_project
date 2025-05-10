import requests

BASE_URL = "http://localhost:5000"
cookies = {
    'access_token_cookie': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJvemFya29ib2hkYW5AZ21haWwuY29tIiwiZXhwIjoxNzQ2ODk1MzY1fQ.OV6i4YYVVfSDq7wvZ6nspzB_uOTIEYtdH2dJcdoT6iI'
}

protected_response = requests.get(f"{BASE_URL}/protected", cookies=cookies)
print("Protected Route Status:", protected_response.status_code)
print("Protected Route Response:", protected_response.text)
