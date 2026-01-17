import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.pool import QueuePool
from config import Config

# Create engine
engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI, 
    pool_size=5, 
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

metadata = MetaData()

# Define tables
users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('email', String, unique=True, nullable=False),
    Column('password_hash', String, nullable=False),
    Column('created_at', DateTime, server_default=func.now())
)

generated_files = Table('generated_files', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
    Column('filename', String, nullable=False),
    Column('requirements', Text),
    Column('test_cases', Text, nullable=False), # Stores JSON string
    Column('project_type', String, nullable=False),
    Column('created_at', DateTime, server_default=func.now())
)

sessions = Table('sessions', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
    Column('token', String, unique=True, nullable=False),
    Column('expires_at', DateTime, nullable=False),
    Column('created_at', DateTime, server_default=func.now())
)

def init_db():
    """Initialize the database (create tables)."""
    with engine.begin() as conn:
        metadata.create_all(conn)
    print("Database initialized successfully!")

def get_db_connection():
    """Return a raw connection for legacy support (not recommended, use engine.connect())."""
    # This is a temporary bridge or we just update all callers.
    # We will update all callers to use engine directly or a helper.
    return engine.connect()


if __name__ == '__main__':
    init_db()
