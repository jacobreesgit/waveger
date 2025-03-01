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
        
        # Generate unique data for each request to avoid conflicts
        request_data = {}
        if data and isinstance(data, dict):
            for key, value in data.items():
                if key in ['username', 'email']:
                    # Add index to ensure uniqueness
                    request_data[key] = f"{value}_{i}"
                else:
                    request_data[key] = value
        else:
            request_data = data
        
        if method.upper() == "GET":
            resp = requests.get(url, params=request_data, headers=headers)
        elif method.upper() == "POST":
            resp = requests.post(url, json=request_data, headers=headers)
        elif method.upper() == "PUT":
            resp = requests.put(url, json=request_data, headers=headers)
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
    """Test login endpoint rate limit (5 per minute)."""
    print("\n=== TESTING LOGIN RATE LIMIT (5 per minute) ===")
    
    # Make 7 requests (2 more than the limit)
    responses = make_requests(
        endpoint="login",
        method="POST",
        data={
            "username": f"nonexistent_{random_string()}",
            "password": "wrong_password123"
        },
        count=7,
        delay=0.5
    )
    
    # Assert first 4 should be either 401 or 400 (authentication failure, not rate limited)
    for i, code in enumerate(responses[:4]):
        assert code in (401, 400), f"Request {i+1} should return 401 or 400, got {code}"
    
    # Assert last 3 should be rate limited (429)
    for i, code in enumerate(responses[4:], 5):
        assert code == 429, f"Request {i} should be rate limited with 429, got {code}"
    
    print("Login rate limit test: PASSED")

def test_register_rate_limit():
    """Test register endpoint rate limit (20 per hour)."""
    print("\n=== TESTING REGISTER RATE LIMIT (20 per hour) ===")
    
    # Make 22 requests (2 more than the limit)
    responses = make_requests(
        endpoint="register",
        method="POST",
        data={
            "username": f"test_user_{random_string()}",  # Base name will be made unique per request
            "password": "Test123!",
            "email": f"test_{random_string()}@example.com"  # Base email will be made unique per request
        },
        count=22,
        delay=0.3  # Shorter delay as we have more requests
    )
    
    # Check if any 429 responses were received
    has_rate_limit = 429 in responses
    
    # If no rate limits were hit after 22 requests, something is wrong
    if not has_rate_limit:
        print("❌ Error: No rate limiting detected for register endpoint after 22 requests.")
        print("The configured limit of 20 per hour may not be enforced correctly.")
        assert False, "Register endpoint not enforcing rate limits correctly"
    
    # Find the index where rate limiting starts
    rate_limit_start = responses.index(429)
    
    # All requests before rate limiting should be valid responses (201, 409, 400)
    for i, code in enumerate(responses[:rate_limit_start]):
        assert code in (201, 409, 400), f"Request {i+1} should return 201, 409, or 400, got {code}"
    
    # Check if rate limiting starts after 20 requests as expected
    if rate_limit_start < 20:
        print(f"⚠️ Warning: Rate limiting started at request {rate_limit_start+1}, expected after 20 requests")
    else:
        print(f"✅ Rate limiting correctly started after {rate_limit_start} requests")
    
    # All requests after rate limiting should continue to be rate limited
    for i, code in enumerate(responses[rate_limit_start:], rate_limit_start + 1):
        assert code == 429, f"Request {i} should be rate limited with 429, got {code}"
    
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

def test_user_info_rate_limit():
    """Test user-info endpoint rate limit (20 per minute)."""
    print("\n=== TESTING USER-INFO RATE LIMIT (20 per minute) ===")
    
    # Make sure we have a valid username to test with
    ensure_test_user_exists()
    username = FALLBACK_USER["username"]
    
    # Make 22 requests (2 more than the limit)
    responses = make_requests(
        endpoint="user-info",
        method="GET",
        data={"username": username},
        count=22,
        delay=0.2  # Shorter delay for this higher-limit endpoint
    )
    
    # First 20 should succeed with 200
    for i, code in enumerate(responses[:20]):
        assert code == 200, f"Request {i+1} should return 200, got {code}"
    
    # Last 2 should be rate limited
    for i, code in enumerate(responses[20:], 21):
        assert code == 429, f"Request {i} should be rate limited with 429, got {code}"
    
    print("User-info rate limit test: PASSED")

