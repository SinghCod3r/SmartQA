import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

try:
    from app import app
    # Vercel expects 'app' or 'application'
    application = app
except Exception as e:
    print(f"CRITICAL ERROR loading Flask app: {e}")
    import traceback
    traceback.print_exc()
    
    # Create a minimal error app
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/<path:path>')
    def error_handler(path=''):
        return jsonify({
            'error': 'Application failed to initialize',
            'details': str(e),
            'path': path
        }), 500
    
    application = app
