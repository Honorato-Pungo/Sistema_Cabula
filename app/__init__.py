from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from config import Config
from flask_mail import Mail
import os
from flask import Flask, render_template
from flask_session import Session
import pdb
from datetime import datetime, timedelta
import time

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

    app.config['SESSION_TYPE'] = 'filesystem'  # Tipo de sessão (pode ser 'filesystem' ou 'redis')
    app.config['SESSION_PERMANENT'] = True
    Session(app)
    
    # Registra os blueprints
    from app.auth.routes import auth
    from app.main.routes import main
    from app.admin.routes import admin
    #from app.errors.routes import errors

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(admin)
    #app.register_blueprint(errors)  # Registra o blueprint de erros

    # Verificar e criar o diretório de uploads se não existir
    upload_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # Manipulador para o erro 429 (Too Many Requests)
    @app.errorhandler(429)
    def rate_limit_error(e):
        # Redirecionar o usuário para a página de erro
        ip_address = request.remote_addr
        last_failed_login = session.get(f"last_failed_login_{ip_address}")

        if last_failed_login is None:
            last_failed_login = datetime.utcnow()

        # Calcular o tempo até o desbloqueio
        blocked_until = last_failed_login + (app.config['COOLDOWN_TIME'])
        
        time_remaining = blocked_until - time.time()
        
        # Garantir que time_remaining não seja negativo (caso o bloqueio tenha expirado)
        if time_remaining < 0:
            time_remaining = 0

        # Limpar a chave "failed" da sessão para impedir tentativas repetidas
        session.pop(f"failed_{ip_address}", None)

        return render_template('errors/limite_excedido.html', time_remaining=time_remaining)

    return app