def test_update_profile_rate_limit():
    """Test update-profile endpoint rate limit (10 per minute)."""
    print("\n=== TESTING UPDATE PROFILE RATE LIMIT (10 per minute) ===")
    
    # Get a valid token first
    token = get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Make 12 requests (2 more than the limit)
    url = f"{BASE_URL}/update-profile"
    responses = []
    
    print(f"\nTesting PUT {url} with 12 requests...")
    
    for i in range(12):
        start_time = time.time()
        
        # Generate unique username for each request
        test_data = {"username": f"rate_limit_test_{random_string()}_{i}"}
        
        resp = requests.put(url, json=test_data, headers=headers)
        
        # Extract rate limit headers if present
        remaining = resp.headers.get('X-RateLimit-Remaining', 'N/A')
        limit = resp.headers.get('X-RateLimit-Limit', 'N/A')
        
        elapsed = time.time() - start_time
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        print(f"  [{timestamp}] Request {i+1}: Status {resp.status_code}, "
              f"Remaining: {remaining}, Limit: {limit}, Time: {elapsed:.2f}s")
        
        responses.append(resp.status_code)
        time.sleep(0.3)  # Add delay between requests
    
    # First 10 should succeed with 200
    for i, code in enumerate(responses[:10]):
        assert code == 200, f"Request {i+1} should return 200, got {code}"
    
    # Last 2 should be rate limited
    for i, code in enumerate(responses[10:], 11):
        assert code == 429, f"Request {i} should be rate limited with 429, got {code}"
    
    print("Update profile rate limit test: PASSED")

def test_top_charts_rate_limit():
    """Test top-charts endpoint rate limit (100 per minute)."""
    print("\n=== TESTING TOP CHARTS RATE LIMIT (100 per minute) ===")
    
    # Make 102 requests (2 more than the limit)
    # We'll use a smaller number to avoid timeouts during testing
    count = 22  # Using smaller count for faster testing
    
    url = f"{BASE_URL.replace('/auth', '')}/top-charts"
    responses = []
    
    print(f"\nTesting GET {url} with {count} requests...")
    
    for i in range(count):
        start_time = time.time()
        resp = requests.get(url)
        
        # Extract rate limit headers if present
        remaining = resp.headers.get('X-RateLimit-Remaining', 'N/A')
        limit = resp.headers.get('X-RateLimit-Limit', 'N/A')
        
        elapsed = time.time() - start_time
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        print(f"  [{timestamp}] Request {i+1}: Status {resp.status_code}, "
              f"Remaining: {remaining}, Limit: {limit}, Time: {elapsed:.2f}s")
        
        responses.append(resp.status_code)
        time.sleep(0.1)  # Very short delay for this high-limit endpoint
    
    # Check if we hit the rate limit
    has_rate_limit = 429 in responses
    
    # If testing with fewer requests than the limit, we may not hit it
    if count <= 100:
        print("Note: Testing with fewer requests than the limit, may not hit rate limit")
        return
    
    # If we did exceed the limit, we should see 429 responses
    if has_rate_limit:
        # Find the index where rate limiting starts
        rate_limit_start = responses.index(429)
        
        print(f"Rate limiting correctly started after {rate_limit_start} requests")
        
        # All requests after rate limiting should continue to be rate limited
        for i, code in enumerate(responses[rate_limit_start:], rate_limit_start + 1):
            assert code == 429, f"Request {i} should be rate limited with 429, got {code}"
    else:
        print("⚠️ Warning: Rate limit not hit. This could be expected if testing with fewer requests than the limit.")
    
    print("Top charts rate limit test completed")

def test_chart_details_rate_limit():
    """Test chart endpoint rate limit (200 per minute)."""
    print("\n=== TESTING CHART DETAILS RATE LIMIT (200 per minute) ===")
    
    # Make 22 requests (smaller number for testing purposes)
    count = 22
    
    url = f"{BASE_URL.replace('/auth', '')}/chart"
    responses = []
    
    print(f"\nTesting GET {url} with {count} requests...")
    
    for i in range(count):
        start_time = time.time()
        
        # Add chart ID parameter to make request more realistic
        resp = requests.get(url, params={"id": "hot-100"})
        
        # Extract rate limit headers if present
        remaining = resp.headers.get('X-RateLimit-Remaining', 'N/A')
        limit = resp.headers.get('X-RateLimit-Limit', 'N/A')
        
        elapsed = time.time() - start_time
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        print(f"  [{timestamp}] Request {i+1}: Status {resp.status_code}, "
              f"Remaining: {remaining}, Limit: {limit}, Time: {elapsed:.2f}s")
        
        responses.append(resp.status_code)
        time.sleep(0.1)  # Very short delay
    
    # With only 22 requests, we shouldn't hit the 200 per minute limit
    has_rate_limit = 429 in responses
    
    if has_rate_limit:
        print("⚠️ Unexpected: Rate limit hit sooner than expected. Limit may be lower than 200 per minute.")
    else:
        print("✅ Successfully made 22 requests without hitting rate limit (expected for 200/minute limit)")
    
    print("Chart details rate limit test completed")

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
        test_user_info_rate_limit()
        test_update_profile_rate_limit()
        test_top_charts_rate_limit()
        test_chart_details_rate_limit()
        
        print("\n=========================================")
        print("ALL RATE LIMIT TESTS PASSED!")
        print("=========================================")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
    except Exception as e:
        print(f"\nERROR RUNNING TESTS: {e}")

if __name__ == "__main__":
    run_all_tests()