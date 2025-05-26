from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

class AprovarTrabalhoForm(FlaskForm):
    acao = SelectField('Ação', choices=[
        ('aprovar', 'Aprovar Trabalho'),
        ('rejeitar', 'Rejeitar Trabalho')
    ], validators=[DataRequired()])
    motivo = TextAreaField('Motivo (opcional)')
    submit = SubmitField('Confirmar')

class AprovarUpgradeForm(FlaskForm):
    acao = SelectField('Ação', choices=[
        ('aprovar', 'Aprovar Upgrade'),
        ('rejeitar', 'Rejeitar Solicitação')
    ], validators=[DataRequired()])
    motivo = TextAreaField('Motivo (opcional)')
    submit = SubmitField('Confirmar')