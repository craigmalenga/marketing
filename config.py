"""
Configuration settings for Marketing Analytics Platform
"""

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'marketing_analytics.db')
    
    # Handle Railway's postgres:// to postgresql:// change
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG  # Log SQL queries in debug mode
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(basedir, 'data', 'uploads')
    EXPORT_FOLDER = os.path.join(basedir, 'data', 'exports')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'docx', 'doc'}
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Application settings
    ITEMS_PER_PAGE = 50
    MAX_EXPORT_ROWS = 100000
    
    # Date format settings
    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Status mapping defaults
    DEFAULT_STATUS_MAPPINGS = {
        'Active': {'received': 1, 'processed': 1, 'approved': 1},
        'Affordability check failed': {'received': 1, 'processed': 1, 'approved': 0},
        'Affordability check for review': {'received': 1, 'processed': 1, 'approved': 0},
        'Affordability check partial received': {'received': 0, 'processed': 0, 'approved': 0},
        'Affordability check passed': {'received': 1, 'processed': 1, 'approved': 1},
        'Awaiting affordability check': {'received': 1, 'processed': 0, 'approved': 0},
        'Cancelled': {'received': 0, 'processed': 0, 'approved': 0},
        'Future': {'received': 0, 'processed': 0, 'approved': 0}
    }
    
    # Report settings
    CACHE_TIMEOUT = 300  # 5 minutes cache for reports
    
    @staticmethod
    def init_app(app):
        """Initialize application with config"""
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Select configuration based on environment
def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])