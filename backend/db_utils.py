import psycopg2
import os
import logging
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any

DATABASE_URL = os.getenv("DATABASE_URL")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the PostgreSQL database."""
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def get_or_create_song(song_name: str, artist: str, image_url: Optional[str] = None) -> int:
    """
    Get an existing song ID or create a new song record.
    Returns the song ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if song exists
        cursor.execute(
            "SELECT id FROM songs WHERE song_name = %s AND artist = %s",
            (song_name, artist)
        )
        
        result = cursor.fetchone()
        
        if result:
            # Song exists, return ID
            return result[0]
        
        # Song doesn't exist, insert new record
        cursor.execute(
            """
            INSERT INTO songs (song_name, artist, image_url)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (song_name, artist, image_url)
        )
        
        song_id = cursor.fetchone()[0]
        conn.commit()
        
        return song_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in get_or_create_song: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def update_song_chart_data(
    song_id: int,
    chart_id: str,
    chart_title: str,
    position: int = None,
    peak_position: int = None,
    weeks_on_chart: int = None,
    last_week_position: int = None,
    chart_date: str = None
) -> int:
    """
    Update chart data for a song.
    Returns the song_chart_data ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if record exists
        cursor.execute(
            """
            SELECT id FROM song_chart_data 
            WHERE song_id = %s AND chart_id = %s AND 
                  (chart_date = %s OR (chart_date IS NULL AND %s IS NULL))
            """,
            (song_id, chart_id, chart_date, chart_date)
        )
        
        result = cursor.fetchone()
        
        if result:
            # Update existing record
            cursor.execute(
                """
                UPDATE song_chart_data SET
                chart_title = %s,
                position = COALESCE(%s, position),
                peak_position = COALESCE(%s, peak_position),
                weeks_on_chart = COALESCE(%s, weeks_on_chart),
                last_week_position = COALESCE(%s, last_week_position),
                updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id
                """,
                (
                    chart_title,
                    position,
                    peak_position,
                    weeks_on_chart,
                    last_week_position,
                    result[0]
                )
            )
            
            chart_data_id = cursor.fetchone()[0]
        else:
            # Insert new record
            cursor.execute(
                """
                INSERT INTO song_chart_data
                (song_id, chart_id, chart_title, position, peak_position, 
                 weeks_on_chart, last_week_position, chart_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    song_id,
                    chart_id,
                    chart_title,
                    position,
                    peak_position,
                    weeks_on_chart,
                    last_week_position,
                    chart_date
                )
            )
            
            chart_data_id = cursor.fetchone()[0]
        
        conn.commit()
        return chart_data_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in update_song_chart_data: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def get_song_with_chart_data(song_id: int, chart_id: str = None) -> Dict[str, Any]:
    """
    Get song data with chart information.
    If chart_id is provided, include specific chart data.
    Returns a dict with song and chart data.
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        if chart_id:
            # Get song with specific chart data
            cursor.execute(
                """
                SELECT 
                    s.id, 
                    s.song_name, 
                    s.artist, 
                    s.image_url,
                    cd.chart_id,
                    cd.chart_title,
                    cd.position,
                    cd.peak_position,
                    cd.weeks_on_chart,
                    cd.last_week_position,
                    cd.chart_date
                FROM songs s
                LEFT JOIN song_chart_data cd ON s.id = cd.song_id AND cd.chart_id = %s
                WHERE s.id = %s
                """,
                (chart_id, song_id)
            )
        else:
            # Get song with all chart data
            cursor.execute(
                """
                SELECT 
                    s.id, 
                    s.song_name, 
                    s.artist, 
                    s.image_url,
                    cd.chart_id,
                    cd.chart_title,
                    cd.position,
                    cd.peak_position,
                    cd.weeks_on_chart,
                    cd.last_week_position,
                    cd.chart_date
                FROM songs s
                LEFT JOIN song_chart_data cd ON s.id = cd.song_id
                WHERE s.id = %s
                """,
                (song_id,)
            )
        
        results = cursor.fetchall()
        
        if not results:
            return None
        
        # Extract song data
        song_data = {
            "id": results[0]["id"],
            "song_name": results[0]["song_name"],
            "artist": results[0]["artist"],
            "image_url": results[0]["image_url"],
            "charts": []
        }
        
        # Add chart data
        for row in results:
            if row["chart_id"]:  # Only add if chart data exists
                song_data["charts"].append({
                    "chart_id": row["chart_id"],
                    "chart_title": row["chart_title"],
                    "position": row["position"],
                    "peak_position": row["peak_position"],
                    "weeks_on_chart": row["weeks_on_chart"],
                    "last_week_position": row["last_week_position"],
                    "chart_date": row["chart_date"].isoformat() if row["chart_date"] else None
                })
        
        return song_data
    except Exception as e:
        logger.error(f"Error in get_song_with_chart_data: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def get_user_favourites(user_id: int, chart_id: str = None) -> List[Dict[str, Any]]:
    """
    Get user favourite songs with chart data.
    If chart_id is provided, filter by that chart.
    Returns a list of dicts with song and chart data.
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        if chart_id:
            # Get favourites for specific chart
            cursor.execute(
                """
                SELECT 
                    f.id AS favourite_id,
                    f.added_at,
                    s.id AS song_id,
                    s.song_name,
                    s.artist,
                    s.image_url,
                    cd.chart_id,
                    cd.chart_title,
                    cd.position,
                    cd.peak_position,
                    cd.weeks_on_chart,
                    cd.last_week_position
                FROM user_favourites f
                JOIN songs s ON f.song_id = s.id
                LEFT JOIN song_chart_data cd ON s.id = cd.song_id AND cd.chart_id = f.chart_id
                WHERE f.user_id = %s AND f.chart_id = %s
                ORDER BY f.added_at DESC
                """,
                (user_id, chart_id)
            )
        else:
            # Get all favourites
            cursor.execute(
                """
                SELECT 
                    f.id AS favourite_id,
                    f.added_at,
                    f.chart_id AS favourite_chart_id,
                    s.id AS song_id,
                    s.song_name,
                    s.artist,
                    s.image_url,
                    cd.chart_id,
                    cd.chart_title,
                    cd.position,
                    cd.peak_position,
                    cd.weeks_on_chart,
                    cd.last_week_position
                FROM user_favourites f
                JOIN songs s ON f.song_id = s.id
                LEFT JOIN song_chart_data cd ON s.id = cd.song_id AND cd.chart_id = f.chart_id
                WHERE f.user_id = %s
                ORDER BY f.added_at DESC
                """,
                (user_id,)
            )
        
        results = cursor.fetchall()
        
        # Process results to group by song
        songs_dict = {}
        for row in results:
            song_id = row["song_id"]
            
            if song_id not in songs_dict:
                songs_dict[song_id] = {
                    "song_id": song_id,
                    "song_name": row["song_name"],
                    "artist": row["artist"],
                    "image_url": row["image_url"],
                    "charts": [],
                    "added_at": row["added_at"].isoformat() if row["added_at"] else None
                }
            
            # Add chart data if it exists
            if row["chart_id"]:
                songs_dict[song_id]["charts"].append({
                    "favourite_id": row["favourite_id"],
                    "chart_id": row["chart_id"],
                    "chart_title": row["chart_title"],
                    "position": row["position"],
                    "peak_position": row["peak_position"],
                    "weeks_on_chart": row["weeks_on_chart"],
                    "last_week_position": row["last_week_position"],
                    "added_at": row["added_at"].isoformat() if row["added_at"] else None
                })
        
        return list(songs_dict.values())
    except Exception as e:
        logger.error(f"Error in get_user_favourites: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def toggle_favourite(
    user_id: int,
    song_name: str,
    artist: str,
    chart_id: str,
    chart_title: str,
    image_url: str = None,
    position: int = None,
    peak_position: int = None,
    weeks_on_chart: int = None,
    last_week_position: int = None
) -> Dict[str, Any]:
    """
    Toggle a song's favourite status.
    If not favourited, add to favourites.
    If already favourited, remove from favourites.
    Returns info about the toggled state.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get or create song
        song_id = get_or_create_song(song_name, artist, image_url)
        
        # Update chart data
        update_song_chart_data(
            song_id,
            chart_id,
            chart_title,
            position,
            peak_position,
            weeks_on_chart,
            last_week_position
        )
        
        # Check if already favourited
        cursor.execute(
            """
            SELECT id FROM user_favourites
            WHERE user_id = %s AND song_id = %s AND chart_id = %s
            """,
            (user_id, song_id, chart_id)
        )
        
        existing = cursor.fetchone()
        
        if existing:
            # Already favourited, remove it
            cursor.execute(
                "DELETE FROM user_favourites WHERE id = %s",
                (existing[0],)
            )
            conn.commit()
            
            return {
                "action": "removed",
                "favourite_id": existing[0],
                "song_id": song_id
            }
        else:
            # Not favourited, add it
            cursor.execute(
                """
                INSERT INTO user_favourites
                (user_id, song_id, chart_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (user_id, song_id, chart_id)
            )
            
            favourite_id = cursor.fetchone()[0]
            conn.commit()
            
            return {
                "action": "added",
                "favourite_id": favourite_id,
                "song_id": song_id
            }
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in toggle_favourite: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def check_favourite_status(
    user_id: int,
    song_name: str,
    artist: str,
    chart_id: str
) -> Dict[str, Any]:
    """
    Check if a song is favourited by the user.
    Returns status and favourite_id if found.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Find the song
        cursor.execute(
            "SELECT id FROM songs WHERE song_name = %s AND artist = %s",
            (song_name, artist)
        )
        
        song_result = cursor.fetchone()
        
        if not song_result:
            return {
                "is_favourited": False,
                "favourite_id": None
            }
            
        song_id = song_result[0]
        
        # Check if favourited
        cursor.execute(
            """
            SELECT id FROM user_favourites
            WHERE user_id = %s AND song_id = %s AND chart_id = %s
            """,
            (user_id, song_id, chart_id)
        )
        
        fav_result = cursor.fetchone()
        
        return {
            "is_favourited": bool(fav_result),
            "favourite_id": fav_result[0] if fav_result else None,
            "song_id": song_id
        }
    except Exception as e:
        logger.error(f"Error in check_favourite_status: {e}")
        return {
            "is_favourited": False,
            "favourite_id": None,
            "error": str(e)
        }
    finally:
        cursor.close()
        conn.close()