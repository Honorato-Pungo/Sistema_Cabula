import logging
import time
import io
import base64
import qrcode
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app.auth.forms import LoginForm, RegistrationForm, MFAForm
from app.models import Usuario, Sessao
from app import db, bcrypt, mail
from app.auth.utils import send_mfa_email
from datetime import datetime, timedelta
import pyotp
from user_agents import parse
from flask_mail import Message

auth = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

COOLDOWN_TIME = 60 * 30  # 30 minutos

# ========== LOGIN ==========
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    ip_address = request.remote_addr
    last_failed_login = session.get(f"last_failed_login_{ip_address}")
    failed = session.get(f"failed_{ip_address}") or 0

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
        if usuario and usuario.verificar_senha(form.senha.data):
            if usuario.tentativas_falhadas >= 10:
                usuario.is_locked = True
                db.session.commit()
                flash('Conta bloqueada por tentativas incorretas. Contate o suporte.', 'danger')
                return redirect(url_for('auth.login'))

            usuario.tentativas_falhadas = 0
            db.session.commit()

            # Verificar se o MFA está ativado para o usuário
            if usuario.mfa_secret:
                session['mfa_user_id'] = usuario.id
                session['mfa_expiry'] = (datetime.utcnow() + timedelta(seconds=current_app.config['MFA_EXPIRATION'])).timestamp()
                return redirect(url_for('auth.mfa_verify'))  # Redireciona para verificação do MFA

            # Caso o MFA não esteja ativado, realiza o login normalmente
            login_user(usuario)

            # Criar a sessão de login
            ip = request.remote_addr
            user_agent = parse(request.headers.get('User-Agent'))
            sessao = Sessao(
                usuario_id=usuario.id,
                ip=ip,
                dispositivo=user_agent.device.family,
                navegador=user_agent.browser.family,
                data_login=datetime.utcnow()
            )
            db.session.add(sessao)
            db.session.commit()

            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('main.index'))

        elif usuario:
            usuario.tentativas_falhadas += 1
            db.session.commit()
            session[f"last_failed_login_{ip_address}"] = time.time()
            session[f"failed_{ip_address}"] = failed + 1
            flash('Credenciais inválidas.', 'danger')
        else:
            flash('Credenciais inválidas.', 'danger')

    return render_template('auth/login.html', title='Login', form=form)


# ========== MFA SETUP ==========
@auth.route('/mfa/setup')
@login_required
def mfa_setup():
    if current_user.mfa_secret:
        flash('MFA já está ativado.', 'info')
        return redirect(url_for('main.index'))

    secret = pyotp.random_base32()
    session['temp_mfa_secret'] = secret

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.email, issuer_name="SeuSistema")

    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf)
    qr_code = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template('auth/mfa_setup.html', qr_code=qr_code, secret=secret)


@auth.route('/mfa/setup/confirm', methods=['POST'])
@login_required
def mfa_setup_confirm():
    code = request.form.get('code')
    secret = session.get('temp_mfa_secret')

    if not secret:
        flash('Chave MFA expirada. Tente novamente.', 'danger')
        return redirect(url_for('auth.mfa_setup'))

    totp = pyotp.TOTP(secret)
    if totp.verify(code):
        current_user.mfa_secret = secret
        db.session.commit()
        session.pop('temp_mfa_secret', None)
        flash('MFA ativado com sucesso!', 'success')
        return redirect(url_for('main.index'))
    else:
        flash('Código inválido.', 'danger')
        return redirect(url_for('auth.mfa_setup'))


# ========== MFA VERIFY ==========
@auth.route('/mfa_verify', methods=['GET', 'POST'])
def mfa_verify():
    if 'mfa_user_id' not in session:
        return redirect(url_for('auth.login'))

    form = MFAForm()
    usuario = Usuario.query.get(session['mfa_user_id'])

    if request.method == 'POST':
        totp = pyotp.TOTP(usuario.mfa_secret)
        if totp.verify(form.mfa_code.data):
            # Criar a sessão de login após a verificação do MFA
            login_user(usuario)
            session.pop('mfa_user_id', None)
            session.pop('mfa_expiry', None)

            ip = request.remote_addr
            user_agent = parse(request.headers.get('User-Agent'))
            sessao = Sessao(
                usuario_id=usuario.id,
                ip=ip,
                dispositivo=user_agent.device.family,
                navegador=user_agent.browser.family,
                data_login=datetime.utcnow()
            )
            db.session.add(sessao)
            db.session.commit()

            flash('Login com MFA realizado!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Código MFA inválido.', 'danger')

    time_remaining = session.get('mfa_expiry', 0) - time.time()
    return render_template('auth/mfa_verify.html', title='Verificação MFA', form=form, time_remaining=time_remaining)


# ========== MFA RESEND ==========
@auth.route('/resend_mfa_code')
def resend_mfa_code():
    usuario_id = session.get('mfa_user_id')
    if not usuario_id:
        flash('Você não está autenticado.', 'danger')
        return redirect(url_for('auth.login'))

    usuario = Usuario.query.get(usuario_id)
    if usuario and usuario.mfa_secret:
        totp = pyotp.TOTP(usuario.mfa_secret)
        mfa_code = totp.now()
        send_mfa_email(usuario.email, mfa_code)
        flash('Novo código enviado por e-mail.', 'info')
        return redirect(url_for('auth.mfa_verify'))

    flash('Erro ao enviar código.', 'danger')
    return redirect(url_for('auth.login'))


# ========== REGISTRO ==========
@auth.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        senha_hash = bcrypt.generate_password_hash(form.senha.data).decode('utf-8')
        usuario = Usuario(
            nome=form.nome.data,
            email=form.email.data,
            senha_hash=senha_hash,
            plano='gratuito'
        )
        db.session.add(usuario)
        db.session.commit()
        flash('Conta criada! Faça login agora.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/registrar.html', title='Registrar', form=form)


# ========== LOGOUT ==========
@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


# ========== ALERTA DE SEGURANÇA ==========
def send_security_alert_email(email):
    msg = Message('Alerta de Login', sender='no-reply@seusite.com', recipients=[email])
    msg.body = '''
Detectamos uma tentativa de login na sua conta. Se não foi você, altere sua senha.
Se foi você, ignore este e-mail.
    '''
    mail.send(msg)

@auth.route('/mfa/deactivate')
@login_required
def mfa_deactivate():
    current_user.mfa_secret = None
    db.session.commit()
    flash('MFA desativado com sucesso!', 'success')
    return redirect(url_for('auth.painel'))  # Redireciona para o painel do usuário
