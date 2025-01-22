import os
import psycopg2
import billboard
from flask import Flask, jsonify
from datetime import datetime, timedelta
from flask_cors import CORS  # Import CORS

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

def get_db_connection():
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://wavegerdatabase_user:cafvWdvIlSiZbBe7hX9uXki02Bv3UcP1@dpg-cu8g5bggph6c73cpbaj0-a.frankfurt-postgres.render.com/wavegerdatabase")
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

@app.route('/')
def get_hot_100():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the table is empty
    cursor.execute("SELECT COUNT(*) FROM hot_100;")
    count = cursor.fetchone()[0]

    # If the table is empty, fetch data from Billboard and populate the table
    if count == 0:
        print("Fetching new data from Billboard...")  # Print message to console
        chart = billboard.ChartData('hot-100')
        for song in chart:
            cursor.execute("""
            INSERT INTO hot_100 (rank, title, artist, weeks_on_chart, last_updated)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (rank) DO UPDATE
            SET title = %s, artist = %s, weeks_on_chart = %s, last_updated = CURRENT_TIMESTAMP;
            """, (song.rank, song.title, song.artist, song.weeks, song.title, song.artist, song.weeks))
        conn.commit()
        print("New data has been fetched and inserted into the database.")
    else:
        print("Data is already in the database. Fetching data from the database...")  # Print message if no insertion is done

    # Fetch the data from the database (regardless of whether it was updated)
    cursor.execute("SELECT * FROM hot_100 ORDER BY rank;")
    rows = cursor.fetchall()

    result = [{
        'rank': row[0],
        'title': row[1],
        'artist': row[2],
        'weeks_on_chart': row[3],
        'last_updated': row[4].strftime('%B %d, %Y at %I:%M %p')  # Format datetime
    } for row in rows]

    cursor.close()
    conn.close()

    return jsonify(result)

@app.route('/update-chart')
def update_chart():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch new Billboard Hot 100 data and update the table
    print("Fetching new data from Billboard...")  # Print message to console
    chart = billboard.ChartData('hot-100')
    for song in chart:
        cursor.execute("""
        INSERT INTO hot_100 (rank, title, artist, weeks_on_chart, last_updated)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (rank) DO UPDATE
        SET title = %s, artist = %s, weeks_on_chart = %s, last_updated = CURRENT_TIMESTAMP;
        """, (song.rank, song.title, song.artist, song.weeks, song.title, song.artist, song.weeks))
    conn.commit()

    print("New data has been fetched and updated in the database.")  # Print message to console

    cursor.close()
    conn.close()

    return jsonify({"message": "Billboard Hot 100 data has been updated successfully!"})

if __name__ == "__main__":
    # Set the port to 5002
    app.run(debug=True, host='0.0.0.0', port=5002)
