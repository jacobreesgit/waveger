from __init__ import app, bcrypt, limiter
from flask import jsonify, request
from charts import charts_bp
from apple_music import apple_music_bp
from auth import auth_bp
from favourites import favourites_bp
from admin import admin_bp
from predictions import predictions_bp  # Import the new predictions blueprint
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register blueprints
app.register_blueprint(charts_bp, url_prefix="/api")
app.register_blueprint(apple_music_bp, url_prefix="/api")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(favourites_bp, url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(predictions_bp, url_prefix="/api")  # Register the new blueprint

# Rest of the existing code...