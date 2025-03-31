#!/usr/bin/env python3
"""
Prediction Data Generator - Uses Existing Contest

This script creates fake prediction data for the currently active contest,
processes it, and updates user statistics.
"""

import psycopg2
from psycopg2.extras import Json
import random
from datetime import datetime, timedelta
import logging
import bcrypt
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters
DATABASE_URL = "postgresql://wavegerdatabase_user:cafvWdvIlSiZbBe7hX9uXki02Bv3UcP1@dpg-cu8g5bggph6c73cpbaj0-a.frankfurt-postgres.render.com:5432/wavegerdatabase"

# Configuration
NUM_USERS = 10  # Number of fake users to create
PREDICTIONS_PER_USER = 5  # Number of predictions per user
PROCESS_PREDICTIONS = True  # Set to True to process predictions

# Sample song data for predictions
SAMPLE_SONGS = [
    {"name": "Midnight Rain", "artist": "Taylor Swift"},
    {"name": "Die With A Smile", "artist": "Lady Gaga & Bruno Mars"},
    {"name": "Birds of a Feather", "artist": "Billie Eilish"},
    {"name": "Texas Hold 'Em", "artist": "Beyoncé"},
    {"name": "Stick Season", "artist": "Noah Kahan"},
    {"name": "Espresso", "artist": "Sabrina Carpenter"},
    {"name": "Paint The Town Red", "artist": "Doja Cat"},
    {"name": "First Person Shooter", "artist": "Drake ft. J. Cole"},
    {"name": "Snooze", "artist": "SZA"},
    {"name": "Is It Over Now?", "artist": "Taylor Swift"},
    {"name": "Greedy", "artist": "Tate McRae"},
    {"name": "Good Luck, Babe!", "artist": "Chappell Roan"},
    {"name": "Feather", "artist": "Sabrina Carpenter"},
    {"name": "We Can't Be Friends", "artist": "Ariana Grande"},
    {"name": "Fortnight", "artist": "Taylor Swift"},
    {"name": "Not Like Us", "artist": "Kendrick Lamar"},
    {"name": "A Bar Song (Tipsy)", "artist": "Shaboozey"},
    {"name": "Please Please Please", "artist": "Sabrina Carpenter"},
    {"name": "One Of The Girls", "artist": "The Weeknd, JENNIE & Lily-Rose Depp"},
    {"name": "Cruel Summer", "artist": "Taylor Swift"},
]

