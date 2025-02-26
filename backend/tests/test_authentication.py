import unittest
import json
import jwt
import time
from datetime import datetime, timedelta
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from flask_bcrypt import Bcrypt
import os
import sys

# Add the parent directory to sys.path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import generate_unique_token_id
import requests  # For integration testing

# Base API URL for integration tests
BASE_URL = "https://wavegerpython.onrender.com/api/auth"

class AuthenticationUnitTests(unittest.TestCase):
    """Unit tests for authentication-related functions."""
    
    def setUp(self):
        """Set up test app with bcrypt and JWT."""
        self.app = Flask(__name__)
        self.app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        self.jwt = JWTManager(self.app)
        self.bcrypt = Bcrypt(self.app)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        """Clean up after tests."""
        self.app_context.pop()
    
    def test_password_hashing(self):
        """Test that password hashing works correctly."""
        # Arrange
        password = "TestPassword123!"
        
        # Act
        password_hash = self.bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Assert
        self.assertTrue(self.bcrypt.check_password_hash(password_hash, password))
        self.assertFalse(self.bcrypt.check_password_hash(password_hash, "WrongPassword"))
    
    def test_token_generation(self):
        """Test JWT token generation and validation."""
        # Arrange
        user_id = "123"
        username = "testuser"
        email = "test@example.com"
        
        # Act - Create token with additional claims
        access_token = create_access_token(
            identity=user_id,
            additional_claims={
                "username": username,
                "email": email,
                "token_id": generate_unique_token_id()
            }
        )
        
        # Assert - Decode and verify token
        decoded = jwt.decode(
            access_token, 
            self.app.config['JWT_SECRET_KEY'], 
            algorithms=["HS256"]
        )
        
        self.assertEqual(decoded['sub'], user_id)
        self.assertEqual(decoded['username'], username)
        self.assertEqual(decoded['email'], email)
        self.assertIn('token_id', decoded)
        self.assertIn('exp', decoded)
        
    def test_token_expiration(self):
        """Test that tokens expire according to configuration."""
        # Arrange - Create token with short expiry
        user_id = "123"
        expires_delta = timedelta(seconds=1)  # Very short expiration
        
        # Act - Create token
        access_token = create_access_token(
            identity=user_id,
            expires_delta=expires_delta
        )
        
        # Decode without verification to see expiry time
        unverified = jwt.decode(
            access_token,
            options={"verify_signature": False}
        )
        exp_time = unverified['exp']
        
        # Assert expiry is close to current time + delta
        self.assertAlmostEqual(
            exp_time, 
            int(time.time()) + 1,  # 1 second from now
            delta=2  # Allow 2 seconds of leeway for test execution
        )
        
        # Wait for token to expire
        time.sleep(2)
        
        # Attempt to decode after expiration
        with self.assertRaises(jwt.ExpiredSignatureError):
            jwt.decode(
                access_token,
                self.app.config['JWT_SECRET_KEY'],
                algorithms=["HS256"]
            )
            
    def test_unique_token_id(self):
        """Test that generate_unique_token_id returns unique values."""
        # Act - Generate multiple token IDs
        token_ids = set(generate_unique_token_id() for _ in range(100))
        
        # Assert - All IDs should be unique
        self.assertEqual(len(token_ids), 100)


class AuthenticationIntegrationTests(unittest.TestCase):
    """Integration tests for authentication endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.test_user = {
            "username": f"test_user_{int(time.time())}",  # Unique username
            "email": f"test_{int(time.time())}@example.com",  # Unique email
            "password": "TestPassword123!"
        }
        
    def test_registration_and_login_flow(self):
        """Test the complete registration and login flow."""
        # 1. Register a new user
        register_response = requests.post(
            f"{BASE_URL}/register",
            json=self.test_user
        )
        
        self.assertEqual(register_response.status_code, 201, 
                         f"Registration failed: {register_response.text}")
        
        register_data = register_response.json()
        self.assertIn('access_token', register_data)
        self.assertIn('refresh_token', register_data)
        self.assertIn('user', register_data)
        
        # 2. Test login with the same credentials
        login_response = requests.post(
            f"{BASE_URL}/login",
            json={
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
        )
        
        self.assertEqual(login_response.status_code, 200,
                        f"Login failed: {login_response.text}")
        
        login_data = login_response.json()
        self.assertIn('access_token', login_data)
        self.assertIn('refresh_token', login_data)
        
        # 3. Test token usage with user endpoint
        user_response = requests.get(
            f"{BASE_URL}/user",
            headers={"Authorization": f"Bearer {login_data['access_token']}"}
        )
        
        self.assertEqual(user_response.status_code, 200,
                        f"User endpoint access failed: {user_response.text}")
        
        user_data = user_response.json()
        self.assertEqual(user_data['username'], self.test_user['username'])
        self.assertEqual(user_data['email'], self.test_user['email'])
    
    def test_invalid_login(self):
        """Test login with invalid credentials."""
        # Act - Attempt login with wrong password
        login_response = requests.post(
            f"{BASE_URL}/login",
            json={
                "username": "nonexistent_user",
                "password": "wrong_password"
            }
        )
        
        # Assert
        self.assertEqual(login_response.status_code, 401)
        self.assertIn('error', login_response.json())
    
    def test_token_refresh(self):
        """Test refresh token functionality."""
        # 1. Register a new user to get a fresh refresh token
        register_response = requests.post(
            f"{BASE_URL}/register",
            json=self.test_user
        )
        
        register_data = register_response.json()
        refresh_token = register_data['refresh_token']
        
        # 2. Use refresh token to get new access token
        refresh_response = requests.post(
            f"{BASE_URL}/refresh",
            json={"refresh_token": refresh_token}
        )
        
        self.assertEqual(refresh_response.status_code, 200,
                        f"Token refresh failed: {refresh_response.text}")
        
        refresh_data = refresh_response.json()
        self.assertIn('access_token', refresh_data)
        
        # 3. Verify the new access token works
        user_response = requests.get(
            f"{BASE_URL}/user",
            headers={"Authorization": f"Bearer {refresh_data['access_token']}"}
        )
        
        self.assertEqual(user_response.status_code, 200)
    
    def test_username_email_availability(self):
        """Test the availability checking endpoint."""
        # 1. Register a user first
        requests.post(
            f"{BASE_URL}/register",
            json=self.test_user
        )
        
        # 2. Check username availability (should be taken)
        username_check = requests.get(
            f"{BASE_URL}/check-availability",
            params={"username": self.test_user["username"]}
        )
        
        self.assertEqual(username_check.status_code, 200)
        username_data = username_check.json()
        self.assertTrue(username_data.get('username_exists'))
        
        # 3. Check email availability (should be taken)
        email_check = requests.get(
            f"{BASE_URL}/check-availability",
            params={"email": self.test_user["email"]}
        )
        
        self.assertEqual(email_check.status_code, 200)
        email_data = email_check.json()
        self.assertTrue(email_data.get('email_exists'))
        
        # 4. Check availability of unused username
        unused_check = requests.get(
            f"{BASE_URL}/check-availability",
            params={"username": f"unused_{int(time.time())}"}
        )
        
        unused_data = unused_check.json()
        self.assertFalse(unused_data.get('username_exists'))


if __name__ == '__main__':
    unittest.main()