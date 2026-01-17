import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models.database import init_db
from routes.auth import auth_bp
from routes.generate import generate_bp
from routes.export import export_bp


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    
    # Enable CORS for frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",  # Allow all origins for Vercel deployment
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(generate_bp)
    app.register_blueprint(export_bp)
    
    # Initialize database
    with app.app_context():
        init_db()
    
    # Create upload folder
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Smart QA Test Case Generator API is running'
        }), 200
    
    return app


app = create_app()


if __name__ == '__main__':
    print("=" * 60)
    print("Smart QA Test Case Generator - Backend Server")
    print("=" * 60)
    print(f"API running at: http://localhost:5000")
    print(f"Health check: http://localhost:5000/api/health")
    print("=" * 60)
    
    if not Config.ANTHROPIC_API_KEY:
        print("\n⚠️  WARNING: ANTHROPIC_API_KEY not set!")
        print("   Set it in .env file or environment variable")
        print("   Mock test cases will be generated without API key\n")
    
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)
