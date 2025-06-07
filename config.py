import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-segura'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'site.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Configuração para usar o Flask-Session com armazenamento no sistema de arquivos
    SESSION_TYPE = 'filesystem'  # Usando filesystem para armazenar as sessões
    SESSION_FILE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'flask_session')  # Diretório onde as sessões serão armazenadas
    SESSION_PERMANENT = True  # As sessões podem ser permanentes (ou seja, não expiram após a sessão do navegador ser fechada)
    SESSION_USE_SIGNER = True  # Para assinar os cookies de sessão
    SESSION_COOKIE_HTTPONLY = True  # Proteger contra ataques de XSS
    SESSION_COOKIE_SECURE = False  # Defina como True apenas se estiver usando HTTPS
    
    # Upload settings
    # Configurando o caminho para 'app/static/uploads'
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)),'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB
    
    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour;10 per minute"
    
    # MFA settings
    MFA_EXPIRATION = 60  # 1 minutes in seconds
    
    # Email settings (for MFA)
    # Configurações do Flask-Mail
    MAIL_SERVER = 'smtp.gmail.com'  # Exemplo para Gmail
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # Coloque suas credenciais
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@example.com')
