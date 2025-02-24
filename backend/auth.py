from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
import psycopg2
from datetime import datetime, timedelta
import os
import logging

auth_bp = Blueprint("auth", __name__)
bcrypt = Bcrypt()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not all([username, email, password]):
            return jsonify({"error": "All fields are required"}), 400

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (username, email, password_hash)
            )
            user_id = cursor.fetchone()[0]
            conn.commit()

            access_token = create_access_token(identity=user_id)
            return jsonify({
                "message": "Registration successful",
                "access_token": access_token,
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": email
                }
            }), 201

        except psycopg2.IntegrityError as e:
            conn.rollback()
            if "username" in str(e):
                return jsonify({"error": "Username already taken"}), 409
            if "email" in str(e):
                return jsonify({"error": "Email already registered"}), 409
            return jsonify({"error": "Registration failed"}), 400

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logging.error(f"Registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not all([username, password]):
            return jsonify({"error": "All fields are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT id, username, email, password_hash FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()

            if user and bcrypt.check_password_hash(user[3], password):
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = %s WHERE id = %s",
                    (datetime.utcnow(), user[0])
                )
                conn.commit()

                access_token = create_access_token(identity=user[0])
                return jsonify({
                    "access_token": access_token,
                    "user": {
                        "id": user[0],
                        "username": user[1],
                        "email": user[2]
                    }
                }), 200
            else:
                return jsonify({"error": "Invalid credentials"}), 401

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500

@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT username, email, created_at, last_login, 
                       total_points, weekly_points, predictions_made, 
                       correct_predictions
                FROM users WHERE id = %s
                """,
                (user_id,)
            )
            user = cursor.fetchone()

            if user:
                return jsonify({
                    "username": user[0],
                    "email": user[1],
                    "created_at": user[2],
                    "last_login": user[3],
                    "total_points": user[4],
                    "weekly_points": user[5],
                    "predictions_made": user[6],
                    "correct_predictions": user[7]
                }), 200
            else:
                return jsonify({"error": "User not found"}), 404

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logging.error(f"Profile fetch error: {e}")
        return jsonify({"error": "Failed to fetch profile"}), 500