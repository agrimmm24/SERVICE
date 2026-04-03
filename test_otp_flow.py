import requests
import json

BASE_URL = "http://localhost:8000"

def test_signup_otp():
    print("\n--- Testing Signup OTP ---")
    email = f"test_{int(__import__('time').time())}@example.com"
    payload = {
        "email": email,
        "phone_number": "1234567890",
        "password": "password123",
        "full_name": "Test User",
        "role": "CUSTOMER"
    }
    
    # Register
    resp = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print(f"Register Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error: {resp.json()}")
        return None
    
    # In this mock environment, we'd need to check the server logs for the OTP.
    # Since we can't do that easily from this script, let's assume the flow works if the status is 200.
    # Actually, let's manually verify in the terminal once I run this.
    print(f"User created: {email}. Please check terminal logs for OTP.")
    return email

def test_login_otp(email):
    print("\n--- Testing Login OTP ---")
    payload = {
        "username": email,
        "password": "password123"
    }
    
    # Request Login OTP
    resp = requests.post(f"{BASE_URL}/auth/login/request-otp", json=payload)
    print(f"Login Request OTP Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error: {resp.json()}")
        return
    
    print("OTP sent. Check terminal logs.")

if __name__ == "__main__":
    email = test_signup_otp()
    if email:
        test_login_otp(email)
