from flask import Blueprint, request, jsonify
import requests
import os
import json
import logging
from datetime import datetime
from db import get_db_connection

charts_bp = Blueprint("charts", __name__)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "billboard-charts-api.p.rapidapi.com"

logging.basicConfig(level=logging.DEBUG)

def fetch_api(endpoint, chart_id=None, historical_week=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    if chart_id and historical_week:
        cursor.execute("SELECT data FROM charts WHERE title = %s AND week = %s", (chart_id, historical_week))
        existing_record = cursor.fetchone()

        if existing_record:
            try:
                # Properly parse JSON data
                data = json.loads(existing_record[0])  # existing_record[0] contains the JSON string

                logging.debug(f"Returning cached chart data for {chart_id} on {historical_week}")
                return {
                    "source": "database",
                    "data": data
                }
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing database data for {chart_id} on {historical_week}: {e}")
                return {"error": "Corrupt data in database"}, 500

    # If not found in DB, fetch from API
    if not RAPIDAPI_KEY:
        logging.error("Missing API key")
        return {"error": "Missing API key"}, 500

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    url = f"https://{RAPIDAPI_HOST}{endpoint}"
    logging.debug(f"Fetching data from API: {url}")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Store API response in DB before returning
        if chart_id and historical_week:
            store_chart_data(data, chart_id, historical_week)

        return {
            "source": "api",
            "data": data
        }
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
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
        logging.debug(f"Stored chart data for {chart_id} on {historical_week}")

    cursor.close()
    conn.close()

@charts_bp.route("/chart", methods=["GET"])
def get_chart_details():
    chart_id = request.args.get("id", "hot-100")
    historical_week = request.args.get("week", datetime.today().strftime('%Y-%m-%d'))
    range_param = request.args.get("range", "1-10")  # Default to first 10 entries

    logging.debug(f"Request for chart: {chart_id}, Week: {historical_week}, Range: {range_param}")

    response = fetch_api(f"/chart.php?id={chart_id}&week={historical_week}", chart_id, historical_week)

    # Fix: Ensure correct handling of error responses
    if isinstance(response, tuple):  # Error responses are returned as (dict, status_code)
        return jsonify(response[0]), response[1]

    data = response["data"]

    if "songs" in data and isinstance(data["songs"], list):
        try:
            start, end = map(int, range_param.split("-"))
            data["songs"] = data["songs"][start-1:end]  # Slice the song list
        except ValueError:
            logging.error("Invalid range format")
            return jsonify({"error": "Invalid range format. Use 'start-end' format."}), 400

    return jsonify(response)
