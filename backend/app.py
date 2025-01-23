import os
import psycopg2
import billboard
from flask import Flask, jsonify, request
from datetime import datetime
import traceback
from flask_cors import CORS  # Import CORS



app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

def get_db_connection():
    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        "postgresql://wavegerdatabase_user:cafvWdvIlSiZbBe7hX9uXki02Bv3UcP1@dpg-cu8g5bggph6c73cpbaj0-a.frankfurt-postgres.render.com/wavegerdatabase"
    )
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def create_week_table(conn, cursor, week_id):
    """Create a table for the specified week if it doesn't exist."""
    table_name = f"hot_100_{week_id}"
    try:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                rank INT PRIMARY KEY,
                title TEXT,
                artist TEXT,
                weeks_on_chart INT
            );
        """)
        conn.commit()  # Commit the table creation immediately
        print(f"Table '{table_name}' ensured.")
    except Exception as e:
        conn.rollback()
        print(f"Error ensuring table '{table_name}': {e}")
        raise e

@app.route('/hot-100', methods=['GET'])
def get_hot_100():
    week = request.args.get('week', 'current')
    conn = get_db_connection()
    cursor = conn.cursor()

    if week == 'current':
        # Fetch current chart data
        chart = billboard.ChartData('hot-100')
        week = chart.date  # Use the chart's published date as the week identifier
    else:
        try:
            datetime.strptime(week, '%Y-%m-%d')  # Validate week format
        except ValueError:
            return jsonify({"error": "Invalid week format. Use YYYY-MM-DD."}), 400

    # Create or fetch the table for the specified week
    table_name = f"hot_100_{week.replace('-', '_')}"
    create_week_table(conn, cursor, week.replace('-', '_'))

    try:
        # Check if the table is already populated
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]

        if count == 0:
            # Fetch Billboard data and populate the table
            chart = billboard.ChartData('hot-100', date=week)
            for song in chart:
                cursor.execute(f"""
                    INSERT INTO {table_name} (rank, title, artist, weeks_on_chart)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (rank) DO UPDATE
                    SET title = %s, artist = %s, weeks_on_chart = %s;
                """, (song.rank, song.title, song.artist, song.weeks, song.title, song.artist, song.weeks))
            conn.commit()

        # Fetch the data for the specified week from the database
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY rank;")
        rows = cursor.fetchall()

        result = [{
            'rank': row[0],
            'title': row[1],
            'artist': row[2],
            'weeks_on_chart': row[3]
        } for row in rows]

    except Exception as e:
        conn.rollback()
        print(f"Unexpected error: {e}")
        traceback.print_exc()  # Log the full error stack trace
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5002)
