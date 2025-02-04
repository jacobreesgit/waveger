from flask import Blueprint, request, jsonify
import requests
import os

charts_bp = Blueprint("charts", __name__)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "billboard-charts-api.p.rapidapi.com"

@charts_bp.route("/charts-categories", methods=["GET"])
def get_chart_categories():
    return fetch_api("/charts-categories.php")

@charts_bp.route("/charts", methods=["GET"])
def get_charts_by_category():
    category_id = request.args.get("id")
    if not category_id:
        return jsonify({"error": "Missing category_id parameter"}), 400
    return fetch_api(f"/charts.php?id={category_id}")

@charts_bp.route("/chart", methods=["GET"])
def get_chart_details():
    chart_id = request.args.get("id")
    historical_date = request.args.get("date", "")
    if not chart_id:
        return jsonify({"error": "Missing chart_id parameter"}), 400
    return fetch_api(f"/chart.php?id={chart_id}&date={historical_date}")

@charts_bp.route("/hot-100", methods=["GET"])
def get_hot_100():
    return fetch_api("/hot-100.php")

@charts_bp.route("/global-200", methods=["GET"])
def get_global_200():
    return fetch_api("/200.php")

@charts_bp.route("/popular-albums", methods=["GET"])
def get_popular_albums():
    return fetch_api("/200.php")

@charts_bp.route("/top-artists", methods=["GET"])
def get_top_artists():
    return fetch_api("/artist-100.php")

@charts_bp.route("/tiktok-top-songs", methods=["GET"])
def get_tiktok_top_songs():
    return fetch_api("/tiktok-50.php")

@charts_bp.route("/top-charts", methods=["GET"])
def get_top_charts():
    return fetch_api("/top-charts.php")

def fetch_api(endpoint):
    if not RAPIDAPI_KEY:
        return jsonify({"error": "Missing API key"}), 500

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    url = f"https://{RAPIDAPI_HOST}{endpoint}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
