from flask import Blueprint, request, jsonify
import requests
import os
import psycopg2
import json
from datetime import datetime
import logging
from __init__ import limiter, get_real_ip

charts_bp = Blueprint("charts", __name__)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "billboard-charts-api.p.rapidapi.com"
DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(level=logging.DEBUG)

if not RAPIDAPI_KEY:
    logging.error("RAPIDAPI_KEY is missing! API requests will fail.")
    raise RuntimeError("RAPIDAPI_KEY is not set. Check your environment variables.")

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        raise

def fetch_api(endpoint, chart_id=None, historical_week=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # For top-charts endpoint
            if endpoint == "/top-charts.php":
                logging.debug("Checking database for top charts")
                cursor.execute("SELECT data FROM top_charts ORDER BY created_at DESC LIMIT 1")
                existing_record = cursor.fetchone()
                
                if existing_record:
                    logging.debug("Found top charts in database")
                    # Handle the data correctly based on its type
                    data = existing_record[0]
                    if isinstance(data, str):
                        data = json.loads(data)
                    return jsonify({
                        "source": "database",
                        "data": data
                    })
                logging.debug("No top charts found in database")
            
            # For individual charts
            elif chart_id and historical_week:
                cursor.execute("SELECT data FROM charts WHERE title = %s AND week = %s", (chart_id, historical_week))
                existing_record = cursor.fetchone()
                
                if existing_record:
                    data = existing_record[0]
                    if isinstance(data, str):
                        data = json.loads(data)
                    return jsonify({
                        "source": "database",
                        "data": data
                    })
            
            # Fetch from API if not found in DB
            if not RAPIDAPI_KEY:
                return jsonify({"error": "Missing API key"}), 500

            headers = {
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": RAPIDAPI_HOST
            }
            url = f"https://{RAPIDAPI_HOST}{endpoint}"
            
            logging.debug(f"Fetching from API: {url}")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            api_data = response.json()
            logging.debug(f"API response received: {api_data}")
            
            # Store in appropriate table
            if endpoint == "/top-charts.php":
                logging.debug("Storing top charts in database")
                # Store the data as a JSON string
                cursor.execute(
                    "INSERT INTO top_charts (data) VALUES (%s)",
                    (json.dumps(api_data),)
                )
                conn.commit()
                logging.debug("Top charts stored successfully")
            elif chart_id and historical_week:
                store_chart_data(api_data, chart_id, historical_week)
            
            return jsonify({
                "source": "api",
                "data": api_data
            })
        except Exception as e:
            logging.error(f"Error in fetch_api: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        logging.error(f"Unhandled error in fetch_api: {e}")
        return jsonify({"error": str(e)}), 500

def store_chart_data(data, chart_id, historical_week):
    """Stores chart data in PostgreSQL if it doesn't already exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM charts WHERE title = %s AND week = %s", (chart_id, historical_week))
        existing_record = cursor.fetchone()
        
        if not existing_record:
            cursor.execute("INSERT INTO charts (title, week, data) VALUES (%s, %s, %s)", 
                         (chart_id, historical_week, json.dumps(data)))
            conn.commit()
        
        cursor.close()
        conn.close()
    except Exception as e:
        logging.error(f"Error storing chart data: {e}")
        raise

@charts_bp.route("/top-charts", methods=["GET"])
@limiter.limit("100 per minute", key_func=get_real_ip)  # Add rate limit: 100 requests per minute
def get_top_charts():
    try:
        logging.debug("Top charts endpoint called")
        return fetch_api("/top-charts.php")
    except Exception as e:
        logging.error(f"Error in get_top_charts: {e}")
        return jsonify({"error": str(e)}), 500

@charts_bp.route("/chart", methods=["GET"])
@limiter.limit("200 per minute", key_func=get_real_ip)  # Add rate limit: 200 requests per minute
def get_chart_details():
    try:
        chart_id = request.args.get("id", "hot-100")
        historical_week = request.args.get("week", datetime.today().strftime('%Y-%m-%d'))
        range_param = request.args.get("range", "1-10")  # Default to first 10 entries

        response = fetch_api(f"/chart.php?id={chart_id}&week={historical_week}", chart_id, historical_week)
        
        if isinstance(response, tuple) and response[1] != 200:
            return response  # Return error response if any

        data = response.get_json()
        if "data" in data and isinstance(data["data"], dict) and "songs" in data["data"]:
            try:
                start, end = map(int, range_param.split("-"))
                data["data"]["songs"] = data["data"]["songs"][start-1:end]  # Slice the song list
            except ValueError:
                return jsonify({"error": "Invalid range format. Use 'start-end' format."}), 400

        return jsonify(data)
    except Exception as e:
        logging.error(f"Error in get_chart_details: {e}")
        return jsonify({"error": str(e)}), 500