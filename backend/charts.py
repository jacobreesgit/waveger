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

        logging.debug(f"Database query result for {chart_id} on {historical_week}: {existing_record}")

        if existing_record is None:
            logging.debug(f"No cache found for {chart_id} on {historical_week}. Fetching from API.")
        elif not isinstance(existing_record, tuple) or len(existing_record) == 0:
            logging.error(f"Unexpected database format: {existing_record}")
            return {"error": "Unexpected database format"}, 500
        else:
            try:
                json_data = existing_record[0]
                data = json.loads(json_data) if isinstance(json_data, str) else json_data
                logging.debug(f"Returning cached chart data for {chart_id} on {historical_week}")
                return {
                    "source": "database",
                    "data": data
                }
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing database data for {chart_id} on {historical_week}: {e}")
                return {"error": "Corrupt data in database"}, 500

    # If no record, fall back to API
    if not RAPIDAPI_KEY:
        logging.error("Missing API key")
        return {"error": "Missing API key"}, 500

def store_chart_data(data, chart_id, historical_week):
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
    range_param = request.args.get("range", "1-10")

    logging.debug(f"Request for chart: {chart_id}, Week: {historical_week}, Range: {range_param}")

    response = fetch_api(f"/chart.php?id={chart_id}&week={historical_week}", chart_id, historical_week)

    if isinstance(response, tuple):
        return jsonify(response[0]), response[1]

    data = response["data"]

    if "songs" in data and isinstance(data["songs"], list):
        try:
            start, end = map(int, range_param.split("-"))
            data["songs"] = data["songs"][start-1:end]
        except ValueError:
            logging.error("Invalid range format")
            return jsonify({"error": "Invalid range format. Use 'start-end' format."}), 400

    return jsonify(response)
