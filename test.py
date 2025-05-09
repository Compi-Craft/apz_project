import requests

BASE_URL = "http://localhost:8000"

# Sample user data
user_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
}

def test_signup():
    print("Testing /signup...")
    response = requests.post(f"{BASE_URL}/signup", params=user_data)
    print("Status Code:", response.status_code)
    print("Response:", response.json())

def test_login():
    print("Testing /login...")
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    response = requests.post(f"{BASE_URL}/login", params=login_data)
    print("Status Code:", response.status_code)
    print("Response:", response.json())

if __name__ == "__main__":
    test_signup()
    test_login()
