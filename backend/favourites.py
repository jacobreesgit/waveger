from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import CORS
from db import get_db_connection

favourites_bp = Blueprint("favourites", __name__)
CORS(favourites_bp)  # Apply CORS to Blueprint

@favourites_bp.route("/favourites/<int:user_id>", methods=["GET"])
@jwt_required()
def get_favourites(user_id):
    """Fetch user's favourite songs."""
    logged_in_user = get_jwt_identity()

    if logged_in_user != user_id:
        return jsonify({"error": "Unauthorized access"}), 403

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, title, artist FROM favourites WHERE user_id = %s", (user_id,))
        favourites = cursor.fetchall()
        return jsonify(favourites)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@favourites_bp.route("/favourites", methods=["POST"])
@jwt_required()
def add_favourite():
    """Add a song to the user's favourites."""
    logged_in_user = get_jwt_identity()
    data = request.json

    if "title" not in data or "artist" not in data:
        return jsonify({"error": "Missing song title or artist"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO favourites (user_id, title, artist) VALUES (%s, %s, %s) RETURNING id",
            (logged_in_user, data["title"], data["artist"]),
        )
        favourite_id = cursor.fetchone()["id"]
        conn.commit()
        return jsonify({"message": "Song added to favourites!", "id": favourite_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@favourites_bp.route("/favourites/<int:fav_id>", methods=["DELETE"])
@jwt_required()
def remove_favourite(fav_id):
    """Remove a favourite song by ID."""
    logged_in_user = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM favourites WHERE id = %s AND user_id = %s RETURNING id",
            (fav_id, logged_in_user),
        )
        deleted_id = cursor.fetchone()

        if deleted_id:
            conn.commit()
            return jsonify({"message": "Favourite removed"}), 200
        return jsonify({"error": "Favourite not found or not owned by user"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
