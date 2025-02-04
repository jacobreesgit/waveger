from flask import Blueprint, request, jsonify
import requests
import os

charts_bp = Blueprint("charts", __name__)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "billboard-charts-api.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}/hot-100.php"

@charts_bp.route("/hot-100", methods=["GET"])
def get_hot_100():
    if not RAPIDAPI_KEY:
        return jsonify({"error": "Missing API key"}), 500

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(BASE_URL, headers=headers)
        response.raise_for_status()
        data = response.json()

        return jsonify({
            "source": "api",
            "title": data.get("title", "Billboard Hot 100"),
            "info": data.get("info", ""),
            "week": data.get("week", ""),
            "songs": data.get("songs", [])
        })
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
