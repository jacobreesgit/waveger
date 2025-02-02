from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from db import get_db_connection
from flask_cors import CORS 

auth_bp = Blueprint("auth", __name__)
CORS(auth_bp) 

@auth_bp.route("/register", methods=["POST"])
def register_user():
    """Registers a new user with hashed password"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        hashed_password = generate_password_hash(data["password"])  # Hash password
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
    """Logs in a user and returns an access token"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch user from DB
        cursor.execute("SELECT id, username, email, password_hash FROM users WHERE username = %s", (data["username"],))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Ensure password is checked correctly
        if not check_password_hash(user["password_hash"], data["password"]):
            return jsonify({"error": "Invalid credentials"}), 401

        # Create JWT token
        access_token = create_access_token(identity=user["id"], expires_delta=timedelta(days=7))

        # Return user details & token
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            },
            "access_token": access_token
        }), 200

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

@auth_bp.route("/validate-token", methods=["GET"])
@jwt_required()
def validate_token():
    """Validate JWT token and return user data."""
    user_id = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"user": user}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()