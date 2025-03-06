from __init__ import app, bcrypt, limiter
from flask import jsonify, request
from charts import charts_bp
from apple_music import apple_music_bp
from auth import auth_bp
from favourites import favourites_bp
from admin import admin_bp  # Import the new admin blueprint
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register blueprints
app.register_blueprint(charts_bp, url_prefix="/api")
app.register_blueprint(apple_music_bp, url_prefix="/api")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(favourites_bp, url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/api/admin")  # Register admin blueprint

# Add this to app.py after registering blueprints
@app.route("/api/test-limiter", methods=["GET"])
@limiter.limit("3 per minute")
def test_rate_limit():
    # Log the request details for debugging
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logger.info(f"Rate limit test accessed by: {client_ip}")
    
    # Include the client IP in the response for troubleshooting
    return jsonify({
        "status": "ok", 
        "message": "Rate limit test endpoint", 
        "client_ip": client_ip
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)