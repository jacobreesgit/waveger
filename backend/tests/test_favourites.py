import requests
import json
import time
import random
import string
from datetime import datetime
import os
import sys

# Reset rate limiter at the beginning of tests
def reset_rate_limiter():
    """Reset all rate limits to 0 at the start of tests"""
    try:
        # Try to import the limiter from the main application
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        sys.path.insert(0, backend_dir)
        
        from __init__ import limiter
        
        # Reset all limits
        limiter.reset()
        print("Successfully reset rate limiter")
    except Exception as e:
        print(f"Failed to reset rate limiter: {e}")

# Reset rate limits before running tests
reset_rate_limiter()

# Base API URLs
BASE_URL = "https://wavegerpython.onrender.com/api"
AUTH_URL = f"{BASE_URL}/auth"

# Test data for favorites
TEST_FAVORITE = {
    "song_name": "Test Song",
    "artist": "Test Artist",
    "chart_id": "hot-100",
    "chart_title": "Billboard Hot 100",
    "position": 1,
    "image_url": "https://example.com/image.jpg",
    "peak_position": 1,
    "weeks_on_chart": 10
}

# ---------------------- Helper Functions ----------------------

def random_string(length=8):
    """Generate a random string for unique test data."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def create_test_user():
    """Create a new test user and return credentials."""
    username = f"test_fav_{random_string()}"
    email = f"{username}@example.com"
    password = "Test123!Special"
    
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{AUTH_URL}/register", json=register_data)
    
    # If registration fails due to rate limiting, use a delay and retry
    if response.status_code == 429:
        print("Rate limit hit during test user creation. Waiting 60 seconds to retry...")
        time.sleep(60)
        response = requests.post(f"{AUTH_URL}/register", json=register_data)
    
    # If still problematic, raise exception with details
    if response.status_code != 201:
        raise Exception(f"Failed to create test user. Status: {response.status_code}, Response: {response.text}")
    
    # Extract token from response
    data = response.json()
    
    return {
        "username": username,
        "email": email,
        "password": password,
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
        "user_id": data.get("user", {}).get("id")
    }

def get_auth_headers(token):
    """Get authorization headers with the provided token."""
    return {"Authorization": f"Bearer {token}"}

def add_favorite_helper(token):
    """Helper function to add a favorite and return its ID."""
    # Generate a unique song name to avoid conflicts
    unique_favorite = TEST_FAVORITE.copy()
    unique_favorite["song_name"] = f"Test Song {random_string()}"
    
    headers = get_auth_headers(token)
    response = requests.post(f"{BASE_URL}/favourites", json=unique_favorite, headers=headers)
    
    if response.status_code not in (200, 201):
        raise Exception(f"Failed to create test favorite. Status: {response.status_code}, Response: {response.text}")
    
    return response.json().get("favourite_id"), unique_favorite

# ---------------------- Test Functions ----------------------

def test_add_favourite():
    """Test adding a song to favorites."""
    print("\n=== TESTING ADD FAVOURITE ===")
    
    # Create a test user
    user = create_test_user()
    headers = get_auth_headers(user["access_token"])
    
    # Generate a unique favorite
    unique_favorite = TEST_FAVORITE.copy()
    unique_favorite["song_name"] = f"Test Song {random_string()}"
    
    # Add the favorite
    response = requests.post(f"{BASE_URL}/favourites", json=unique_favorite, headers=headers)
    
    # Check response
    assert response.status_code in (200, 201), f"Add favorite failed with status {response.status_code}: {response.text}"
    
    data = response.json()
    assert "favourite_id" in data, "Response missing favourite_id"
    assert "message" in data, "Response missing message"
    
    favorite_id = data["favourite_id"]
    print(f"✅ Successfully added favorite with ID: {favorite_id}")
    
    # Test adding the same favorite again (should return success but indicate it's already favorited)
    duplicate_response = requests.post(f"{BASE_URL}/favourites", json=unique_favorite, headers=headers)
    
    assert duplicate_response.status_code == 200, f"Duplicate add request failed with status {duplicate_response.status_code}"
    duplicate_data = duplicate_response.json()
    assert "already in favourites" in duplicate_data.get("message", ""), "Missing duplicate detection message"
    
    print("✅ Duplicate detection works correctly")
    
    return favorite_id, user

def test_get_favourites():
    """Test retrieving favorites for a user."""
    print("\n=== TESTING GET FAVOURITES ===")
    
    # Create a test user
    user = create_test_user()
    headers = get_auth_headers(user["access_token"])
    
    # Add a test favorite first
    favorite_id, favorite_data = add_favorite_helper(user["access_token"])
    print(f"Added test favorite with ID: {favorite_id} for retrieval test")
    
    # Get all favorites
    response = requests.get(f"{BASE_URL}/favourites", headers=headers)
    
    # Check response
    assert response.status_code == 200, f"Get favorites failed with status {response.status_code}: {response.text}"
    
    data = response.json()
    assert "favourites" in data, "Response missing favourites list"
    
    # Check if our test favorite is in the list
    found = False
    for favorite in data["favourites"]:
        if any(chart["id"] == favorite_id for chart in favorite.get("charts", [])):
            found = True
            break
    
    assert found, f"Added favorite (ID: {favorite_id}) not found in the favorites list"
    
    print(f"✅ Successfully retrieved {len(data['favourites'])} favorites, including test favorite")

def test_check_favourite():
    """Test checking if a song is favorited."""
    print("\n=== TESTING CHECK FAVOURITE STATUS ===")
    
    # Create a test user
    user = create_test_user()
    headers = get_auth_headers(user["access_token"])
    
    # Add a test favorite first
    favorite_id, favorite_data = add_favorite_helper(user["access_token"])
    print(f"Added test favorite with ID: {favorite_id} for status check test")
    
    # Check if favorited
    params = {
        "song_name": favorite_data["song_name"],
        "artist": favorite_data["artist"],
        "chart_id": favorite_data["chart_id"]
    }
    
    response = requests.get(f"{BASE_URL}/favourites/check", params=params, headers=headers)
    
    # Check response
    assert response.status_code == 200, f"Check favorite failed with status {response.status_code}: {response.text}"
    
    data = response.json()
    assert "is_favourited" in data, "Response missing is_favourited flag"
    assert data["is_favourited"] is True, "Favorite should be marked as favorited"
    assert "favourite_id" in data, "Response missing favourite_id"
    
    print("✅ Successfully verified favorite status")
    
    # Check a non-favorited item
    non_favorite_params = {
        "song_name": f"Non Favorite Song {random_string()}",
        "artist": "Non Favorite Artist",
        "chart_id": "hot-100"
    }
    
    non_favorite_response = requests.get(
        f"{BASE_URL}/favourites/check", 
        params=non_favorite_params, 
        headers=headers
    )
    
    assert non_favorite_response.status_code == 200, "Check non-favorite failed"
    non_favorite_data = non_favorite_response.json()
    assert non_favorite_data["is_favourited"] is False, "Non-favorite should not be marked as favorited"
    
    print("✅ Successfully verified non-favorite status")

def test_remove_favourite():
    """Test removing a song from favorites."""
    print("\n=== TESTING REMOVE FAVOURITE ===")
    
    # Create a test user
    user = create_test_user()
    headers = get_auth_headers(user["access_token"])
    
    # Add a test favorite first
    favorite_id, _ = add_favorite_helper(user["access_token"])
    print(f"Added test favorite with ID: {favorite_id} for removal test")
    
    # Remove the favorite
    response = requests.delete(f"{BASE_URL}/favourites/{favorite_id}", headers=headers)
    
    # Check response
    assert response.status_code == 200, f"Remove favorite failed with status {response.status_code}: {response.text}"
    
    data = response.json()
    assert "message" in data, "Response missing message"
    assert "removed" in data["message"].lower(), "Message should indicate removal"
    
    print(f"✅ Successfully removed favorite with ID: {favorite_id}")
    
    # Verify it's gone by checking favorites list
    get_response = requests.get(f"{BASE_URL}/favourites", headers=headers)
    assert get_response.status_code == 200, "Get favorites failed after removal"
    
    get_data = get_response.json()
    
    # Check if our test favorite is NOT in the list
    found = False
    for favorite in get_data["favourites"]:
        if any(chart["id"] == favorite_id for chart in favorite.get("charts", [])):
            found = True
            break
    
    assert not found, f"Removed favorite (ID: {favorite_id}) is still in the favorites list"
    
    print("✅ Verified favorite was removed successfully")

def test_unauthorized_access():
    """Test accessing favorites endpoints without authorization."""
    print("\n=== TESTING UNAUTHORIZED ACCESS ===")
    
    # Try to get favorites without a token
    get_response = requests.get(f"{BASE_URL}/favourites")
    assert get_response.status_code == 401, f"Expected 401 for unauthorized get, got {get_response.status_code}"
    
    # Try to add a favorite without a token
    add_response = requests.post(f"{BASE_URL}/favourites", json=TEST_FAVORITE)
    assert add_response.status_code == 401, f"Expected 401 for unauthorized add, got {add_response.status_code}"
    
    # Try to check a favorite without a token
    check_response = requests.get(
        f"{BASE_URL}/favourites/check",
        params={
            "song_name": TEST_FAVORITE["song_name"],
            "artist": TEST_FAVORITE["artist"],
            "chart_id": TEST_FAVORITE["chart_id"]
        }
    )
    assert check_response.status_code == 401, f"Expected 401 for unauthorized check, got {check_response.status_code}"
    
    # Try to remove a favorite without a token
    remove_response = requests.delete(f"{BASE_URL}/favourites/1")
    assert remove_response.status_code == 401, f"Expected 401 for unauthorized remove, got {remove_response.status_code}"
    
    print("✅ All unauthorized access attempts correctly returned 401")

def test_invalid_inputs():
    """Test handling of invalid inputs to favorites endpoints."""
    print("\n=== TESTING INVALID INPUTS ===")
    
    # Create a test user
    user = create_test_user()
    headers = get_auth_headers(user["access_token"])
    
    # Test missing required fields for add favorite
    for field in ["song_name", "artist", "chart_id", "chart_title"]:
        invalid_data = TEST_FAVORITE.copy()
        invalid_data.pop(field)
        
        response = requests.post(f"{BASE_URL}/favourites", json=invalid_data, headers=headers)
        assert response.status_code == 400, f"Expected 400 for missing {field}, got {response.status_code}"
    
    print("✅ Missing required fields correctly return 400")
    
    # Test invalid favorite ID for remove endpoint
    invalid_id = 99999999  # Assuming this ID doesn't exist
    remove_response = requests.delete(f"{BASE_URL}/favourites/{invalid_id}", headers=headers)
    assert remove_response.status_code == 404, f"Expected 404 for invalid ID, got {remove_response.status_code}"
    
    print("✅ Invalid favorite ID correctly returns 404")
    
    # Test missing parameters for check endpoint
    for field in ["song_name", "artist", "chart_id"]:
        params = {
            "song_name": TEST_FAVORITE["song_name"],
            "artist": TEST_FAVORITE["artist"],
            "chart_id": TEST_FAVORITE["chart_id"]
        }
        params.pop(field)
        
        check_response = requests.get(f"{BASE_URL}/favourites/check", params=params, headers=headers)
        assert check_response.status_code == 400, f"Expected 400 for missing {field}, got {check_response.status_code}"
    
    print("✅ Missing check parameters correctly return 400")

def test_concurrent_operations():
    """Test concurrent operations on favorites."""
    print("\n=== TESTING CONCURRENT OPERATIONS ===")
    
    # Create a test user
    user = create_test_user()
    headers = get_auth_headers(user["access_token"])
    
    # Create multiple unique favorites simultaneously
    import threading
    
    favorites = []
    errors = []
    
    def add_favorite(index):
        try:
            unique_favorite = TEST_FAVORITE.copy()
            unique_favorite["song_name"] = f"Concurrent Test Song {random_string()}"
            unique_favorite["position"] = index
            
            response = requests.post(f"{BASE_URL}/favourites", json=unique_favorite, headers=headers)
            
            if response.status_code not in (200, 201):
                errors.append(f"Concurrent add failed with status {response.status_code}: {response.text}")
            else:
                favorites.append(response.json().get("favourite_id"))
        except Exception as e:
            errors.append(f"Exception in add_favorite: {str(e)}")
    
    # Start 5 concurrent add operations
    threads = []
    for i in range(5):
        thread = threading.Thread(target=add_favorite, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check for errors
    assert not errors, f"Concurrent operations had errors: {errors}"
    
    # Verify all favorites were added
    get_response = requests.get(f"{BASE_URL}/favourites", headers=headers)
    assert get_response.status_code == 200, "Get favorites failed after concurrent adds"
    
    favourites_data = get_response.json()["favourites"]
    
    # Count how many of our concurrent favorites we can find
    found_count = 0
    for favorite_id in favorites:
        for favorite in favourites_data:
            if any(chart["id"] == favorite_id for chart in favorite.get("charts", [])):
                found_count += 1
                break
    
    assert found_count == len(favorites), f"Found {found_count} favorites, expected {len(favorites)}"
    
    print(f"✅ Successfully verified {found_count} concurrent favorite additions")
    
    # Clean up by removing all favorites
    for favorite_id in favorites:
        requests.delete(f"{BASE_URL}/favourites/{favorite_id}", headers=headers)

def run_all_tests():
    """Run all favorites tests in sequence."""
    print("\n=========================================")
    print("BEGINNING FAVOURITES API TESTS")
    print("=========================================")
    
    try:
        # Run the basic CRUD tests
        test_add_favourite()
        test_get_favourites()
        test_check_favourite()
        test_remove_favourite()
        
        # Run the error handling tests
        test_unauthorized_access()
        test_invalid_inputs()
        
        # Run the concurrent operations test
        test_concurrent_operations()
        
        print("\n=========================================")
        print("ALL FAVOURITES API TESTS PASSED!")
        print("=========================================")
        
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
    except Exception as e:
        print(f"\nERROR RUNNING TESTS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()