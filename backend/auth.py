from flask import Blueprint, request, jsonify, g, current_app
from __init__ import limiter, bcrypt, get_real_ip
from flask_jwt_extended import (
    create_access_token, 
    get_jwt_identity, 
    jwt_required, 
    create_refresh_token
)
import psycopg2
from datetime import datetime, timedelta
import os
import logging
import uuid
import jwt as pyjwt
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

auth_bp = Blueprint("auth", __name__)

DATABASE_URL = os.getenv("DATABASE_URL")
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define a token expiration time (1 hour)
RESET_TOKEN_EXPIRY = timedelta(hours=1)

# SMTP configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USERNAME)
APP_URL = os.getenv("APP_URL", "https://www.waveger.com")

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
@limiter.limit("20 per hour", key_func=get_real_ip)
def register():
    try:
        data = request.get_json()
        logger.info(f"Registration request from IP: {get_real_ip()}")
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
@limiter.limit("5 per minute", key_func=get_real_ip)
def login():
    try:
        data = request.get_json()
        # Log client IP for debugging
        logger.info(f"Login request from IP: {get_real_ip()}")
        
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
@limiter.limit("30 per minute", key_func=get_real_ip)
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
@limiter.limit("20 per minute", key_func=get_real_ip)
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
@limiter.limit("10 per minute", key_func=get_real_ip)
def refresh():
    try:
        data = request.get_json()
        refresh_token = data.get("refresh_token")
        
        if not refresh_token:
            logger.error("Refresh token missing")
            return jsonify({"error": "Refresh token is required"}), 400
            
        # Get the JWT secret key
        jwt_secret_key = current_app.config.get("JWT_SECRET_KEY")
        if not jwt_secret_key:
            jwt_secret_key = current_app.config.get("SECRET_KEY")
        
        if not jwt_secret_key:
            logger.error("JWT secret key not configured")
            return jsonify({"error": "Server configuration error"}), 500
            
        # Verify the refresh token using PyJWT directly
        try:
            # First, decode without verification to get the token_id
            unverified_payload = pyjwt.decode(
                refresh_token, 
                options={"verify_signature": False}
            )
            token_id = unverified_payload.get("token_id")
            
            # Now properly decode and verify
            decoded_token = pyjwt.decode(
                refresh_token,
                jwt_secret_key,
                algorithms=["HS256"]
            )
            
            # Extract user information
            user_id = decoded_token.get('sub')
            if not user_id:
                raise ValueError("Missing user ID in token")
                
            # Connect to DB to get user details
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT username, email FROM users WHERE id = %s",
                (int(user_id),)
            )
            
            db_user = cursor.fetchone()
            if not db_user:
                cursor.close()
                conn.close()
                raise ValueError("User not found")
                
            username = db_user[0]
            email = db_user[1]
            
            cursor.close()
            conn.close()
            
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
            logger.error(f"Token validation error: {e}")
            return jsonify({"error": "Invalid refresh token"}), 401
            
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({"error": "Failed to refresh token"}), 500

