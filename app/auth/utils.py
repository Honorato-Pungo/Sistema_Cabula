from flask import current_app
from flask_mail import Message
from app import mail
import pyotp


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