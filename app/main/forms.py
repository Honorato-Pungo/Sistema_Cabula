from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, FileField, SubmitField
from wtforms.validators import DataRequired, Length
from datetime import date

class TrabalhoForm(FlaskForm):
    titulo = StringField('Título do Trabalho', validators=[DataRequired(), Length(max=200)])
    autores = StringField('Autor(es)', validators=[DataRequired(), Length(max=200)])
    disciplina = StringField('Disciplina', validators=[DataRequired(), Length(max=100)])
    periodo = StringField('Período Acadêmico', validators=[DataRequired(), Length(max=50)])
    tipo = SelectField('Tipo de Trabalho', choices=[
        ('tese', 'Tese'), 
        ('dissertacao', 'Dissertação'),
        ('projeto', 'Projeto'),
        ('artigo', 'Artigo'),
        ('relatorio', 'Relatório'),
        ('outro', 'Outro')
    ], validators=[DataRequired()])
    palavras_chave = StringField('Palavras-chave (separadas por vírgula)')
    nivel_acesso = SelectField('Nível de Acesso', choices=[
        ('publico', 'Público'),
        ('restrito', 'Restrito à Instituição'),
        ('privado', 'Privado (apenas para avaliação)')
    ], validators=[DataRequired()])
    arquivo = FileField('Arquivo do Trabalho (PDF ou DOCX)', validators=[DataRequired()])
    submit = SubmitField('Submeter Trabalho')

class ProvaForm(FlaskForm):
    disciplina = StringField('Disciplina', validators=[DataRequired(), Length(max=100)])
    professor = StringField('Professor Responsável', validators=[DataRequired(), Length(max=100)])
    data_prova = DateField('Data da Prova', default=date.today, validators=[DataRequired()])
    arquivo_enunciado = FileField('Enunciado da Prova (PDF ou DOCX)', validators=[DataRequired()])
    arquivo_resolucao = FileField('Resolução da Prova (Opcional)')
    submit = SubmitField('Submeter Prova')

class UpgradeForm(FlaskForm):
    submit = SubmitField('Solicitar Upgrade para Premium')