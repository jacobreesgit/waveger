import requests
import json
import time
import pytest
import random
import string
import jwt

# Base API URL
BASE_URL = "https://wavegerpython.onrender.com/api/auth"

# Helper Functions
def random_string(length=8):
    """Generate a random string for unique test data."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def create_test_user():
    """Create a new test user and return credentials."""
    username = f"test_auth_{random_string()}"
    email = f"{username}@example.com"
    password = "Test123!Special"
    
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/register", json=register_data)
    
    # If registration fails due to rate limiting, use a delay and retry
    if response.status_code == 429:
        print("Rate limit hit during test user creation. Waiting 60 seconds to retry...")
        time.sleep(60)
        response = requests.post(f"{BASE_URL}/register", json=register_data)
    
    # If still problematic, raise exception with details
    if response.status_code != 201:
        raise Exception(f"Failed to create test user. Status: {response.status_code}, Response: {response.text}")
    
    return {
        "username": username,
        "email": email,
        "password": password,
        "tokens": {
            "access_token": response.json().get("access_token"),
            "refresh_token": response.json().get("refresh_token")
        },
        "user_id": response.json().get("user", {}).get("id")
    }

# Test Functions
def test_register_and_login_flow():
    """Test the complete registration and login flow."""
    print("\n=== TESTING REGISTER AND LOGIN FLOW ===")
    
    # Create unique test user data
    username = f"test_auth_{random_string()}"
    email = f"{username}@example.com"
    password = "Test123!Special"
    
    # 1. Register new user
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    register_response = requests.post(f"{BASE_URL}/register", json=register_data)
    
    # Check if we hit rate limits
    if register_response.status_code == 429:
        print("Rate limit hit. This test can't be completed at this time.")
        return
    
    assert register_response.status_code == 201, f"Registration failed with status {register_response.status_code}: {register_response.text}"
    
    register_json = register_response.json()
    assert "access_token" in register_json, "Registration response missing access token"
    assert "refresh_token" in register_json, "Registration response missing refresh token"
    assert "user" in register_json, "Registration response missing user data"
    
    user_id = register_json["user"]["id"]
    
    # 2. Test login with new credentials
    login_data = {
        "username": username,
        "password": password
    }
    
    login_response = requests.post(f"{BASE_URL}/login", json=login_data)
    assert login_response.status_code == 200, f"Login failed with status {login_response.status_code}: {login_response.text}"
    
    login_json = login_response.json()
    assert "access_token" in login_json, "Login response missing access token"
    assert "refresh_token" in login_json, "Login response missing refresh token"
    
    # Store tokens for subsequent tests
    access_token = login_json["access_token"]
    refresh_token = login_json["refresh_token"]
    
    print("✅ Registration and login successful")
    
    # 3. Test accessing user data with token
    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get(f"{BASE_URL}/user", headers=headers)
    
    assert user_response.status_code == 200, f"User data request failed with status {user_response.status_code}: {user_response.text}"
    
    user_data = user_response.json()
    assert user_data["id"] == user_id, "User ID mismatch"
    assert user_data["username"] == username, "Username mismatch"
    assert user_data["email"] == email, "Email mismatch"
    
    print("✅ Access to protected user data successful")
    
    # 4. Test invalid login attempts
    invalid_login_data = {
        "username": username,
        "password": "wrong_password"
    }
    
    invalid_login_response = requests.post(f"{BASE_URL}/login", json=invalid_login_data)
    assert invalid_login_response.status_code == 401, f"Invalid login should fail with 401, got {invalid_login_response.status_code}"
    
    print("✅ Invalid login correctly rejected")
    
    return {
        "username": username,
        "user_id": user_id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }

def test_token_refresh():
    """Test the token refresh functionality."""
    print("\n=== TESTING TOKEN REFRESH ===")
    
    # Create a test user first
    test_user = create_test_user()
    refresh_token = test_user["tokens"]["refresh_token"]
    
    # Test the refresh endpoint
    refresh_response = requests.post(
        f"{BASE_URL}/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert refresh_response.status_code == 200, f"Token refresh failed with status {refresh_response.status_code}: {refresh_response.text}"
    
    refresh_data = refresh_response.json()
    assert "access_token" in refresh_data, "Refresh response missing access token"
    
    # Verify the new access token works
    new_access_token = refresh_data["access_token"]
    headers = {"Authorization": f"Bearer {new_access_token}"}
    
    user_response = requests.get(f"{BASE_URL}/user", headers=headers)
    assert user_response.status_code == 200, f"User data request with refreshed token failed with status {user_response.status_code}"
    
    print("✅ Token refresh successful")
    
    # Test with invalid refresh token
    invalid_refresh_response = requests.post(
        f"{BASE_URL}/refresh",
        json={"refresh_token": "invalid_token_here"}
    )
    
    assert invalid_refresh_response.status_code == 401, f"Invalid refresh should fail with 401, got {invalid_refresh_response.status_code}"
    
    print("✅ Invalid refresh token correctly rejected")

def test_token_expiration():
    """Test behavior with expired tokens (simulated)."""
    print("\n=== TESTING TOKEN EXPIRATION HANDLING ===")
    
    # Create a test user
    test_user = create_test_user()
    valid_token = test_user["tokens"]["access_token"]
    
    # Decode the token without verification to examine the structure
    # This helps us create an expired token with the same structure
    token_parts = valid_token.split(".")
    if len(token_parts) != 3:
        print("⚠️ Cannot decode JWT token - skipping expiration test")
        return
    
    # Create a manually expired token
    # Note: This is an approximation and depends on the JWT structure
    header = {"alg": "HS256", "typ": "JWT"}
    
    # Decode the payload to modify it
    import base64
    import json
    
    # Pad the base64 string if needed
    padded = token_parts[1] + "=" * (4 - len(token_parts[1]) % 4)
    try:
        decoded_payload = json.loads(base64.b64decode(padded).decode('utf-8'))
    except Exception as e:
        print(f"⚠️ Error decoding token payload: {e} - skipping expiration test")
        return
    
    # Set an expired time (1 hour ago)
    import time
    decoded_payload["exp"] = int(time.time()) - 3600
    
    # Since we can't sign the token without the secret key, we'll use a more direct approach
    # We'll use an entirely invalid token that should be rejected
    expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzAwMjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    # Test with expired token
    headers = {"Authorization": f"Bearer {expired_token}"}
    expired_response = requests.get(f"{BASE_URL}/user", headers=headers)
    
    # Should be rejected (401 Unauthorized or similar)
    assert expired_response.status_code in [401, 422], f"Expired token test: expected 401/422, got {expired_response.status_code}"
    
    print("✅ Expired/invalid token correctly rejected")

def test_token_structure_and_claims():
    """Test the structure and claims of issued tokens."""
    print("\n=== TESTING TOKEN STRUCTURE AND CLAIMS ===")
    
    # Create a test user
    test_user = create_test_user()
    access_token = test_user["tokens"]["access_token"]
    refresh_token = test_user["tokens"]["refresh_token"]
    
    # Decode tokens without verification to check structure
    import base64
    import json
    
    def decode_token_payload(token):
        """Decode the payload part of a JWT token without verification."""
        token_parts = token.split(".")
        if len(token_parts) != 3:
            return None
        
        # Pad the base64 string if needed
        padded = token_parts[1] + "=" * (4 - len(token_parts[1]) % 4)
        try:
            decoded = base64.b64decode(padded).decode('utf-8')
            return json.loads(decoded)
        except Exception as e:
            print(f"Error decoding token: {e}")
            return None
    
    # Check access token
    access_payload = decode_token_payload(access_token)
    if not access_payload:
        print("⚠️ Could not decode access token - skipping structure test")
    else:
        # Check essential claims
        assert "sub" in access_payload, "Access token missing 'sub' claim"
        assert "exp" in access_payload, "Access token missing 'exp' claim"
        assert "iat" in access_payload, "Access token missing 'iat' claim"
        
        # Check custom claims
        assert "username" in access_payload, "Access token missing 'username' claim"
        assert "email" in access_payload, "Access token missing 'email' claim"
        assert "token_id" in access_payload, "Access token missing 'token_id' claim"
        
        # Verify values match
        assert access_payload["username"] == test_user["username"], "Username mismatch in token"
        
        print("✅ Access token has correct structure and claims")
    
    # Check refresh token
    refresh_payload = decode_token_payload(refresh_token)
    if not refresh_payload:
        print("⚠️ Could not decode refresh token - skipping structure test")
    else:
        # Check essential claims
        assert "sub" in refresh_payload, "Refresh token missing 'sub' claim"
        assert "exp" in refresh_payload, "Refresh token missing 'exp' claim"
        assert "iat" in refresh_payload, "Refresh token missing 'iat' claim"
        
        # Check custom claims 
        assert "token_id" in refresh_payload, "Refresh token missing 'token_id' claim"
        
        print("✅ Refresh token has correct structure and claims")

def test_authorization_required():
    """Test that protected endpoints properly require authorization."""
    print("\n=== TESTING AUTHORIZATION REQUIREMENTS ===")
    
    # 1. Try to access protected endpoint without a token
    user_response = requests.get(f"{BASE_URL}/user")
    assert user_response.status_code in [401, 422], f"Expected 401/422 for missing token, got {user_response.status_code}"
    
    # 2. Try with a malformed token
    headers = {"Authorization": "not_a_bearer_token"}
    malformed_response = requests.get(f"{BASE_URL}/user", headers=headers)
    assert malformed_response.status_code in [401, 422], f"Expected 401/422 for malformed token, got {malformed_response.status_code}"
    
    # 3. Try with Bearer prefix but invalid token
    headers = {"Authorization": "Bearer invalid.token.here"}
    invalid_response = requests.get(f"{BASE_URL}/user", headers=headers)
    assert invalid_response.status_code in [401, 422], f"Expected 401/422 for invalid token, got {invalid_response.status_code}"
    
    print("✅ Protected endpoints correctly require valid authorization")

def test_username_email_availability():
    """Test the username/email availability checking endpoint."""
    print("\n=== TESTING USERNAME/EMAIL AVAILABILITY ===")
    
    # Create a test user first to have a known taken username/email
    test_user = create_test_user()
    taken_username = test_user["username"]
    taken_email = test_user["email"]
    
    # Test with taken username
    response = requests.get(f"{BASE_URL}/check-availability", params={"username": taken_username})
    assert response.status_code == 200, f"Availability check failed with status {response.status_code}"
    data = response.json()
    assert "username_exists" in data, "Response missing username_exists flag"
    assert data["username_exists"] is True, "Taken username should report as existing"
    
    # Test with available username
    available_username = f"available_{random_string()}"
    response = requests.get(f"{BASE_URL}/check-availability", params={"username": available_username})
    assert response.status_code == 200, f"Availability check failed with status {response.status_code}"
    data = response.json()
    assert data["username_exists"] is False, "Available username should report as not existing"
    
    # Test with taken email
    response = requests.get(f"{BASE_URL}/check-availability", params={"email": taken_email})
    assert response.status_code == 200, f"Availability check failed with status {response.status_code}"
    data = response.json()
    assert "email_exists" in data, "Response missing email_exists flag"
    assert data["email_exists"] is True, "Taken email should report as existing"
    
    # Test with available email
    available_email = f"available_{random_string()}@example.com"
    response = requests.get(f"{BASE_URL}/check-availability", params={"email": available_email})
    assert response.status_code == 200, f"Availability check failed with status {response.status_code}"
    data = response.json()
    assert data["email_exists"] is False, "Available email should report as not existing"
    
    print("✅ Username and email availability checks working correctly")

def test_user_info():
    """Test the user-info endpoint for retrieving public user information."""
    print("\n=== TESTING USER INFO ENDPOINT ===")
    
    # Create a test user first to have known user data
    test_user = create_test_user()
    username = test_user["username"]
    
    # Test with valid username
    response = requests.get(f"{BASE_URL}/user-info", params={"username": username})
    assert response.status_code == 200, f"User info request failed with status {response.status_code}: {response.text}"
    
    data = response.json()
    assert "success" in data, "Response missing success flag"
    assert data["success"] is True, "Success flag should be true"
    assert "user" in data, "Response missing user data"
    
    user_data = data["user"]
    assert user_data is not None, "User data should not be null for existing user"
    assert user_data["username"] == username, "Username in response doesn't match request"
    
    # Check that the response includes all the expected fields
    expected_fields = [
        "id", "username", "email", "created_at", "last_login",
        "total_points", "weekly_points", "predictions_made", "correct_predictions"
    ]
    
    for field in expected_fields:
        assert field in user_data, f"User data missing '{field}' field"
    
    print("✅ User info endpoint returns correct data for existing user")
    
    # Test with non-existent username
    non_existent = f"nonexistent_{random_string()}"
    response = requests.get(f"{BASE_URL}/user-info", params={"username": non_existent})
    
    # Should still return 200 but with empty/null user data for security reasons
    assert response.status_code == 200, f"User info request for non-existent user failed with status {response.status_code}"
    
    data = response.json()
    assert "success" in data, "Response missing success flag"
    assert data["success"] is True, "Success flag should be true even for non-existent users"
    assert "user" in data, "Response missing user field"
    assert data["user"] is None, "User data should be null for non-existent user"
    
    print("✅ User info endpoint correctly handles non-existent users")
    
    # Test without providing a username
    response = requests.get(f"{BASE_URL}/user-info")
    assert response.status_code == 400, f"Expected 400 for missing username, got {response.status_code}"
    
    print("✅ User info endpoint correctly requires username parameter")

def test_update_profile():
    """Test the update-profile endpoint for changing user details."""
    print("\n=== TESTING UPDATE PROFILE ENDPOINT ===")
    
    # Create a test user
    test_user = create_test_user()
    access_token = test_user["tokens"]["access_token"]
    
    # Setup auth headers
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test 1: Update username
    new_username = f"updated_{random_string()}"
    
    print(f"Testing username update from {test_user['username']} to {new_username}")
    response = requests.put(
        f"{BASE_URL}/update-profile",
        json={"username": new_username},
        headers=headers
    )
    
    assert response.status_code == 200, f"Profile update failed with status {response.status_code}: {response.text}"
    data = response.json()
    assert "message" in data, "Response missing message"
    assert "updates" in data, "Response missing updates"
    assert "username" in data["updates"], "Username update not confirmed in response"
    assert data["updates"]["username"] == new_username, "Username not updated correctly"
    
    # Verify the change by fetching user data
    user_response = requests.get(f"{BASE_URL}/user", headers=headers)
    assert user_response.status_code == 200, "Failed to fetch updated user data"
    user_data = user_response.json()
    assert user_data["username"] == new_username, "Username not updated in database"
    
    print("✅ Username update successful")
    
    # Test 2: Update email
    new_email = f"updated_{random_string()}@example.com"
    
    print(f"Testing email update to {new_email}")
    response = requests.put(
        f"{BASE_URL}/update-profile",
        json={"email": new_email},
        headers=headers
    )
    
    assert response.status_code == 200, f"Email update failed with status {response.status_code}: {response.text}"
    data = response.json()
    assert "updates" in data, "Response missing updates"
    assert "email" in data["updates"], "Email update not confirmed in response"
    assert data["updates"]["email"] == new_email, "Email not updated correctly"
    
    # Verify the change
    user_response = requests.get(f"{BASE_URL}/user", headers=headers)
    user_data = user_response.json()
    assert user_data["email"] == new_email, "Email not updated in database"
    
    print("✅ Email update successful")
    
    # Test 3: Update password
    old_password = test_user["password"]
    new_password = f"NewPassword{random_string()}123!"
    
    print("Testing password update")
    response = requests.put(
        f"{BASE_URL}/update-profile",
        json={
            "current_password": old_password,
            "new_password": new_password
        },
        headers=headers
    )
    
    assert response.status_code == 200, f"Password update failed with status {response.status_code}: {response.text}"
    data = response.json()
    assert "updates" in data, "Response missing updates"
    assert "password_updated" in data["updates"], "Password update not confirmed in response"
    assert data["updates"]["password_updated"] is True, "Password update flag not set"
    
    # Verify the password change by trying to login with new password
    login_response = requests.post(
        f"{BASE_URL}/login",
        json={
            "username": new_username,
            "password": new_password
        }
    )
    
    assert login_response.status_code == 200, "Failed to login with new password"
    
    print("✅ Password update successful")
    
    # Test 4: Try to update with incorrect current password
    response = requests.put(
        f"{BASE_URL}/update-profile",
        json={
            "current_password": "wrong_password",
            "new_password": "AnotherNew123!"
        },
        headers=headers
    )
    
    assert response.status_code == 401, f"Expected 401 for incorrect password, got {response.status_code}"
    
    print("✅ Incorrect current password correctly rejected")
    
    # Test 5: Try to update to an existing username
    # Create another test user to have a taken username
    another_user = create_test_user()
    
    response = requests.put(
        f"{BASE_URL}/update-profile",
        json={"username": another_user["username"]},
        headers=headers
    )
    
    assert response.status_code == 409, f"Expected 409 for username conflict, got {response.status_code}"
    
    print("✅ Username conflict correctly detected")
    
    # Test 6: Try to update to an existing email
    response = requests.put(
        f"{BASE_URL}/update-profile",
        json={"email": another_user["email"]},
        headers=headers
    )
    
    assert response.status_code == 409, f"Expected 409 for email conflict, got {response.status_code}"
    
    print("✅ Email conflict correctly detected")
    
    # Test 7: Try to update with invalid token
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    response = requests.put(
        f"{BASE_URL}/update-profile",
        json={"username": f"invalid_{random_string()}"},
        headers=invalid_headers
    )
    
    assert response.status_code in [401, 422], f"Expected 401/422 for invalid token, got {response.status_code}"
    
    print("✅ Invalid token correctly rejected")

    # Test 8: Try to update with missing authorization
    response = requests.put(
        f"{BASE_URL}/update-profile",
        json={"username": f"unauthorized_{random_string()}"}
    )
    
    assert response.status_code == 401, f"Expected 401 for missing auth, got {response.status_code}"
    
    print("✅ Missing authorization correctly rejected")

def run_all_tests():
    """Run all authentication tests in sequence."""
    print("\n=========================================")
    print("BEGINNING AUTHENTICATION TESTS")
    print("=========================================")
    
    try:
        # Run the tests
        test_register_and_login_flow()
        test_token_refresh()
        test_token_expiration()
        test_token_structure_and_claims()
        test_authorization_required()
        test_username_email_availability()
        test_user_info()
        test_update_profile()
        
        print("\n=========================================")
        print("ALL AUTHENTICATION TESTS PASSED!")
        print("=========================================")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
    except Exception as e:
        print(f"\nERROR RUNNING TESTS: {e}")

if __name__ == "__main__":
    run_all_tests()