def get_db_connection():
    """Connect to the PostgreSQL database server"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def create_fake_users(num_users=NUM_USERS):
    """Create fake users for testing"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check existing users count
    cursor.execute("SELECT COUNT(*) FROM users")
    existing_count = cursor.fetchone()[0]
    
    if existing_count >= num_users:
        logger.info(f"Already have {existing_count} users, skipping user creation")
        cursor.close()
        conn.close()
        return get_user_ids(num_users)
    
    # Create additional users if needed
    users_to_create = num_users - existing_count
    logger.info(f"Creating {users_to_create} fake users")
    
    created_user_ids = []
    
    try:
        for i in range(users_to_create):
            username = f"testuser_{str(i+1).zfill(2)}"
            email = f"{username}@example.com"
            password_hash = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
            
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, created_at, last_login)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (username, email, password_hash, datetime.now(), datetime.now())
            )
            
            user_id = cursor.fetchone()[0]
            created_user_ids.append(user_id)
            logger.info(f"Created user: {username} with ID: {user_id}")
        
        conn.commit()
        logger.info(f"Successfully created {len(created_user_ids)} users")
        
        # Get the IDs of all users (including pre-existing ones)
        all_user_ids = get_user_ids(num_users)
        
        return all_user_ids
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating users: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def get_user_ids(limit=NUM_USERS):
    """Get IDs of existing users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM users ORDER BY id LIMIT %s", (limit,))
        user_ids = [row[0] for row in cursor.fetchall()]
        return user_ids
    except Exception as e:
        logger.error(f"Error getting user IDs: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def get_active_contest():
    """Get the currently active contest"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            SELECT id, start_date, end_date, chart_release_date, status
            FROM weekly_contests
            WHERE status = 'open'
            ORDER BY chart_release_date DESC
            LIMIT 1
            """
        )
        
        contest = cursor.fetchone()
        
        if not contest:
            logger.error("No active contest found")
            return None
            
        contest_id, start_date, end_date, chart_release_date, status = contest
        
        logger.info(f"Found active contest: ID={contest_id}, release date={chart_release_date}")
        
        return {
            "id": contest_id,
            "start_date": start_date,
            "end_date": end_date,
            "chart_release_date": chart_release_date,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Error getting active contest: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def create_predictions_for_contest(user_ids, contest_id, start_date, end_date, predictions_per_user=PREDICTIONS_PER_USER):
    """Create predictions for the specified contest"""
    if not user_ids:
        logger.error("No users provided for prediction creation")
        return []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    prediction_ids = []
    
    try:
        # Create predictions for each user
        for user_id in user_ids:
            # Check if user already has predictions for this contest
            cursor.execute(
                """
                SELECT COUNT(*) FROM predictions
                WHERE user_id = %s AND contest_id = %s
                """,
                (user_id, contest_id)
            )
            
            existing_count = cursor.fetchone()[0]
            
            if existing_count >= predictions_per_user:
                logger.info(f"User {user_id} already has {existing_count} predictions for contest {contest_id}, skipping")
                continue
            
            # Create new predictions
            to_create = predictions_per_user - existing_count
            
            for _ in range(to_create):
                # Randomly choose prediction type
                prediction_type = random.choice(['entry', 'position_change', 'exit'])
                
                # Choose chart type
                chart_id = random.choice(['hot-100', 'billboard-200'])
                
                # Select random song
                song = random.choice(SAMPLE_SONGS)
                song_name = song["name"]
                artist_name = song["artist"]
                
                # Generate appropriate position or change value
                predicted_position = None
                predicted_change = None
                
                if prediction_type == 'entry':
                    predicted_position = random.randint(1, 100)
                elif prediction_type == 'position_change':
                    predicted_change = random.randint(-50, 50)
                
                # Generate a random creation date between contest start and a day ago
                # (to make it seem like predictions were made throughout the contest period)
                end_creation = min(end_date, datetime.now() - timedelta(hours=1))
                days_offset = random.randint(0, (end_creation - start_date).days)
                hours_offset = random.randint(0, 23)
                minutes_offset = random.randint(0, 59)
                
                created_at = start_date + timedelta(
                    days=days_offset,
                    hours=hours_offset,
                    minutes=minutes_offset
                )
                
                # Create the prediction
                cursor.execute(
                    """
                    INSERT INTO predictions (
                        user_id, contest_id, chart_id, chart_date, prediction_type,
                        song_name, artist_name, predicted_position, predicted_change, processed, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        user_id,
                        contest_id,
                        chart_id,
                        created_at.date(),
                        prediction_type,
                        song_name,
                        artist_name,
                        predicted_position,
                        predicted_change,
                        False,  # Not processed initially
                        created_at
                    )
                )
                
                prediction_id = cursor.fetchone()[0]
                prediction_ids.append(prediction_id)
                
            logger.info(f"Created {to_create} predictions for user {user_id} in contest {contest_id}")
        
        conn.commit()
        logger.info(f"Successfully created {len(prediction_ids)} predictions")
        
        return prediction_ids
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating predictions: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def get_unprocessed_predictions(contest_id=None):
    """Get all unprocessed predictions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if contest_id:
            cursor.execute(
                """
                SELECT 
                    p.id, p.user_id, p.prediction_type, p.predicted_position, 
                    p.predicted_change, p.song_name, p.artist_name, p.chart_id, p.contest_id,
                    p.created_at
                FROM predictions p
                WHERE p.processed = FALSE AND p.contest_id = %s
                """,
                (contest_id,)
            )
        else:
            cursor.execute(
                """
                SELECT 
                    p.id, p.user_id, p.prediction_type, p.predicted_position, 
                    p.predicted_change, p.song_name, p.artist_name, p.chart_id, p.contest_id,
                    p.created_at
                FROM predictions p
                WHERE p.processed = FALSE
                """
            )
            
        predictions = cursor.fetchall()
        logger.info(f"Found {len(predictions)} unprocessed predictions")
        return predictions
        
    except Exception as e:
        logger.error(f"Error getting unprocessed predictions: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def process_predictions(predictions, chart_release_date):
    """Create fake prediction results for the given predictions"""
    if not predictions:
        logger.info("No predictions to process")
        return
    
    logger.info(f"Processing {len(predictions)} predictions")
    conn = get_db_connection()
    
    try:
        with conn:
            cursor = conn.cursor()
            
            # Process time is 2PM on release day
            processed_at = datetime.combine(chart_release_date, datetime.min.time()) + timedelta(hours=14)
            
            # User stats tracking
            user_stats = {}
            
            # Track which contests need statistics updates
            contest_ids = set()
            
            # Process each prediction
            for prediction in predictions:
                pred_id, user_id, pred_type, pred_position, pred_change, song_name, artist_name, chart_id, contest_id, created_at = prediction
                
                contest_ids.add(contest_id)
                
                # Determine result (60% chance of being correct)
                is_correct = random.random() < 0.6
                
                # Calculate points based on result
                points = 0
                actual_position = None
                actual_change = None
                
                if is_correct:
                    if pred_type == 'entry':
                        # Points based on predicted position
                        if pred_position <= 10:
                            points = 15
                        elif pred_position <= 50:
                            points = 10
                        else:
                            points = 5
                            
                        # Generate actual position close to predicted
                        variation = min(10, max(1, int(pred_position * 0.2) if pred_position else 5))
                        actual_position = max(1, pred_position + random.randint(-variation, variation) if pred_position else random.randint(1, 100))
                        
                    elif pred_type == 'position_change':
                        # Points for position change
                        points = random.choice([2, 5, 10])
                        
                        # Generate actual change close to predicted
                        variation = max(1, abs(int(pred_change * 0.3) if pred_change else 3))
                        actual_change = pred_change + random.randint(-variation, variation) if pred_change else random.randint(-10, 10)
                        
                    elif pred_type == 'exit':
                        # Fixed points for exit
                        points = 10
                else:
                    # Incorrect prediction, zero points
                    if pred_type == 'position_change':
                        # Generate actual change significantly different from predicted
                        actual_change = -pred_change + random.randint(-10, 10) if pred_change else random.randint(-30, 30)
                
                # Insert result
                cursor.execute(
                    """
                    INSERT INTO prediction_results
                    (prediction_id, actual_position, actual_change, is_correct, points_earned, processed_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (pred_id, actual_position, actual_change, is_correct, points, processed_at)
                )
                
                # Mark prediction as processed
                cursor.execute(
                    """
                    UPDATE predictions
                    SET processed = TRUE
                    WHERE id = %s
                    """,
                    (pred_id,)
                )
                
                # Track user stats for bulk update
                if user_id not in user_stats:
                    user_stats[user_id] = {
                        'points': 0,
                        'correct': 0,
                        'total': 0
                    }
                    
                user_stats[user_id]['points'] += points
                user_stats[user_id]['correct'] += 1 if is_correct else 0
                user_stats[user_id]['total'] += 1
                
                logger.info(f"Processed prediction {pred_id}: {pred_type} - {song_name} by {artist_name} - Correct: {is_correct}, Points: {points}")
            
            # Update user statistics
            for user_id, stats in user_stats.items():
                cursor.execute(
                    """
                    UPDATE users
                    SET 
                        total_points = total_points + %s,
                        weekly_points = weekly_points + %s,
                        predictions_made = predictions_made + %s,
                        correct_predictions = correct_predictions + %s
                    WHERE id = %s
                    """,
                    (
                        stats['points'],
                        stats['points'],
                        stats['total'],
                        stats['correct'],
                        user_id
                    )
                )
                
                logger.info(f"Updated stats for user {user_id}: +{stats['points']} points, +{stats['correct']}/{stats['total']} predictions")
            
            # Generate contest statistics for each affected contest
            for contest_id in contest_ids:
                update_contest_statistics(cursor, contest_id)
                
        logger.info("Successfully processed all predictions")
            
    except Exception as e:
        logger.error(f"Error processing predictions: {e}")
        raise
    finally:
        conn.close()

