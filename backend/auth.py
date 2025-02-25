from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, 
    get_jwt_identity, 
    jwt_required, 
    create_refresh_token,
    jwt
)
from flask_bcrypt import Bcrypt
import psycopg2
from datetime import datetime, timedelta
import os
import logging
import uuid

auth_bp = Blueprint("auth", __name__)
bcrypt = Bcrypt()

DATABASE_URL = os.getenv("DATABASE_URL")
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def generate_unique_token_id():
    """Generate a unique identifier for tokens."""
    return str(uuid.uuid4())

@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        logger.info(f"Received registration request: {data}")
        
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not all([username, email, password]):
            logger.error("Missing required fields")
            return jsonify({"error": "All fields are required"}), 400

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            logger.info("Attempting to insert new user")
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (username, email, password_hash)
            )
            user_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"Successfully registered user {username}")

            # Generate tokens with additional metadata
            additional_claims = {
                "username": username,
                "email": email,
                "token_id": generate_unique_token_id()
            }
            
            access_token = create_access_token(
                identity=str(user_id),  # Ensure identity is a string
                additional_claims=additional_claims,
                expires_delta=timedelta(hours=24)
            )
            
            refresh_token = create_refresh_token(
                identity=str(user_id),
                additional_claims=additional_claims,
                expires_delta=timedelta(days=30)
            )
            
            response = jsonify({
                "message": "Registration successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
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
            logger.error(f"Database integrity error: {e}")
            if "username" in str(e):
                return jsonify({"error": "Username already taken"}), 409
            if "email" in str(e):
                return jsonify({"error": "Email already registered"}), 409
            return jsonify({"error": "Registration failed"}), 400
        except Exception as e:
            conn.rollback()
            logger.error(f"Unexpected database error: {e}")
            return jsonify({"error": "Registration failed"}), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"General registration error: {e}")
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
                # Generate tokens with additional metadata
                additional_claims = {
                    "username": user[1],
                    "email": user[2],
                    "token_id": generate_unique_token_id()
                }
                
                access_token = create_access_token(
                    identity=str(user[0]),  # Ensure identity is a string
                    additional_claims=additional_claims,
                    expires_delta=timedelta(hours=24)
                )
                
                refresh_token = create_refresh_token(
                    identity=str(user[0]),
                    additional_claims=additional_claims,
                    expires_delta=timedelta(days=30)
                )

                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = %s WHERE id = %s",
                    (datetime.utcnow(), user[0])
                )
                conn.commit()

                response = jsonify({
                    "access_token": access_token,
                    "refresh_token": refresh_token,
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
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500

@auth_bp.route("/user", methods=["GET"])
@jwt_required()
def get_user_data():
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

            # Ensure user_id is converted to an integer
            cursor.execute(query, (int(user_id),))
            
            # Fetch the user
            user = cursor.fetchone()
            logger.debug(f"Query result: {user}")

            if not user:
                logger.error(f"No user found with ID: {user_id}")
                return jsonify({"error": "User not found"}), 404

            # Detailed field conversion and logging
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

        except Exception as e:
            logger.error(f"Error processing user data: {e}")
            return jsonify({"error": "Failed to process user data", "details": str(e)}), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Unexpected error in get_user_data: {e}")
        return jsonify({"error": "Unexpected server error", "details": str(e)}), 500

@auth_bp.route("/check-availability", methods=["GET"])
def check_availability():
    """
    Check if a username or email is already in use.
    
    Query parameters:
    - username: username to check
    - email: email to check
    """
    username = request.args.get('username')
    email = request.args.get('email')

    if not username and not email:
        return jsonify({"error": "Please provide username or email to check"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        result = {}

        # Check username availability
        if username:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM users WHERE username = %s)",
                (username,)
            )
            result['username_exists'] = cursor.fetchone()[0]

        # Check email availability
        if email:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM users WHERE email = %s)",
                (email,)
            )
            result['email_exists'] = cursor.fetchone()[0]

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Availability check error: {e}")
        return jsonify({"error": "Error checking availability"}), 500
    finally:
        cursor.close()
        conn.close()

@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    try:
        data = request.get_json()
        refresh_token = data.get("refresh_token")
        
        if not refresh_token:
            logger.error("Refresh token missing")
            return jsonify({"error": "Refresh token is required"}), 400
            
        # Verify the refresh token
        try:
            # Decode without verification to get token_id
            unverified_payload = jwt.decode(
                refresh_token, 
                options={"verify_signature": False}
            )
            token_id = unverified_payload.get("token_id")
            
            # Now properly decode and verify
            decoded_token = jwt.decode(
                refresh_token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"]
            )
            
            user_id = decoded_token['sub']
            username = decoded_token['username']
            email = decoded_token['email']
            
        except Exception as e:
            logger.error(f"Invalid refresh token: {e}")
            return jsonify({"error": "Invalid refresh token"}), 401
            
        # Generate a new access token
        access_token = create_access_token(
            identity=user_id,
            additional_claims={
                "username": username,
                "email": email,
                "token_id": token_id  # Keep the same token_id for tracking
            }
        )
        
        return jsonify({
            "access_token": access_token,
            "user": {
                "id": int(user_id),
                "username": username,
                "email": email
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({"error": "Failed to refresh token"}), 500