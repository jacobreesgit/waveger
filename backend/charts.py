from flask import Blueprint, request, jsonify
import requests
import json
from datetime import datetime, timedelta
from db import get_db_connection
import os

charts_bp = Blueprint("charts", __name__)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "billboard-api2.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}/hot-100"

def get_most_recent_tuesday(input_date):
    input_date = datetime.strptime(input_date, '%Y-%m-%d')
    return (input_date - timedelta(days=(input_date.weekday() - 1) % 7)).strftime('%Y-%m-%d')

@charts_bp.route("/hot-100", methods=["GET"])
def get_hot_100():
    requested_date = request.args.get("date", datetime.today().strftime('%Y-%m-%d'))
    range_param = request.args.get("range", "1-10")

    try:
        datetime.strptime(requested_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    aligned_tuesday = get_most_recent_tuesday(requested_date)
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM hot_100_data WHERE date = %s AND range = %s", (aligned_tuesday, range_param))
        db_result = cursor.fetchone()

        if db_result:
            return jsonify({"source": "database", "content": json.loads(db_result["data"])})

        headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": RAPIDAPI_HOST}
        response = requests.get(BASE_URL, headers=headers, params={"date": aligned_tuesday, "range": range_param})
        response.raise_for_status()
        
        api_data = response.json()
        cursor.execute("INSERT INTO hot_100_data (date, range, data) VALUES (%s, %s, %s)", (aligned_tuesday, range_param, json.dumps(api_data)))
        conn.commit()

        return jsonify({"source": "api", "content": api_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
