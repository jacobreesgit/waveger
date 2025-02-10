from flask import Blueprint, jsonify
import os
import jwt
import time

# Create a Blueprint for Apple Music
apple_music_bp = Blueprint("apple_music", __name__)

# Apple Music API Credentials
TEAM_ID = os.getenv("APPLE_MUSIC_TEAM_ID")
KEY_ID = os.getenv("APPLE_MUSIC_KEY_ID")
PRIVATE_KEY_PATH = "/etc/secrets/AuthKey.p8"  # Using Render Secret Files

def generate_apple_music_token():
    if not os.path.exists(PRIVATE_KEY_PATH):
        return jsonify({"error": "Private key file missing"}), 500

    try:
        with open(PRIVATE_KEY_PATH, "r") as key_file:
            private_key = key_file.read()
        
        payload = {
            "iss": TEAM_ID,
            "exp": int(time.time()) + (180 * 24 * 60 * 60),
            "iat": int(time.time()),
        }

        token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": KEY_ID})
        return jsonify({"token": token})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@apple_music_bp.route("/apple-music-token", methods=["GET"])
def get_apple_music_token():
    """Returns the Apple Music API token."""
    token = generate_apple_music_token()
    return jsonify({"token": token})
