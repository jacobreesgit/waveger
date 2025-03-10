from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from __init__ import limiter, get_real_ip
import logging
import psycopg2
import os
from datetime import datetime, timedelta

predictions_bp = Blueprint("predictions", __name__)

DATABASE_URL = os.getenv("DATABASE_URL")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

# Helper function to check if a prediction contest is active
def get_current_active_contest():
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

# GET /api/predictions/current-contest - Returns active prediction window info
@predictions_bp.route("/predictions/current-contest", methods=["GET"])
@limiter.limit("30 per minute", key_func=get_real_ip)
def get_current_contest():
    """Get the current active prediction contest information"""
    try:
        contest = get_current_active_contest()
        
        if not contest:
            return jsonify({
                "active": False,
                "message": "No active prediction contest at this time."
            }), 404
            
        return jsonify({
            "active": True,
            "contest_id": contest[0],
            "start_date": contest[1].isoformat() if contest[1] else None,
            "end_date": contest[2].isoformat() if contest[2] else None,
            "chart_release_date": contest[3].isoformat() if contest[3] else None,
            "status": contest[4]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting current contest: {e}")
        return jsonify({"error": "Failed to retrieve contest information"}), 500

# POST /api/predictions - Submit a new prediction
@predictions_bp.route("/predictions", methods=["POST"])
@jwt_required()
@limiter.limit("60 per minute", key_func=get_real_ip)
def submit_prediction():
    """Submit a new prediction for a Billboard chart"""
    user_id = get_jwt_identity()
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["contest_id", "chart_type", "prediction_type", "target_name", "position"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
                
        # Get contest information
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if contest exists and is open
            cursor.execute(
                """
                SELECT status, end_date
                FROM weekly_contests
                WHERE id = %s
                """,
                (data["contest_id"],)
            )
            
            contest = cursor.fetchone()
            if not contest:
                return jsonify({"error": "Contest not found"}), 404
                
            contest_status, contest_end_date = contest
            
            # Check if contest is open
            if contest_status != "open":
                return jsonify({"error": "Contest is no longer open for predictions"}), 400
                
            # Check if current time is before contest end date
            if datetime.utcnow() > contest_end_date:
                return jsonify({"error": "Contest has ended"}), 400
                
            # Check prediction limit per user for this contest
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM predictions
                WHERE user_id = %s AND contest_id = %s
                """,
                (user_id, data["contest_id"])
            )
            
            prediction_count = cursor.fetchone()[0]
            
            # Limit to 10 predictions per contest
            if prediction_count >= 10:
                return jsonify({"error": "Maximum prediction limit reached for this contest (10)"}), 400
                
            # Validate chart_type (normalize by removing trailing slash)
            chart_id = data["chart_type"].rstrip('/')
            if chart_id not in ["hot-100", "billboard-200"]:
                return jsonify({"error": "Invalid chart type. Must be 'hot-100' or 'billboard-200'"}), 400
                
            # Validate prediction_type
            if data["prediction_type"] not in ["entry", "exit", "position_change"]:
                return jsonify({"error": "Invalid prediction type. Must be 'entry', 'exit', or 'position_change'"}), 400
                
            # Insert the prediction
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
                    data["contest_id"],
                    chart_id,
                    datetime.utcnow().date(),  # Current date for chart_date
                    data["prediction_type"],
                    data["target_name"],
                    data.get("artist", ""),
                    data["position"] if data["prediction_type"] == "entry" else None,
                    data["position"] if data["prediction_type"] == "position_change" else None,
                    False,  # Newly inserted predictions aren't processed yet
                    datetime.utcnow()
                )
            )
            
            prediction_id = cursor.fetchone()[0]
            conn.commit()
            
            return jsonify({
                "message": "Prediction submitted successfully",
                "prediction_id": prediction_id
            }), 201
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error during prediction submission: {e}")
            return jsonify({"error": f"Failed to submit prediction: {str(e)}"}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error submitting prediction: {e}")
        return jsonify({"error": "Failed to process prediction"}), 500

# GET /api/predictions/user - Get user's predictions
@predictions_bp.route("/predictions/user", methods=["GET"])
@jwt_required()
@limiter.limit("30 per minute", key_func=get_real_ip)
def get_user_predictions():
    """Get predictions made by the authenticated user"""
    user_id = get_jwt_identity()
    
    try:
        # Get query parameters
        contest_id = request.args.get("contest_id")
        chart_type = request.args.get("chart_type")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Build the query based on parameters
            query = """
                SELECT p.id, p.contest_id, p.chart_id AS chart_type, p.prediction_type, 
                       p.song_name AS target_name, p.artist_name AS artist, 
                       CASE 
                         WHEN p.prediction_type = 'entry' THEN p.predicted_position
                         WHEN p.prediction_type = 'position_change' THEN p.predicted_change
                         ELSE NULL
                       END AS position, 
                       p.created_at AS prediction_date, pr.is_correct, pr.points_earned as points, 
                       pr.processed_at as result_date,
                       wc.chart_release_date, wc.status
                FROM predictions p
                LEFT JOIN prediction_results pr ON p.id = pr.prediction_id
                LEFT JOIN weekly_contests wc ON p.contest_id = wc.id
                WHERE p.user_id = %s
            """
            params = [user_id]
            
            if contest_id:
                query += " AND p.contest_id = %s"
                params.append(contest_id)
                
            if chart_type:
                query += " AND p.chart_id = %s"
                params.append(chart_type.rstrip('/'))  # Normalize chart type
                
            query += " ORDER BY p.created_at DESC"
            
            # Add debug logging
            logger.info(f"Executing query for user_id {user_id} with params: {params}")
            logger.debug(f"SQL Query: {query}")
            
            cursor.execute(query, params)
            predictions = cursor.fetchall()
            
            # Add debug logging for result count
            logger.info(f"Retrieved {len(predictions)} predictions for user {user_id}")
            
            result = []
            for prediction in predictions:
                # Add debug logging if any prediction processing fails
                try:
                    result.append({
                        "id": prediction[0],
                        "contest_id": prediction[1],
                        "chart_type": prediction[2],
                        "prediction_type": prediction[3],
                        "target_name": prediction[4],
                        "artist": prediction[5],
                        "position": prediction[6],
                        "prediction_date": prediction[7].isoformat() if prediction[7] else None,
                        "is_correct": prediction[8],
                        "points": prediction[9],
                        "result_date": prediction[10].isoformat() if prediction[10] else None,
                        "chart_release_date": prediction[11].isoformat() if prediction[11] else None,
                        "contest_status": prediction[12]
                    })
                except Exception as row_err:
                    logger.error(f"Error processing prediction row: {row_err}")
                    logger.error(f"Problem row data: {prediction}")
                    # Continue processing other rows
                
            return jsonify({"predictions": result}), 200
            
        except Exception as db_err:
            logger.error(f"Database error in get_user_predictions: {db_err}")
            return jsonify({"error": "Database error", "details": str(db_err)}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Unexpected error in get_user_predictions: {e}")
        return jsonify({"error": "Failed to retrieve predictions", "details": str(e)}), 500

# GET /api/predictions/leaderboard - Get global leaderboard
@predictions_bp.route("/predictions/leaderboard", methods=["GET"])
@limiter.limit("30 per minute", key_func=get_real_ip)
def get_leaderboard():
    """Get the prediction leaderboard"""
    try:
        # Get query parameters
        contest_id = request.args.get("contest_id")
        limit = request.args.get("limit", 50, type=int)
        period = request.args.get("period", "all")  # 'all', 'weekly'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if period == "weekly" and contest_id:
                # Get leaderboard for a specific contest
                query = """
                    SELECT u.id, u.username, COUNT(p.id) as predictions_made,
                           SUM(CASE WHEN pr.is_correct = TRUE THEN 1 ELSE 0 END) as correct_predictions,
                           SUM(COALESCE(pr.points_earned, 0)) as total_points
                    FROM users u
                    JOIN predictions p ON u.id = p.user_id
                    LEFT JOIN prediction_results pr ON p.id = pr.prediction_id
                    WHERE p.contest_id = %s
                    GROUP BY u.id, u.username
                    ORDER BY total_points DESC, correct_predictions DESC
                    LIMIT %s
                """
                params = [contest_id, limit]
            else:
                # Get all-time leaderboard
                query = """
                    SELECT id, username, predictions_made, correct_predictions, total_points
                    FROM users
                    WHERE predictions_made > 0
                    ORDER BY total_points DESC, correct_predictions DESC
                    LIMIT %s
                """
                params = [limit]
                
            cursor.execute(query, params)
            users = cursor.fetchall()
            
            result = []
            for i, user in enumerate(users, 1):
                predictions_made = user[2] or 0
                correct_predictions = user[3] or 0
                accuracy = round((correct_predictions / predictions_made * 100), 1) if predictions_made > 0 else 0
                
                result.append({
                    "rank": i,
                    "user_id": user[0],
                    "username": user[1],
                    "predictions_made": predictions_made,
                    "correct_predictions": correct_predictions,
                    "total_points": user[4] or 0,
                    "accuracy": accuracy
                })
                
            return jsonify({"leaderboard": result}), 200
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({"error": "Failed to retrieve leaderboard"}), 500