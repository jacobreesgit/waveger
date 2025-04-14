from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from __init__ import limiter, get_real_ip
import logging
import os
from db_utils import (
    get_db_connection,
    get_user_favourites,
    toggle_favourite,
    check_favourite_status
)

favourites_bp = Blueprint("favourites", __name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@favourites_bp.route("/favourites", methods=["GET"])
@jwt_required()
@limiter.limit("120 per minute", key_func=get_real_ip)
def get_favourites():
    """Get all favourites for the authenticated user."""
    user_id = get_jwt_identity()
    chart_id = request.args.get('chart_id')
    
    try:
        # Get favourites with chart data
        favourites = get_user_favourites(user_id, chart_id)
        
        return jsonify({"favourites": favourites}), 200
    
    except Exception as e:
        logger.error(f"Error getting favourites: {e}")
        return jsonify({"error": "Failed to retrieve favourites"}), 500

@favourites_bp.route("/favourites", methods=["POST"])
@jwt_required()
@limiter.limit("120 per minute", key_func=get_real_ip)
def add_favourite():
    """Add or update a song's favourite status."""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    required_fields = ["song_name", "artist", "chart_id", "chart_title"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    try:
        # Toggle favourite status
        result = toggle_favourite(
            user_id=user_id,
            song_name=data["song_name"],
            artist=data["artist"],
            chart_id=data["chart_id"],
            chart_title=data["chart_title"],
            image_url=data.get("image_url"),
            position=data.get("position"),
            peak_position=data.get("peak_position"),
            weeks_on_chart=data.get("weeks_on_chart"),
            last_week_position=data.get("last_week_position")
        )
        
        if result["action"] == "added":
            return jsonify({
                "message": "Song added to favourites",
                "favourite_id": result["favourite_id"]
            }), 201
        else:
            return jsonify({
                "message": "Song removed from favourites",
                "favourite_id": result["favourite_id"]
            }), 200
    
    except Exception as e:
        logger.error(f"Error toggling favourite: {e}")
        return jsonify({"error": "Failed to update favourite status"}), 500

@favourites_bp.route("/favourites/<int:favourite_id>", methods=["DELETE"])
@jwt_required()
@limiter.limit("120 per minute", key_func=get_real_ip)
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
@limiter.limit("120 per minute", key_func=get_real_ip)
def check_favourite():
    """Check if a song is already favourited by the user."""
    user_id = get_jwt_identity()
    song_name = request.args.get("song_name")
    artist = request.args.get("artist")
    chart_id = request.args.get("chart_id")
    
    if not all([song_name, artist, chart_id]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        # Check favourite status
        result = check_favourite_status(
            user_id=user_id,
            song_name=song_name,
            artist=artist,
            chart_id=chart_id
        )
        
        return jsonify({
            "is_favourited": result["is_favourited"],
            "favourite_id": result["favourite_id"]
        }), 200
    
    except Exception as e:
        logger.error(f"Error checking favourite status: {e}")
        return jsonify({"error": "Failed to check favourite status"}), 500