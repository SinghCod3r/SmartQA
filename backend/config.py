import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration settings."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Database settings
    # Use DATABASE_URL if available (for Vercel/Production), otherwise fallback to local SQLite
    # SQLAlchemy requires 'postgresql://' but some providers give 'postgres://'
    _db_url = os.environ.get('DATABASE_URL')
    if _db_url and _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = _db_url or f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Keep DATABASE_PATH for backward compatibility if needed, but we should rely on URI
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
    
    # Anthropic API settings
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    AI_MODEL = 'claude-sonnet-4-20250514'
    
    # Google Gemini API settings (FREE: 1,500 requests/day)
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
    GEMINI_MODEL = 'gemini-1.5-flash'
    
    # Groq API settings (FREE: 14,400 requests/day)
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    GROQ_MODEL = 'llama-3.1-70b-versatile'
    
    # Together AI settings (FREE: $1 credit on signup)
    TOGETHER_API_KEY = os.environ.get('TOGETHER_API_KEY', '')
    TOGETHER_MODEL = 'meta-llama/Llama-3-70b-chat-hf'
    
    # OpenRouter settings (FREE models available)
    # Get key from: https://openrouter.ai/keys
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
    OPENROUTER_MODEL = 'deepseek/deepseek-chat-free'  # Free DeepSeek model
    
    # Default AI provider (options: 'gemini', 'groq', 'together', 'openrouter', 'anthropic', 'mock')
    DEFAULT_AI_PROVIDER = os.environ.get('DEFAULT_AI_PROVIDER', 'openrouter')
    
    # File upload settings
    # use /tmp for serverless environments (Vercel)
    if os.environ.get('VERCEL'):
        UPLOAD_FOLDER = '/tmp/uploads'
    else:
        UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
        
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    
    # Token settings
    TOKEN_EXPIRY_HOURS = 24
