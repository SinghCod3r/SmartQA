import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from routes.auth import get_current_user
from services.ai_service import AIService
from services.file_parser import FileParser
from models.database import get_db_connection
from config import Config

generate_bp = Blueprint('generate', __name__)
ai_service = AIService()


@generate_bp.route('/api/providers', methods=['GET'])
def get_providers():
    """Get list of available AI providers."""
    providers = ai_service.get_available_providers()
    return jsonify({
        'providers': providers,
        'default': Config.DEFAULT_AI_PROVIDER
    }), 200


def save_generated_file(user_id: int, filename: str, requirements: str, 
                        test_cases: dict, project_type: str) -> int:
    """Save generated test cases to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO generated_files (user_id, filename, requirements, test_cases, project_type)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, filename, requirements, json.dumps(test_cases), project_type))
    
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return file_id


@generate_bp.route('/api/generate', methods=['POST'])
def generate_test_cases():
    """Generate test cases from requirements."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        requirements = None
        project_type = 'Web'  # Default
        
        # Check if file was uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                if not FileParser.allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
                    return jsonify({'error': 'Invalid file type. Allowed: PDF, DOCX, TXT'}), 400
                
                # Ensure upload folder exists
                os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                
                # Save file temporarily
                filename = secure_filename(file.filename)
                file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(file_path)
                
                try:
                    # Extract text from file
                    requirements = FileParser.extract_text(file_path)
                finally:
                    # Clean up uploaded file
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
        
        # Validate
        if not requirements:
            return jsonify({'error': 'Requirements are required'}), 400
        
        if project_type not in ['Web', 'Mobile', 'API', 'Desktop']:
            project_type = 'Web'
        
        # Generate test cases with specified provider
        result = ai_service.generate_test_cases(requirements, project_type, ai_provider)
        
        # Save to database
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_cases_{project_type.lower()}_{timestamp}"
        
        file_id = save_generated_file(
            user.id, 
            filename, 
            requirements[:1000],  # Store first 1000 chars of requirements
            result, 
            project_type
        )
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': filename,
            'test_cases': result.get('test_cases', []),
            'summary': result.get('summary', {}),
            'provider': result.get('provider', 'unknown'),
            'note': result.get('note', '')
        }), 200
        
    except Exception as e:
        print(f"Generation error: {str(e)}")
        return jsonify({'error': 'An error occurred during test case generation'}), 500


@generate_bp.route('/api/generate/<int:file_id>', methods=['GET'])
def get_generated_file(file_id):
    """Get a specific generated file."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM generated_files WHERE id = ? AND user_id = ?
    ''', (file_id, user.id))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'File not found'}), 404
    
    test_cases = json.loads(row['test_cases'])
    
    return jsonify({
        'id': row['id'],
        'filename': row['filename'],
        'requirements': row['requirements'],
        'test_cases': test_cases.get('test_cases', []),
        'summary': test_cases.get('summary', {}),
        'project_type': row['project_type'],
        'created_at': row['created_at']
    }), 200
