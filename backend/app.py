from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
import logging

from charts import charts_bp
from apple_music import apple_music_bp  
from users import users_bp

app = Flask(__name__)

# Allow requests from frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")
if not JWT_SECRET_KEY:
    logging.error("JWT_SECRET_KEY is missing! Authentication is not secure.")
    raise RuntimeError("JWT_SECRET_KEY must be set in environment variables.")

app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(charts_bp, url_prefix="/api")
app.register_blueprint(apple_music_bp, url_prefix="/api") 
app.register_blueprint(users_bp, url_prefix="/api")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
