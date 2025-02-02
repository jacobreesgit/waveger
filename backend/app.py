from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os

from auth import auth_bp
from charts import charts_bp
from favourites import favourites_bp

app = Flask(__name__)

# Allow requests from frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "supersecret")
jwt = JWTManager(app)

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(charts_bp, url_prefix="/api")
app.register_blueprint(favourites_bp, url_prefix="/api")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
