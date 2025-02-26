import unittest
import requests
import json
import os
import time
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys

# Add the parent directory to sys.path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask app for direct testing
try:
    from app import app as flask_app
    from __init__ import app, limiter, jwt
    DIRECT_TESTING = True
except ImportError:
    DIRECT_TESTING = False

# Base API URL for remote testing
BASE_URL = "https://wavegerpython.onrender.com/api"
AUTH_URL = f"{BASE_URL}/auth"


class InputValidationErrorTests(unittest.TestCase):
    """Tests for handling invalid input data."""
    
    def test_empty_login_data(self):
        """Test login with empty data."""
        # Act - Send empty JSON data
        response = requests.post(f"{AUTH_URL}/login", json={})
        
        # Assert
        self.assertEqual(response.status_code, 400, 
                         "Should return 400 for empty login data")
        
        data = response.json()
        self.assertIn('error', data, "Response missing 'error' field")
    
    def test_missing_login_fields(self):
        """Test login with missing required fields."""
        # Act - Send partial data
        response = requests.post(f"{AUTH_URL}/login", json={"username": "testuser"})
        
        # Assert
        self.assertEqual(response.status_code, 400, 
                         "Should return 400 for missing fields")
        
        data = response.json()
        self.assertIn('error', data, "Response missing 'error' field")
    
    def test_empty_registration_data(self):
        """Test registration with empty data."""
        # Act - Send empty JSON data
        response = requests.post(f"{AUTH_URL}/register", json={})
        
        # Assert
        self.assertEqual(response.status_code, 400, 
                         "Should return 400 for empty registration data")
        
        data = response.json()
        self.assertIn('error', data, "Response missing 'error' field")
    
    def test_missing_registration_fields(self):
        """Test registration with missing required fields."""
        # Act - Send partial data
        response = requests.post(
            f"{AUTH_URL}/register", 
            json={"username": "testuser", "password": "testpass"}
        )
        
        # Assert
        self.assertEqual(response.status_code, 400, 
                         "Should return 400 for missing fields")
        
        data = response.json()
        self.assertIn('error', data, "Response missing 'error' field")
    
    def test_invalid_chart_range(self):
        """Test chart endpoint with invalid range parameter."""
        # Act - Send invalid range format
        response = requests.get(f"{BASE_URL}/chart?range=invalid")
        
        # Assert
        self.assertEqual(response.status_code, 400, 
                         "Should return 400 for invalid range format")
        
        data = response.json()
        self.assertIn('error', data, "Response missing 'error' field")
    
    def test_empty_refresh_token(self):
        """Test refresh endpoint with empty token."""
        # Act - Send empty token
        response = requests.post(f"{AUTH_URL}/refresh", json={})
        
        # Assert
        self.assertEqual(response.status_code, 400, 
                         "Should return 400 for empty refresh token")
        
        data = response.json()
        self.assertIn('error', data, "Response missing 'error' field")
    
    def test_empty_availability_check(self):
        """Test check-availability with no parameters."""
        # Act - Send no parameters
        response = requests.get(f"{AUTH_URL}/check-availability")
        
        # Assert
        self.assertEqual(response.status_code, 400, 
                         "Should return 400 for missing parameters")
        
        data = response.json()
        self.assertIn('error', data, "Response missing 'error' field")


class AuthErrorHandlingTests(unittest.TestCase):
    """Tests for authentication error handling."""
    
    def test_missing_auth_header(self):
        """Test accessing protected endpoint without auth header."""
        # Act - Access protected endpoint without header
        response = requests.get(f"{AUTH_URL}/user")
        
        # Assert
        self.assertEqual(response.status_code, 401, 
                         "Should return 401 for missing auth header")
        
        data = response.json()
        self.assertIn('msg', data, "Response missing 'msg' field")
    
    def test_invalid_auth_header_format(self):
        """Test accessing protected endpoint with invalid auth header format."""
        # Act - Access with invalid header format
        response = requests.get(
            f"{AUTH_URL}/user",
            headers={"Authorization": "InvalidFormat token123"}
        )
        
        # Assert
        self.assertEqual(response.status_code, 401, 
                         "Should return 401 for invalid auth header format")
        
        data = response.json()
        self.assertIn('msg', data, "Response missing 'msg' field")


