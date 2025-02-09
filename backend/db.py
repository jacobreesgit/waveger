import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging

DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(level=logging.DEBUG)

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        logging.debug("Database connection successful")
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise RuntimeError(f"Database connection failed: {e}")
