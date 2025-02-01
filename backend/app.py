from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# API Configuration
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "billboard-api2.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}/hot-100"


# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

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
    input_date = datetime.strptime(input_date, '%Y-%m-%d')
    days_since_tuesday = (input_date.weekday() - 1) % 7  # Tuesday is weekday 1
    last_tuesday = input_date - timedelta(days=days_since_tuesday)
    return last_tuesday.strftime('%Y-%m-%d')

@app.route('/')
def home():
    """Provides a detailed HTML explanation of the API usage."""
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <title>Billboard Hot 100 API Proxy</title>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
          h1 { colour: #2c3e50; }
          ul { list-style-type: square; }
          li { margin-bottom: 10px; }
        </style>
      </head>
      <body>
        <h1>Welcome to the Billboard Hot 100 API Proxy!</h1>
        <p>This API proxy allows you to retrieve Billboard Hot 100 data based on a specified date and range.</p>
        <h2>Usage</h2>
        <ul>
          <li><strong>/hot-100</strong> - Endpoint to retrieve chart data.</li>
        </ul>
        <h2>Parameters</h2>
        <ul>
          <li><strong>date</strong>: The date (in YYYY-MM-DD format) for which you wish to retrieve chart data. If omitted, today’s date is used.</li>
          <li><strong>range</strong>: The range of chart positions to retrieve (for example, "1-10"). If omitted, the default range "1-10" is used.</li>
        </ul>
        <h2>How it works</h2>
        <ul>
          <li>The provided date is aligned to the most recent Tuesday.</li>
          <li>If the data for that date and range is already cached in our PostgreSQL database, it is returned directly.</li>
          <li>If not, the data is fetched from the Billboard API and then stored in the database for future requests.</li>
        </ul>
      </body>
    </html>
    """
    return html

@app.route('/hot-100', methods=['GET'])
def get_hot_100():
    # Parse user-provided date; use today's date if not provided or empty
    today_date = datetime.today().strftime('%Y-%m-%d')
    requested_date = request.args.get("date", "").strip()
    if not requested_date:
        requested_date = today_date

    range_param = request.args.get("range", "1-10")  # Default range

    # Validate date format
    try:
        datetime.strptime(requested_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # Get the most recent Tuesday for the requested date
    aligned_tuesday = get_most_recent_tuesday(requested_date)

    conn = None
    cursor = None

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
            stored_data = db_result["data"]
            # If stored_data is a string, parse it as JSON
            if isinstance(stored_data, str):
                stored_data = json.loads(stored_data)
            content = stored_data["content"]
            return jsonify({
                "source": "database",
                "content": content,
                "info": {
                    "category": "Billboard",
                    "chart": "HOT 100",
                    "date": aligned_tuesday,
                    "source": "database"
                }
            })

        # Data not in database, fetch from API
        headers = {
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": RAPIDAPI_KEY,
        }
        query_params = {"date": aligned_tuesday, "range": range_param}

        response = requests.get(BASE_URL, headers=headers, params=query_params)
        response.raise_for_status()  # Raise an error for HTTP issues
        api_data = response.json()

        # Store the data in the database using json.dumps for serialisation
        cursor.execute(
            """
            INSERT INTO hot_100_data (date, range, data)
            VALUES (%s, %s, %s)
            """,
            (aligned_tuesday, range_param, json.dumps(api_data)),
        )
        conn.commit()

        content = api_data["content"]
        return jsonify({
            "source": "api",
            "content": content,
            "info": {
                "category": "Billboard",
                "chart": "HOT 100",
                "date": aligned_tuesday,
                "source": "api"
            }
        })
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Database or server error: {e}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Register a new user
@app.route("/api/users", methods=["POST"])
def register_user():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        hashed_password = generate_password_hash(data["password"])

        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (data["username"], data["email"], hashed_password),
        )
        user_id = cursor.fetchone()["id"]
        conn.commit()

        return jsonify({"message": "User registered successfully", "id": user_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Log in an existing user
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, username, email, password_hash FROM users WHERE username = %s", (data["username"],))
        user = cursor.fetchone()

        if user and check_password_hash(user["password_hash"], data["password"]):
            return jsonify({
                "message": "Login successful",
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"]  # 🔥 Now includes email
                }
            })

        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Fetch all users (Admin use case)
@app.route("/api/users", methods=["GET"])
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, username, email FROM users")
        users = cursor.fetchall()
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Fetch user by ID
@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            return jsonify(user)
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/favourites", methods=["POST"])
def add_favourite():
    """Add a song to the user's favourites."""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO favourites (user_id, title, artist, rank) VALUES (%s, %s, %s, %s) RETURNING id",
            (data["user_id"], data["title"], data["artist"], data["rank"]),
        )
        favourite_id = cursor.fetchone()["id"]
        conn.commit()
        return jsonify({"message": "Song added to favourites!", "id": favourite_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/favourites/<int:user_id>", methods=["GET"])
def get_favourites(user_id):
    """Retrieve a user's favourite songs."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, title, artist, rank FROM favourites WHERE user_id = %s", (user_id,))
        favourites = cursor.fetchall()
        return jsonify(favourites)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
