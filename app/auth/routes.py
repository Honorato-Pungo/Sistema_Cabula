from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.auth.forms import LoginForm, RegistrationForm, MFAForm
from app.models import Usuario
from app import db, bcrypt, limiter
from app.auth.utils import send_mfa_email
from flask import session, current_app
import pyotp
import datetime


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        
        if usuario and usuario.verificar_senha(form.senha.data):
            # Verificar se MFA está habilitado
            if usuario.mfa_secret:
                # Gerar código MFA e enviar por email
                totp = pyotp.TOTP(usuario.mfa_secret)
                mfa_code = totp.now()
                send_mfa_email(usuario.email, mfa_code)
                
                # Armazenar temporariamente o ID do usuário na sessão
                session['mfa_user_id'] = usuario.id
                session['mfa_expiry'] = (datetime.datetime.utcnow() + 
                                       datetime.timedelta(seconds=current_app.config['MFA_EXPIRATION'])).timestamp()
                
                flash('Um código de verificação foi enviado para seu email', 'info')
                return redirect(url_for('auth.mfa_verify'))
            
            # Se MFA não estiver habilitado, fazer login diretamente
            login_user(usuario, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Login inválido. Verifique seu email e senha', 'danger')
    
    return render_template('auth/login.html', title='Login', form=form)

@auth.route('/mfa_verify', methods=['GET', 'POST'])
def mfa_verify():
    if 'mfa_user_id' not in session:
        return redirect(url_for('auth.login'))
    
    form = MFAForm()
    if form.validate_on_submit():
        # Verificar se o código MFA ainda é válido
        if datetime.datetime.utcnow().timestamp() > session['mfa_expiry']:
            flash('O código de verificação expirou. Por favor, faça login novamente', 'danger')
            return redirect(url_for('auth.login'))
        
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
    
    return render_template('auth/mfa_verify.html', title='Verificação MFA', form=form)

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