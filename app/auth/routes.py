import logging
import time
import io
import base64
import qrcode
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app.auth.forms import LoginForm, RegistrationForm, MFAForm
from app.models import Usuario, Sessao
from app import db, bcrypt, mail, limiter
from app.auth.utils import send_mfa_email, generate_auth_token, send_email_with_auth_token, gerar_fingerprint, send_email_with_auth_token_for_new_device
from datetime import datetime, timedelta
import pyotp
from user_agents import parse
from flask_mail import Message
import pdb
import jwt

auth = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

COOLDOWN_TIME = 60 * 1  # 30 minutos

# ========== LOGIN ==========
@auth.route('/login', methods=['GET', 'POST'])
#@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    ip_address = request.remote_addr
    last_failed_login = session.get(f"last_failed_login_{ip_address}")
    failed = session.get(f"failed_{ip_address}") or 0

    if last_failed_login and failed >= 5:
        blocked_until = last_failed_login + COOLDOWN_TIME
        time_remaining = blocked_until - time.time()
        session[f"time_remaining_{ip_address}"] = time_remaining

        if time_remaining > 0:
            return render_template('errors/limite_excedido.html', time_remaining=time_remaining)
        else:
            session.pop(f"failed_{ip_address}", None)

    form = LoginForm()
    
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        if usuario and usuario.verificar_senha(form.senha.data):
            fingerprint = gerar_fingerprint(request)
            # Verifica se fingerprint já existe
            sessao_existente = Sessao.query.filter_by(usuario_id=usuario.id, fingerprint=fingerprint).first()

            if not sessao_existente:
                # Novo dispositivo detectado → enviar verificação por e-mail
                token = generate_auth_token(usuario)
                send_email_with_auth_token_for_new_device(usuario.email, token)

                session['pending_user_id'] = usuario.id
                session['pending_fingerprint'] = fingerprint

                flash('Detectamos um novo dispositivo. Verifique seu e-mail para continuar.', 'warning')
                return redirect(url_for('auth.login'))  # Ou página de "aguardando verificação"

            if usuario.tentativas_falhadas == 5:
                #send_security_alert_email(usuario.email)
                pass

            if usuario.tentativas_falhadas >= 10:
                usuario.is_locked = True
                usuario.email_confirmado = False
                is_locked = True
                session['mfa_email'] = usuario.email

                """send_security_alert_email(email=usuario.email,
                    message='''
                    A tua conta esta bloqueda devido a varias tentativas de login. Se não foi você, altere sua senha.
                    Se foi você, ignore este e-mail.''')"""
                db.session.commit()
                #flash('Conta bloqueada por tentativas incorretas. Contate o suporte.', 'danger')
                #return redirect(url_for('auth.login'))
                return render_template('auth/login.html', form=form, is_locked=is_locked)

            usuario.tentativas_falhadas = 0
            db.session.commit()

            # Verificar se o MFA está ativado para o usuário
            if usuario.mfa_secret:
                session['mfa_user_id'] = usuario.id
                session['mfa_expiry'] = (datetime.utcnow() + timedelta(seconds=current_app.config['MFA_EXPIRATION'])).timestamp()

                print(f"Valor de mfa_tipo: '{usuario.mfa_tipo}'")  # Os apóstrofos ajudam a visualizar espaços extras

                if usuario.mfa_tipo.strip() == "app":
                    return redirect(url_for('auth.mfa_verify'))  # Redireciona para verificação do MFA
                else:
                    return redirect(url_for('auth.mfa_email_verify'))

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
                fingerprint=fingerprint,
                data_login=datetime.utcnow()
            )
            db.session.add(sessao)
            db.session.commit()

            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('main.index'))

        elif usuario:
            usuario.tentativas_falhadas += 1
            session[f"last_failed_login_{ip_address}"] = time.time()
            session[f"failed_{ip_address}"] = failed + 1

            db.session.commit()
            flash('Credenciais inválidas.', 'danger')
        else:
            session[f"last_failed_login_{ip_address}"] = time.time()
            """session[f"failed_{ip_address}"] = failed + 1"""
            
            flash('Credenciais inválidas.', 'danger')

    # Ponto de interrupção para debug
    #pdb.set_trace()
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
    uri = totp.provisioning_uri(name=current_user.email, issuer_name="Cabula")

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
            return redirect(url_for('main.dashboard'))
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
    secret = session.get('mfa_secret')

    if usuario and secret:
        totp = pyotp.TOTP(secret)
        mfa_code = totp.now()
        send_mfa_email(usuario.email, mfa_code)
        flash('Novo código enviado por e-mail.', 'info')
        return redirect(url_for('auth.mfa_email_verify'))

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
    print("estou aqui", session.get('_user_id'))
    if '_user_id' in session:
        # Deleta a sessão associada ao usuário no banco de dados
        sessao = Sessao.query.filter_by(usuario_id=session['_user_id']).first()

        print("sessao em: ",sessao)

        if sessao:
            db.session.delete(sessao)
            db.session.commit()
    
    logout_user()
        
    return redirect(url_for('main.index'))

