import psycopg2
import os
import logging
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = "postgresql://wavegerdatabase_user:cafvWdvIlSiZbBe7hX9uXki02Bv3UcP1@dpg-cu8g5bggph6c73cpbaj0-a.frankfurt-postgres.render.com:5432/wavegerdatabase"

def execute_migration():
    """
    Execute the database migration to normalize song data.
    Returns information about what was migrated.
    """
    logger.info("Starting database migration")
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        # Step 1: Create the new tables if they don't exist
        logger.info("Creating new tables...")
        
        cursor.execute("""
        -- Create new normalized songs table if it doesn't exist
        CREATE TABLE IF NOT EXISTS songs (
            id SERIAL PRIMARY KEY,
            song_name TEXT NOT NULL,
            artist TEXT NOT NULL,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_song_artist UNIQUE(song_name, artist)
        );
        """)
        
        # Fixed: Removed the problematic UNIQUE constraint from table definition
        cursor.execute("""
        -- Create new song_chart_data table for chart-specific info
        CREATE TABLE IF NOT EXISTS song_chart_data (
            id SERIAL PRIMARY KEY,
            song_id INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
            chart_id TEXT NOT NULL,
            chart_title TEXT NOT NULL,
            position INTEGER,
            peak_position INTEGER,
            weeks_on_chart INTEGER,
            last_week_position INTEGER,
            chart_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Create a unique index instead of constraint (supports expressions better)
        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_song_chart_date 
        ON song_chart_data(song_id, chart_id, COALESCE(chart_date, '1970-01-01'::date));
        """)
        
        # Create indexes
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_song_chart_data_song_id ON song_chart_data(song_id);
        CREATE INDEX IF NOT EXISTS idx_song_chart_data_chart_id ON song_chart_data(chart_id);
        """)
        
        # Step 2: Create a backup of the user_favourites table
        logger.info("Creating backup of current favourites table...")
        cursor.execute("CREATE TABLE IF NOT EXISTS user_favourites_backup AS SELECT * FROM user_favourites;")
        
        # Step 3: Count current favourites for reporting
        cursor.execute("SELECT COUNT(*) FROM user_favourites;")
        original_favourites_count = cursor.fetchone()[0]
        logger.info(f"Found {original_favourites_count} favourites to migrate")
        
        # Step 4: Populate the songs table
        logger.info("Migrating unique songs to songs table...")
        cursor.execute("""
        INSERT INTO songs (song_name, artist, image_url)
        SELECT DISTINCT 
            song_name, 
            artist, 
            image_url
        FROM user_favourites
        ON CONFLICT (song_name, artist) DO UPDATE
        SET image_url = COALESCE(EXCLUDED.image_url, songs.image_url);
        """)
        
        # Count songs migrated
        cursor.execute("SELECT COUNT(*) FROM songs;")
        songs_count = cursor.fetchone()[0]
        logger.info(f"Migrated {songs_count} unique songs")
        
        # Step 5: Populate the song_chart_data table
        logger.info("Migrating chart data...")
        # Fixed: Use ON CONFLICT format without COALESCE in the ON CONFLICT clause
        cursor.execute("""
        WITH chart_data AS (
            SELECT DISTINCT 
                s.id AS song_id,
                uf.chart_id,
                uf.chart_title,
                uf.position,
                uf.peak_position,
                uf.weeks_on_chart,
                uf.last_week_position
            FROM user_favourites uf
            JOIN songs s ON uf.song_name = s.song_name AND uf.artist = s.artist
        )
        INSERT INTO song_chart_data 
            (song_id, chart_id, chart_title, position, peak_position, weeks_on_chart, last_week_position)
        SELECT 
            song_id, chart_id, chart_title, position, peak_position, weeks_on_chart, last_week_position
        FROM chart_data
        ON CONFLICT DO NOTHING;
        """)
        
        # Count chart data entries migrated
        cursor.execute("SELECT COUNT(*) FROM song_chart_data;")
        chart_data_count = cursor.fetchone()[0]
        logger.info(f"Migrated {chart_data_count} chart data entries")
        
        # Step 6: Alter the user_favourites table to add song_id column if it doesn't exist
        logger.info("Updating user_favourites table structure...")
        
        # Check if the column already exists first
        cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'user_favourites' AND column_name = 'song_id';
        """)
        column_exists = cursor.fetchone()
        
        if not column_exists:
            cursor.execute("ALTER TABLE user_favourites ADD COLUMN song_id INTEGER;")
        
        # Step 7: Set the song_id for each record
        logger.info("Setting song_id references...")
        cursor.execute("""
        UPDATE user_favourites uf
        SET song_id = s.id
        FROM songs s
        WHERE uf.song_name = s.song_name AND uf.artist = s.artist
          AND uf.song_id IS NULL;
        """)
        
        # Step 8: Drop old columns if using a transitional approach - comment this out to keep both models during transition
        # logger.info("Removing old redundant columns...")
        # cursor.execute("""
        # ALTER TABLE user_favourites 
        #     DROP COLUMN IF EXISTS song_name,
        #     DROP COLUMN IF EXISTS artist,
        #     DROP COLUMN IF EXISTS position,
        #     DROP COLUMN IF EXISTS image_url,
        #     DROP COLUMN IF EXISTS peak_position,
        #     DROP COLUMN IF EXISTS weeks_on_chart,
        #     DROP COLUMN IF EXISTS last_week_position;
        # """)
        
        # Step 9: Make song_id NOT NULL if it's not already
        cursor.execute("""
        SELECT column_name, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'user_favourites' AND column_name = 'song_id';
        """)
        song_id_info = cursor.fetchone()
        
        if song_id_info and song_id_info[1] == 'YES':  # If it's nullable
            cursor.execute("ALTER TABLE user_favourites ALTER COLUMN song_id SET NOT NULL;")
        
        # Step 10: Add foreign key constraint if it doesn't exist
        cursor.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'user_favourites' 
        AND constraint_name = 'fk_user_favourites_song_id';
        """)
        constraint_exists = cursor.fetchone()
        
        if not constraint_exists:
            cursor.execute("""
            ALTER TABLE user_favourites 
                ADD CONSTRAINT fk_user_favourites_song_id 
                FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE;
            """)
        
        # Step 11: Add unique constraint to prevent duplicates
        cursor.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'user_favourites' 
        AND constraint_name = 'unique_user_song_chart';
        """)
        unique_constraint_exists = cursor.fetchone()
        
        if not unique_constraint_exists:
            cursor.execute("""
            ALTER TABLE user_favourites
                ADD CONSTRAINT unique_user_song_chart UNIQUE(user_id, song_id, chart_id);
            """)
        
        # Step 12: Create indexes for faster lookups
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_favourites_song_id ON user_favourites(song_id);
        CREATE INDEX IF NOT EXISTS idx_user_favourites_user_id ON user_favourites(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_favourites_chart_id ON user_favourites(chart_id);
        """)
        
        # Step 13: Create a trigger to update the updated_at timestamp
        cursor.execute("""
        CREATE OR REPLACE FUNCTION update_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
           NEW.updated_at = CURRENT_TIMESTAMP;
           RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS update_songs_timestamp ON songs;
        CREATE TRIGGER update_songs_timestamp
        BEFORE UPDATE ON songs
        FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

        DROP TRIGGER IF EXISTS update_song_chart_data_timestamp ON song_chart_data;
        CREATE TRIGGER update_song_chart_data_timestamp
        BEFORE UPDATE ON song_chart_data
        FOR EACH ROW EXECUTE PROCEDURE update_timestamp();
        """)
        
        conn.commit()
        logger.info("Migration completed successfully!")
        
        return {
            "success": True,
            "original_favourites": original_favourites_count,
            "songs_migrated": songs_count,
            "chart_entries_migrated": chart_data_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Run the migration when the script is executed directly
    result = execute_migration()
    print(f"Migration {'succeeded' if result['success'] else 'failed'}")
    for key, value in result.items():
        if key != 'success':
            print(f"{key}: {value}")