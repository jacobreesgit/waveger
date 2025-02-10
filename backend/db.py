import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
import time

DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(level=logging.DEBUG)

def get_db_connection(retries=3, delay=5):
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            logging.debug("Database connection successful")
            ensure_tables_exist(conn)
            return conn
        except Exception as e:
            logging.error(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    
    raise RuntimeError("Database connection failed after multiple attempts")

def ensure_tables_exist(conn):
    """Checks if the 'charts' table exists and creates it if missing."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'charts'
            );
        """)
        exists = cur.fetchone()[0]
        
        if not exists:
            logging.info("⚠️ 'charts' table missing. Creating it now...")
            cur.execute("""
                CREATE TABLE charts (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    week DATE NOT NULL,
                    data JSONB NOT NULL,
                    UNIQUE (title, week)  -- Prevent duplicate chart data
                );
            """)
            conn.commit()
            logging.info("✅ 'charts' table created successfully.")
