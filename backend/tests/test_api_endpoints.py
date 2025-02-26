import unittest
import requests
import json
import os
import time
from datetime import datetime
import jwt
from unittest.mock import patch, MagicMock

# Base API URL
BASE_URL = "https://wavegerpython.onrender.com/api"
AUTH_URL = f"{BASE_URL}/auth"


class ChartsAPITests(unittest.TestCase):
    """Tests for the charts API endpoints."""
    
    def test_top_charts_endpoint(self):
        """Test the /top-charts endpoint."""
        # Act
        response = requests.get(f"{BASE_URL}/top-charts")
        
        # Assert
        self.assertEqual(response.status_code, 200, 
                         f"Failed to get top charts: {response.text}")
        
        data = response.json()
        self.assertIn('data', data, "Response missing 'data' field")
        self.assertIn('source', data, "Response missing 'source' field")
        
        # Validate data structure
        chart_data = data['data']
        self.assertTrue(isinstance(chart_data, list), "Charts data should be a list")
        
        if len(chart_data) > 0:
            # Verify first chart has required fields
            first_chart = chart_data[0]
            self.assertIn('title', first_chart, "Chart missing 'title' field")
            self.assertIn('chart_name', first_chart, "Chart missing 'chart_name' field")
    
    def test_chart_details_endpoint(self):
        """Test the /chart endpoint with parameters."""
        # Act - Test with default parameters (hot-100)
        response = requests.get(f"{BASE_URL}/chart")
        
        # Assert
        self.assertEqual(response.status_code,
                         200, f"Failed to get chart details: {response.text}")
        
        data = response.json()
        self.assertIn('data', data, "Response missing 'data' field")
        
        chart_data = data['data']
        self.assertIn('chart', chart_data, "Chart data missing 'chart' field")
        self.assertIn('songs', chart_data, "Chart data missing 'songs' field")
        
        # Check if songs were limited by range parameter
        songs = chart_data['songs']
        self.assertLessEqual(len(songs), 10, "Should return at most 10 songs by default")
    
    def test_chart_with_custom_range(self):
        """Test the /chart endpoint with custom range parameter."""
        # Act - Test with custom range parameter
        response = requests.get(f"{BASE_URL}/chart?range=1-5")
        
        # Assert
        self.assertEqual(response.status_code, 200, 
                         f"Failed to get chart with custom range: {response.text}")
        
        data = response.json()
        songs = data['data']['songs']
        self.assertLessEqual(len(songs), 5, "Should return at most 5 songs")
    
    def test_chart_with_custom_id(self):
        """Test the /chart endpoint with custom chart ID."""
        # Act - Test with a different chart ID
        response = requests.get(f"{BASE_URL}/chart?id=billboard-global-200")
        
        # Assert
        self.assertEqual(response.status_code, 200, 
                         f"Failed to get custom chart: {response.text}")
        
        data = response.json()
        chart_info = data['data']['chart']
        self.assertIn('billboard-global-200', chart_info.get('url', ''), 
                      "Chart URL should contain the requested chart ID")


class AppleMusicAPITests(unittest.TestCase):
    """Tests for the Apple Music API endpoints."""
    
    def test_apple_music_token_endpoint(self):
        """Test the /apple-music-token endpoint."""
        # Act
        response = requests.get(f"{BASE_URL}/apple-music-token")
        
        # Parse response
        status_code = response.status_code
        response_data = response.json()
        
        # Check if this is an expected error due to missing credentials
        if status_code != 200:
            # If credentials are missing, we expect a specific error
            self.assertIn('error', response_data, 
                         "Error response should contain 'error' field")
            
            # This is an acceptable error since we're testing without proper credentials
            error_msg = response_data.get('error', '')
            acceptable_errors = [
                'Private key file missing', 
                'environment variable', 
                'secret'
            ]
            
            error_is_acceptable = any(msg in error_msg.lower() for msg in acceptable_errors)
            
            # If it's not an acceptable credential-related error, fail the test
            if not error_is_acceptable:
                self.fail(f"Unexpected error: {error_msg}")
                
            # Skip the rest of the test if credentials are missing
            self.skipTest("Apple Music credentials not configured")
        else:
            # If the request succeeded, validate the token
            self.assertIn('token', response_data, 
                         "Success response should contain 'token' field")
            
            token = response_data['token']
            self.assertTrue(token, "Token should not be empty")
            
            # Try to decode the token (without verification)
            try:
                decoded = jwt.decode(token, options={"verify_signature": False})
                self.assertIn('iss', decoded, "Token should have issuer claim")
                self.assertIn('exp', decoded, "Token should have expiration claim")
            except Exception as e:
                self.fail(f"Token is not a valid JWT: {e}")


