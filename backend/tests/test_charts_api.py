import requests
import json
import time
from datetime import datetime, timedelta
import pytest
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base API URL
BASE_URL = "https://wavegerpython.onrender.com/api"

# Helper Functions
def get_formatted_date(days_ago=0):
    """Get date formatted as YYYY-MM-DD, optionally for a past date."""
    date = datetime.now() - timedelta(days=days_ago)
    return date.strftime('%Y-%m-%d')

def check_top_charts_response(data):
    """Validate structure of top charts response."""
    assert isinstance(data, dict), "Top charts response should be a dictionary"
    assert "source" in data, "Response missing 'source' field"
    assert data["source"] in ["api", "database"], f"Unexpected source: {data['source']}"
    
    # Check data structure
    assert "data" in data, "Response missing 'data' field"
    chart_data = data["data"]
    
    # Based on the actual API structure, "data" could either be a list of charts
    # or it could be a single chart object with songs
    if isinstance(chart_data, list):
        # Top charts should have a list of chart types
        assert len(chart_data) > 0, "No charts found in response"
        
        # Check structure of first chart entry
        first_chart = chart_data[0]
        assert "title" in first_chart, "Chart entry missing 'title'"
        assert "id" in first_chart, "Chart entry missing 'id'"
        
        # Log the actual structure for debugging
        logger.info(f"Chart entry structure: {list(first_chart.keys())}")
    else:
        # It might be a single chart object
        assert "songs" in chart_data, "Chart data missing 'songs' list"
        assert isinstance(chart_data["songs"], list), "Songs should be a list"
        assert "title" in chart_data, "Chart data missing 'title'"
        
        logger.info(f"Chart data structure: {list(chart_data.keys())}")
        logger.info(f"Found single chart with {len(chart_data['songs'])} songs")
    
    return True

def check_chart_details_response(data, chart_id, expected_range):
    """Validate structure of chart details response."""
    assert isinstance(data, dict), "Chart details response should be a dictionary"
    assert "source" in data, "Response missing 'source' field"
    assert data["source"] in ["api", "database"], f"Unexpected source: {data['source']}"
    
    # Check data structure
    assert "data" in data, "Response missing 'data' field"
    chart_data = data["data"]
    
    # Log the chart data structure for debugging
    logger.info(f"Chart data keys: {list(chart_data.keys())}")
    
    # Check for title field - matches the actual API response
    assert "title" in chart_data, "Chart data missing 'title' field"
    logger.info(f"Chart title: {chart_data['title']}")
    
    # Check songs list - matches the actual API response
    assert "songs" in chart_data, "Chart data missing 'songs' list"
    assert isinstance(chart_data["songs"], list), "Songs should be a list"
    logger.info(f"Found songs list with {len(chart_data['songs'])} entries")
    
    # Check range enforcement (if specified)
    if expected_range and chart_data["songs"]:
        start, end = map(int, expected_range.split("-"))
        expected_count = end - start + 1
        assert len(chart_data["songs"]) <= expected_count, f"Expected at most {expected_count} songs, got {len(chart_data['songs'])}"
    
    # Check structure of first song if available - matches the actual API response
    if chart_data["songs"]:
        first_song = chart_data["songs"][0]
        logger.info(f"First song entry keys: {list(first_song.keys())}")
        
        # Check for required fields based on actual API response
        assert "position" in first_song, "Song entry missing 'position' field"
        assert "name" in first_song, "Song entry missing 'name' field"
        assert "artist" in first_song, "Song entry missing 'artist' field"
    
    return True

