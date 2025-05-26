from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import Usuario

class RegistrationForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirmar_senha = PasswordField('Confirmar Senha', 
                                  validators=[DataRequired(), EqualTo('senha')])
    submit = SubmitField('Registrar')

    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario:
            raise ValidationError('Este email já está em uso. Por favor escolha outro.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Login')

class MFAForm(FlaskForm):
    mfa_code = IntegerField('Código de Verificação', validators=[DataRequired()])
    submit = SubmitField('Verificar')