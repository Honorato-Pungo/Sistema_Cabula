import logging
import pdb
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, current_user
from app.auth.forms import LoginForm, RegistrationForm, MFAForm
from app.models import Usuario, Sessao
from app import db, bcrypt, limiter, mail
from app.auth.utils import send_mfa_email
import pyotp
from datetime import datetime, timedelta
import time
from user_agents import parse
from flask_mail import Message

# Logger para depuração
logger = logging.getLogger(__name__)

auth = Blueprint('auth', __name__)

# Tempo de bloqueio após falha (em segundos)
COOLDOWN_TIME = 60 * 30  # 30 minutos de cooldown

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    ip_address = request.remote_addr
    # Obter o tempo da última falha de login para o IP
    last_failed_login = session.get(f"last_failed_login_{ip_address}")
    failed = session.get(f"failed_{ip_address}") or 0

    # Verificar o tempo restante de bloqueio
    if last_failed_login and failed >= 5:
        blocked_until = last_failed_login + COOLDOWN_TIME
        time_remaining = blocked_until - time.time()

        if time_remaining > 0:
            return render_template('errors/limite_excedido.html', time_remaining=time_remaining)
        else:
            session.pop(f"failed_{ip_address}", None)

    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        
        if usuario:
            # Salvar o ID do usuário e a data de expiração da MFA na sessão
            session['mfa_user_id'] = usuario.id
            session['mfa_expiry'] = (datetime.utcnow() + timedelta(seconds=current_app.config['MFA_EXPIRATION'])).timestamp()

            # Verificar se a conta está bloqueada devido a tentativas falhadas
            if usuario.tentativas_falhadas >= 10:
                usuario.is_locked = True
                db.session.commit()
                flash('Sua conta foi bloqueada devido a muitas tentativas falhadas. Verifique seu email para desbloqueio.', 'danger')
                return redirect(url_for('auth.mfa_verify'))

            # Verificar senha fornecida pelo usuário
            if usuario.verificar_senha(form.senha.data):
                usuario.tentativas_falhadas = 0
                db.session.commit()

                # Informações sobre o dispositivo e IP
                ip_atual = request.remote_addr
                user_agent = parse(request.headers.get('User-Agent'))
                dispositivo_atual = user_agent.device.family
                navegador_atual = user_agent.browser.family

                # Verificar sessões ativas e, se necessário, enviar MFA
                sessoes_ativas = Sessao.query.filter_by(usuario_id=usuario.id).all()
                for sessao in sessoes_ativas:
                    if sessao.ip != ip_atual or sessao.dispositivo != dispositivo_atual:
                        if usuario.mfa_secret:
                            totp = pyotp.TOTP(usuario.mfa_secret)
                            mfa_code = totp.now()
                            send_mfa_email(usuario.email, mfa_code)

                            flash('Um código de verificação foi enviado para seu email', 'info')
                            return redirect(url_for('auth.mfa_verify'))

                # Login bem-sucedido, criando uma nova sessão
                login_user(usuario, remember=form.remember.data)

                nova_sessao = Sessao(
                    usuario_id=usuario.id,
                    ip=ip_atual,
                    dispositivo=dispositivo_atual,
                    navegador=navegador_atual,
                    data_login=datetime.utcnow()
                )
                db.session.add(nova_sessao)
                db.session.commit()

                # Elimina as tentativas de erro armazenadas na sessao
                # Remove o valor da chave 'test' da sessão
                session.pop(f"last_failed_login_{ip_address}", None)
                session.pop(f"failed_{ip_address}", None)

                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.index'))

            else:
                # Incrementando tentativas falhadas em caso de senha incorreta
                usuario.tentativas_falhadas += 1
                db.session.commit()

                # Salvar timestamp da falha na sessão
                session[f"last_failed_login_{ip_address}"] = time.time()
                # Salvar regista o numero de tentativas
                if session.get(f"failed_{ip_address}"):
                    session[f"failed_{ip_address}"] = session.get(f"failed_{ip_address}") + 1
                else:
                     session[f"failed_{ip_address}"] = 1

                if usuario.tentativas_falhadas >= 10:
                    usuario.is_locked = True
                    db.session.commit()
                    flash('Sua conta foi bloqueada devido a muitas tentativas falhadas. Verifique seu email para desbloqueio.', 'danger')

                    return redirect(url_for('auth.mfa_verify'))
                else:
                    flash('Login inválido. Verifique seu email e senha', 'danger')

        else:
            flash('Login inválido. Verifique seu email e senha', 'danger')

    # Adicionando o ponto de depuração
    #pdb.set_trace()  # Aqui a execução do código será pausada para depuração

    return render_template('auth/login.html', title='Login', form=form)

@auth.route('/mfa_verify', methods=['GET', 'POST'])
def mfa_verify():
    if 'mfa_user_id' not in session:
        return redirect(url_for('auth.login'))
    
    form = MFAForm()
    # Verificar se o código MFA ainda é válido
    if 'mfa_expiry' in session:
        mfa_expiry = session['mfa_expiry']
        time_remaining = mfa_expiry - time.time()
    else:
        time_remaining = 0  # Se não existir expiração armazenada, setamos 0

   
        usuario = Usuario.query.get(session['mfa_user_id'])
        if usuario:
            totp = pyotp.TOTP(usuario.mfa_secret)
            if totp.verify(form.mfa_code.data):
                login_user(usuario)
                session.pop('mfa_user_id')
                session.pop('mfa_expiry')
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('main.index'))
        
        flash('Código de verificação inválido', 'danger')
    
    return render_template('auth/mfa_verify.html', title='Verificação MFA', form=form, time_remaining=time_remaining)

@auth.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_senha = bcrypt.generate_password_hash(form.senha.data).decode('utf-8')
        usuario = Usuario(
            nome=form.nome.data,
            email=form.email.data,
            senha_hash=hashed_senha,
            plano='gratuito'
        )
        db.session.add(usuario)
        db.session.commit()
        flash('Sua conta foi criada! Agora você pode fazer login', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/registrar.html', title='Registrar', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

def send_security_alert_email(email):
    """ Enviar um alerta de segurança por e-mail sobre tentativas de login """
    msg = Message(
        'Alerta de Tentativa de Login',
        sender='no-reply@seusite.com',
        recipients=[email]
    )
    msg.body = '''
    Detectamos uma tentativa de login em sua conta. Se você não foi responsável por essa tentativa, por favor, altere sua senha imediatamente.

    Se foi você quem fez essa tentativa, ignore este e-mail.
    '''
    mail.send(msg)

@auth.route('/resend_mfa_code', methods=['GET'])
def resend_mfa_code():
    usuario_id = session.get('mfa_user_id')
    if not usuario_id:
        flash('Você precisa estar autenticado para reenviar o código.', 'danger')
        return redirect(url_for('auth.login'))
    
    usuario = Usuario.query.get(usuario_id)
    if usuario:
        # Enviar novo código MFA
        totp = pyotp.TOTP(usuario.mfa_secret)
        mfa_code = totp.now()
        send_mfa_email(usuario.email, mfa_code)
        flash('Novo código de verificação enviado para o seu e-mail.', 'info')
        return redirect(url_for('auth.mfa_verify'))
    
    flash('Ocorreu um erro ao reenviar o código.', 'danger')
    return redirect(url_for('auth.login'))
