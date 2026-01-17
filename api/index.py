import os
import secrets
import bcrypt
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

# Optional Supabase import
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: Supabase library not found. Falling back to in-memory mode.")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Global DB client
supabase = None

# In-memory fallbacks
users_memory = {}
sessions_store = {}

def get_db():
    global supabase
    if not SUPABASE_AVAILABLE:
        return None
        
    if not supabase:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if url and key:
            try:
                supabase = create_client(url, key)
            except Exception as e:
                print(f"Supabase init failed: {e}")
                return None
    return supabase

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
    
    return {'email': session_data['user_email']}

@app.route('/')
@app.route('/api')
def index():
    db_status = "Connected" if get_db() else "Memory Mode (No DB)"
    return jsonify({
        'status': 'success', 
        'message': f'Smart QA Backend is Running. Mode: {db_status}'
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
            
        hashed = hash_password(password)
        db = get_db()
        
        if db:
            # Use Supabase
            try:
                res = db.table('users').insert({
                    'name': name,
                    'email': email,
                    'password_hash': hashed,
                    'created_at': datetime.now().isoformat()
                }).execute()
            except Exception as e:
                return jsonify({'error': 'Email likely already exists or DB error'}), 409
        else:
            # Fallback to Memory
            if email in users_memory:
                 return jsonify({'error': 'Email already registered'}), 409
            users_memory[email] = {
                'name': name, 'email': email, 'password_hash': hashed
            }

        token = create_session_token(email)
        return jsonify({'message': 'Account created', 'token': token, 'user': {'name': name, 'email': email}}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        db = get_db()
        user = None
        
        if db:
            # Use Supabase
            res = db.table('users').select("*").eq('email', email).execute()
            if res.data:
                user = res.data[0]
        else:
            # Fallback Memory
            user = users_memory.get(email)
            
        if not user or not verify_password(password, user['password_hash']):
            return jsonify({'error': 'Invalid credentials'}), 401
            
        token = create_session_token(email)
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {'name': user.get('name'), 'email': email}
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
    return jsonify({'user': user}), 200

@app.route('/api/history', methods=['GET'])
def get_history():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'history': []}), 200

@app.route('/api/providers', methods=['GET'])
def get_providers():
    try:
        from services.ai_service import AIService
        service = AIService()
        return jsonify({'providers': service.get_available_providers(), 'default': 'mock'}), 200
    except Exception as e:
        return jsonify({'providers': [{'id': 'mock', 'name': 'Demo Mode', 'description': str(e)}], 'default': 'mock'}), 200

@app.route('/api/generate', methods=['POST'])
def generate():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json() or {}
        requirements = data.get('requirements', '').strip()
        project_type = data.get('project_type', 'Web')
        ai_provider = data.get('ai_provider', None)
        
        if not requirements:
            return jsonify({'error': 'Requirements are required'}), 400
        
        # Use AI service
        from services.ai_service import AIService
        service = AIService()
        result = service.generate_test_cases(requirements, project_type, ai_provider)
        
        return jsonify({
            'success': True,
            'test_cases': result.get('test_cases', []),
            'summary': result.get('summary', {}),
            'provider': result.get('provider', 'unknown'),
            'note': result.get('note', '')
        }), 200
    except Exception as e:
        print(f"Generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500
