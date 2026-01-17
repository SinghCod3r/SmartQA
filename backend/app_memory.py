import os
import secrets
import bcrypt
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, session
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Enable CORS with credentials support
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "supports_credentials": True,
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# In-memory storage (will reset on each deployment, but works for demo)
users = {}  # {email: {name, password_hash, created_at}}
sessions_store = {}  # {token: {user_email, expires_at}}
files_store = {}  # {file_id: {user_email, filename, test_cases, created_at}}

# Import services
from services.ai_service import AIService
from services.file_parser import FileParser
from config import Config

# Lazy load AI service
_ai_service = None

def get_ai_service():
    global _ai_service
    if _ai_service is None:
        try:
            _ai_service = AIService()
        except Exception as e:
            print(f"Failed to initialize AI Service: {e}")
            return None
    return _ai_service

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
    
    if not session_data:
        return None
    
    if session_data['expires_at'] < datetime.now():
        del sessions_store[token]
        return None
    
    return users.get(session_data['user_email'])

@app.route('/', methods=['GET'])
def index():
    return "Smart QA Test Case Generator - Backend is Running", 200

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'users_count': len(users),
        'sessions_count': len(sessions_store)
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
        if token in sessions_store:
            del sessions_store[token]
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/me', methods=['GET'])
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'user': {'name': user['name'], 'email': user['email']}}), 200

@app.route('/api/providers', methods=['GET'])
def get_providers():
    service = get_ai_service()
    if not service:
        return jsonify({
            'providers': [{'id': 'mock', 'name': 'Demo Mode', 'description': 'Fallback'}],
            'default': 'mock'
        }), 200
    
    return jsonify({
        'providers': service.get_available_providers(),
        'default': Config.DEFAULT_AI_PROVIDER
    }), 200

@app.route('/api/generate', methods=['POST'])
def generate():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        requirements = None
        project_type = 'Web'
        
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                if not FileParser.allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
                    return jsonify({'error': 'Invalid file type'}), 400
                
                os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                from werkzeug.utils import secure_filename
                filename = secure_filename(file.filename)
                file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(file_path)
                
                try:
                    requirements = FileParser.extract_text(file_path)
                finally:
                    if os.path.exists(file_path):
                        os.remove(file_path)
        
        if request.content_type and 'multipart/form-data' in request.content_type:
            if not requirements:
                requirements = request.form.get('requirements', '').strip()
            project_type = request.form.get('project_type', 'Web')
            ai_provider = request.form.get('ai_provider', None)
        else:
            data = request.get_json() or {}
            if not requirements:
                requirements = data.get('requirements', '').strip()
            project_type = data.get('project_type', 'Web')
            ai_provider = data.get('ai_provider', None)
        
        if not requirements:
            return jsonify({'error': 'Requirements are required'}), 400
        
        service = get_ai_service()
        if not service:
            return jsonify({'error': 'AI Service failed to initialize'}), 500
        
        result = service.generate_test_cases(requirements, project_type, ai_provider)
        
        # Store in memory
        file_id = len(files_store) + 1
        files_store[file_id] = {
            'user_email': user['email'],
            'filename': f"test_cases_{project_type.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'test_cases': result,
            'project_type': project_type,
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'test_cases': result.get('test_cases', []),
            'summary': result.get('summary', {}),
            'provider': result.get('provider', 'unknown')
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_files = [
        {
            'id': fid,
            'filename': fdata['filename'],
            'project_type': fdata['project_type'],
            'created_at': fdata['created_at']
        }
        for fid, fdata in files_store.items()
        if fdata['user_email'] == user['email']
    ]
    
    return jsonify({'history': user_files}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
