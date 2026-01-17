import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for all origins
CORS(app, resources={r"/*": {"origins": "*"}})

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

@app.route('/', methods=['GET'])
def index():
    return "Smart QA Test Case Generator - Backend is Running", 200

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'message': 'API is running'}), 200

@app.route('/api/providers', methods=['GET'])
def get_providers():
    service = get_ai_service()
    if not service:
        return jsonify({
            'providers': [{'id': 'mock', 'name': 'Demo Mode', 'description': 'Fallback mode'}],
            'default': 'mock'
        }), 200
    
    providers = service.get_available_providers()
    return jsonify({
        'providers': providers,
        'default': Config.DEFAULT_AI_PROVIDER
    }), 200

@app.route('/api/generate', methods=['POST'])
def generate_test_cases():
    try:
        requirements = None
        project_type = 'Web'
        
        # Check if file was uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                if not FileParser.allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
                    return jsonify({'error': 'Invalid file type. Allowed: PDF, DOCX, TXT'}), 400
                
                # Save file temporarily
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
        
        # Get form data or JSON data
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
        
        if project_type not in ['Web', 'Mobile', 'API', 'Desktop']:
            project_type = 'Web'
        
        # Generate test cases
        service = get_ai_service()
        if not service:
            return jsonify({'error': 'AI Service failed to initialize'}), 500
        
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
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
