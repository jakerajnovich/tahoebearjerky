import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import sqlite3

# Load environment variables
load_dotenv()

DB_TYPE = os.getenv('DB_TYPE', 'sqlite')

class Database:
    """Database connection manager supporting both PostgreSQL and SQLite"""
    
    def __init__(self):
        self.db_type = DB_TYPE
        self.conn = None
        
    def connect(self):
        """Create a database connection"""
        if self.db_type == 'postgresql':
            self.conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5433'),
                database=os.getenv('POSTGRES_DB', 'tahoe_bear_jerky'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', '')
            )
            # Use RealDictCursor for dict-like row access
            self.conn.cursor_factory = psycopg2.extras.RealDictCursor
        else:
            # SQLite fallback
            db_path = os.getenv('SQLITE_DB_PATH', 'database/tahoe_bear_jerky.db')
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
        
        return self.conn
    
    def get_cursor(self):
        """Get a cursor from the connection"""
        if not self.conn:
            self.connect()
        return self.conn.cursor()
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.close()

def get_db_connection():
    """
    Get a database connection
    Returns a connection object that works with both PostgreSQL and SQLite
    """
    db = Database()
    return db.connect()

def dict_from_row(row):
    """
    Convert database row to dictionary
    Works with both PostgreSQL RealDictRow and SQLite Row
    """
    if isinstance(row, dict):
        # PostgreSQL RealDictRow is already dict-like
        return dict(row)
    else:
        # SQLite Row
        return dict(zip(row.keys(), row))
