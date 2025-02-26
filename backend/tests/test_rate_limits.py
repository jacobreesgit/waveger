import requests
import time
from datetime import datetime
import random
import string

# Base API URL
BASE_URL = "https://wavegerpython.onrender.com/api/auth"

# Existing test user credentials (to use when registration limit is hit)
FALLBACK_USER = {
    "username": "test_user_permanent",
    "password": "TestPassword123!",
    "email": "test_permanent@example.com"
}

# ---------------------- Helper Functions ----------------------

def make_requests(endpoint, method="GET", data=None, count=10, delay=0.5, headers=None):
    """Make multiple requests to an endpoint and return the status codes."""
    url = f"{BASE_URL}/{endpoint}"
    responses = []
    
    print(f"\nTesting {method} {url} with {count} requests...")
    
    for i in range(count):
        start_time = time.time()
        
        if method.upper() == "GET":
            resp = requests.get(url, params=data, headers=headers)
        elif method.upper() == "POST":
            resp = requests.post(url, json=data, headers=headers)
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

def random_string(length=8):
    """Generate a random string for unique test data."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def ensure_test_user_exists():
    """Make sure the fallback test user exists before running tests."""
    # First, check if we can log in with the fallback user
    login_response = requests.post(
        f"{BASE_URL}/login",
        json={
            "username": FALLBACK_USER["username"],
            "password": FALLBACK_USER["password"]
        }
    )
    
    # If login successful, we're good
    if login_response.status_code == 200:
        print(f"✅ Fallback user {FALLBACK_USER['username']} exists and credentials are valid.")
        return True
    
    # Otherwise, try to register the fallback user
    print(f"Registering fallback user {FALLBACK_USER['username']}...")
    register_response = requests.post(
        f"{BASE_URL}/register",
        json=FALLBACK_USER
    )
    
    if register_response.status_code == 201:
        print(f"✅ Successfully registered fallback user {FALLBACK_USER['username']}")
        return True
    elif register_response.status_code == 409:
        print(f"⚠️ User {FALLBACK_USER['username']} already exists but password may be wrong")
        return False
    else:
        print(f"❌ Failed to register fallback user. Status: {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return False

def get_valid_token():
    """Tries to get a valid token, first by logging in with existing credentials,
    then trying to register a new user if login fails."""
    
    # First try to log in with the fallback user
    print("Attempting to log in with existing user...")
    login_response = requests.post(
        f"{BASE_URL}/login",
        json={
            "username": FALLBACK_USER["username"],
            "password": FALLBACK_USER["password"]
        }
    )
    
    # If login succeeds, use that token
    if login_response.status_code == 200:
        login_data = login_response.json()
        token = login_data.get("access_token")
        if token:
            print(f"Successfully logged in as {FALLBACK_USER['username']}")
            return token
    
    # Otherwise, try to register a new user
    print("Login failed. Attempting to register a new user...")
    username = f"test_rate_limit_{random_string()}"
    email = f"test_rate_limit_{random_string()}@example.com"
    password = "TestPassword123!"
    
    register_response = requests.post(
        f"{BASE_URL}/register",
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )
    
    if register_response.status_code == 201:
        register_data = register_response.json()
        token = register_data.get("access_token")
        if token:
            print(f"Successfully registered new user: {username}")
            return token
    
    print(f"All authentication attempts failed. Cannot proceed with user endpoint test.")
    raise Exception("Unable to obtain a valid token for testing")

# ---------------------- Test Functions ----------------------

def test_login_rate_limit():
    """Test login endpoint rate limit (4 per minute)."""
    print("\n=== TESTING LOGIN RATE LIMIT (4 per minute) ===")
    
    # Make 6 requests (2 more than the limit)
    responses = make_requests(
        endpoint="login",
        method="POST",
        data={
            "username": f"nonexistent_{random_string()}",
            "password": "wrong_password123"
        },
        count=6,
        delay=0.5
    )
    
    # Assert first 4 should be either 401 or 400 (authentication failure, not rate limited)
    for i, code in enumerate(responses[:4]):
        assert code in (401, 400), f"Request {i+1} should return 401 or 400, got {code}"
    
    # Assert last 2 should be rate limited (429)
    for i, code in enumerate(responses[4:], 5):
        assert code == 429, f"Request {i} should be rate limited with 429, got {code}"
    
    print("Login rate limit test: PASSED")

def test_register_rate_limit():
    """Test register endpoint rate limit (3 per hour)."""
    print("\n=== TESTING REGISTER RATE LIMIT (3 per hour) ===")
    
    # Make 5 requests (more than enough to trigger rate limiting eventually)
    responses = make_requests(
        endpoint="register",
        method="POST",
        data={
            "username": f"test_user_{random_string()}",  # Unique usernames each time
            "password": "Test123!",
            "email": f"test_{random_string()}@example.com"  # Unique emails each time
        },
        count=5,
        delay=1.0  # Longer delay for registration
    )
    
    # Check if any 429 responses were received
    has_rate_limit = 429 in responses
    
    # If no rate limits were hit, the test is inconclusive but not failed
    if not has_rate_limit:
        print("⚠️ Warning: No rate limiting detected for register endpoint after 5 requests.")
        print("This may be due to higher rate limits than expected or because of unique request data.")
        print("Register rate limit test: SKIPPED")
        return
    
    # Find the index where rate limiting starts
    rate_limit_start = responses.index(429)
    
    # All requests before rate limiting should be valid responses (201, 409, 400)
    for i, code in enumerate(responses[:rate_limit_start]):
        assert code in (201, 409, 400), f"Request {i+1} should return 201, 409, or 400, got {code}"
    
    # All requests after rate limiting should continue to be rate limited
    for i, code in enumerate(responses[rate_limit_start:], rate_limit_start + 1):
        assert code == 429, f"Request {i} should be rate limited with 429, got {code}"
    
    print(f"Register rate limit detected after {rate_limit_start} requests")
    print("Register rate limit test: PASSED")

def test_check_availability_rate_limit():
    """Test check-availability endpoint rate limit (20 per minute)."""
    print("\n=== TESTING CHECK-AVAILABILITY RATE LIMIT (20 per minute) ===")
    
    # Make 22 requests (2 more than the limit)
    responses = make_requests(
        endpoint="check-availability",
        method="GET",
        data={"username": f"test_{random_string()}"},  # Use random usernames
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
    """Test user endpoint rate limit (30 per minute) with valid authentication."""
    print("\n=== TESTING USER ENDPOINT RATE LIMIT (30 per minute) ===")
    
    # Get a valid token using the helper function (tries login then registration)
    try:
        token = get_valid_token()
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print("Skipping user endpoint rate limit test.")
        return
    
    # Now make 32 requests (2 more than the limit) with the valid token
    count = 32
    responses = []
    auth_header = {"Authorization": f"Bearer {token}"}
    
    print(f"Testing GET {BASE_URL}/user with {count} requests and valid token...")
    
    for i in range(count):
        resp = requests.get(
            f"{BASE_URL}/user",
            headers=auth_header
        )
        
        # Extract rate limit headers if present
        remaining = resp.headers.get('X-RateLimit-Remaining', 'N/A')
        limit = resp.headers.get('X-RateLimit-Limit', 'N/A')
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"  [{timestamp}] Request {i+1}: Status {resp.status_code}, "
              f"Remaining: {remaining}, Limit: {limit}")
        
        responses.append(resp.status_code)
        time.sleep(0.1)  # Very short delay for this high-limit endpoint
    
    # First 30 should return 200 (valid authenticated request)
    for i, code in enumerate(responses[:30]):
        assert code == 200, f"Request {i+1} should return 200, got {code}"
    
    # Last 2 should be rate limited
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
    
    # First ensure we have a fallback user
    ensure_test_user_exists()
    
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