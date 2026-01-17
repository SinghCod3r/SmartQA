import os
import secrets
import bcrypt
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# In-memory storage (resets on deployment)
users = {}  # {email: {name, password_hash, created_at}}
sessions_store = {}  # {token: {user_email, expires_at}}

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_session_token(email):
    token = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(hours=24)
    sessions_store[token] = {'user_email': email, 'expires_at': expires_at}
    return token

def get_current_user():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header[7:]
    session_data = sessions_store.get(token)
    
    if not session_data or session_data['expires_at'] < datetime.now():
        return None
    
    return users.get(session_data['user_email'])

@app.route('/')
@app.route('/api')
def index():
    return jsonify({'status': 'success', 'message': 'Smart QA Backend is Running'}), 200

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'users': len(users),
        'sessions': len(sessions_store)
    }), 200

@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not name or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        if email in users:
            return jsonify({'error': 'Email already registered'}), 409
        
        users[email] = {
            'name': name,
            'email': email,
            'password_hash': hash_password(password),
            'created_at': datetime.now().isoformat()
        }
        
        token = create_session_token(email)
        
        return jsonify({
            'message': 'Account created successfully',
            'user': {'name': name, 'email': email},
            'token': token
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = users.get(email)
        if not user or not verify_password(password, user['password_hash']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        token = create_session_token(email)
        
        return jsonify({
            'message': 'Login successful',
            'user': {'name': user['name'], 'email': user['email']},
            'token': token
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        sessions_store.pop(token, None)
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/me', methods=['GET'])
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'user': {'name': user['name'], 'email': user['email']}}), 200

@app.route('/api/generate', methods=['POST'])
def generate():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json() or {}
        requirements = data.get('requirements', '').strip()
        
        if not requirements:
            return jsonify({'error': 'Requirements are required'}), 400
        
        # Mock test case generation for now
        test_cases = [
            {
                'test_id': 'TC_001',
                'module': 'Core Functionality',
                'test_scenario': 'Verify basic functionality',
                'preconditions': 'System is accessible',
                'steps': '1. Navigate to feature\n2. Perform action\n3. Verify result',
                'test_data': 'Valid input',
                'expected_result': 'Action completes successfully',
                'actual_result': '',
                'status': 'Pending',
                'priority': 'High',
                'severity': 'Critical',
                'edge_cases': 'Test with min/max values'
            }
        ]
        
        return jsonify({
            'success': True,
            'test_cases': test_cases,
            'summary': {'total_test_cases': 1, 'high_priority': 1},
            'provider': 'mock'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
