import os
from datetime import timedelta
import secrets

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    # Use SQLite database in project folder by default
    db_path = os.path.join(os.path.dirname(__file__), 'cp_event.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', f'sqlite:///{db_path}')
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS', 'False').lower() in ['true', '1', 't']
    TEMPLATES_AUTO_RELOAD = os.environ.get('TEMPLATES_AUTO_RELOAD', 'True').lower() in ['true', '1', 't']
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 1800)))
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_hex(32))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.environ.get('TOKEN_EXPIRATION_MINUTES', 30)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('REFRESH_TOKEN_EXPIRATION_DAYS', 7)))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig    
}

