from flask import Blueprint, request, jsonify
import requests
import os
import psycopg2
from datetime import datetime

charts_bp = Blueprint("charts", __name__)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "billboard-charts-api.p.rapidapi.com"
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

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
        data = response.json()
        store_chart_data(data)
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

def store_chart_data(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    title = data.get("title")
    week = data.get("week")
    
    cursor.execute("SELECT * FROM charts WHERE title = %s AND week = %s", (title, week))
    existing_record = cursor.fetchone()
    
    if not existing_record:
        cursor.execute("INSERT INTO charts (title, week, data) VALUES (%s, %s, %s)", (title, week, json.dumps(data)))
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
    return fetch_api(f"/chart.php?id={chart_id}&week={historical_week}")
