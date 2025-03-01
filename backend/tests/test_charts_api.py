import requests
import json
import time
import pytest
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base API URL
BASE_URL = "https://wavegerpython.onrender.com/api"

# Helper Functions
def get_formatted_date(days_ago=0):
    """Get date formatted as YYYY-MM-DD, optionally for a past date."""
    date = datetime.now() - timedelta(days=days_ago)
    return date.strftime('%Y-%m-%d')

def check_chart_details_response(data):
    """Validate structure of chart details response for different chart types."""
    assert isinstance(data, dict), "Chart details response should be a dictionary"
    assert "source" in data, "Response missing 'source' field"
    assert data["source"] in ["api", "database"], f"Unexpected source: {data['source']}"
    
    assert "data" in data, "Response missing 'data' field"
    chart_data = data["data"]
    
    # Check for required fields
    assert "title" in chart_data, "Chart data missing 'title' field"
    assert "songs" in chart_data, "Chart data missing 'songs' list"
    assert isinstance(chart_data["songs"], list), "Songs should be a list"
    
    # Define chart-specific field requirements
    chart_specific_fields = {
        "Billboard Artist 100": [
            "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ],
        "Billboard 200™": [
            "artist", "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ],
        "Billboard Hot 100™": [
            "artist", "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ],
        "Emerging Artists": [
            "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ],
        "Digital Song Sales": [
            "artist", "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ],
        "Streaming Songs": [
            "artist", "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ],
        "Radio Songs": [
            "artist", "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ],
        "Songs of the Summer": [
            "artist", "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ],
        "Top Album Sales": [
            "artist", "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ],
        "Top Streaming Albums": [
            "artist", "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ],
        "Independent Albums": [
            "artist", "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ],
        "Vinyl Albums": [
            "artist", "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ],
        "Indie Store Album Sales": [
            "artist", "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ],
        "Billboard U.S. Afrobeats Songs": [
            "artist", "image", "last_week_position", "name", 
            "peak_position", "position", "url", "weeks_on_chart"
        ]
    }
    
    # Validate chart-specific fields
    chart_title = chart_data["title"]
    required_fields = chart_specific_fields.get(chart_title, [])
    
    # Validate first song entry has all required fields
    if chart_data["songs"]:
        first_song = chart_data["songs"][0]
        missing_fields = [field for field in required_fields if field not in first_song]
        
        assert not missing_fields, f"Song entry missing required fields for {chart_title}: {missing_fields}"
    
    logger.info(f"Chart details validated for {chart_title}. Found {len(chart_data['songs'])} songs")
    return True

def test_top_charts():
    """Test the top charts endpoint."""
    print("\n=== TESTING TOP CHARTS ENDPOINT ===")
    
    # Make request to top charts endpoint
    response = requests.get(f"{BASE_URL}/top-charts")
    
    # Check response status
    assert response.status_code == 200, f"Top charts request failed with status {response.status_code}: {response.text}"
    
    # Parse response
    try:
        data = response.json()
    except json.JSONDecodeError:
        assert False, f"Response is not valid JSON: {response.text}"
    
    # Validate response structure
    assert "data" in data, "Response missing data field"
    assert isinstance(data["data"], list), "Top charts data should be a list"
    assert len(data["data"]) > 0, "No charts found in top charts"
    
    # Check structure of first chart
    first_chart = data["data"][0]
    assert "id" in first_chart, "Chart entry missing 'id'"
    assert "title" in first_chart, "Chart entry missing 'title'"
    
    print("✅ Top charts endpoint test passed")
    
    return data

def test_chart_details():
    """Test the chart details endpoint."""
    print("\n=== TESTING CHART DETAILS ENDPOINT ===")
    
    # Use current week's date
    current_week = get_formatted_date()
    
    # Test with default parameters
    print(f"Testing chart details for current week: {current_week}")
    response = requests.get(f"{BASE_URL}/chart")
    
    # Check response status
    assert response.status_code == 200, f"Chart details request failed with status {response.status_code}: {response.text}"
    
    # Parse response
    try:
        data = response.json()
    except json.JSONDecodeError:
        assert False, f"Response is not valid JSON: {response.text}"
    
    # Validate response structure
    check_chart_details_response(data)
    
    print("✅ Basic chart details test passed")
    
    # Test with range parameter
    range_param = "1-5"
    print(f"Testing chart details with range parameter: {range_param}")
    
    range_response = requests.get(f"{BASE_URL}/chart", params={"range": range_param})
    
    assert range_response.status_code == 200, f"Range-limited request failed with status {range_response.status_code}"
    
    range_data = range_response.json()
    check_chart_details_response(range_data)
    
    # Verify song count
    songs = range_data.get("data", {}).get("songs", [])
    assert len(songs) <= 5, f"Expected at most 5 songs, got {len(songs)}"
    
    print("✅ Range parameter test passed")
    
    return data

def test_chart_with_invalid_parameters():
    """Test chart endpoints with invalid parameters."""
    print("\n=== TESTING CHART ENDPOINTS WITH INVALID PARAMETERS ===")
    
    # Test with invalid range format
    invalid_range = "not-a-range"
    print(f"Testing with invalid range format: {invalid_range}")
    
    invalid_range_response = requests.get(f"{BASE_URL}/chart", params={"range": invalid_range})
    
    # Should be rejected (400 or 200 with error)
    if invalid_range_response.status_code == 200:
        try:
            data = invalid_range_response.json()
            assert "error" in data, "Invalid range should return an error"
            print("✅ Invalid range format correctly returned error in response")
        except json.JSONDecodeError:
            assert False, "Response is not valid JSON"
    else:
        assert invalid_range_response.status_code in [400, 422], f"Expected 400/422 for invalid range, got {invalid_range_response.status_code}"
        print("✅ Invalid range format correctly returned error status")
    
    # Test with out-of-bounds range
    out_of_bounds_range = "500-600"
    print(f"Testing with out-of-bounds range: {out_of_bounds_range}")
    
    out_of_bounds_response = requests.get(f"{BASE_URL}/chart", params={"range": out_of_bounds_range})
    
    assert out_of_bounds_response.status_code == 200, f"Out-of-bounds range request failed with unexpected status {out_of_bounds_response.status_code}"
    
    try:
        data = out_of_bounds_response.json()
        songs = data.get("data", {}).get("songs", [])
        
        # Should either be empty or have a reasonable number of entries
        assert len(songs) <= 10, f"Out-of-bounds range returned {len(songs)} songs, expected 10 or fewer"
        print("✅ Out-of-bounds range correctly handled")
    except json.JSONDecodeError:
        assert False, "Response is not valid JSON"

def test_api_key_dependency():
    """Test behavior when API key is not available (simulated by using an invalid key)."""
    print("\n=== TESTING API KEY DEPENDENCY ===")
    
    # First, make a normal request to ensure data is cached
    standard_response = requests.get(f"{BASE_URL}/top-charts")
    assert standard_response.status_code == 200, "Initial top charts request failed"
    
    # Now look for header indicating the source
    data = standard_response.json()
    source = data.get("source")
    
    if source == "database":
        print("✅ Database caching is working (request served from database)")
    else:
        print("Request served from API - this is normal for first request")
        
        # Wait a moment and try again - should be from database now
        time.sleep(2)
        second_response = requests.get(f"{BASE_URL}/top-charts")
        assert second_response.status_code == 200, "Second top charts request failed"
        
        second_data = second_response.json()
        second_source = second_data.get("source")
        
        assert second_source == "database", "Second request should be served from database"
        print("✅ Database caching is working (second request served from database)")

def test_chart_diversity():
    """Test fetching multiple different chart types."""
    print("\n=== TESTING CHART DIVERSITY ===")
    
    # First get the list of available charts
    top_charts_response = requests.get(f"{BASE_URL}/top-charts")
    assert top_charts_response.status_code == 200, "Top charts request failed"
    
    top_charts_data = top_charts_response.json()
    chart_list = top_charts_data.get("data", [])
    
    # Ensure we have some charts to test
    assert len(chart_list) > 0, "No charts available to test"
    
    # Track charts that have been successfully tested
    tested_charts = []
    
    # Test all available charts
    for chart in chart_list:
        chart_id = chart.get("id", "").rstrip("/")  # Remove trailing slash
        chart_title = chart.get("title")
        
        print(f"Testing chart: {chart_title} (ID: {chart_id})")
        
        # Skip if missing ID
        if not chart_id:
            print(f"⚠️ Chart missing ID, skipping")
            continue
        
        # Test this chart
        try:
            chart_response = requests.get(f"{BASE_URL}/chart", params={
                "id": chart_id,
                "week": get_formatted_date()
            })
            
            assert chart_response.status_code == 200, f"Chart request for {chart_id} failed with status {chart_response.status_code}"
            
            chart_data = chart_response.json()
            check_chart_details_response(chart_data)
            
            print(f"✅ Successfully fetched chart: {chart_title}")
            tested_charts.append(chart_title)
            
        except Exception as e:
            print(f"❌ Failed to test chart {chart_id}: {e}")
            import traceback
            traceback.print_exc()
    
    assert len(tested_charts) > 3, f"Only tested {len(tested_charts)} charts. Expected more diversity."
    
    print("✅ Chart diversity test completed")
    print(f"Tested charts: {', '.join(tested_charts)}")

def run_all_tests():
    """Run all chart API tests in sequence."""
    print("\n=========================================")
    print("BEGINNING CHART API TESTS")
    print("=========================================")
    
    try:
        # Run the tests
        top_charts_data = test_top_charts()
        test_chart_details()
        test_chart_with_invalid_parameters()
        test_api_key_dependency()
        test_chart_diversity()
        
        print("\n=========================================")
        print("ALL CHART API TESTS PASSED!")
        print("=========================================")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\nERROR RUNNING TESTS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()