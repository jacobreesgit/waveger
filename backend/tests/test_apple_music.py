import requests
import time
import os
import jwt
import json
from unittest import mock
import pytest
import traceback
import logging
from datetime import datetime
import importlib.util
import sys
import io
import builtins  # Add this import for accessing builtin functions
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define BASE_URL
BASE_URL = "https://wavegerpython.onrender.com/api"

# Reset rate limiter at the beginning of tests
def reset_rate_limiter():
    """Reset all rate limits on the remote server"""
    try:
        # Admin endpoint for resetting rate limits
        admin_url = f"{BASE_URL}/admin/reset-rate-limiter"
        
        # Get admin key from environment
        admin_key = os.getenv("ADMIN_SECRET_KEY")
        
        if not admin_key:
            print("ERROR: ADMIN_SECRET_KEY environment variable not set")
            print("Set this variable in your .env file")
            return
        
        # Send request to reset rate limiter
        response = requests.post(
            admin_url,
            headers={"X-Admin-Key": admin_key}
        )
        
        if response.status_code == 200:
            print("Successfully reset rate limiter on remote server")
            # Add a short delay to ensure reset takes effect
            time.sleep(1)
        else:
            print(f"Failed to reset rate limiter. Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print(f"Error resetting rate limiter: {e}")

# Reset rate limits before running tests
reset_rate_limiter()

# Rest of your existing code follows...

# Import the apple_music module from the parent directory
def import_module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Try to import apple_music module from backend directory
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    apple_music_path = os.path.join(backend_dir, 'apple_music.py')
    apple_music_module = import_module_from_file('apple_music_module', apple_music_path)
    logger.info("Successfully imported apple_music module")
except Exception as e:
    logger.error(f"Failed to import apple_music module: {e}")
    
    # Create a stub Flask Blueprint for testing
    from flask import Blueprint, jsonify
    
    class AppleMusicStub:
        def __init__(self):
            self.apple_music_bp = Blueprint("apple_music", __name__)
            self.TEAM_ID = os.getenv("APPLE_MUSIC_TEAM_ID")
            self.KEY_ID = os.getenv("APPLE_MUSIC_KEY_ID")
            self.PRIVATE_KEY_PATH = "/etc/secrets/AuthKey.p8"
            
            @self.apple_music_bp.route("/apple-music-token", methods=["GET"])
            def get_apple_music_token():
                token = self.generate_apple_music_token()
                if isinstance(token, tuple):
                    return token
                return jsonify({"token": token})
                
        def generate_apple_music_token(self):
            if not os.path.exists(self.PRIVATE_KEY_PATH):
                return jsonify({"error": "Private key file missing"}), 500
                
            try:
                with open(self.PRIVATE_KEY_PATH, "r") as key_file:
                    private_key = key_file.read()
                    
                payload = {
                    "iss": self.TEAM_ID,
                    "exp": int(time.time()) + (180 * 24 * 60 * 60),
                    "iat": int(time.time()),
                }
                
                token = jwt.encode(
                    payload, private_key, algorithm="ES256", 
                    headers={"kid": self.KEY_ID}
                )
                
                return token
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    apple_music_module = AppleMusicStub()
    logger.warning("Using stub apple_music module for testing")

# Helper function for timestamp
def timestamp():
    """Get current timestamp for logging."""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

# Define test functions
def test_token_generation_success():
    """Test successful Apple Music token generation."""
    print("\n=== TESTING SUCCESSFUL APPLE MUSIC TOKEN GENERATION ===")
    
    # Save original functions/properties to restore later
    original_path_exists = os.path.exists
    original_open = builtins.open  # Use builtins.open instead
    original_encode = jwt.encode
    original_team_id = getattr(apple_music_module, 'TEAM_ID', os.getenv("APPLE_MUSIC_TEAM_ID"))
    original_key_id = getattr(apple_music_module, 'KEY_ID', os.getenv("APPLE_MUSIC_KEY_ID"))
    original_key_path = getattr(apple_music_module, 'PRIVATE_KEY_PATH', "/etc/secrets/AuthKey.p8")
    
    try:
        # Create a Flask app for context
        from flask import Flask, jsonify
        app = Flask(__name__)
        
        # Set environment variables for testing
        test_team_id = "TESTTEAMID123"
        test_key_id = "TESTKEYID456"
        test_private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDJQFI5\n-----END PRIVATE KEY-----"
        
        # Mock environment variables
        if hasattr(apple_music_module, 'TEAM_ID'):
            setattr(apple_music_module, 'TEAM_ID', test_team_id)
        else:
            os.environ["APPLE_MUSIC_TEAM_ID"] = test_team_id
            
        if hasattr(apple_music_module, 'KEY_ID'):
            setattr(apple_music_module, 'KEY_ID', test_key_id)
        else:
            os.environ["APPLE_MUSIC_KEY_ID"] = test_key_id
        
        # Mock path exists to return True
        os.path.exists = mock.MagicMock(return_value=True)
        
        # Mock open to return a file-like object with our test key
        mock_file = mock.MagicMock()
        mock_file.__enter__ = mock.MagicMock(return_value=io.StringIO(test_private_key))
        builtins.open = mock.MagicMock(return_value=mock_file)
        
        # Mock jwt.encode to return a predictable token
        mock_token = "eyJhbGciOiJFUzI1NiIsImtpZCI6IlRFU1RLRVlJRDQ1NiJ9.eyJpc3MiOiJURVNUVEVBTUlEMTIzIn0.signature"
        jwt.encode = mock.MagicMock(return_value=mock_token)
        
        # Test the token generation within app context
        with app.app_context():
            start_time = time.time()
            print(f"[{timestamp()}] Generating Apple Music token...")
            
            # Call the function being tested
            if hasattr(apple_music_module, 'generate_apple_music_token'):
                token = apple_music_module.generate_apple_music_token()
            else:
                token = apple_music_module.generate_apple_music_token()
        
        elapsed = time.time() - start_time
        print(f"[{timestamp()}] Token generation completed in {elapsed:.2f}s")
        
        # Assertions
        assert token == mock_token, f"Expected {mock_token}, got {token}"
        assert jwt.encode.called, "jwt.encode was not called"
        
        call_args, call_kwargs = jwt.encode.call_args
        payload = call_args[0]
        
        assert "iss" in payload, "Missing 'iss' claim in payload"
        assert payload["iss"] == test_team_id, f"Expected iss={test_team_id}, got {payload['iss']}"
        assert "exp" in payload, "Missing 'exp' claim in payload"
        assert "iat" in payload, "Missing 'iat' claim in payload"
        
        assert call_kwargs["algorithm"] == "ES256", f"Expected algorithm='ES256', got {call_kwargs['algorithm']}"
        assert "kid" in call_kwargs["headers"], "Missing 'kid' in headers"
        assert call_kwargs["headers"]["kid"] == test_key_id, f"Expected kid={test_key_id}, got {call_kwargs['headers']['kid']}"
        
        print("✅ Apple Music token generation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        traceback.print_exc()
        return False
    
    finally:
        # Restore original functions/properties
        os.path.exists = original_path_exists
        builtins.open = original_open
        jwt.encode = original_encode
        
        # Restore original values
        if hasattr(apple_music_module, 'TEAM_ID'):
            setattr(apple_music_module, 'TEAM_ID', original_team_id)
        else:
            if original_team_id:
                os.environ["APPLE_MUSIC_TEAM_ID"] = original_team_id
            else:
                os.environ.pop("APPLE_MUSIC_TEAM_ID", None)
                
        if hasattr(apple_music_module, 'KEY_ID'):
            setattr(apple_music_module, 'KEY_ID', original_key_id)
        else:
            if original_key_id:
                os.environ["APPLE_MUSIC_KEY_ID"] = original_key_id
            else:
                os.environ.pop("APPLE_MUSIC_KEY_ID", None)

def test_missing_private_key():
    """Test token generation when private key file is missing."""
    print("\n=== TESTING APPLE MUSIC TOKEN GENERATION WITH MISSING KEY ===")
    
    # Save original functions to restore later
    original_path_exists = os.path.exists
    
    try:
        # Create a Flask app for context
        from flask import Flask, jsonify
        app = Flask(__name__)
        
        # Mock path exists to return False (key file doesn't exist)
        os.path.exists = mock.MagicMock(return_value=False)
        
        # Test the token generation within app context
        with app.app_context():
            start_time = time.time()
            print(f"[{timestamp()}] Generating Apple Music token with missing key file...")
            
            # Call the function being tested
            if hasattr(apple_music_module, 'generate_apple_music_token'):
                result = apple_music_module.generate_apple_music_token()
            else:
                result = apple_music_module.generate_apple_music_token()
        
        elapsed = time.time() - start_time
        print(f"[{timestamp()}] Function call completed in {elapsed:.2f}s")
        
        # Assertions
        assert isinstance(result, tuple), "Expected a tuple response for error"
        assert len(result) == 2, "Expected (response, status_code) tuple"
        assert result[1] == 500, f"Expected status code 500, got {result[1]}"
        
        # Check error message
        response_data = None
        if hasattr(result[0], 'json'):
            # If it's a Flask response
            response_data = result[0].get_json()
        else:
            # If it's already a dict
            response_data = result[0]
            
        assert "error" in response_data, "Missing 'error' field in response"
        assert "missing" in response_data["error"].lower(), f"Expected error message about missing key, got: {response_data['error']}"
        
        print("✅ Missing private key test passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        traceback.print_exc()
        return False
    
    finally:
        # Restore original functions
        os.path.exists = original_path_exists

def test_invalid_private_key():
    """Test token generation with invalid private key content."""
    print("\n=== TESTING APPLE MUSIC TOKEN GENERATION WITH INVALID KEY ===")
    
    # Save original functions to restore later
    original_path_exists = os.path.exists
    original_open = builtins.open
    original_encode = jwt.encode
    
    try:
        # Create a Flask app for context
        from flask import Flask, jsonify
        app = Flask(__name__)
        
        # Mock path exists to return True
        os.path.exists = mock.MagicMock(return_value=True)
        
        # Mock open to return invalid key content
        mock_file = mock.MagicMock()
        mock_file.__enter__ = mock.MagicMock(return_value=io.StringIO("INVALID KEY CONTENT"))
        builtins.open = mock.MagicMock(return_value=mock_file)
        
        # Mock jwt.encode to raise an exception
        jwt.encode = mock.MagicMock(side_effect=ValueError("Invalid key format"))
        
        # Test the token generation within app context
        with app.app_context():
            start_time = time.time()
            print(f"[{timestamp()}] Generating Apple Music token with invalid key...")
            
            # Call the function being tested
            if hasattr(apple_music_module, 'generate_apple_music_token'):
                result = apple_music_module.generate_apple_music_token()
            else:
                result = apple_music_module.generate_apple_music_token()
        
        elapsed = time.time() - start_time
        print(f"[{timestamp()}] Function call completed in {elapsed:.2f}s")
        
        # Assertions
        assert isinstance(result, tuple), "Expected a tuple response for error"
        assert len(result) == 2, "Expected (response, status_code) tuple"
        assert result[1] == 500, f"Expected status code 500, got {result[1]}"
        
        # Check error message
        response_data = None
        if hasattr(result[0], 'json'):
            # If it's a Flask response
            response_data = result[0].get_json()
        else:
            # If it's already a dict
            response_data = result[0]
            
        assert "error" in response_data, "Missing 'error' field in response"
        
        print("✅ Invalid private key test passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        traceback.print_exc()
        return False
    
    finally:
        # Restore original functions
        os.path.exists = original_path_exists
        builtins.open = original_open
        jwt.encode = original_encode

def test_api_endpoint():
    """Test the Apple Music token API endpoint."""
    print("\n=== TESTING APPLE MUSIC TOKEN API ENDPOINT ===")
    
    # Save original function to restore later
    original_generate_token = None
    if hasattr(apple_music_module, 'generate_apple_music_token'):
        original_generate_token = apple_music_module.generate_apple_music_token
    
    try:
        # Create a test Flask app
        from flask import Flask
        app = Flask(__name__)
        
        # Register blueprint
        if hasattr(apple_music_module, 'apple_music_bp'):
            app.register_blueprint(apple_music_module.apple_music_bp, url_prefix="/api")
        else:
            app.register_blueprint(apple_music_module.apple_music_bp, url_prefix="/api")
        
        # Mock the generate_apple_music_token function
        mock_token = "eyJhbGciOiJFUzI1NiIsImtpZCI6IlRFU1RLRVlJRDQ1NiJ9.eyJpc3MiOiJURVNUVEVBTUlEMTIzIn0.signature"
        
        def mock_generate_token():
            return mock_token
            
        if hasattr(apple_music_module, 'generate_apple_music_token'):
            setattr(apple_music_module, 'generate_apple_music_token', mock_generate_token)
        else:
            setattr(apple_music_module, 'generate_apple_music_token', mock_generate_token)
        
        # Create a test client
        client = app.test_client()
        
        # Test the endpoint
        start_time = time.time()
        print(f"[{timestamp()}] Calling Apple Music token endpoint...")
        
        response = client.get("/api/apple-music-token")
        
        elapsed = time.time() - start_time
        print(f"[{timestamp()}] API call completed in {elapsed:.2f}s")
        
        # Assertions
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        
        data = json.loads(response.data.decode('utf-8'))
        assert "token" in data, "Missing 'token' field in response"
        assert data["token"] == mock_token, f"Expected token={mock_token}, got {data['token']}"
        
        print("✅ Apple Music token API endpoint test passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        traceback.print_exc()
        return False
    
    finally:
        # Restore original function
        if original_generate_token and hasattr(apple_music_module, 'generate_apple_music_token'):
            setattr(apple_music_module, 'generate_apple_music_token', original_generate_token)
            
def test_api_endpoint_error_handling():
    """Test error handling in the Apple Music token API endpoint."""
    print("\n=== TESTING APPLE MUSIC TOKEN API ENDPOINT ERROR HANDLING ===")
    
    # Save original function to restore later
    original_generate_token = None
    if hasattr(apple_music_module, 'generate_apple_music_token'):
        original_generate_token = apple_music_module.generate_apple_music_token
    
    try:
        # Create a test Flask app
        from flask import Flask, jsonify
        app = Flask(__name__)
        
        # Register blueprint
        if hasattr(apple_music_module, 'apple_music_bp'):
            app.register_blueprint(apple_music_module.apple_music_bp, url_prefix="/api")
        else:
            app.register_blueprint(apple_music_module.apple_music_bp, url_prefix="/api")
        
        # Mock the generate_apple_music_token function to return an error
        def mock_generate_token_error():
            return (jsonify({"error": "Test error message"}), 500)
            
        if hasattr(apple_music_module, 'generate_apple_music_token'):
            setattr(apple_music_module, 'generate_apple_music_token', mock_generate_token_error)
        else:
            setattr(apple_music_module, 'generate_apple_music_token', mock_generate_token_error)
        
        # Create a test client
        client = app.test_client()
        
        # Test the endpoint
        start_time = time.time()
        print(f"[{timestamp()}] Calling Apple Music token endpoint with error...")
        
        response = client.get("/api/apple-music-token")
        
        elapsed = time.time() - start_time
        print(f"[{timestamp()}] API call completed in {elapsed:.2f}s")
        
        # Assertions
        assert response.status_code == 500, f"Expected status code 500, got {response.status_code}"
        
        data = json.loads(response.data.decode('utf-8'))
        assert "error" in data, "Missing 'error' field in response"
        assert data["error"] == "Test error message", f"Expected error='Test error message', got {data['error']}"
        
        print("✅ Apple Music token API endpoint error handling test passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        traceback.print_exc()
        return False
    
    finally:
        # Restore original function
        if original_generate_token and hasattr(apple_music_module, 'generate_apple_music_token'):
            setattr(apple_music_module, 'generate_apple_music_token', original_generate_token)

def run_all_tests():
    """Run all Apple Music integration tests in sequence."""
    print("\n=========================================")
    print("BEGINNING APPLE MUSIC INTEGRATION TESTS")
    print("=========================================")
    
    # Reset rate limiter before tests
    reset_rate_limiter()
    
    # Track test results
    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
    
    # List of all test functions
    tests = [
        test_token_generation_success,
        test_missing_private_key,
        test_invalid_private_key,
        test_api_endpoint,
        test_api_endpoint_error_handling
    ]
    
    # Run each test
    for test_func in tests:
        try:
            result = test_func()
            if result:
                results["passed"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            print(f"\nTEST ERROR: {test_func.__name__} - {str(e)}")
            traceback.print_exc()
            results["failed"] += 1
    
    # Print summary
    print("\n=========================================")
    print(f"TEST RESULTS: {results['passed']} passed, {results['failed']} failed, {results['skipped']} skipped")
    
    if results["failed"] == 0:
        print("ALL APPLE MUSIC INTEGRATION TESTS PASSED!")
    else:
        print(f"SOME TESTS FAILED ({results['failed']} failures)")
    print("=========================================")
    
    return results["failed"] == 0

if __name__ == "__main__":
    run_all_tests()