class AuthAPITests(unittest.TestCase):
    """Tests for authentication API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.test_user = {
            "username": f"test_user_{int(time.time())}",  # Unique username
            "email": f"test_{int(time.time())}@example.com",  # Unique email
            "password": "TestPassword123!"
        }
    
    def test_registration_success(self):
        """Test successful user registration."""
        # Act
        response = requests.post(f"{AUTH_URL}/register", json=self.test_user)
        
        # Assert
        self.assertEqual(response.status_code, 201, 
                         f"Registration failed: {response.text}")
        
        data = response.json()
        self.assertIn('message', data, "Response missing 'message' field")
        self.assertIn('access_token', data, "Response missing 'access_token' field")
        self.assertIn('refresh_token', data, "Response missing 'refresh_token' field")
        self.assertIn('user', data, "Response missing 'user' field")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        # Act - Try to login with wrong password
        login_data = {
            "username": self.test_user["username"],
            "password": "WrongPassword123!"
        }
        
        response = requests.post(f"{AUTH_URL}/login", json=login_data)
        
        # Assert
        self.assertEqual(response.status_code, 401, 
                         "Should return 401 for invalid credentials")
        
        data = response.json()
        self.assertIn('error', data, "Response missing 'error' field")
    
    def test_user_endpoint_with_valid_token(self):
        """Test accessing user data with a valid token."""
        # Arrange - Register and get a token
        reg_response = requests.post(f"{AUTH_URL}/register", json=self.test_user)
        self.assertEqual(reg_response.status_code, 201, "Registration failed")
        
        access_token = reg_response.json()['access_token']
        
        # Act - Access user endpoint with token
        response = requests.get(
            f"{AUTH_URL}/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Assert
        self.assertEqual(response.status_code, 200, 
                         f"User endpoint access failed: {response.text}")
        
        data = response.json()
        self.assertEqual(data['username'], self.test_user['username'])
        self.assertEqual(data['email'], self.test_user['email'])
    
    def test_user_endpoint_with_invalid_token(self):
        """Test accessing user data with an invalid token."""
        # Act - Access user endpoint with an invalid token
        response = requests.get(
            f"{AUTH_URL}/user",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        # Assert
        self.assertEqual(response.status_code, 422, 
                         "Should return 422 for invalid token")
    
    def test_check_availability_endpoint(self):
        """Test the check-availability endpoint."""
        # Arrange - Register a user first
        reg_response = requests.post(f"{AUTH_URL}/register", json=self.test_user)
        self.assertEqual(reg_response.status_code, 201, "Registration failed")
        
        # Act - Check username availability (should exist)
        username_response = requests.get(
            f"{AUTH_URL}/check-availability",
            params={"username": self.test_user["username"]}
        )
        
        # Assert for username
        self.assertEqual(username_response.status_code, 200)
        username_data = username_response.json()
        self.assertTrue(username_data.get('username_exists'))
        
        # Act - Check email availability (should exist)
        email_response = requests.get(
            f"{AUTH_URL}/check-availability",
            params={"email": self.test_user["email"]}
        )
        
        # Assert for email
        self.assertEqual(email_response.status_code, 200)
        email_data = email_response.json()
        self.assertTrue(email_data.get('email_exists'))
        
        # Act - Check availability of non-existent username
        nonexistent_response = requests.get(
            f"{AUTH_URL}/check-availability",
            params={"username": f"nonexistent_{int(time.time())}"}
        )
        
        # Assert for non-existent username
        self.assertEqual(nonexistent_response.status_code, 200)
        nonexistent_data = nonexistent_response.json()
        self.assertFalse(nonexistent_data.get('username_exists'))
    
    def test_refresh_token_endpoint(self):
        """Test the refresh token endpoint."""
        # Arrange - Register and get a refresh token
        reg_response = requests.post(f"{AUTH_URL}/register", json=self.test_user)
        self.assertEqual(reg_response.status_code, 201, "Registration failed")
        
        refresh_token = reg_response.json()['refresh_token']
        
        # Act - Use refresh token to get new access token
        response = requests.post(
            f"{AUTH_URL}/refresh",
            json={"refresh_token": refresh_token}
        )
        
        # Assert
        self.assertEqual(response.status_code, 200, 
                        f"Token refresh failed: {response.text}")
        
        data = response.json()
        self.assertIn('access_token', data, "Response missing 'access_token' field")
        self.assertIn('user', data, "Response missing 'user' field")
        
        # Verify the user data
        user_data = data['user']
        self.assertEqual(user_data['username'], self.test_user['username'])
        self.assertEqual(user_data['email'], self.test_user['email'])
    
    def test_refresh_with_invalid_token(self):
        """Test refresh with an invalid token."""
        # Act - Try to refresh with an invalid token
        response = requests.post(
            f"{AUTH_URL}/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        # Assert
        self.assertEqual(response.status_code, 401, 
                         "Should return 401 for invalid refresh token")
        
        data = response.json()
        self.assertIn('error', data, "Response missing 'error' field")


if __name__ == '__main__':
    unittest.main()
        
        user_data = data['user']
        self.assertEqual(user_data['username'], self.test_user['username'])
        self.assertEqual(user_data['email'], self.test_user['email'])
    
    def test_registration_duplicate_username(self):
        """Test registration with duplicate username."""
        # Arrange - Register a user first
        initial_reg = requests.post(f"{AUTH_URL}/register", json=self.test_user)
        self.assertEqual(initial_reg.status_code, 201, "Initial registration failed")
        
        # Act - Try to register again with same username but different email
        duplicate_user = {
            "username": self.test_user["username"],
            "email": f"different_{int(time.time())}@example.com",
            "password": "DifferentPass123!"
        }
        
        response = requests.post(f"{AUTH_URL}/register", json=duplicate_user)
        
        # Assert
        self.assertEqual(response.status_code, 409, 
                         "Should return 409 for duplicate username")
        
        data = response.json()
        self.assertIn('error', data, "Response missing 'error' field")
    
    def test_registration_duplicate_email(self):
        """Test registration with duplicate email."""
        # Arrange - Register a user first
        initial_reg = requests.post(f"{AUTH_URL}/register", json=self.test_user)
        self.assertEqual(initial_reg.status_code, 201, "Initial registration failed")
        
        # Act - Try to register again with same email but different username
        duplicate_user = {
            "username": f"different_{int(time.time())}",
            "email": self.test_user["email"],
            "password": "DifferentPass123!"
        }
        
        response = requests.post(f"{AUTH_URL}/register", json=duplicate_user)
        
        # Assert
        self.assertEqual(response.status_code, 409, 
                         "Should return 409 for duplicate email")
        
        data = response.json()
        self.assertIn('error', data, "Response missing 'error' field")
    
    def test_login_success(self):
        """Test successful login."""
        # Arrange - Register a user first
        initial_reg = requests.post(f"{AUTH_URL}/register", json=self.test_user)
        self.assertEqual(initial_reg.status_code, 201, "Initial registration failed")
        
        # Act - Try to login
        login_data = {
            "username": self.test_user["username"],
            "password": self.test_user["password"]
        }
        
        response = requests.post(f"{AUTH_URL}/login", json=login_data)
        
        # Assert
        self.assertEqual(response.status_code, 200, 
                         f"Login failed: {response.text}")
        
        data = response.json()
        self.assertIn('access_token', data, "Response missing 'access_token' field")
        self.assertIn('refresh_token', data, "Response missing 'refresh_token' field")
        self.assertIn('user', data, "Response missing 'user' fiel