# Verificando a expiração da sessão antes de cada requisição
@auth.before_request
def verificar_sessao_expirada():
    if '_user_id' in session:
        # Recupera a sessão do banco de dados
        sessao = Sessao.query.filter_by(usuario_id=session['_user_id']).first()
        
        if sessao and sessao.data_login < datetime.utcnow():
             # Se a sessão expirou, faz o logout e remove o registro da sessão
            logout_user()  # Faz o logout do usuário

            db.session.delete(sessao)
            db.session.commit()

            #flash("Sua sessão expirou.", "warning")
            return redirect(url_for('auth.login'))

@auth.before_request
def renovar_sessao():
    # Renovar a sessão se o usuário estiver autenticado
    if '_user_id' in session:
        session.permanent = True  # Ativa a expiração automática
        current_app.permanent_session_lifetime = current_app.config['PERMANENT_SESSION_LIFETIME']
        
        # Renovar a data de expiração da sessão no banco de dados
        sessao = Sessao.query.filter_by(user_id=session['_user_id']).first()
        if sessao:
            sessao.data_login = datetime.utcnow() + current_app.config['PERMANENT_SESSION_LIFETIME']
            db.session.commit()            

# ========== ALERTA DE SEGURANÇA ==========
def send_security_alert_email(email, message=None):
    msg = Message('Alerta de Login', sender='jkotingo25@gmail.com', recipients=[email])
    msg.body = message or '''
    Detectamos uma tentativa de login na sua conta. Se não foi você, altere sua senha.
    Se foi você, ignore este e-mail.
    '''
    try:
        #mail.send(msg)
        pass
    except smtplib.SMTPException as e:
        pass

@auth.route('/mfa/deactivate')
@login_required
def mfa_deactivate():
    current_user.mfa_secret = None
    current_user.mfa_tipo = None
    db.session.commit()
    flash('MFA desativado com sucesso!', 'success')
    return redirect(url_for('main.dashboard'))  # Redireciona para o painel do usuário

# ========== SEND MFA CODE BY EMAIL ==========
@auth.route('/send_mfa_email', methods=['POST'])
def send_mfa_email_request():
    email = session.get('mfa_email')

    usuario = Usuario.query.filter_by(email=email).first()
    if usuario and usuario.is_locked:
        # Aqui é onde geramos o link de autenticação único
        token = generate_auth_token(usuario)  # Função para gerar o token
        send_email_with_auth_token(usuario.email, token)
        flash('Link de autenticação enviado para o seu e-mail!', 'info')
        return redirect(url_for('auth.login'))

    flash('Não encontramos uma conta com esse e-mail ou a conta não está bloqueada.', 'danger')
    
    # Ponto de interrupção para debug
    #pdb.set_trace()
    
    return redirect(url_for('auth.login'))

@auth.route('/authenticate/<token>')
def authenticate_with_token(token):
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        usuario = Usuario.query.get(data['user_id'])

        if usuario:
            usuario.is_locked = False
            usuario.email_confirmado = True
            usuario.tentativas_falhadas = 0
            db.session.commit()

            flash('Conta desbloqueada. Agora você pode fazer login.', 'success')
            return redirect(url_for('auth.login'))

    except jwt.ExpiredSignatureError:
        flash('Link expirado.', 'danger')
    except jwt.InvalidTokenError:
        flash('Token inválido.', 'danger')

    return redirect(url_for('auth.login'))

@auth.route('/mfa_email_send')
def mfa_email_send():
    usuario_id = session.get('mfa_user_id')
    if not usuario_id:
        flash('Sessão expirada. Faça login novamente.', 'warning')
        return redirect(url_for('auth.login'))

    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('auth.login'))

    secret = usuario.mfa_secret or pyotp.random_base32()
    if not usuario.mfa_secret:
        usuario.mfa_secret = secret
        db.session.commit()

    session['mfa_secret'] = secret

    totp = pyotp.TOTP(secret)
    codigo = totp.now()
    session['mfa_code'] = codigo
    session['mfa_expiry'] = (datetime.utcnow() + timedelta(seconds=current_app.config['MFA_EXPIRATION'])).timestamp()

    if send_mfa_email(usuario.email, codigo):
        flash('Código enviado para seu e-mail.', 'info')
    else:
        flash('Erro ao enviar o código.', 'danger')
        return redirect(url_for('auth.login'))

    return redirect(url_for('auth.mfa_email_verify'))

