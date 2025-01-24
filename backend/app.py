from flask import Flask, request, jsonify
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# API Configuration
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "billboard-api2.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}/hot-100"

# Database Configuration
DATABASE_URL = "postgresql://wavegerdatabase_user:cafvWdvIlSiZbBe7hX9uXki02Bv3UcP1@dpg-cu8g5bggph6c73cpbaj0-a.frankfurt-postgres.render.com/wavegerdatabase"


def get_db_connection():
    """Establishes a connection to the database."""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise


def get_most_recent_tuesday(input_date):
    """Returns the most recent Tuesday on or before the given input date."""
    # Parse the input date
    input_date = datetime.strptime(input_date, '%Y-%m-%d')
    days_since_tuesday = (input_date.weekday() - 1) % 7  # Tuesday is weekday 1
    last_tuesday = input_date - timedelta(days=days_since_tuesday)
    return last_tuesday.strftime('%Y-%m-%d')


@app.route('/')
def home():
    return "Welcome to the Billboard Hot 100 API Proxy!"


@app.route('/hot-100', methods=['GET'])
def get_hot_100():
    # Parse user-provided date or use today's date as default
    today_date = datetime.today().strftime('%Y-%m-%d')
    requested_date = request.args.get("date", today_date)  # Default to today's date
    range_param = request.args.get("range", "1-10")  # Default range

    # Get the most recent Tuesday for the requested date
    aligned_tuesday = get_most_recent_tuesday(requested_date)

    # Check if the data for the aligned Tuesday is already in the database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query the database for the aligned Tuesday's data
        cursor.execute(
            """
            SELECT * FROM hot_100_data
            WHERE date = %s AND range = %s
            """,
            (aligned_tuesday, range_param),
        )
        db_result = cursor.fetchone()

        if db_result:
            # Data exists in the database
            return jsonify({"source": "database", "data": db_result["data"]})

        # Data not in database, fetch from API
        headers = {
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": RAPIDAPI_KEY,
        }
        query_params = {"date": aligned_tuesday, "range": range_param}

        response = requests.get(BASE_URL, headers=headers, params=query_params)
        response.raise_for_status()  # Raise an error for HTTP issues
        api_data = response.json()

        # Store the API data in the database
        cursor.execute(
            """
            INSERT INTO hot_100_data (date, range, data)
            VALUES (%s, %s, %s)
            """,
            (aligned_tuesday, range_param, jsonify(api_data).data.decode()),
        )
        conn.commit()

        return jsonify({"source": "api", "data": api_data})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Database or server error: {e}"}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
