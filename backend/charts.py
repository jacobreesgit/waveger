from flask import Blueprint, request, jsonify
import requests
import json
from datetime import datetime, timedelta
from db import get_db_connection
import os
from bs4 import BeautifulSoup

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
            stored_data = db_result["data"]
            if isinstance(stored_data, str):  # Ensure it's a string before parsing
                stored_data = json.loads(stored_data)

            return jsonify({
                "source": "database",
                "content": stored_data.get("content", []),  # Avoid KeyError if "content" is missing
                "info": {
                    "category": "Billboard",
                    "chart": "HOT 100",
                    "date": aligned_tuesday,
                    "source": "database"
                }
            })

        # If not found in the database, fetch from API
        headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": RAPIDAPI_HOST}
        response = requests.get(BASE_URL, headers=headers, params={"date": aligned_tuesday, "range": range_param})
        response.raise_for_status()
        
        api_data = response.json()
        cursor.execute("INSERT INTO hot_100_data (date, range, data) VALUES (%s, %s, %s)", (aligned_tuesday, range_param, json.dumps(api_data)))
        conn.commit()

        return jsonify({
            "source": "api",
            "content": api_data.get("content", []),
            "info": {
                "category": "Billboard",
                "chart": "HOT 100",
                "date": aligned_tuesday,
                "source": "api"
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@charts_bp.route("/backup-hot-100", methods=["GET"])
def backup_hot_100():
    date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))

    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    url = f"https://www.billboard.com/charts/hot-100/{date}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
                      '(KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return jsonify({'error': 'Could not retrieve data from Billboard.'}), 500

    soup = BeautifulSoup(response.text, 'html.parser')

    rows = soup.find_all('div', class_='o-chart-results-list-row-container')
    if not rows:
        return jsonify({'error': 'Could not parse chart data. The website structure might have changed.'}), 500

    chart_data = []
    for row in rows:
        pos_tag = row.find('span', class_='c-label')
        position = pos_tag.get_text(strip=True) if pos_tag else None

        title_tag = row.find('h3', id='title-of-a-story')
        if not title_tag:
            title_tag = row.find('h3', class_='c-title')
        title = title_tag.get_text(strip=True) if title_tag else None

        labels = row.find_all('span', class_='c-label')
        artist = labels[1].get_text(strip=True) if len(labels) > 1 else None

        if position and title and artist:
            chart_data.append({
                'position': position,
                'title': title,
                'artist': artist
            })

    return jsonify({
        'source': 'web_scraping',
        'date': date,
        'chart': chart_data
    })
