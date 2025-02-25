import requests
import time
import pytest
from datetime import datetime

# Base API URL
BASE_URL = "https://wavegerpython.onrender.com/api/auth"

# Test data
TEST_USER = {
    "username": "test_user_rate_limit",
    "password": "wrong_password123",
    "email": "test_rate_limit@example.com"
}

# ---------------------- Helper Functions ----------------------

def make_requests(endpoint, method="GET", data=None, count=10, delay=0.5):
    """Make multiple requests to an endpoint and return the status codes."""
    url = f"{BASE_URL}/{endpoint}"
    responses = []
    
    print(f"\nTesting {method} {url} with {count} requests...")
    
    for i in range(count):
        start_time = time.time()
        
        if method.upper() == "GET":
            resp = requests.get(url, params=data)
        elif method.upper() == "POST":
            resp = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Extract rate limit headers if present
        remaining = resp.headers.get('X-RateLimit-Remaining', 'N/A')
        limit = resp.headers.get('X-RateLimit-Limit', 'N/A')
        
        elapsed = time.time() - start_time
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        print(f"  [{timestamp}] Request {i+1}: Status {resp.status_code}, "
              f"Remaining: {remaining}, Limit: {limit}, Time: {elapsed:.2f}s")
        
        responses.append(resp.status_code)
        time.sleep(delay)  # Add delay between requests
    
    return responses

# ---------------------- Test Functions ----------------------

def test_login_rate_limit():
    """Test login endpoint rate limit (5 per minute)."""
    print("\n=== TESTING LOGIN RATE LIMIT (5 per minute) ===")
    
    # Make 7 requests (2 more than the limit)
    responses = make_requests(
        endpoint="login",
        method="POST",
        data=TEST_USER,
        count=7,
        delay=0.5
    )
    
    # Assert first 5 should be either 401 or 400 (authentication failure, not rate limited)
    for i, code in enumerate(responses[:5]):
        assert code in (401, 400), f"Request {i+1} should return 401 or 400, got {code}"
    
    # Assert last 2 should be rate limited (429)
    for i, code in enumerate(responses[5:], 6):
        assert code == 429, f"Request {i} should be rate limited with 429, got {code}"
    
    print("Login rate limit test: PASSED")

def test_register_rate_limit():
    """Test register endpoint rate limit (3 per hour)."""
    print("\n=== TESTING REGISTER RATE LIMIT (3 per hour) ===")
    
    # Make 4 requests (1 more than the limit)
    responses = make_requests(
        endpoint="register",
        method="POST",
        data={
            "username": f"test_user_{int(time.time())}",  # Unique usernames
            "password": "Test123!",
            "email": f"test_{int(time.time())}@example.com"  # Unique emails
        },
        count=4,
        delay=1.0  # Longer delay for registration
    )
    
    # First 3 should succeed with either 201 (created) or 409 (conflict) or 400 (validation error)
    for i, code in enumerate(responses[:3]):
        assert code in (201, 409, 400), f"Request {i+1} should return 201, 409, or 400, got {code}"
    
    # 4th should be rate limited
    assert responses[3] == 429, f"Request 4 should be rate limited with 429, got {responses[3]}"
    
    print("Register rate limit test: PASSED")

def test_check_availability_rate_limit():
    """Test check-availability endpoint rate limit (20 per minute)."""
    print("\n=== TESTING CHECK-AVAILABILITY RATE LIMIT (20 per minute) ===")
    
    # Make 22 requests (2 more than the limit)
    responses = make_requests(
        endpoint="check-availability",
        method="GET",
        data={"username": "test_username"},
        count=22,
        delay=0.2  # Shorter delay for this higher-limit endpoint
    )
    
    # First 20 should succeed with 200
    for i, code in enumerate(responses[:20]):
        assert code == 200, f"Request {i+1} should return 200, got {code}"
    
    # Last 2 should be rate limited
    for i, code in enumerate(responses[20:], 21):
        assert code == 429, f"Request {i} should be rate limited with 429, got {code}"
    
    print("Check-availability rate limit test: PASSED")

def test_user_endpoint_rate_limit():
    """Test user endpoint rate limit (30 per minute)."""
    print("\n=== TESTING USER ENDPOINT RATE LIMIT (30 per minute) ===")
    
    # We need an auth token for this test, but we'll use an invalid one
    # to test rate limits without needing valid credentials
    invalid_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYxMjM3NjY3NiwianRpIjoiNDA3MjE3YmUtZTY3ZS00NGIzLTkzZTMtNmZlMzVkMTAyMmYwIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEyMzQ1Njc4OSIsIm5iZiI6MTYxMjM3NjY3Nn0.invalid_signature"
    
    # Make 32 requests (2 more than the limit)
    count = 32
    responses = []
    
    print(f"\nTesting GET {BASE_URL}/user with {count} requests...")
    
    for i in range(count):
        resp = requests.get(
            f"{BASE_URL}/user",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        # Extract rate limit headers if present
        remaining = resp.headers.get('X-RateLimit-Remaining', 'N/A')
        limit = resp.headers.get('X-RateLimit-Limit', 'N/A')
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"  [{timestamp}] Request {i+1}: Status {resp.status_code}, "
              f"Remaining: {remaining}, Limit: {limit}")
        
        responses.append(resp.status_code)
        time.sleep(0.1)  # Very short delay for this high-limit endpoint
    
    # First 30 should return 401 (invalid token) or 422 (invalid token format)
    for i, code in enumerate(responses[:30]):
        assert code in (401, 422), f"Request {i+1} should return 401 or 422, got {code}"
    
    # Last 2 should be rate limited (429)
    for i, code in enumerate(responses[30:], 31):
        assert code == 429, f"Request {i} should be rate limited with 429, got {code}"
    
    print("User endpoint rate limit test: PASSED")

def test_refresh_token_rate_limit():
    """Test refresh token endpoint rate limit (10 per minute)."""
    print("\n=== TESTING REFRESH TOKEN RATE LIMIT (10 per minute) ===")
    
    # Make 12 requests (2 more than the limit)
    responses = make_requests(
        endpoint="refresh",
        method="POST",
        data={"refresh_token": "invalid_token"},
        count=12,
        delay=0.3
    )
    
    # First 10 should return 400 or 401 (invalid token, not rate limited)
    for i, code in enumerate(responses[:10]):
        assert code in (400, 401), f"Request {i+1} should return 400 or 401, got {code}"
    
    # Last 2 should be rate limited
    for i, code in enumerate(responses[10:], 11):
        assert code == 429, f"Request {i} should be rate limited with 429, got {code}"
    
    print("Refresh token rate limit test: PASSED")

# ---------------------- Main function to run tests ----------------------

def run_all_tests():
    """Run all rate limit tests in sequence."""
    print("\n=========================================")
    print("BEGINNING RATE LIMIT TESTS")
    print("=========================================")
    
    try:
        test_login_rate_limit()
        test_register_rate_limit()
        test_check_availability_rate_limit()
        test_user_endpoint_rate_limit()
        test_refresh_token_rate_limit()
        
        print("\n=========================================")
        print("ALL RATE LIMIT TESTS PASSED!")
        print("=========================================")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
    except Exception as e:
        print(f"\nERROR RUNNING TESTS: {e}")

if __name__ == "__main__":
    run_all_tests()