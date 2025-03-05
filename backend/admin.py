from flask import Blueprint, jsonify, request
from __init__ import limiter, get_real_ip
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)

# Secret key for admin operations - must be set in Render environment variables
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY")

@admin_bp.route("/reset-rate-limiter", methods=["POST"])
def reset_rate_limiter():
    """Reset all rate limits on the server.
    Requires X-Admin-Key header with correct admin secret."""
    # Check for secret key in header
    auth_header = request.headers.get("X-Admin-Key")
    
    # Log attempt with IP address for security
    client_ip = get_real_ip()
    logger.info(f"Rate limiter reset attempt from IP: {client_ip}")
    
    if not ADMIN_SECRET_KEY:
        logger.error("ADMIN_SECRET_KEY not set in environment variables")
        return jsonify({"error": "Server misconfiguration: Admin key not set"}), 500
    
    if not auth_header or auth_header != ADMIN_SECRET_KEY:
        logger.warning(f"Unauthorized rate limiter reset attempt from {client_ip}")
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Reset the limiter
        limiter.reset()
        logger.info(f"Rate limiter reset successfully by {client_ip}")
        return jsonify({
            "success": True, 
            "message": "Rate limiter reset successfully"
        }), 200
    except Exception as e:
        logger.error(f"Error resetting rate limiter: {e}")
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500