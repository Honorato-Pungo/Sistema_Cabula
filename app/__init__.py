from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from config import Config
from flask_mail import Mail

# Inicializando as extensões
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
migrate = Migrate()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializa as extensões
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Configura o login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Registra os blueprints
    from app.auth.routes import auth
    from app.main.routes import main
    from app.admin.routes import admin

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(admin)

    # Não usamos db.create_all() aqui, agora gerenciamos o banco com migrações
    # As migrações são aplicadas com os comandos flask db migrate e flask db upgrade

    return app