def update_contest_statistics(cursor, contest_id):
    """Update contest statistics in the rules JSONB field"""
    try:
        # Get statistics
        cursor.execute(
            """
            SELECT 
                COUNT(p.id) as total_predictions,
                SUM(CASE WHEN pr.is_correct THEN 1 ELSE 0 END) as correct_predictions,
                SUM(pr.points_earned) as total_points
            FROM predictions p
            LEFT JOIN prediction_results pr ON p.id = pr.prediction_id
            WHERE p.contest_id = %s AND p.processed = TRUE
            """,
            (contest_id,)
        )
        
        stats = cursor.fetchone()
        
        if not stats or stats[0] == 0:
            logger.warning(f"No processed predictions found for contest {contest_id}")
            return
            
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
        
        # Format top performers for JSONB
        top_performers_json = []
        for performer in top_performers:
            top_performers_json.append({
                "id": performer[0],
                "username": performer[1],
                "points": int(performer[2])
            })
        
        # Calculate stats by prediction type
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
        
        # Format prediction stats for JSONB
        prediction_stats_json = []
        for stat in prediction_stats:
            total = int(stat[1])
            correct = int(stat[2])
            prediction_stats_json.append({
                "type": stat[0],
                "total": total,
                "correct": correct,
                "success_rate": round(correct / total * 100, 2) if total > 0 else 0,
                "avg_points": round(float(stat[3]), 2) if stat[3] is not None else 0
            })
        
        # Store the stats in the 'rules' JSONB field
        cursor.execute(
            """
            UPDATE weekly_contests
            SET rules = %s
            WHERE id = %s
            """,
            (
                Json({
                    'contest_summary': {
                        'total_predictions': int(stats[0]) if stats[0] else 0,
                        'correct_predictions': int(stats[1]) if stats[1] else 0,
                        'total_points': int(stats[2]) if stats[2] else 0
                    },
                    'top_performers': top_performers_json,
                    'prediction_stats': prediction_stats_json
                }),
                contest_id
            )
        )
        
        logger.info(f"Updated statistics for contest {contest_id}")
        
    except Exception as e:
        logger.error(f"Error updating contest statistics: {e}")
        raise

