import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-segura'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload settings
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB
    
    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour;10 per minute"
    
    # MFA settings
    MFA_EXPIRATION = 300  # 5 minutes in seconds
    
    # Email settings (for MFA)
    MAIL_SERVER = 'smtp.example.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('EMAIL_USER')
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')
    MAIL_DEFAULT_SENDER = 'no-reply@sistemacabula.com'