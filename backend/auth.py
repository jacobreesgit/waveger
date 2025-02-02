from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register_user():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        hashed_password = generate_password_hash(data["password"])
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (data["username"], data["email"], hashed_password),
        )
        user_id = cursor.fetchone()["id"]
        conn.commit()
        return jsonify({"message": "User registered", "id": user_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (data["username"],))
        user = cursor.fetchone()

        if user and check_password_hash(user["password_hash"], data["password"]):
            access_token = create_access_token(identity=user["id"], expires_delta=timedelta(days=7))
            return jsonify({"message": "Login successful", "access_token": access_token})

        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@auth_bp.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    """Admin-only: Fetch all users"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, username, email FROM users")
        users = cursor.fetchall()
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
