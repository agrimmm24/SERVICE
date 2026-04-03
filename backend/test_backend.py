import requests
import json

BASE_URL = "http://localhost:8000"

def test_registration():
    print("Testing Registration...")
    url = f"{BASE_URL}/auth/register"
    payload = {
        "email": "testuser@example.com",
        "full_name": "Test User",
        "password": "TestPassword123",
        "role": "CUSTOMER"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Registration successful")
    elif response.status_code == 400 and "Email already registered" in response.text:
        print(" User already exists, proceeding to login")
    else:
        print(f" Registration failed: {response.text}")

def test_login():
    print("Testing Login...")
    url = f"{BASE_URL}/token"
    # FastAPI OAuth2 expects form data
    data = {
        "username": "testuser@example.com",
        "password": "TestPassword123"
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        res_data = response.json()
        print(f" Login successful. Role: {res_data.get('role')}")
        return res_data.get("access_token")
    else:
        print(f" Login failed: {response.text}")
        return None

def test_create_booking(token):
    if not token: return
    print("Testing Booking Creation...")
    url = f"{BASE_URL}/bookings/create"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Mocking FormData
    data = {
        "brand": "Toyota",
        "model": "Camry",
        "licensePlate": "TEST-123",
        "serviceType": "General Service",
        "date": "2026-03-01",
        "pickupLocation": "123 Main St",
        "dropLocation": "Workshop"
    }
    
    # Since it's multipart/form-data, we use files or just data if no actual file
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print(f" Booking created: {response.json().get('booking_id')}")
    else:
        print(f" Booking creation failed: {response.text}")

def test_admin_get_users():
    # Login as admin (using seed data if available)
    print("Testing Admin User List...")
    url = f"{BASE_URL}/token"
    data = {
        "username": "sri.agrimsri@gmail.com",
        "password": "admin123"
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        users_response = requests.get(f"{BASE_URL}/users/", headers=headers)
        if users_response.status_code == 200:
            print(f" Admin fetched {len(users_response.json())} users")
        else:
            print(f" Admin fetch failed: {users_response.text}")
    else:
        print(" Admin login failed (did you run seed.py?)")

if __name__ == "__main__":
    test_registration()
    token = test_login()
    test_create_booking(token)
    test_admin_get_users()
