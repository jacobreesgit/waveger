#!/usr/bin/env python3
# prediction_processor.py
# Scheduled task to process Billboard chart predictions, update contests, and calculate points

import logging
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import os
from datetime import datetime, timedelta
import requests
import json
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    raise EnvironmentError("DATABASE_URL must be set in environment variables")

# Billboard API credentials
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "billboard-charts-api.p.rapidapi.com"

def get_db_connection():
    """Get a connection to the database"""
    try:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def fetch_chart_data(chart_id: str, date: str) -> Dict:
    """
    Fetch chart data from Billboard API or database
    
    Args:
        chart_id: The chart ID (e.g., 'hot-100' or 'billboard-200')
        date: Date string in 'YYYY-MM-DD' format
        
    Returns:
        Dictionary containing chart data
    """
    # First try to get from database (cached data)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if we have this chart data already cached
        cursor.execute(
            "SELECT data FROM charts WHERE title = %s AND week = %s",
            (chart_id, date)
        )
        cached_data = cursor.fetchone()
        
        if cached_data:
            logger.info(f"Using cached chart data for {chart_id} on {date}")
            return cached_data["data"]
        
        # If not in database, fetch from API
        if not RAPIDAPI_KEY:
            logger.error("RAPIDAPI_KEY not set, cannot fetch chart data")
            raise EnvironmentError("RAPIDAPI_KEY must be set in environment variables")
        
        logger.info(f"Fetching chart data from API for {chart_id} on {date}")
        
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST
        }
        
        url = f"https://{RAPIDAPI_HOST}/chart.php"
        params = {
            "id": chart_id,
            "week": date
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        chart_data = response.json()
        
        # Store in database for future use
        cursor.execute(
            "INSERT INTO charts (title, week, data) VALUES (%s, %s, %s) ON CONFLICT (title, week) DO UPDATE SET data = %s",
            (chart_id, date, json.dumps(chart_data), json.dumps(chart_data))
        )
        conn.commit()
        
        return chart_data
        
    except Exception as e:
        logger.error(f"Error fetching chart data: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def get_current_active_contest() -> Optional[Dict]:
    """Get the current active prediction contest"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get the current active contest
        cursor.execute(
            """
            SELECT id, start_date, end_date, chart_release_date, status
            FROM weekly_contests
            WHERE status = 'open'
            ORDER BY start_date DESC
            LIMIT 1
            """
        )
        contest = cursor.fetchone()
        return contest
    except Exception as e:
        logger.error(f"Error fetching active contest: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def close_active_contest() -> Optional[int]:
    """
    Close the currently active contest
    
    Returns:
        contest_id if successful, None otherwise
    """
    active_contest = get_current_active_contest()
    if not active_contest:
        logger.warning("No active contest found to close")
        return None
    
    contest_id = active_contest["id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update the contest status to 'closed'
        cursor.execute(
            """
            UPDATE weekly_contests
            SET status = 'closed', 
                closed_at = NOW()
            WHERE id = %s
            """,
            (contest_id,)
        )
        conn.commit()
        
        logger.info(f"Contest ID {contest_id} has been closed")
        return contest_id
    except Exception as e:
        logger.error(f"Error closing contest: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def create_next_contest() -> Optional[int]:
    """
    Create a new weekly contest
    
    Returns:
        New contest ID if successful, None otherwise
    """
    # Calculate dates for the new contest
    today = datetime.now().date()
    
    # Find next Tuesday (chart release day)
    days_until_tuesday = (1 - today.weekday()) % 7  # Tuesday is weekday 1
    if days_until_tuesday == 0:  # If today is Tuesday, go to next Tuesday
        days_until_tuesday = 7
        
    next_tuesday = today + timedelta(days=days_until_tuesday)
    
    # Contest starts now and ends on the next chart release
    start_date = today
    end_date = next_tuesday - timedelta(days=1)  # Day before release
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert the new contest
        cursor.execute(
            """
            INSERT INTO weekly_contests
            (start_date, end_date, chart_release_date, status)
            VALUES (%s, %s, %s, 'open')
            RETURNING id
            """,
            (start_date, end_date, next_tuesday)
        )
        
        new_contest_id = cursor.fetchone()["id"]
        conn.commit()
        
        logger.info(f"Created new contest ID {new_contest_id} starting {start_date} ending {end_date}, release date {next_tuesday}")
        return new_contest_id
    except Exception as e:
        logger.error(f"Error creating new contest: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def calculate_entry_points(actual_position: int) -> int:
    """
    Calculate points for an entry prediction
    
    Args:
        actual_position: The actual position where the song entered
        
    Returns:
        Points earned
    """
    if actual_position <= 10:
        return 15  # Top 10 entry
    elif actual_position <= 50:
        return 10  # Top 50 entry
    else:
        return 5   # Entry anywhere else
        
def calculate_position_points(predicted_change: int, actual_change: int) -> int:
    """
    Calculate points for a position change prediction
    
    Args:
        predicted_change: The predicted position change
        actual_change: The actual position change
        
    Returns:
        Points earned
    """
    # Calculate the difference between predicted and actual change
    difference = abs(predicted_change - actual_change)
    
    if difference == 0:
        return 10  # Exactly correct
    elif difference <= 5:
        return 5   # Within 5 positions
    elif difference <= 10:
        return 2   # Within 10 positions
    else:
        return 0   # More than 10 positions off
        
def calculate_exit_points(is_correct: bool) -> int:
    """
    Calculate points for an exit prediction
    
    Args:
        is_correct: Whether the prediction was correct
        
    Returns:
        Points earned
    """
    return 10 if is_correct else 0

def evaluate_entry_prediction(prediction: Dict, current_chart: Dict, previous_chart: Dict) -> Dict:
    """
    Evaluate an entry prediction
    
    Args:
        prediction: The prediction to evaluate
        current_chart: Current week's chart data
        previous_chart: Previous week's chart data
        
    Returns:
        Dictionary with result details
    """
    song_name = prediction["song_name"]
    artist = prediction["artist"]  # Using the aliased column in the query
    predicted_position = prediction["predicted_position"]
    
    # Extract songs from charts data - ensure we handle the data structure correctly
    current_songs = current_chart.get("data", {}).get("songs", [])
    previous_songs = previous_chart.get("data", {}).get("songs", [])
    
    # Check if song was in previous chart
    in_previous = any(
        s["name"].lower() == song_name.lower() and 
        s["artist"].lower() == artist.lower() 
        for s in previous_songs
    )
    
    if in_previous:
        # Song was already in chart, so this is not a new entry
        return {
            "is_correct": False,
            "points": 0,
            "actual_position": None
        }
    
    # Find the song in current chart
    song_in_current = None
    for song in current_songs:
        if song["name"].lower() == song_name.lower() and song["artist"].lower() == artist.lower():
            song_in_current = song
            break
    
    if not song_in_current:
        # Song didn't enter the chart
        return {
            "is_correct": False,
            "points": 0,
            "actual_position": None
        }
    
    # Song did enter the chart, calculate points
    actual_position = song_in_current["position"]
    points = calculate_entry_points(actual_position)
    
    return {
        "is_correct": True,
        "points": points,
        "actual_position": actual_position
    }

def evaluate_position_prediction(prediction: Dict, current_chart: Dict, previous_chart: Dict) -> Dict:
    """
    Evaluate a position change prediction
    
    Args:
        prediction: The prediction to evaluate
        current_chart: Current week's chart data
        previous_chart: Previous week's chart data
        
    Returns:
        Dictionary with result details
    """
    song_name = prediction["song_name"]
    artist = prediction["artist"]  # Using the aliased column in the query
    predicted_change = prediction["predicted_change"]
    
    # Extract songs from charts data - ensure we handle the data structure correctly
    current_songs = current_chart.get("data", {}).get("songs", [])
    previous_songs = previous_chart.get("data", {}).get("songs", [])
    
    # Find the song in both charts
    song_in_previous = None
    for song in previous_songs:
        if song["name"].lower() == song_name.lower() and song["artist"].lower() == artist.lower():
            song_in_previous = song
            break
    
    song_in_current = None
    for song in current_songs:
        if song["name"].lower() == song_name.lower() and song["artist"].lower() == artist.lower():
            song_in_current = song
            break
    
    # If not in either chart, prediction is wrong
    if not song_in_previous or not song_in_current:
        return {
            "is_correct": False,
            "points": 0,
            "actual_change": None
        }
    
    # Calculate actual position change
    previous_position = song_in_previous["position"]
    current_position = song_in_current["position"]
    actual_change = previous_position - current_position  # Positive = moved up, negative = moved down
    
    # Calculate points
    points = calculate_position_points(predicted_change, actual_change)
    is_correct = (points > 0)
    
    return {
        "is_correct": is_correct,
        "points": points,
        "actual_change": actual_change
    }

def evaluate_exit_prediction(prediction: Dict, current_chart: Dict, previous_chart: Dict) -> Dict:
    """
    Evaluate an exit prediction
    
    Args:
        prediction: The prediction to evaluate
        current_chart: Current week's chart data
        previous_chart: Previous week's chart data
        
    Returns:
        Dictionary with result details
    """
    song_name = prediction["song_name"]
    artist = prediction["artist"]  # Using the aliased column in the query
    
    # Extract songs from charts data - ensure we handle the data structure correctly
    current_songs = current_chart.get("data", {}).get("songs", [])
    previous_songs = previous_chart.get("data", {}).get("songs", [])
    
    # Check if song was in previous chart
    in_previous = any(
        s["name"].lower() == song_name.lower() and 
        s["artist"].lower() == artist.lower() 
        for s in previous_songs
    )
    
    if not in_previous:
        # Song wasn't in previous chart, so can't exit
        return {
            "is_correct": False,
            "points": 0
        }
    
    # Check if song is in current chart
    in_current = any(
        s["name"].lower() == song_name.lower() and 
        s["artist"].lower() == artist.lower() 
        for s in current_songs
    )
    
    # Song exited if it was in previous but not in current
    is_correct = not in_current
    points = calculate_exit_points(is_correct)
    
    return {
        "is_correct": is_correct,
        "points": points
    }

def update_user_stats(user_id: int, points: int, is_correct: bool) -> bool:
    """
    Update user statistics after a prediction is processed
    
    Args:
        user_id: User ID
        points: Points earned
        is_correct: Whether the prediction was correct
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update user stats
        cursor.execute(
            """
            UPDATE users
            SET 
                total_points = total_points + %s,
                weekly_points = weekly_points + %s,
                predictions_made = predictions_made + 1,
                correct_predictions = correct_predictions + %s
            WHERE id = %s
            """,
            (points, points, 1 if is_correct else 0, user_id)
        )
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating user stats: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def generate_contest_stats(contest_id: int) -> bool:
    """
    Generate and store statistics for a contest
    
    Args:
        contest_id: Contest ID
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get total predictions, correct predictions, and points earned
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_predictions,
                SUM(CASE WHEN pr.is_correct THEN 1 ELSE 0 END) as correct_predictions,
                SUM(pr.points_earned) as total_points
            FROM predictions p
            JOIN prediction_results pr ON p.id = pr.prediction_id
            WHERE p.contest_id = %s
            """,
            (contest_id,)
        )
        
        stats = cursor.fetchone()
        
        # Get top performers
        cursor.execute(
            """
            SELECT 
                u.id,
                u.username,
                SUM(pr.points_earned) as points
            FROM predictions p
            JOIN prediction_results pr ON p.id = pr.prediction_id
            JOIN users u ON p.user_id = u.id
            WHERE p.contest_id = %s
            GROUP BY u.id, u.username
            ORDER BY points DESC
            LIMIT 10
            """,
            (contest_id,)
        )
        
        top_performers = cursor.fetchall()
        
        # Convert top performers to a JSON-friendly format
        top_performers_json = []
        for performer in top_performers:
            top_performers_json.append({
                "id": performer["id"],
                "username": performer["username"],
                "points": int(performer["points"])
            })
        
        # Calculate success rates by prediction type
        cursor.execute(
            """
            SELECT 
                p.prediction_type,
                COUNT(*) as total,
                SUM(CASE WHEN pr.is_correct THEN 1 ELSE 0 END) as correct,
                AVG(pr.points_earned) as avg_points
            FROM predictions p
            JOIN prediction_results pr ON p.id = pr.prediction_id
            WHERE p.contest_id = %s
            GROUP BY p.prediction_type
            """,
            (contest_id,)
        )
        
        prediction_stats = cursor.fetchall()
        
        # Convert prediction stats to JSON-friendly format
        prediction_stats_json = []
        for stat in prediction_stats:
            prediction_stats_json.append({
                "type": stat["prediction_type"],
                "total": int(stat["total"]),
                "correct": int(stat["correct"]),
                "success_rate": round(int(stat["correct"]) / int(stat["total"]) * 100, 2) if int(stat["total"]) > 0 else 0,
                "avg_points": round(float(stat["avg_points"]), 2)
            })
        
        # Store the stats in the weekly_contests table
        cursor.execute(
            """
            UPDATE weekly_contests
            SET 
                total_predictions = %s,
                correct_predictions = %s,
                total_points_awarded = %s,
                contest_stats = %s
            WHERE id = %s
            """,
            (
                int(stats["total_predictions"]) if stats["total_predictions"] else 0,
                int(stats["correct_predictions"]) if stats["correct_predictions"] else 0,
                int(stats["total_points"]) if stats["total_points"] else 0,
                Json({
                    'top_performers': top_performers_json,
                    'prediction_stats': prediction_stats_json
                }),
                contest_id
            )
        )
        
        conn.commit()
        logger.info(f"Generated stats for contest {contest_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error generating contest stats: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def process_predictions(contest_id: int) -> bool:
    """
    Process all predictions for a contest
    
    Args:
        contest_id: The ID of the contest to process
        
    Returns:
        True if successful, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get contest details
        cursor.execute(
            """
            SELECT chart_release_date
            FROM weekly_contests
            WHERE id = %s
            """,
            (contest_id,)
        )
        contest = cursor.fetchone()
        
        if not contest:
            logger.error(f"Contest ID {contest_id} not found")
            return False
            
        release_date = contest["chart_release_date"]
        
        # Get previous week's date
        previous_date = release_date - timedelta(days=7)
        
        # Format dates for API
        release_date_str = release_date.strftime("%Y-%m-%d")
        previous_date_str = previous_date.strftime("%Y-%m-%d")
        
        # Fetch current and previous chart data for both Hot 100 and Billboard 200
        logger.info(f"Fetching chart data for Hot 100 and Billboard 200")
        hot100_current = fetch_chart_data("hot-100", release_date_str)
        hot100_previous = fetch_chart_data("hot-100", previous_date_str)
        billboard200_current = fetch_chart_data("billboard-200", release_date_str)
        billboard200_previous = fetch_chart_data("billboard-200", previous_date_str)
        
        # Get all predictions for this contest
        cursor.execute(
            """
            SELECT id, user_id, prediction_type, song_name, artist_name AS artist, predicted_position, 
                   predicted_change, chart_id AS chart_type
            FROM predictions
            WHERE contest_id = %s AND processed = FALSE
            """,
            (contest_id,)
        )
        
        predictions = cursor.fetchall()
        logger.info(f"Processing {len(predictions)} predictions for contest {contest_id}")
        
        # Process each prediction
        for prediction in predictions:
            logger.info(f"Processing prediction ID {prediction['id']} - {prediction['prediction_type']} for {prediction['song_name']}")
            
            # Select appropriate charts based on prediction chart type
            if prediction["chart_type"] == "hot-100":
                current_chart = hot100_current
                previous_chart = hot100_previous
            else:  # billboard-200
                current_chart = billboard200_current
                previous_chart = billboard200_previous
                
            # Evaluate the prediction based on its type
            if prediction["prediction_type"] == "entry":
                result = evaluate_entry_prediction(prediction, current_chart, previous_chart)
            elif prediction["prediction_type"] == "position_change":
                result = evaluate_position_prediction(prediction, current_chart, previous_chart)
            elif prediction["prediction_type"] == "exit":
                result = evaluate_exit_prediction(prediction, current_chart, previous_chart)
            else:
                logger.warning(f"Unknown prediction type: {prediction['prediction_type']}")
                continue
                
            # Save the result
            prediction_id = prediction["id"]
            user_id = prediction["user_id"]
            is_correct = result["is_correct"]
            points = result["points"]
            actual_position = result.get("actual_position")
            actual_change = result.get("actual_change")
            
            logger.info(f"Prediction result: Correct: {is_correct}, Points: {points}")
            
            # Insert the result into prediction_results
            cursor.execute(
                """
                INSERT INTO prediction_results
                (prediction_id, actual_position, actual_change, is_correct, points_earned)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (prediction_id, actual_position, actual_change, is_correct, points)
            )
            
            # Mark the prediction as processed
            cursor.execute(
                """
                UPDATE predictions
                SET processed = TRUE
                WHERE id = %s
                """,
                (prediction_id,)
            )
            
            # Update user stats
            update_user_stats(user_id, points, is_correct)
            
        conn.commit()
        logger.info(f"Successfully processed all predictions for contest {contest_id}")
        
        # Generate contest stats
        generate_contest_stats(contest_id)
        
        # Reset weekly points for all users at the end of processing
        cursor.execute(
            """
            UPDATE users
            SET weekly_points = 0
            WHERE weekly_points > 0
            """
        )
        
        conn.commit()
        logger.info("Reset weekly points for all users")
        
        return True
    
    except Exception as e:
        logger.error(f"Error processing predictions: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def run_weekly_processor() -> bool:
    """
    Main entry point for the weekly prediction processing
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("Starting weekly prediction processing")
    
    try:
        # Step 1: Close the current active contest
        contest_id = close_active_contest()
        
        if not contest_id:
            logger.warning("No active contest to close, checking if we should create a new one")
        else:
            # Step 2: Process predictions for the closed contest
            success = process_predictions(contest_id)
            if not success:
                logger.error(f"Failed to process predictions for contest {contest_id}")
                return False
                
            logger.info(f"Successfully processed predictions for contest {contest_id}")
        
        # Step 3: Create a new contest for the next week
        new_contest_id = create_next_contest()
        
        if not new_contest_id:
            logger.error("Failed to create new contest")
            return False
            
        logger.info(f"Successfully created new contest with ID {new_contest_id}")
        
        # If we get here, everything was successful
        logger.info("Weekly prediction processing completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in weekly prediction processing: {e}")
        return False

if __name__ == "__main__":
    # This allows the script to be run directly
    success = run_weekly_processor()
    exit(0 if success else 1)