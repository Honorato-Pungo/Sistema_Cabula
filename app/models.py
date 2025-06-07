from datetime import datetime
from app import db, bcrypt, login_manager
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from sqlalchemy import Enum
import pyotp

# Função obrigatória para o Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    plano = db.Column(db.String(20), default='gratuito', nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # Campos de segurança
    email_confirmado = db.Column(db.Boolean, default=False, nullable=False)  # Flag para confirmar o e-mail
    email_confirmacao_token = db.Column(db.String(100), nullable=True)  # Token para confirmação de e-mail
    mfa_secret = db.Column(db.String(16), default=True,  nullable=True)  # Chave de MFA (autenticação multifatorial)
    deletado_em = db.Column(db.DateTime, nullable=True)  # Soft delete (exclusão lógica)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)  # Flag para conta bloqueada devido a falhas
    tentativas_falhadas = db.Column(db.Integer, default=0)  # Contador de tentativas falhadas

    data_criacao = db.Column(db.DateTime, default=datetime.now)

    # Relacionamentos
    trabalhos = db.relationship('Trabalho', backref='autor', lazy=True)
    provas = db.relationship('Prova', backref='autor', lazy=True)
    solicitacoes_upgrade = db.relationship('SolicitacaoUpgrade', backref='usuario', lazy=True)

    # Propriedades e métodos de senha
    @property
    def senha(self):
        raise AttributeError('senha não é um atributo legível')

    @senha.setter
    def senha(self, senha):
        self.senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')

    def verificar_senha(self, senha):
        return bcrypt.check_password_hash(self.senha_hash, senha)

    # Funções relacionadas a e-mail
    def gerar_token_confirmacao_email(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'usuario_id': self.id}, salt='email-confirmation-salt')

    @staticmethod
    def verificar_token_confirmacao_email(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt='email-confirmation-salt', max_age=3600)  # Expira em 1h
        except:
            return None
        return Usuario.query.get(data['usuario_id'])

    # Funções de MFA
    def gerar_token_mfa(self):
        """Gera um token MFA para o usuário usando o segredo MFA"""
        if self.mfa_secret:
            totp = pyotp.TOTP(self.mfa_secret)
            return totp.now()
        return None

    def verificar_mfa(self, mfa_code):
        """Verifica se o código MFA fornecido é válido"""
        if self.mfa_secret:
            totp = pyotp.TOTP(self.mfa_secret)
            return totp.verify(mfa_code)
        return False

    # Soft delete: desativa a conta sem excluir os dados
    def deletar(self):
        self.deletado_em = datetime.utcnow()
        db.session.commit()

    def restaurar(self):
        self.deletado_em = None
        db.session.commit()

    def bloquear(self):
        """Bloqueia a conta devido a tentativas falhadas de login"""
        self.is_locked = True
        db.session.commit()

    def desbloquear(self):
        """Desbloqueia a conta após MFA"""
        self.is_locked = False
        self.tentativas_falhadas = 0  # Reseta as tentativas falhadas
        db.session.commit()

    def incrementar_tentativas(self):
        """Incrementa o número de tentativas falhadas"""
        self.tentativas_falhadas += 1
        db.session.commit()

    def resetar_tentativas(self):
        """Reseta o contador de tentativas falhadas"""
        self.tentativas_falhadas = 0
        db.session.commit()

    def __repr__(self):
        return f"Usuario('{self.nome}', '{self.email}', '{self.plano}')"

class Trabalho(db.Model):
    __tablename__ = 'trabalhos'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autores = db.Column(db.String(200), nullable=False)
    disciplina = db.Column(db.String(100), nullable=False)
    periodo = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    palavras_chave = db.Column(db.String(200))
    nivel_acesso = db.Column(db.String(20), default='publico', nullable=False)
    arquivo = db.Column(db.String(100), nullable=False)
    aprovado = db.Column(db.Boolean, default=False, nullable=False)
    data_submissao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    def __repr__(self):
        return f"Trabalho('{self.titulo}', '{self.disciplina}', '{self.tipo}')"


class Prova(db.Model):
    __tablename__ = 'provas'

    id = db.Column(db.Integer, primary_key=True)
    disciplina = db.Column(db.String(100), nullable=False)
    professor = db.Column(db.String(100), nullable=False)
    data_prova = db.Column(db.Date, nullable=False)
    arquivo_enunciado = db.Column(db.String(100), nullable=False)
    arquivo_resolucao = db.Column(db.String(100))
    aprovado = db.Column(db.Boolean, default=True, nullable=False)
    data_submissao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    def __repr__(self):
        return f"Prova('{self.disciplina}', '{self.professor}', '{self.data_prova}')"


class SolicitacaoUpgrade(db.Model):
    __tablename__ = 'solicitacoes_upgrade'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow)
    aprovada = db.Column(db.Boolean, default=False, nullable=False)
    data_aprovacao = db.Column(db.DateTime)

    def __repr__(self):
        return f"SolicitacaoUpgrade('{self.usuario_id}', '{self.data_solicitacao}', '{self.aprovada}')"

class Sessao(db.Model):
    __tablename__ = 'sessoes'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    ip = db.Column(db.String(45), nullable=False)  # Suporta IPv6
    dispositivo = db.Column(db.String(255), nullable=False)
    navegador = db.Column(db.String(255), nullable=False)
    data_login = db.Column(db.DateTime, default=datetime.utcnow)
    expirado = db.Column(db.Boolean, default=False, nullable=False)
    
    usuario = db.relationship('Usuario', backref='sessoes', lazy=True)

    def __repr__(self):
        return f"<Sessao(usuario_id={self.usuario_id}, ip={self.ip}, dispositivo={self.dispositivo}, navegador={self.navegador}, data_login={self.data_login})>"
