from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import os
import psycopg2
from db import get_db_connection
from werkzeug.utils import secure_filename

users_bp = Blueprint("users", __name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@users_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.form
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        profile_pic = request.files.get("profile_pic")

        if not username or not email or not password:
            return jsonify({"error": "Missing required fields"}), 400

        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Email already registered"}), 400

        profile_pic_filename = None
        if profile_pic:
            profile_pic_filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(UPLOAD_FOLDER, profile_pic_filename))

        cursor.execute(
            "INSERT INTO users (username, email, password, profile_pic) VALUES (%s, %s, %s, %s) RETURNING id",
            (username, email, hashed_password, profile_pic_filename),
        )

        user_row = cursor.fetchone()
        print(f"DEBUG: Insert result: {user_row}") 

        if not user_row or "id" not in user_row:
            conn.rollback()
            return jsonify({"error": "Failed to create user"}), 500

        user_id = user_row["id"] 
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "User registered successfully", "user_id": user_id})
    
    except Exception as e:
        print(f"Error in /register: {str(e)}") 
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@users_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    identifier = data.get("identifier")  # This can be either email or username
    password = data.get("password")
    
    if not identifier or not password:
        return jsonify({"error": "Missing credentials"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check for either username or email match
    cursor.execute(
        "SELECT id, password FROM users WHERE email = %s OR username = %s", 
        (identifier, identifier)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    access_token = create_access_token(identity=user["id"])
    return jsonify({"access_token": access_token})

@users_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, email, profile_pic FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({"username": user[0], "email": user[1], "profile_pic": user[2]})

@users_bp.route("/upload-profile-pic", methods=["POST"])
@jwt_required()
def upload_profile_pic():
    user_id = get_jwt_identity()
    profile_pic = request.files.get("profile_pic")
    
    if not profile_pic:
        return jsonify({"error": "No file uploaded"}), 400
    
    filename = secure_filename(profile_pic.filename)
    profile_pic.save(os.path.join(UPLOAD_FOLDER, filename))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET profile_pic = %s WHERE id = %s", (filename, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"message": "Profile picture updated successfully", "filename": filename})

@users_bp.route("/profile-pic/<filename>", methods=["GET"])
def get_profile_pic(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
