from flask import Blueprint, request, jsonify
import secrets
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from models.user import User
from models.database import engine, sessions
from config import Config

auth_bp = Blueprint('auth', __name__)


def create_session_token(user_id: int) -> str:
    """Create a new session token for a user."""
    token = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(hours=Config.TOKEN_EXPIRY_HOURS)
    
    with engine.connect() as conn:
        # Remove any existing sessions for this user
        conn.execute(
            delete(sessions).where(sessions.c.user_id == user_id)
        )
        
        # Create new session
        conn.execute(
            sessions.insert().values(
                user_id=user_id,
                token=token,
                expires_at=expires_at
            )
        )
        conn.commit()
    
    return token


def validate_token(token: str) -> int:
    """Validate a session token and return user_id if valid."""
    if not token:
        return None
    
    with engine.connect() as conn:
        stmt = select(sessions.c.user_id, sessions.c.expires_at).where(sessions.c.token == token)
        result = conn.execute(stmt)
        row = result.first()
    
    if not row:
        return None
    
    # Handle datetime conversion if necessary (SQLAlchemy usually handles this, but just in case)
    expires_at = row.expires_at
    if isinstance(expires_at, str):
        try:
            expires_at = datetime.fromisoformat(expires_at)
        except ValueError:
            # Fallback for some SQLite formats
            expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S.%f')
            
    if expires_at < datetime.now():
        return None
    
    return row.user_id


def get_current_user():
    """Get the current authenticated user from request headers."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header[7:]  # Remove 'Bearer ' prefix
    user_id = validate_token(token)
    
    if user_id:
        return User.find_by_id(user_id)
    return None


@auth_bp.route('/api/signup', methods=['POST'])
def signup():
    """Create a new user account."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if user already exists
        existing_user = User.find_by_email(email)
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create user
        user = User.create(name, email, password)
        
        # Create session token
        token = create_session_token(user.id)
        
        return jsonify({
            'message': 'Account created successfully',
            'user': user.to_dict(),
            'token': token
        }), 201
        
    except Exception as e:
        print(f"Signup error: {str(e)}") # Add logging for debug
        return jsonify({'error': 'An error occurred during signup'}), 500


@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Authenticate user and return session token."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        # Find user
        user = User.find_by_email(email)
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Verify password
        if not User.verify_password(password, user.password_hash):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create session token
        token = create_session_token(user.id)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': token
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'An error occurred during login'}), 500


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    """Invalidate the current session."""
    try:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            
            with engine.connect() as conn:
                conn.execute(
                    delete(sessions).where(sessions.c.token == token)
                )
                conn.commit()
        
        return jsonify({'message': 'Logged out successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'An error occurred during logout'}), 500


@auth_bp.route('/api/me', methods=['GET'])
def get_current_user_info():
    """Get current authenticated user information."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({'user': user.to_dict()}), 200
