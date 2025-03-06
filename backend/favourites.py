from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from __init__ import limiter, get_real_ip
import logging
import psycopg2
import os

favourites_bp = Blueprint("favourites", __name__)

DATABASE_URL = os.getenv("DATABASE_URL")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

@favourites_bp.route("/favourites", methods=["GET"])
@jwt_required()
@limiter.limit(os.getenv("WAVEGER_TEST_FAVOURITES_LIMIT", "120 per minute"), key_func=get_real_ip)
def get_favourites():
    """Get all favourites for the authenticated user."""
    user_id = get_jwt_identity()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get favourites with chart metadata
        query = """
        SELECT 
            id, song_name, artist, chart_id, chart_title, 
            position, image_url, peak_position, weeks_on_chart, 
            added_at
        FROM 
            user_favourites
        WHERE 
            user_id = %s
        ORDER BY 
            added_at DESC
        """
        
        cursor.execute(query, (user_id,))
        favourites = cursor.fetchall()
        
        # Transform into a list of dictionaries
        results = []
        for fav in favourites:
            results.append({
                "id": fav[0],
                "song_name": fav[1],
                "artist": fav[2],
                "chart_id": fav[3],
                "chart_title": fav[4],
                "position": fav[5],
                "image_url": fav[6],
                "peak_position": fav[7],
                "weeks_on_chart": fav[8],
                "added_at": fav[9].isoformat() if fav[9] else None
            })
        
        # Group by song and artist to show multiple chart appearances
        grouped_results = {}
        for item in results:
            key = f"{item['song_name']}||{item['artist']}"
            if key not in grouped_results:
                grouped_results[key] = {
                    "song_name": item["song_name"],
                    "artist": item["artist"],
                    "image_url": item["image_url"],
                    "charts": [],
                    "first_added_at": item["added_at"]
                }
            
            grouped_results[key]["charts"].append({
                "id": item["id"],
                "chart_id": item["chart_id"],
                "chart_title": item["chart_title"],
                "position": item["position"],
                "peak_position": item["peak_position"],
                "weeks_on_chart": item["weeks_on_chart"],
                "added_at": item["added_at"]
            })
        
        # Convert back to list
        final_results = list(grouped_results.values())
        
        cursor.close()
        conn.close()
        
        return jsonify({"favourites": final_results}), 200
    
    except Exception as e:
        logger.error(f"Error getting favourites: {e}")
        return jsonify({"error": "Failed to retrieve favourites"}), 500

@favourites_bp.route("/favourites", methods=["POST"])
@jwt_required()
@limiter.limit(os.getenv("WAVEGER_TEST_FAVOURITES_LIMIT", "120 per minute"), key_func=get_real_ip)
def add_favourite():
    """Add a song to favourites."""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    required_fields = ["song_name", "artist", "chart_id", "chart_title"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if this song from this chart is already favourited
        cursor.execute(
            """
            SELECT id FROM user_favourites
            WHERE user_id = %s AND song_name = %s AND artist = %s AND chart_id = %s
            """,
            (user_id, data["song_name"], data["artist"], data["chart_id"])
        )
        
        existing = cursor.fetchone()
        
        if existing:
            # Already favourited - return success but with a message
            cursor.close()
            conn.close()
            return jsonify({
                "message": "Song is already in favourites",
                "favourite_id": existing[0]
            }), 200
        
        # Add to favourites
        cursor.execute(
            """
            INSERT INTO user_favourites
            (user_id, song_name, artist, chart_id, chart_title, position, image_url, peak_position, weeks_on_chart)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                user_id,
                data["song_name"],
                data["artist"],
                data["chart_id"],
                data["chart_title"],
                data.get("position"),
                data.get("image_url"),
                data.get("peak_position"),
                data.get("weeks_on_chart")
            )
        )
        
        favourite_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "Song added to favourites",
            "favourite_id": favourite_id
        }), 201
    
    except Exception as e:
        logger.error(f"Error adding favourite: {e}")
        return jsonify({"error": "Failed to add song to favourites"}), 500

@favourites_bp.route("/favourites/<int:favourite_id>", methods=["DELETE"])
@jwt_required()
@limiter.limit(os.getenv("WAVEGER_TEST_FAVOURITES_LIMIT", "120 per minute"), key_func=get_real_ip)
def remove_favourite(favourite_id):
    """Remove a song from favourites."""
    user_id = get_jwt_identity()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if the favourite exists and belongs to this user
        cursor.execute(
            "SELECT id FROM user_favourites WHERE id = %s AND user_id = %s",
            (favourite_id, user_id)
        )
        
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Favourite not found or unauthorized"}), 404
        
        # Delete the favourite
        cursor.execute(
            "DELETE FROM user_favourites WHERE id = %s AND user_id = %s",
            (favourite_id, user_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Favourite removed successfully"}), 200
    
    except Exception as e:
        logger.error(f"Error removing favourite: {e}")
        return jsonify({"error": "Failed to remove favourite"}), 500

@favourites_bp.route("/favourites/check", methods=["GET"])
@jwt_required()
@limiter.limit(os.getenv("WAVEGER_TEST_FAVOURITES_LIMIT", "120 per minute"), key_func=get_real_ip)
def check_favourite():
    """Check if a song is already favourited by the user."""
    user_id = get_jwt_identity()
    song_name = request.args.get("song_name")
    artist = request.args.get("artist")
    chart_id = request.args.get("chart_id")
    
    if not all([song_name, artist, chart_id]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if favourited
        cursor.execute(
            """
            SELECT id FROM user_favourites
            WHERE user_id = %s AND song_name = %s AND artist = %s AND chart_id = %s
            """,
            (user_id, song_name, artist, chart_id)
        )
        
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        is_favourited = bool(result)
        favourite_id = result[0] if result else None
        
        return jsonify({
            "is_favourited": is_favourited,
            "favourite_id": favourite_id
        }), 200
    
    except Exception as e:
        logger.error(f"Error checking favourite status: {e}")
        return jsonify({"error": "Failed to check favourite status"}), 500