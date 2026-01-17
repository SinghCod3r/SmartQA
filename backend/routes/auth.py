from flask import Blueprint, request, jsonify
import secrets
from datetime import datetime, timedelta
from models.user import User
from models.database import get_db_connection
from config import Config

auth_bp = Blueprint('auth', __name__)


def create_session_token(user_id: int) -> str:
    """Create a new session token for a user."""
    token = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(hours=Config.TOKEN_EXPIRY_HOURS)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Remove any existing sessions for this user
    cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
    
    # Create new session
    cursor.execute(
        'INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)',
        (user_id, token, expires_at)
    )
    conn.commit()
    conn.close()
    
    return token


def validate_token(token: str) -> int:
    """Validate a session token and return user_id if valid."""
    if not token:
        return None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT user_id, expires_at FROM sessions WHERE token = ?',
        (token,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    expires_at = datetime.fromisoformat(row['expires_at'])
    if expires_at < datetime.now():
        return None
    
    return row['user_id']


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
        return jsonify({'error': 'An error occurred during login'}), 500


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    """Invalidate the current session."""
    try:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sessions WHERE token = ?', (token,))
            conn.commit()
            conn.close()
        
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
