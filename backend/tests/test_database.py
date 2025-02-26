import unittest
import os
import sys
from unittest.mock import patch, MagicMock
import psycopg2
import time
from contextlib import contextmanager

# Add the parent directory to sys.path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your actual database functions
from db import get_db_connection
from auth import get_db_connection as auth_get_db_connection
from charts import get_db_connection as charts_get_db_connection

class DatabaseIntegrationTests(unittest.TestCase):
    """Tests for database connection and operations."""
    
    def setUp(self):
        """Set up test environment."""
        # Save the original DATABASE_URL to restore it later
        self.original_db_url = os.environ.get('DATABASE_URL')
        
        # Use test database if available, otherwise mock connections
        self.test_db_url = os.environ.get('TEST_DATABASE_URL')
        if self.test_db_url:
            os.environ['DATABASE_URL'] = self.test_db_url
        
    def tearDown(self):
        """Clean up after tests."""
        # Restore the original DATABASE_URL
        if self.original_db_url:
            os.environ['DATABASE_URL'] = self.original_db_url
        else:
            del os.environ['DATABASE_URL']
    
    @patch('psycopg2.connect')
    def test_connection_retry_logic(self, mock_connect):
        """Test that connection retries work correctly."""
        # Arrange - Set up mock to fail twice then succeed
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        # First two calls raise an exception, third call succeeds
        mock_connect.side_effect = [
            psycopg2.OperationalError("Connection refused"),
            psycopg2.OperationalError("Connection timeout"),
            mock_conn
        ]
        
        # Act - Call the function which should retry connections
        with patch('time.sleep') as mock_sleep:  # Mock sleep to speed up test
            actual_conn = get_db_connection(retries=3, delay=0.1)
        
        # Assert
        self.assertEqual(mock_connect.call_count, 3)
        mock_sleep.assert_called_with(0.1)
        self.assertEqual(actual_conn, mock_conn)
    
    @patch('psycopg2.connect')
    def test_connection_max_retries_exceeded(self, mock_connect):
        """Test behavior when max connection retries are exceeded."""
        # Arrange - All connection attempts fail
        mock_connect.side_effect = psycopg2.OperationalError("Connection refused")
        
        # Act & Assert - Should raise RuntimeError after max retries
        with patch('time.sleep') as mock_sleep:
            with self.assertRaises(RuntimeError):
                get_db_connection(retries=3, delay=0.1)
        
        self.assertEqual(mock_connect.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # Sleep between retries, not after last
    
    def test_connection_with_real_database(self):
        """Test actual connection to database if credentials are available."""
        # Skip if no test database URL is provided
        if not self.test_db_url:
            self.skipTest("No TEST_DATABASE_URL environment variable set")
        
        # Try to connect to the actual database
        conn = get_db_connection()
        
        # Assert connection is valid
        self.assertFalse(conn.closed)
        
        # Test simple query
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)
        
        # Clean up
        cursor.close()
        conn.close()
    
    @patch('psycopg2.connect')
    def test_connection_string_parsing(self, mock_connect):
        """Test that the DATABASE_URL is correctly passed to psycopg2.connect."""
        # Arrange
        test_url = "postgresql://user:pass@localhost:5432/testdb"
        os.environ['DATABASE_URL'] = test_url
        
        # Act
        get_db_connection()
        
        # Assert
        mock_connect.assert_called_once_with(test_url, cursor_factory=None)
    
    def test_connection_modules_consistency(self):
        """Test that get_db_connection behaves consistently across modules."""
        # Skip if no test database URL is provided
        if not self.test_db_url:
            self.skipTest("No TEST_DATABASE_URL environment variable set")
        
        # Get connections using different module functions
        db_conn = get_db_connection()
        auth_conn = auth_get_db_connection()
        charts_conn = charts_get_db_connection()
        
        # Assert all connections are valid
        self.assertFalse(db_conn.closed)
        self.assertFalse(auth_conn.closed)
        self.assertFalse(charts_conn.closed)
        
        # Clean up
        db_conn.close()
        auth_conn.close()
        charts_conn.close()


class DatabaseTransactionTests(unittest.TestCase):
    """Tests for database transaction management."""
    
    @patch('psycopg2.connect')
    def test_transaction_commit(self, mock_connect):
        """Test that transactions are properly committed."""
        # Arrange - Set up mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Act - Simulate a transaction with commit
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO test (value) VALUES ('test')")
        conn.commit()
        cursor.close()
        conn.close()
        
        # Assert - Transaction was committed
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('psycopg2.connect')
    def test_transaction_rollback(self, mock_connect):
        """Test that transactions are properly rolled back on error."""
        # Arrange - Set up mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Configure cursor.execute to raise an exception
        mock_cursor.execute.side_effect = psycopg2.Error("Test error")
        
        # Act - Simulate a transaction with error
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO test (value) VALUES ('test')")
            conn.commit()
        except psycopg2.Error:
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
        
        # Assert - Transaction was rolled back
        mock_cursor.execute.assert_called_once()
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()


@contextmanager
def mock_db_cursor(fetch_result=None, row_count=0, error_on_execute=None):
    """Context manager to mock database cursor and connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Configure the cursor mock
    if error_on_execute:
        mock_cursor.execute.side_effect = error_on_execute
    
    if fetch_result:
        mock_cursor.fetchone.return_value = fetch_result
        mock_cursor.fetchall.return_value = [fetch_result]
    
    mock_cursor.rowcount = row_count
    mock_conn.cursor.return_value = mock_cursor
    
    with patch('psycopg2.connect', return_value=mock_conn):
        yield mock_conn, mock_cursor


class DatabaseErrorHandlingTests(unittest.TestCase):
    """Tests for database error handling scenarios."""
    
    def test_connection_error_handling(self):
        """Test handling of connection errors."""
        # Act & Assert - Connection error should be caught and retried
        with patch('psycopg2.connect') as mock_connect, \
             patch('time.sleep') as mock_sleep:
            
            # Set up mock to always fail
            mock_connect.side_effect = psycopg2.OperationalError("Connection refused")
            
            # Should raise RuntimeError after retries
            with self.assertRaises(RuntimeError):
                get_db_connection(retries=2, delay=0.1)
            
            # Should have tried the specified number of times
            self.assertEqual(mock_connect.call_count, 2)
            mock_sleep.assert_called_once_with(0.1)
    
    def test_integrity_error_handling(self):
        """Test handling of database integrity errors."""
        # Arrange - Set up context with an integrity error
        integrity_error = psycopg2.IntegrityError("Duplicate key value violates unique constraint")
        
        with mock_db_cursor(error_on_execute=integrity_error) as (mock_conn, mock_cursor):
            # Act - Try to execute a query that would trigger an integrity error
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Assert - IntegrityError should be caught and handled
            with self.assertRaises(psycopg2.IntegrityError):
                cursor.execute("INSERT INTO users (username) VALUES ('test')")
            
            # Connection should be rolled back
            mock_conn.rollback.assert_not_called()  # We're not managing the transaction here
            
            cursor.close()
            conn.close()
    
    def test_operational_error_handling(self):
        """Test handling of database operational errors."""
        # Arrange - Set up context with an operational error
        operational_error = psycopg2.OperationalError("Connection timed out")
        
        with mock_db_cursor(error_on_execute=operational_error) as (mock_conn, mock_cursor):
            # Act - Try to execute a query that would trigger an operational error
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Assert - OperationalError should be caught and handled
            with self.assertRaises(psycopg2.OperationalError):
                cursor.execute("SELECT * FROM users")
            
            cursor.close()
            conn.close()


if __name__ == '__main__':
    unittest.main()