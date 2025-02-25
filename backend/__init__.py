from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from flask_cors import CORS  
from flask_bcrypt import Bcrypt
from datetime import timedelta
import os
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize Flask app
app = Flask(__name__)

# Configure logging more explicitly
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bcrypt
bcrypt = Bcrypt(app)

# Allow requests from frontend with credentials support
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Comprehensive JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")
if not JWT_SECRET_KEY:
    logging.error("JWT_SECRET_KEY is missing! Authentication is not secure.")
    raise RuntimeError("JWT_SECRET_KEY must be set in environment variables.")

# Extensive JWT Configuration
app.config.update(
    JWT_SECRET_KEY=JWT_SECRET_KEY,
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=24),
    JWT_TOKEN_LOCATION=["headers"],
    JWT_HEADER_NAME="Authorization",
    JWT_HEADER_TYPE="Bearer",
    PROPAGATE_EXCEPTIONS=True,
    
    # Debug configurations
    JWT_ERROR_MESSAGE_KEY="msg",  # Helps with error message consistency
)

# Initialize JWT Manager with additional error handling
jwt = JWTManager(app)

# Optional: Add error handlers for JWT-related errors
@jwt.invalid_token_loader
def handle_invalid_token(error_message):
    logging.error(f"Invalid token error: {error_message}")
    return {"msg": "Invalid token"}, 422

@jwt.unauthorized_loader
def handle_unauthorized_request(error_message):
    logging.error(f"Unauthorized request: {error_message}")
    return {"msg": "Missing or invalid Authorization header"}, 401

@jwt.expired_token_loader
def handle_expired_token(jwt_header, jwt_payload):
    logging.error(f"Expired token. Header: {jwt_header}, Payload: {jwt_payload}")
    return {"msg": "Token has expired"}, 401

@jwt.needs_fresh_token_loader
def handle_needs_fresh_token():
    logging.error("Fresh token required")
    return {"msg": "Fresh token required"}, 401

@jwt.revoked_token_loader
def handle_revoked_token(jwt_header, jwt_payload):
    logging.error(f"Revoked token. Header: {jwt_header}, Payload: {jwt_payload}")
    return {"msg": "Token has been revoked"}, 401

# Custom function to get the client's real IP address from behind proxies
def get_real_ip():
    """Get the real IP address, accounting for proxies and load balancers."""
    # Check X-Forwarded-For header (common for proxies)
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # Get the first address in the chain (client's original IP)
        ip = x_forwarded_for.split(',')[0].strip()
        logging.debug(f"Using X-Forwarded-For IP: {ip}")
        return ip
    
    # Check X-Real-IP header (used by some reverse proxies)
    x_real_ip = request.headers.get('X-Real-IP')
    if x_real_ip:
        logging.debug(f"Using X-Real-IP: {x_real_ip}")
        return x_real_ip
    
    # Fall back to the remote address
    logging.debug(f"Using remote address: {request.remote_addr}")
    return request.remote_addr

# Make sure get_real_ip is available for import in other modules
__all__ = ['app', 'bcrypt', 'limiter', 'get_real_ip', 'jwt']

# Before request logging to debug rate limiting
@app.before_request
def debug_request():
    client_ip = get_real_ip()
    logging.info(f"Request: {request.method} {request.path} from {client_ip}")
    logging.debug(f"Headers: {request.headers}")

# Initialize rate limiter with custom key function
limiter = Limiter(
    app=app,  # Pass app directly here
    key_func=get_real_ip,  # Use our custom function
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window",
    headers_enabled=True,  # Enable rate limit headers in responses
)

# Add rate limit exceeded handler
@app.errorhandler(429)
def ratelimit_handler(e):
    logging.warning(f"Rate limit exceeded: {e.description}")
    return jsonify({
        "error": "Too many requests",
        "message": "Rate limit exceeded. Please try again later."
    }), 429

# Add rate limit headers to responses
@app.after_request
def inject_rate_limit_headers(response):
    try:
        if hasattr(limiter, 'current_limit'):
            window_stats = limiter.get_window_stats(*limiter.current_limit)
            if window_stats:
                response.headers.add('X-RateLimit-Remaining', str(window_stats.remaining))
                response.headers.add('X-RateLimit-Limit', str(window_stats.limit))
                response.headers.add('X-RateLimit-Reset', str(window_stats.reset))
    except Exception as e:
        logging.error(f"Error injecting rate limit headers: {e}")
    
    return response