def main():
    try:
        logger.info("Starting prediction data generation for existing contest")
        
        # Step 1: Get current active contest
        contest = get_active_contest()
        if not contest:
            logger.error("No active contest found, exiting")
            return
            
        logger.info(f"Using active contest ID: {contest['id']}")
        
        # Step 2: Create fake users if needed
        user_ids = create_fake_users(NUM_USERS)
        logger.info(f"Working with {len(user_ids)} users")
        
        # Step 3: Create predictions for this contest
        prediction_ids = create_predictions_for_contest(
            user_ids, 
            contest['id'], 
            contest['start_date'], 
            contest['end_date'], 
            PREDICTIONS_PER_USER
        )
        
        logger.info(f"Created {len(prediction_ids)} predictions for contest {contest['id']}")
        
        # Step 4: Optionally process predictions
        if PROCESS_PREDICTIONS:
            # Get all unprocessed predictions for this contest
            predictions = get_unprocessed_predictions(contest['id'])
            
            if predictions:
                # Process with tomorrow's date as the release date
                process_predictions(predictions, contest['chart_release_date'])
                logger.info(f"Processed {len(predictions)} predictions")
            else:
                logger.info("No unprocessed predictions found to process")
        
        logger.info("Prediction data generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")

if __name__ == "__main__":
    main()