from flask import Flask, request, jsonify
import billboard
import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta

app = Flask(__name__)

# Database connection configuration
DB_CONNECTION = "postgresql://wavegerdatabase_user:cafvWdvIlSiZbBe7hX9uXki02Bv3UcP1@dpg-cu8g5bggph6c73cpbaj0-a.frankfurt-postgres.render.com/wavegerdatabase"


def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    return psycopg2.connect(DB_CONNECTION)


def normalize_week_date(week):
    """Adjust non-Tuesday dates to the nearest Tuesday."""
    date = datetime.strptime(week, "%Y-%m-%d")
    offset = (1 - date.weekday()) % 7  # Tuesday is weekday 1
    return (date + timedelta(days=offset)).strftime("%Y-%m-%d")


@app.route("/fetch-chart", methods=["GET"])
def fetch_chart():
    week = request.args.get("week", None)
    if week:
        try:
            week = normalize_week_date(week)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    else:
        week = billboard.ChartData("hot-100").date

    try:
        chart = billboard.ChartData("hot-100", date=week)
        conn = get_db_connection()
        cur = conn.cursor()
        
        table_name = f"hot_100_{week.replace('-', '_')}"
        create_table_query = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {table} (
                rank INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                last_week INTEGER,
                peak_pos INTEGER,
                weeks_on_chart INTEGER
            )
        """).format(table=sql.Identifier(table_name))
        cur.execute(create_table_query)

        for entry in chart:
            insert_query = sql.SQL("""
                INSERT INTO {table} (rank, title, artist, last_week, peak_pos, weeks_on_chart)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (rank) DO UPDATE SET
                    title = EXCLUDED.title,
                    artist = EXCLUDED.artist,
                    last_week = EXCLUDED.last_week,
                    peak_pos = EXCLUDED.peak_pos,
                    weeks_on_chart = EXCLUDED.weeks_on_chart
            """).format(table=sql.Identifier(table_name))
            cur.execute(insert_query, (
                entry.rank, entry.title, entry.artist,
                entry.lastWeek, entry.peakPos, entry.weeks
            ))

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({
            "message": "Chart data fetched and stored successfully.",
            "chart_week": chart.date
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/list-chart-tables", methods=["GET"])
def list_chart_tables():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'hot_100_%' ORDER BY table_name DESC")
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"tables": tables})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get-chart/<week>", methods=["GET"])
def get_chart(week):
    try:
        week = normalize_week_date(week)
        table_name = f"hot_100_{week.replace('-', '_')}"

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql.SQL("SELECT * FROM {table}").format(table=sql.Identifier(table_name)))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return jsonify({"error": f"No data found for week {week}."}), 404

        chart_data = [
            {"rank": row[0], "title": row[1], "artist": row[2], "last_week": row[3], "peak_pos": row[4], "weeks_on_chart": row[5]}
            for row in rows
        ]
        return jsonify({"chart_week": week, "data": chart_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
