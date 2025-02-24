from __init__ import app, bcrypt
from charts import charts_bp
from apple_music import apple_music_bp
from auth import auth_bp

CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Register blueprints
app.register_blueprint(charts_bp, url_prefix="/api")
app.register_blueprint(apple_music_bp, url_prefix="/api")
app.register_blueprint(auth_bp, url_prefix="/api/auth")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)