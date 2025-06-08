from flask import current_app
from flask import url_for, flash, current_app
from flask_mail import Message
from app import mail
import pyotp
import jwt
import datetime
import smtplib
import pdb
from user_agents import parse



def send_mfa_email(email, mfa_code):
    msg = Message(
        'Seu Código de Verificação MFA',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[email]
    )
    msg.body = f'''
    Seu código de verificação para o Sistema Cabula é: {mfa_code}
    
    Este código é válido por 5 minutos. Não compartilhe este código com ninguém.
    
    Se você não solicitou este código, por favor ignore este email.
    '''
    try:
        #mail.send(msg)
        #flash("E-mail de verificação enviado com sucesso!", "success")
        return True
    except smtplib.SMTPException as e:
        flash(f"Erro ao enviar o e-mail: {str(e)}", "danger")
        return False
    # Ponto de interrupção para debug
    #pdb.set_trace()

def generate_mfa_secret():
    return pyotp.random_base32()

def verify_mfa_code(secret, code):
    totp = pyotp.TOTP(secret)
    return totp.verify(code)

def generate_auth_token(user):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)  # Token válido por 15 minutos
    token = jwt.encode({
        'user_id': user.id,
        'exp': expiration
    }, current_app.config['SECRET_KEY'], algorithm='HS256')

    return token

def send_email_with_auth_token(to_email, token):
    base_url = current_app.config['BASE_URL_IP']
    verification_link = f"{base_url}{url_for('auth.authenticate_with_token', token=token)}"
    
    msg = Message("Verificação de MFA", 
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[to_email])
    msg.body = f"Código de verificação: {verification_link}"

    try:
        #mail.send(msg)
        #flash("E-mail de verificação enviado com sucesso!", "success")
        pass
    except smtplib.SMTPException as e:
        flash(f"Erro ao enviar o e-mail: {str(e)}", "danger")
    # Ponto de interrupção para debug
    #pdb.set_trace()

def send_email_with_auth_token_for_new_device(to_email, token):
    base_url = current_app.config['BASE_URL_IP']
    verification_link = f"{base_url}{url_for('auth.verify_device', token=token)}"
    print("link de verificacao", verification_link)
    
    msg = Message("Verificação de MFA", 
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[to_email])
    msg.body = f"Código de verificação: {verification_link}"

    try:
        #mail.send(msg)
        #flash("E-mail de verificação enviado com sucesso!", "success")
        pass
    except smtplib.SMTPException as e:
        flash(f"Erro ao enviar o e-mail: {str(e)}", "danger")
    # Ponto de interrupção para debug
    #pdb.set_trace()

def gerar_fingerprint(request):
    ua = parse(request.headers.get('User-Agent'))
    return f"{ua.os.family}-{ua.browser.family}-{ua.device.family}"
