#!/usr/bin/env python3
# initialize_contest.py
# Manually create a prediction contest for the March 4-10, 2025 cycle

import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
import sys
import dotenv

# Try to load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
if os.path.exists(dotenv_path):
    dotenv.load_dotenv(dotenv_path)
else:
    # Try loading from .envrc file as an alternative
    envrc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.envrc')
    if os.path.exists(envrc_path):
        with open(envrc_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    var = line.strip().split('=', 1)
                    if len(var) == 2:
                        key, value = var
                        os.environ[key] = value

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection - using the provided connection string
DATABASE_URL = "postgresql://wavegerdatabase_user:cafvWdvIlSiZbBe7hX9uXki02Bv3UcP1@dpg-cu8g5bggph6c73cpbaj0-a.frankfurt-postgres.render.com/wavegerdatabase"
logger.info("Using provided database URL")

def get_db_connection():
    """Get a connection to the database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        # Ensure autocommit is off (we want to control transactions)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def get_current_active_contest():
    """Check if there's already an active contest"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute(
            """
            SELECT id, start_date, end_date, chart_release_date, status
            FROM weekly_contests
            WHERE status = 'open'
            ORDER BY start_date DESC
            LIMIT 1
            """
        )
        contest = cursor.fetchone()
        return contest
    except Exception as e:
        logger.error(f"Error fetching active contest: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def close_existing_contest():
    """Close any existing open contests"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update the contest status to 'closed'
        cursor.execute(
            """
            UPDATE weekly_contests
            SET status = 'closed', 
                closed_at = NOW()
            WHERE status = 'open'
            RETURNING id
            """
        )
        
        result = cursor.fetchone()
        
        if result:
            closed_id = result["id"]
            conn.commit()
            logger.info(f"Closed existing contest ID {closed_id}")
            return closed_id
        else:
            logger.info("No open contests to close")
            return None
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error closing contest: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def create_contest_for_current_cycle():
    """Create a contest for the current week cycle (March 4-10, 2025)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if there's already an active contest
        active_contest = get_current_active_contest()
        if active_contest:
            logger.info(f"Active contest already exists: ID {active_contest['id']}")
            logger.info(f"Start date: {active_contest['start_date']}")
            logger.info(f"End date: {active_contest['end_date']}")
            logger.info(f"Chart release date: {active_contest['chart_release_date']}")
            return active_contest['id']
        
        # First close any existing contests
        close_existing_contest()
        
        # Current prediction cycle
        start_date = datetime(2025, 3, 4).date()  # March 4, 2025 (Tuesday)
        
        # Next week's chart release (Tuesday)
        chart_release_date = datetime(2025, 3, 11).date()  # March 11, 2025
        
        # Contest ends the day before the next chart release
        end_date = chart_release_date - timedelta(days=1)  # March 10, 2025
        
        logger.info(f"Creating new contest for March 4-10, 2025 cycle:")
        logger.info(f"Start date: {start_date}")
        logger.info(f"End date: {end_date}")
        logger.info(f"Chart release date: {chart_release_date}")
        
        # Insert the new contest
        cursor.execute(
            """
            INSERT INTO weekly_contests
            (start_date, end_date, chart_release_date, status)
            VALUES (%s, %s, %s, 'open')
            RETURNING id
            """,
            (start_date, end_date, chart_release_date)
        )
        
        new_contest_id = cursor.fetchone()["id"]
        conn.commit()
        
        logger.info(f"Created new contest with ID: {new_contest_id}")
        return new_contest_id
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating contest: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    try:
        logger.info("Initializing prediction contest for the March 4-10, 2025 cycle...")
        contest_id = create_contest_for_current_cycle()
        
        if contest_id:
            logger.info(f"Success! Contest ID {contest_id} is now active.")
            logger.info("Users can now make predictions for the March 11, 2025 chart release.")
            logger.info("Prediction window: March 4-10, 2025")
        else:
            logger.error("Failed to create contest.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)