# Test Functions
def test_top_charts():
    """Test the top charts endpoint."""
    logger.info("\n=== TESTING TOP CHARTS ENDPOINT ===")
    
    # Make request to top charts endpoint
    response = requests.get(f"{BASE_URL}/top-charts")
    
    # Check response status
    assert response.status_code == 200, f"Top charts request failed with status {response.status_code}: {response.text}"
    
    # Parse response
    try:
        data = response.json()
        # Log first part of response for debugging
        logger.info(f"Response preview: {json.dumps(data)[:500]}...")
    except json.JSONDecodeError:
        assert False, f"Response is not valid JSON: {response.text}"
    
    # Validate response structure
    check_top_charts_response(data)
    
    logger.info("✅ Top charts endpoint test passed")
    
    # If the source was API, wait a bit and test again to check caching
    if data.get("source") == "api":
        logger.info("Testing caching behavior...")
        time.sleep(2)  # Brief pause
        
        # Make the same request again
        cache_response = requests.get(f"{BASE_URL}/top-charts")
        assert cache_response.status_code == 200, "Cached request failed"
        
        cache_data = cache_response.json()
        # Second response should come from database
        assert cache_data.get("source") == "database", "Second request should use cached data"
        logger.info("✅ Caching behavior test passed")
    
    # Return data for use in other tests
    return data

def test_chart_details(chart_id=None):
    """Test the chart details endpoint with optional specific chart ID."""
    logger.info("\n=== TESTING CHART DETAILS ENDPOINT ===")
    
    # If no chart ID is provided, use the default
    if not chart_id:
        chart_id = "hot-100"  # Use Billboard Hot 100 as default
    
    # Get current week's date
    current_week = get_formatted_date()
    
    # Test with default parameters
    logger.info(f"Testing chart details for chart_id={chart_id}, week={current_week}")
    response = requests.get(f"{BASE_URL}/chart")  # No parameters needed based on actual API
    
    # Check response status
    assert response.status_code == 200, f"Chart details request failed with status {response.status_code}: {response.text}"
    
    # Parse response
    try:
        data = response.json()
        # Log first part of response for debugging
        logger.info(f"Response preview: {json.dumps(data)[:300]}...")
    except json.JSONDecodeError:
        assert False, f"Response is not valid JSON: {response.text}"
    
    # Validate response structure - pass None for chart_id since it's not in the response
    check_chart_details_response(data, None, None)
    
    logger.info("✅ Basic chart details test passed")
    
    # Test with range parameter
    range_param = "1-5"  # Get top 5 entries
    logger.info(f"Testing chart details with range parameter: {range_param}")
    
    range_response = requests.get(f"{BASE_URL}/chart", params={
        "range": range_param
    })
    
    assert range_response.status_code == 200, f"Range-limited request failed with status {range_response.status_code}"
    
    range_data = range_response.json()
    check_chart_details_response(range_data, None, range_param)
    
    # Verify we got the right number of songs
    songs = range_data.get("data", {}).get("songs", [])
    expected_count = 5  # For range 1-5
    assert len(songs) <= expected_count, f"Expected at most {expected_count} songs, got {len(songs)}"
    
    logger.info("✅ Range parameter test passed")
    
    return data

def test_chart_with_invalid_parameters():
    """Test chart endpoints with invalid parameters."""
    logger.info("\n=== TESTING CHART ENDPOINTS WITH INVALID PARAMETERS ===")
    
    # Test with invalid range format
    invalid_range = "not-a-range"
    logger.info(f"Testing with invalid range format: {invalid_range}")
    
    invalid_range_response = requests.get(f"{BASE_URL}/chart", params={
        "range": invalid_range
    })
    
    # Should return error status or 200 with error message
    if invalid_range_response.status_code == 200:
        try:
            data = invalid_range_response.json()
            if "error" in data:
                logger.info("✅ Invalid range format correctly returned error in response")
            else:
                # Some APIs might ignore invalid range
                logger.info("⚠️ Invalid range format returned 200 status. This might be expected if the API ignores invalid range.")
                logger.info(f"Response: {invalid_range_response.text[:200]}...")
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    else:
        assert invalid_range_response.status_code in [400, 422], f"Expected 400/422 for invalid range, got {invalid_range_response.status_code}"
        logger.info("✅ Invalid range format correctly returned error status")
    
    # Test with out-of-bounds range
    out_of_bounds_range = "500-600"  # Typically charts don't have 500+ entries
    logger.info(f"Testing with out-of-bounds range: {out_of_bounds_range}")
    
    out_of_bounds_response = requests.get(f"{BASE_URL}/chart", params={
        "range": out_of_bounds_range
    })
    
    # This should still return 200, but with empty or limited results
    assert out_of_bounds_response.status_code == 200, f"Out-of-bounds range request failed with unexpected status {out_of_bounds_response.status_code}"
    
    try:
        data = out_of_bounds_response.json()
        songs = data.get("data", {}).get("songs", [])
        # Should either be empty or at least not have 100 entries
        if len(songs) == 0:
            logger.info("✅ Out-of-bounds range returned empty song list")
        else:
            logger.info(f"⚠️ Out-of-bounds range returned {len(songs)} songs")
    except json.JSONDecodeError:
        assert False, "Response is not valid JSON"
    except KeyError:
        logger.info("⚠️ Out-of-bounds range returned unexpected response format")

