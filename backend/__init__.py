from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import os
import logging

# Initialize Flask app
app = Flask(__name__)

# Initialize Bcrypt
bcrypt = Bcrypt(app)

# Allow requests from frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")
if not JWT_SECRET_KEY:
    logging.error("JWT_SECRET_KEY is missing! Authentication is not secure.")
    raise RuntimeError("JWT_SECRET_KEY must be set in environment variables.")

app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
jwt = JWTManager(app)