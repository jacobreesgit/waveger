from flask import Blueprint, request, jsonify
import requests
import os
import json
from datetime import datetime
from db import get_db_connection

charts_bp = Blueprint("charts", __name__)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "billboard-charts-api.p.rapidapi.com"

def fetch_api(endpoint, chart_id=None, historical_week=None):
    conn = get_db_connection() 
    cursor = conn.cursor()
    
    if chart_id and historical_week:
        cursor.execute("SELECT data FROM charts WHERE title = %s AND week = %s", (chart_id, historical_week))
        existing_record = cursor.fetchone()
        
        if existing_record:
            cursor.close()
            conn.close()
            return {
                "source": "database",
                "data": json.loads(existing_record[0]) if isinstance(existing_record[0], str) else existing_record[0]
            }

    if not RAPIDAPI_KEY:
        return {"error": "Missing API key"}, 500

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    url = f"https://{RAPIDAPI_HOST}{endpoint}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if chart_id and historical_week:
            store_chart_data(data, chart_id, historical_week)
        
        return {
            "source": "api",
            "data": data
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500

def store_chart_data(data, chart_id, historical_week):
    """Stores chart data in PostgreSQL if it doesn't already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM charts WHERE title = %s AND week = %s", (chart_id, historical_week))
    existing_record = cursor.fetchone()
    
    if not existing_record:
        cursor.execute("INSERT INTO charts (title, week, data) VALUES (%s, %s, %s)", (chart_id, historical_week, json.dumps(data)))
        conn.commit()
    
    cursor.close()
    conn.close()

@charts_bp.route("/top-charts", methods=["GET"])
def get_top_charts():
    return fetch_api("/top-charts.php")

@charts_bp.route("/chart", methods=["GET"])
def get_chart_details():
    chart_id = request.args.get("id", "hot-100")
    historical_week = request.args.get("week", datetime.today().strftime('%Y-%m-%d'))
    range_param = request.args.get("range", "1-10")  # Default to first 10 entries

    response = fetch_api(f"/chart.php?id={chart_id}&week={historical_week}", chart_id, historical_week)
    
    if response.status_code != 200:
        return response  # Return error response if any

    data = response.get_json()
    if "data" in data and isinstance(data["data"], dict) and "songs" in data["data"]:
        try:
            start, end = map(int, range_param.split("-"))
            data["data"]["songs"] = data["data"]["songs"][start-1:end]  # Slice the song list
        except ValueError:
            return jsonify({"error": "Invalid range format. Use 'start-end' format."}), 400

    return jsonify(data)
