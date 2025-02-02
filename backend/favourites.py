from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection

favourites_bp = Blueprint("favourites", __name__)

@favourites_bp.route("/favourites", methods=["POST"])
@jwt_required()
def add_favourite():
    user_id = get_jwt_identity()
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO favourites (user_id, title, artist) VALUES (%s, %s, %s) RETURNING id", (user_id, data["title"], data["artist"]))
        fav_id = cursor.fetchone()["id"]
        conn.commit()
        return jsonify({"message": "Added to favourites!", "id": fav_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@favourites_bp.route("/favourites", methods=["GET"])
@jwt_required()
def get_favourites():
    user_id = get_jwt_identity()

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
