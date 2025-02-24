from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS  
from flask_bcrypt import Bcrypt
from datetime import timedelta
import os
import logging

# Initialize Flask app
app = Flask(__name__)

# Initialize Bcrypt
bcrypt = Bcrypt(app)

# Allow requests from frontend with credentials support
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")
if not JWT_SECRET_KEY:
    logging.error("JWT_SECRET_KEY is missing! Authentication is not secure.")
    raise RuntimeError("JWT_SECRET_KEY must be set in environment variables.")

app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
jwt = JWTManager(app)

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"
app.config["PROPAGATE_EXCEPTIONS"] = True 