import bcrypt
from datetime import datetime
from sqlalchemy import select
from .database import engine, users


class User:
    """User model for authentication and user management."""
    
    def __init__(self, id=None, name=None, email=None, password_hash=None, created_at=None):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def create(name: str, email: str, password: str) -> 'User':
        """Create a new user in the database."""
        password_hash = User.hash_password(password)
        
        try:
            with engine.connect() as conn:
                # Insert user
                stmt = users.insert().values(
                    name=name,
                    email=email,
                    password_hash=password_hash
                )
                result = conn.execute(stmt)
                conn.commit()
                
                # Get ID
                user_id = result.inserted_primary_key[0]
                
                return User(
                    id=user_id,
                    name=name,
                    email=email,
                    password_hash=password_hash,
                    created_at=datetime.now()
                )
        except Exception as e:
            raise e
    
    @staticmethod
    def find_by_email(email: str) -> 'User':
        """Find a user by their email address."""
        with engine.connect() as conn:
            stmt = select(users).where(users.c.email == email)
            result = conn.execute(stmt)
            row = result.first()
            
            if row:
                return User(
                    id=row.id,
                    name=row.name,
                    email=row.email,
                    password_hash=row.password_hash,
                    created_at=row.created_at
                )
        return None
    
    @staticmethod
    def find_by_id(user_id: int) -> 'User':
        """Find a user by their ID."""
        with engine.connect() as conn:
            stmt = select(users).where(users.c.id == user_id)
            result = conn.execute(stmt)
            row = result.first()
            
            if row:
                return User(
                    id=row.id,
                    name=row.name,
                    email=row.email,
                    password_hash=row.password_hash,
                    created_at=row.created_at
                )
        return None
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding password)."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': str(self.created_at) if self.created_at else None
        }
