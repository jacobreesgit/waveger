from flask import Flask, request, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)

# API Configuration
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "billboard-api2.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}/hot-100"

@app.route('/')
def home():
    return "Welcome to the Billboard Hot 100 API Proxy!"

@app.route('/hot-100', methods=['GET'])
def get_hot_100():
    # Use today's date as default
    today_date = datetime.today().strftime('%Y-%m-%d')
    date = request.args.get("date", today_date)  # Default to today's date
    range_param = request.args.get("range", "1-10")  # Default range

    # Call Billboard API
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY,
    }
    query_params = {"date": date, "range": range_param}

    try:
        response = requests.get(BASE_URL, headers=headers, params=query_params)
        response.raise_for_status()  # Raise an error for HTTP issues
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
