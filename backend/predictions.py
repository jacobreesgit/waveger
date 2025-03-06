from flask import Blueprint, jsonify
from __init__ import limiter, get_real_ip

# Create a minimal blueprint
predictions_bp = Blueprint("predictions", __name__)

# Add a simple test route to verify it works
@predictions_bp.route("/predictions/test", methods=["GET"])
@limiter.limit("30 per minute", key_func=get_real_ip)
def test_prediction_route():
    """Test route to verify the predictions blueprint is working"""
    return jsonify({
        "status": "success",
        "message": "Predictions blueprint is working"
    }), 200