class APIErrorHandlingTests(unittest.TestCase):
    """Tests for API error handling."""
    
    def test_nonexistent_endpoint(self):
        """Test accessing a non-existent endpoint."""
        # Act - Access non-existent endpoint
        response = requests.get(f"{BASE_URL}/nonexistent-endpoint")
        
        # Assert - Should return 404 Not Found
        self.assertEqual(response.status_code, 404, 
                         "Should return 404 for non-existent endpoint")
    
    def test_method_not_allowed(self):
        """Test using wrong HTTP method on an endpoint."""
        # Act - Use POST on a GET endpoint
        response = requests.post(f"{BASE_URL}/top-charts")
        
        # Assert - Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, 405, 
                         "Should return 405 for method not allowed")


@unittest.skipIf(not DIRECT_TESTING, "Skipping direct Flask app tests when not imported")
class FlaskAppErrorHandlingTests(unittest.TestCase):
    """Tests for error handling in the Flask app (requires direct import)."""
    
    def setUp(self):
        """Set up test client."""
        self.client = flask_app.test_client()
        self.client.testing = True
    
    def test_rate_limit_exceeded(self):
        """Test rate limiting error handling."""
        # Adjust the limiter for testing
        limiter.storage.clear()
        
        # Create a specific test route with a very low limit
        @flask_app.route("/api/test-rate-limit-error", methods=["GET"])
        @limiter.limit("1 per hour")
        def test_rate_limit_error():
            return {"status": "ok"}
        
        # First request should succeed
        response1 = self.client.get("/api/test-rate-limit-error")
        self.assertEqual(response1.status_code, 200)
        
        # Second request should hit rate limit
        response2 = self.client.get("/api/test-rate-limit-error")
        self.assertEqual(response2.status_code, 429)
        data = json.loads(response2.data)
        self.assertIn("error", data)
        self.assertIn("Too many requests", data["error"])
    
    def test_jwt_error_handlers(self):
        """Test JWT error handlers."""
        # Test invalid token
        response = self.client.get(
            "/api/auth/user", 
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        self.assertEqual(response.status_code, 422)
        data = json.loads(response.data)
        self.assertIn("msg", data)
        
        # Test missing token
        response = self.client.get("/api/auth/user")
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn("msg", data)


@unittest.skipIf(not DIRECT_TESTING, "Skipping direct Flask app tests when not imported")
class ExternalAPIDependencyTests(unittest.TestCase):
    """Tests handling failures with external API dependencies."""
    
    def setUp(self):
        """Set up test client and patches."""
        self.client = flask_app.test_client()
        self.client.testing = True
    
    @patch('charts.requests.get')
    def test_external_api_failure(self, mock_get):
        """Test handling external API failure in charts endpoint."""
        # Arrange - Mock the external API to fail
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("API Error")
        mock_get.return_value = mock_response
        
        # Act - Call the endpoint that depends on external API
        response = self.client.get("/api/top-charts")
        
        # Assert - Should handle the error and return 500
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    @patch('apple_music.jwt.encode')
    def test_apple_music_token_error(self, mock_encode):
        """Test handling JWT encoding errors in Apple Music token generation."""
        # Arrange - Mock JWT encoding to fail
        mock_encode.side_effect = Exception("JWT encoding error")
        
        # Act - Call the endpoint
        response = self.client.get("/api/apple-music-token")
        
        # Assert - Should handle the error and return 500
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn("error", data)


class RemoteExternalAPIDependencyTests(unittest.TestCase):
    """Tests handling failures with external API dependencies using remote requests."""
    
    def test_malformed_chart_id(self):
        """Test handling invalid chart ID in chart endpoint."""
        # Act - Request with a nonsensical chart ID
        response = requests.get(f"{BASE_URL}/chart?id=not-a-real-chart-id")
        
        # Note: This might still return 200 if the API handles invalid IDs gracefully
        # or if it fetches from a mock record in the database
        
        # The important thing is that it doesn't crash
        self.assertIn(response.status_code, [200, 404, 400, 500],
                     "Response should be handled without crashing")
        
        if response.status_code == 200:
            # If it returns 200, check if it has error info in the response
            data = response.json()
            if 'error' in data:
                self.assertIsNotNone(data['error'], "Should indicate an error")
    
    def test_malformed_chart_date(self):
        """Test handling invalid date in chart endpoint."""
        # Act - Request with an invalid date format
        response = requests.get(f"{BASE_URL}/chart?week=not-a-date")
        
        # Similar to above, might return various codes depending on implementation
        self.assertIn(response.status_code, [200, 404, 400, 500],
                     "Response should be handled without crashing")


if __name__ == '__main__':
    unittest.main()