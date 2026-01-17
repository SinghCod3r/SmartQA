import sqlite3
import os
from config import Config


def get_db_connection():
    """Get a database connection with row factory enabled."""
    db_exists = os.path.exists(Config.DATABASE_PATH)
    
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    if not db_exists:
        create_tables(conn)
        
    return conn


def create_tables(conn):
    """Create tables in the database."""
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create generated_files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS generated_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            requirements TEXT,
            test_cases TEXT NOT NULL,
            project_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create sessions table for token management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()


def init_db():
    """Initialize the database (script entry point)."""
    conn = get_db_connection()
    # Tables are created automatically by get_db_connection if missing
    print("Database initialized successfully!")
    conn.close()


if __name__ == '__main__':
    init_db()
