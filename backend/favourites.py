from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import CORS 
from db import get_db_connection

favourites_bp = Blueprint("favourites", __name__, url_prefix="/api/favourites")
CORS(favourites_bp)  

@favourites_bp.route("/", methods=["GET"])
@jwt_required()
def get_favourites():
    """Fetch all favourite songs for the logged-in user."""
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "Unauthorized access"}), 401  # Explicitly return 401

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, title, artist FROM favourites WHERE user_id = %s", (user_id,))
        favourites = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(favourites)
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Return a proper error message

@favourites_bp.route("/", methods=["POST"])
@jwt_required()
def add_favourite():
    """Add a song to the user's favourites."""
    user_id = get_jwt_identity()
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO favourites (user_id, title, artist) VALUES (%s, %s, %s) RETURNING id",
            (user_id, data["title"], data["artist"])
        )
        favourite_id = cursor.fetchone()["id"]
        conn.commit()
        return jsonify({"message": "Song added to favourites", "id": favourite_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@favourites_bp.route("/<int:song_id>", methods=["DELETE"])
@jwt_required()
def remove_favourite(song_id):
    """Remove a song from the user's favourites."""
    user_id = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM favourites WHERE id = %s AND user_id = %s RETURNING id", (song_id, user_id)
        )
        deleted_song = cursor.fetchone()
        if deleted_song:
            conn.commit()
            return jsonify({"message": "Favourite removed"}), 200
        return jsonify({"error": "Favourite not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@auth_bp.route("/validate-token", methods=["GET"])
@jwt_required()
def validate_token():
    """Validate JWT token and return user data."""
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "Invalid token"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"user": user}), 200
    except Exception as e:
        return jsonify({"error": f"Token validation failed: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()