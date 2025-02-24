from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from flask_bcrypt import Bcrypt
import psycopg2
from datetime import datetime, timedelta
import os
import logging

auth_bp = Blueprint("auth", __name__)
bcrypt = Bcrypt()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        logging.info(f"Received registration request: {data}")
        
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not all([username, email, password]):
            logging.error("Missing required fields")
            return jsonify({"error": "All fields are required"}), 400

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            logging.info("Attempting to insert new user")
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (username, email, password_hash)
            )
            user_id = cursor.fetchone()[0]
            conn.commit()
            logging.info(f"Successfully registered user {username}")

            access_token = create_access_token(identity=user_id)
            
            response = jsonify({
                "message": "Registration successful",
                "access_token": access_token,
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": email
                }
            })
            
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response, 201

        except psycopg2.IntegrityError as e:
            conn.rollback()
            logging.error(f"Database integrity error: {e}")
            if "username" in str(e):
                return jsonify({"error": "Username already taken"}), 409
            if "email" in str(e):
                return jsonify({"error": "Email already registered"}), 409
            return jsonify({"error": "Registration failed"}), 400
        except Exception as e:
            conn.rollback()
            logging.error(f"Unexpected database error: {e}")
            return jsonify({"error": "Registration failed"}), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logging.error(f"General registration error: {e}")
        return jsonify({"error": str(e)}), 500

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
                
                response = jsonify({
                    "access_token": access_token,
                    "user": {
                        "id": user[0],
                        "username": user[1],
                        "email": user[2]
                    }
                })
                
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                return response, 200
            else:
                return jsonify({"error": "Invalid credentials"}), 401

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500


@auth_bp.route("/user", methods=["GET"])
@jwt_required()
def get_user_data():
    # Log incoming request details
    logger.debug("Incoming request to /user endpoint")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    try:
        # Get the user ID from the JWT token
        user_id = get_jwt_identity()
        logger.debug(f"Extracted user ID from token: {user_id}")

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Comprehensive query logging
            logger.debug("Executing user data query")
            query = """
                SELECT 
                    id, username, email, 
                    created_at, last_login, 
                    total_points, weekly_points, 
                    predictions_made, correct_predictions 
                FROM users 
                WHERE id = %s
            """
            logger.debug(f"Query: {query}")
            logger.debug(f"Query parameters: {user_id}")

            # Execute the query
            cursor.execute(query, (user_id,))
            
            # Fetch the user
            user = cursor.fetchone()
            logger.debug(f"Query result: {user}")

            if not user:
                logger.error(f"No user found with ID: {user_id}")
                return jsonify({"error": "User not found"}), 404

            # Detailed field conversion and logging
            try:
                user_data = {
                    "id": int(user[0]) if user[0] is not None else None,
                    "username": str(user[1]) if user[1] is not None else None,
                    "email": str(user[2]) if user[2] is not None else None,
                    "created_at": user[3].isoformat() if user[3] is not None else None,
                    "last_login": user[4].isoformat() if user[4] is not None else None,
                    "total_points": int(user[5]) if user[5] is not None else 0,
                    "weekly_points": int(user[6]) if user[6] is not None else 0,
                    "predictions_made": int(user[7]) if user[7] is not None else 0,
                    "correct_predictions": int(user[8]) if user[8] is not None else 0
                }

                # Log each field for verification
                for key, value in user_data.items():
                    logger.debug(f"User field {key}: {value} (type: {type(value)})")

                return jsonify(user_data), 200

            except Exception as conversion_error:
                logger.error(f"Error converting user data: {conversion_error}")
                logger.error(traceback.format_exc())
                return jsonify({
                    "error": "Failed to process user data",
                    "details": str(conversion_error)
                }), 500

        except psycopg2.Error as db_error:
            logger.error(f"Database error: {db_error}")
            logger.error(traceback.format_exc())
            return jsonify({
                "error": "Database error",
                "details": str(db_error)
            }), 500

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Unexpected error in get_user_data: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": "Unexpected server error",
            "details": str(e)
        }), 500