def send_password_reset_email(email, token):
    """Sends a password reset email with a reset link."""
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD]):
        logger.error("Missing email configuration variables")
        return False
    
    try:
        reset_link = f"{APP_URL}/reset-password/{token}"
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Password Reset Request"
        message["From"] = SENDER_EMAIL
        message["To"] = email
        
        text = f"""
        Hello,
        
        You have requested to reset your password. Please click the link below to reset your password:
        
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you did not request this password reset, please ignore this email.
        
        Best regards,
        Waveger Team
        """
        
        html = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hello,</p>
            <p>You have requested to reset your password. Please click the link below to reset your password:</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you did not request this password reset, please ignore this email.</p>
            <p>Best regards,<br>Waveger Team</p>
        </body>
        </html>
        """
        
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        
        message.attach(part1)
        message.attach(part2)
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, message.as_string())
        server.quit()
        
        logger.info(f"Password reset email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        return False

@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per hour", key_func=get_real_ip)
def forgot_password():
    """Handles forgot password requests by sending a reset email."""
    try:
        data = request.get_json()
        email = data.get("email")
        
        if not email:
            return jsonify({"error": "Email address is required"}), 400
            
        # Log the request for monitoring
        client_ip = get_real_ip()
        logger.info(f"Password reset requested for {email} from IP: {client_ip}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if email exists
            cursor.execute("SELECT id, username FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if not user:
                # For security reasons, still return success even if email is not found
                # This prevents user enumeration
                logger.info(f"Password reset requested for non-existent email: {email}")
                return jsonify({"message": "If your email is registered, you will receive reset instructions"}), 200
                
            user_id, username = user
                
            # Generate a secure random token
            reset_token = secrets.token_urlsafe(32)
            token_expiry = datetime.utcnow() + RESET_TOKEN_EXPIRY
            
            # Store the reset token
            cursor.execute(
                """
                INSERT INTO password_reset_tokens (user_id, token, expiry, used)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, reset_token, token_expiry, False)
            )
            conn.commit()
            
            # Send the reset email
            email_sent = send_password_reset_email(email, reset_token)
            
            if not email_sent:
                # If email fails, still allow alternative reset methods
                logger.error(f"Failed to send password reset email to {email}")
                return jsonify({
                    "message": "Password reset initiated but email could not be sent. Please contact support."
                }), 202
                
            return jsonify({
                "message": "Password reset instructions have been sent to your email"
            }), 200
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error during password reset: {e}")
            return jsonify({"error": "Failed to process password reset request"}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Unexpected error in forgot_password: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@auth_bp.route("/verify-reset-token", methods=["GET"])
@limiter.limit("20 per hour", key_func=get_real_ip)
def verify_reset_token():
    """Verifies if a password reset token is valid."""
    try:
        token = request.args.get("token")
        
        if not token:
            return jsonify({"error": "Token is required"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if the token exists and is valid
            cursor.execute(
                """
                SELECT t.id, t.user_id, t.expiry, t.used, u.username, u.email
                FROM password_reset_tokens t
                JOIN users u ON t.user_id = u.id
                WHERE t.token = %s
                """,
                (token,)
            )
            token_data = cursor.fetchone()
            
            if not token_data:
                return jsonify({"valid": False, "error": "Invalid or expired token"}), 401
                
            token_id, user_id, expiry, used, username, email = token_data
            
            # Check if token is expired
            if expiry < datetime.utcnow():
                return jsonify({"valid": False, "error": "Token has expired"}), 401
                
            # Check if token has been used
            if used:
                return jsonify({"valid": False, "error": "Token has already been used"}), 401
                
            return jsonify({
                "valid": True, 
                "username": username,
                "email": email
            }), 200
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error verifying reset token: {e}")
        return jsonify({"error": "Failed to verify token"}), 500

@auth_bp.route("/reset-password", methods=["POST"])
@limiter.limit("5 per hour", key_func=get_real_ip)
def reset_password():
    """Resets a user's password using a valid reset token."""
    try:
        data = request.get_json()
        token = data.get("token")
        new_password = data.get("password")
        
        if not token or not new_password:
            return jsonify({"error": "Token and new password are required"}), 400
            
        if len(new_password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Begin transaction
            # Check if the token exists and is valid
            cursor.execute(
                """
                SELECT t.id, t.user_id, t.expiry, t.used, u.username
                FROM password_reset_tokens t
                JOIN users u ON t.user_id = u.id
                WHERE t.token = %s
                FOR UPDATE
                """,
                (token,)
            )
            token_data = cursor.fetchone()
            
            if not token_data:
                return jsonify({"error": "Invalid or expired token"}), 401
                
            token_id, user_id, expiry, used, username = token_data
            
            # Check if token is expired
            if expiry < datetime.utcnow():
                return jsonify({"error": "Token has expired"}), 401
                
            # Check if token has been used
            if used:
                return jsonify({"error": "Token has already been used"}), 401
                
            # Hash the new password
            password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            
            # Update the user's password
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (password_hash, user_id)
            )
            
            # Mark the token as used
            cursor.execute(
                "UPDATE password_reset_tokens SET used = %s WHERE id = %s",
                (True, token_id)
            )
            
            # Commit the transaction
            conn.commit()
            
            # Log the successful password reset
            logger.info(f"Password reset successful for user {username}")
            
            return jsonify({
                "message": "Password has been reset successfully. You can now log in with your new password."
            }), 200
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error during password reset: {e}")
            return jsonify({"error": "Failed to reset password"}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Unexpected error in reset_password: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@auth_bp.route("/user-info", methods=["GET"])
@limiter.limit("20 per minute", key_func=get_real_ip)
def get_user_info():
    """
    Get basic user information by username (without requiring authentication).
    This endpoint is used for prefetching user data during login.
    Returns minimal information needed for faster login experience.
    """
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({"error": "Username is required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Query to fetch only necessary user info, excluding sensitive data like password
            query = """
                SELECT 
                    id, username, email, 
                    created_at, last_login, 
                    total_points, weekly_points, 
                    predictions_made, correct_predictions 
                FROM users 
                WHERE username = %s
            """
            logger.debug(f"Fetching user info for username: {username}")
            
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            
            if not user:
                # For security reasons, don't indicate whether the user exists or not
                # Just return a generic success response with empty data
                return jsonify({
                    "success": True,
                    "user": None
                }), 200
            
            # Convert to a dictionary with proper field names
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
            
            return jsonify({
                "success": True,
                "user": user_data
            }), 200
            
        except Exception as e:
            logger.error(f"Database error in user_info: {e}")
            return jsonify({"error": "Database error", "details": str(e)}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Unexpected error in user_info: {e}")
        return jsonify({"error": "Server error", "details": str(e)}), 500

@auth_bp.route("/update-profile", methods=["PUT"])
@jwt_required()
@limiter.limit("10 per minute", key_func=get_real_ip)
def update_profile():
    """Update user profile information (username, email, password)."""
    try:
        # Get the user ID from the JWT token
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get current data to check what's changed
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT username, email, password_hash FROM users WHERE id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            
            if not user:
                return jsonify({"error": "User not found"}), 404
                
            current_username, current_email, current_password_hash = user
            
            # Check what fields were provided and update them
            updates = {}
            update_fields = []
            update_values = []
            
            # Handle username update
            if 'username' in data and data['username'] != current_username:
                # Check if username is available
                cursor.execute(
                    "SELECT EXISTS(SELECT 1 FROM users WHERE username = %s AND id != %s)",
                    (data['username'], user_id)
                )
                username_exists = cursor.fetchone()[0]
                
                if username_exists:
                    return jsonify({"error": "Username already taken"}), 409
                    
                update_fields.append("username = %s")
                update_values.append(data['username'])
                updates['username'] = data['username']
            
            # Handle email update
            if 'email' in data and data['email'] != current_email:
                # Check if email is available
                cursor.execute(
                    "SELECT EXISTS(SELECT 1 FROM users WHERE email = %s AND id != %s)",
                    (data['email'], user_id)
                )
                email_exists = cursor.fetchone()[0]
                
                if email_exists:
                    return jsonify({"error": "Email already registered"}), 409
                    
                update_fields.append("email = %s")
                update_values.append(data['email'])
                updates['email'] = data['email']
            
            # Handle password update
            if 'current_password' in data and 'new_password' in data:
                # Verify current password
                if not bcrypt.check_password_hash(current_password_hash, data['current_password']):
                    return jsonify({"error": "Current password is incorrect"}), 401
                    
                # Hash and update password
                password_hash = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')
                update_fields.append("password_hash = %s")
                update_values.append(password_hash)
                updates['password_updated'] = True
            
            # If there are no updates, return early
            if not update_fields:
                return jsonify({"message": "No changes made"}), 200
                
            # Build and execute update query
            query = "UPDATE users SET " + ", ".join(update_fields) + " WHERE id = %s"
            update_values.append(user_id)
            
            cursor.execute(query, update_values)
            conn.commit()
            
            return jsonify({
                "message": "Profile updated successfully",
                "updates": updates
            }), 200
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error in update_profile: {e}")
            return jsonify({"error": "Failed to update profile", "details": str(e)}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Unexpected error in update_profile: {e}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500