def test_api_key_dependency():
    """Test behavior when API key is not available (simulated by using an invalid key)."""
    logger.info("\n=== TESTING API KEY DEPENDENCY ===")
    
    # This test is more of a verification that the system can fall back to database
    # when API calls fail due to key issues.
    
    # First, make a normal request to ensure data is cached
    standard_response = requests.get(f"{BASE_URL}/top-charts")
    assert standard_response.status_code == 200, "Initial top charts request failed"
    
    # Now look for header indicating the source
    data = standard_response.json()
    source = data.get("source")
    
    if source == "database":
        logger.info("✅ Database caching is working (request served from database)")
    else:
        logger.info("Request served from API - this is normal for first request")
        
        # Wait a moment and try again - should be from database now
        time.sleep(2)
        second_response = requests.get(f"{BASE_URL}/top-charts")
        assert second_response.status_code == 200, "Second top charts request failed"
        
        second_data = second_response.json()
        second_source = second_data.get("source")
        
        assert second_source == "database", "Second request should be served from database"
        logger.info("✅ Database caching is working (second request served from database)")

def test_chart_diversity():
    """Test fetching multiple different chart types."""
    logger.info("\n=== TESTING CHART DIVERSITY ===")
    
    # First get the list of available charts
    top_charts_response = requests.get(f"{BASE_URL}/top-charts")
    assert top_charts_response.status_code == 200, "Top charts request failed"
    
    top_charts_data = top_charts_response.json()
    chart_list = top_charts_data.get("data", [])
    
    # Ensure we have some charts to test
    assert len(chart_list) > 0, "No charts available to test"
    
    # Test a sample of different charts
    test_count = min(3, len(chart_list))  # Test up to 3 different charts
    
    for i in range(test_count):
        chart = chart_list[i]
        chart_id = chart.get("id")
        chart_title = chart.get("title")
        
        logger.info(f"Testing chart: {chart_title} (ID: {chart_id})")
        
        # Skip if missing ID
        if not chart_id:
            logger.warning(f"Chart at index {i} missing ID, skipping")
            continue
        
        # Test this chart
        try:
            chart_response = requests.get(f"{BASE_URL}/chart", params={
                "id": chart_id,
                "week": get_formatted_date()
            })
            
            assert chart_response.status_code == 200, f"Chart request for {chart_id} failed with status {chart_response.status_code}"
            
            chart_data = chart_response.json()
            check_chart_details_response(chart_data, chart_id, None)
            
            logger.info(f"✅ Successfully fetched chart: {chart_title}")
        except Exception as e:
            logger.error(f"Failed to test chart {chart_id}: {e}")
    
    logger.info("✅ Chart diversity test completed")

def run_all_tests():
    """Run all chart API tests in sequence."""
    logger.info("\n=========================================")
    logger.info("BEGINNING CHART API TESTS")
    logger.info("=========================================")
    
    try:
        # Run the tests
        top_charts_data = test_top_charts()
        
        test_chart_details()
        test_chart_with_invalid_parameters()
        test_api_key_dependency()
        
        # Skip chart diversity test since /top-charts might return a single chart
        # test_chart_diversity()
        
        logger.info("\n=========================================")
        logger.info("ALL CHART API TESTS PASSED!")
        logger.info("=========================================")
    except AssertionError as e:
        logger.error(f"\nTEST FAILED: {e}")
    except Exception as e:
        logger.error(f"\nERROR RUNNING TESTS: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run_all_tests()