@auth.route('/mfa_email_verify', methods=['GET', 'POST'])
def mfa_email_verify():
    usuario_id = session.get('mfa_user_id')
    if not usuario_id:
        flash('Sessão de MFA expirada. Faça login novamente.', 'warning')
        return redirect(url_for('auth.login'))

    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('auth.login'))

    now = time.time()
    mfa_code = session.get('mfa_code')
    mfa_expiry = session.get('mfa_expiry', 0)

    # Só envia se o código não existe ou está expirado
    if not mfa_code or now > mfa_expiry:
        secret = usuario.mfa_secret or pyotp.random_base32()
        if not usuario.mfa_secret:
            usuario.mfa_secret = secret
            db.session.commit()

        session['mfa_secret'] = secret

        totp = pyotp.TOTP(secret)
        codigo = totp.now()
        session['mfa_code'] = codigo
        session['mfa_expiry'] = (datetime.utcnow() + timedelta(seconds=current_app.config['MFA_EXPIRATION'])).timestamp()

        print("codigo de email",codigo)

        if send_mfa_email(usuario.email, codigo):
            flash("Código de verificação enviado para seu e-mail.", "info")
        else:
            flash("Erro ao enviar código. Tente novamente.", "danger")
            return redirect(url_for('auth.login'))

        mfa_expiry = session['mfa_expiry']

    # Calcular tempo restante para reenvio
    tempo_restante = int(session['mfa_expiry'] - now)

    # POST - validação do código
    if request.method == 'POST':
        codigo_digitado = request.form.get('mfa_code', '').strip()
        if not codigo_digitado:
            flash("Digite o código recebido por e-mail.", "warning")
        elif now > mfa_expiry:
            flash("O código expirou. Recarregue a página para gerar um novo.", "danger")
        elif codigo_digitado != mfa_code:
            flash("Código incorreto.", "danger")
        else:
            # Login e criação da sessão
            login_user(usuario)
            session.pop('mfa_user_id', None)
            session.pop('mfa_code', None)
            session.pop('mfa_expiry', None)
            session.pop('mfa_secret', None)

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

            flash("Login com MFA realizado com sucesso!", "success")
            return redirect(url_for('main.dashboard'))

    return render_template('auth/mfa_email_verify.html', tempo_restante=tempo_restante)


@auth.route('/verify_device/<token>')
def verify_device(token):
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        usuario = Usuario.query.get(data['user_id'])

        if not usuario:
            flash('Usuário inválido.', 'danger')
            return redirect(url_for('auth.login'))

        fingerprint = session.get('pending_fingerprint') or gerar_fingerprint(request)
        ua = parse(request.headers.get('User-Agent'))

        # Criar nova sessão
        nova_sessao = Sessao(
            usuario_id=usuario.id,
            ip=request.remote_addr,
            dispositivo=ua.device.family,
            navegador=ua.browser.family,
            fingerprint=fingerprint,
            data_login=datetime.utcnow()
        )
        db.session.add(nova_sessao)
        db.session.commit()

        # Limpar dados temporários
        session.pop('pending_user_id', None)
        session.pop('pending_fingerprint', None)

        # Se usuário tiver MFA → redireciona para MFA
        if usuario.mfa_secret:
            session['mfa_user_id'] = usuario.id
            session['mfa_expiry'] = (datetime.utcnow() + timedelta(seconds=current_app.config['MFA_EXPIRATION'])).timestamp()

            if usuario.mfa_tipo == 'app':
                return redirect(url_for('auth.mfa_verify'))
            else:
                return redirect(url_for('auth.mfa_email_verify'))

        # Caso contrário → login direto
        login_user(usuario)

        flash('Dispositivo autorizado com sucesso!', 'success')
        return redirect(url_for('main.index'))

    except jwt.ExpiredSignatureError:
        flash('O link expirou. Solicite um novo.', 'danger')
    except jwt.InvalidTokenError:
        flash('Token inválido.', 'danger')

    return redirect(url_for('auth.login'))




@auth.route('/mfa_setup_choice', methods=['POST'])
def mfa_setup_choice():
    if not current_user.is_authenticated:
        flash('Você precisa estar logado para configurar MFA.', 'danger')
        return redirect(url_for('auth.login'))

    tipo = request.form.get('mfa_tipo')
    if tipo not in ['email', 'app']:
        flash('Tipo de autenticação inválido.', 'danger')
        return redirect(url_for('main.dashboard'))

    session['mfa_tipo'] = tipo

    flash(f'MFA com {tipo.upper()} selecionado. Continue a configuração.', 'info')
    pdb.set_trace()
    
    if tipo == 'email':
        return redirect(url_for('auth.mfa_email_verify'))
    else:
        return redirect(url_for('auth.mfa_setup'))  # setup do QR Code
