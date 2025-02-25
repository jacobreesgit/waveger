from __init__ import app, bcrypt
from charts import charts_bp
from apple_music import apple_music_bp
from auth import auth_bp

# Register blueprints
app.register_blueprint(charts_bp, url_prefix="/api")
app.register_blueprint(apple_music_bp, url_prefix="/api")
app.register_blueprint(auth_bp, url_prefix="/api/auth")

# Add this to app.py after registering blueprints
@app.route("/api/test-rate-limit", methods=["GET"])
@limiter.limit("3 per minute")
def test_rate_limit():
    return jsonify({"status": "ok", "message": "Rate limit test endpoint"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)