"""
Configuration module for Corpus Forge Flask application.

Handles environment setup, database configuration, and app settings.
Environment variables are loaded from .env file.

TODO: Extend with production-specific settings (logging, metrics, etc.)
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Base configuration class with common settings.
    
    All configuration values should be defined here and read from 
    environment variables for security (never hardcode secrets).
    """
    
    # Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', False)
    
    # Database Settings
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///corpus_forge.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google GenAI Settings
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gemini-pro')
    DEFAULT_TEMPERATURE = float(os.getenv('DEFAULT_TEMPERATURE', 0.7))
    DEFAULT_TOP_P = float(os.getenv('DEFAULT_TOP_P', 0.9))
    
    # ChromaDB Settings
    CHROMADB_PATH = os.getenv('CHROMADB_PATH', './.chromadb')
    
    # File Upload Settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))  # 50 MB
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'py', 'js', 'ts', 'java', 'cpp', 'c', 'java'}
    
    @staticmethod
    def init_app(app):
        """
        Initialize app with configuration.
        
        TODO: Add logging configuration
        TODO: Add metrics/monitoring setup
        TODO: Add cache configuration (Redis for production)
        
        Args:
            app: Flask application instance
        """
        pass


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    
class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False
    # TODO: Ensure GOOGLE_API_KEY is set in production environment
    # TODO: Add HTTPS enforcement
    # TODO: Add CORS settings for production domain


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
