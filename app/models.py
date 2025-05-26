from datetime import datetime
from app import db, bcrypt, login_manager
from flask_login import UserMixin

# Função obrigatória para o Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'  # Define explicitamente o nome da tabela

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    plano = db.Column(db.String(20), default='gratuito', nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    email_confirmado = db.Column(db.Boolean, default=False, nullable=False)
    mfa_secret = db.Column(db.String(16))
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
