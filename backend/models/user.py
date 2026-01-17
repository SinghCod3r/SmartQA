import bcrypt
from datetime import datetime
from .database import get_db_connection


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
        conn = get_db_connection()
        cursor = conn.cursor()
        
        password_hash = User.hash_password(password)
        
        try:
            cursor.execute(
                'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
                (name, email, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            
            return User(
                id=user_id,
                name=name,
                email=email,
                password_hash=password_hash,
                created_at=datetime.now()
            )
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def find_by_email(email: str) -> 'User':
        """Find a user by their email address."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row['id'],
                name=row['name'],
                email=row['email'],
                password_hash=row['password_hash'],
                created_at=row['created_at']
            )
        return None
    
    @staticmethod
    def find_by_id(user_id: int) -> 'User':
        """Find a user by their ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row['id'],
                name=row['name'],
                email=row['email'],
                password_hash=row['password_hash'],
                created_at=row['created_at']
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
