import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 5

def test_endpoint(name, method, path, data=None):
    print(f"\n--- Testing {name} ---")
    try:
        if method == "POST":
            resp = requests.post(f"{BASE_URL}{path}", json=data, timeout=TIMEOUT)
        else:
            resp = requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT)
        print(f"Status: {resp.status_code}")
        if resp.status_code >= 400:
            print(f"Error: {resp.text}")
        else:
            print(f"Response: {resp.json()}")
        return resp
    except Exception as e:
        print(f"Failed: {e}")
        return None

if __name__ == "__main__":
    # Test Signup
    email = f"test_{int(__import__('time').time())}@example.com"
    test_endpoint("Signup", "POST", "/auth/register", {
        "email": email,
        "phone_number": "9998887776",
        "password": "password123",
        "full_name": "Test User",
        "role": "CUSTOMER"
    })
    
    # Test Login OTP Request
    test_endpoint("Login OTP Request", "POST", "/auth/login/request-otp", {
        "username": email,
        "password": "password123"
    })
