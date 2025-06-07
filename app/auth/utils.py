from flask import current_app
from flask_mail import Message
from app import mail
import pyotp
import jwt
import datetime


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
    mail.send(msg)

def generate_mfa_secret():
    return pyotp.random_base32()

def verify_mfa_code(secret, code):
    totp = pyotp.TOTP(secret)
    return totp.verify(code)

def generate_auth_token(user):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)  # Token válido por 15 minutos
    token = jwt.encode({
        'user_id': user.id,
        'exp': expiration
    }, current_app.config['SECRET_KEY'], algorithm='HS256')

    return token

def send_email_with_auth_token(email, token):
    msg = Message('Autenticação via E-mail', sender='no-reply@seusite.com', recipients=[email])
    msg.body = f'Clique no link abaixo para autenticar sua conta:\n\n{url_for("auth.authenticate_with_token", token=token, _external=True)}'
    mail.send(msg)