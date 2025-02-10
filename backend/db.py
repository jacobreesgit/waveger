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
            return conn
        except Exception as e:
            logging.error(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    
    raise RuntimeError("Database connection failed after multiple attempts")
