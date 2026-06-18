import os
from datetime import timedelta
import secrets

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()

def get_database_uri():
    if DB_TYPE == "sqlite":
        basedir = os.path.abspath(os.path.dirname(__file__))
        return f"sqlite:///{os.path.join(basedir, 'app.db')}"

    elif DB_TYPE == "mysql":
        user     = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host     = os.getenv("DB_HOST")
        port     = os.getenv("DB_PORT", 3306)
        name     = os.getenv("DB_NAME")
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"

    elif DB_TYPE == "postgres":
        user     = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host     = os.getenv("DB_HOST")
        port     = os.getenv("DB_PORT", 5432)
        name     = os.getenv("DB_NAME")
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"

    elif DB_TYPE == "supabase":
        # Use the full connection string from Supabase dashboard
        # Project Settings → Database → Connection string → URI
        return os.getenv("SUPABASE_URL")

    else:
        raise ValueError(f'Unsupported DB_TYPE: "{DB_TYPE}". Use sqlite, mysql, postgres, or supabase.')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    # Use SQLite database in project folder by default
    db_path = os.path.join(os.path.dirname(__file__), 'cp_event.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', get_database_uri())
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

