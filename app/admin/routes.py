from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Trabalho, SolicitacaoUpgrade, Usuario
from app.admin.forms import AprovarTrabalhoForm, AprovarUpgradeForm
from app import db
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Trabalho, SolicitacaoUpgrade, Usuario
from app.admin.forms import AprovarTrabalhoForm, AprovarUpgradeForm
from app import db, bcrypt
from datetime import datetime


admin = Blueprint('admin', __name__)

@admin.before_request
@login_required
def require_admin():
    if not current_user.is_admin:
        flash('Acesso restrito a administradores', 'danger')
        return redirect(url_for('main.dashboard'))

@admin.route('/admin/painel')
def painel():
    # Obter estatísticas para o painel
    total_usuarios = Usuario.query.count()
    trabalhos_pendentes_count = Trabalho.query.filter_by(aprovado=False).count()
    solicitacoes_pendentes_count = SolicitacaoUpgrade.query.filter_by(aprovada=False).count()
    trabalhos_aprovados_count = Trabalho.query.filter_by(aprovado=True).count()
    
    return render_template(
        'admin/painel.html',
        total_usuarios=total_usuarios,
        trabalhos_pendentes=trabalhos_pendentes_count,
        solicitacoes_pendentes=solicitacoes_pendentes_count,
        trabalhos_aprovados=trabalhos_aprovados_count
    )

@admin.route('/trabalhos_pendentes')
def trabalhos_pendentes():
    trabalhos = Trabalho.query.filter_by(aprovado=False).all()
    return render_template('admin/trabalhos_pendentes.html', trabalhos=trabalhos)

@admin.route('/aprovar_trabalho/<int:trabalho_id>', methods=['GET', 'POST'])
def aprovar_trabalho(trabalho_id):
    trabalho = Trabalho.query.get_or_404(trabalho_id)
    form = AprovarTrabalhoForm()
    
    if form.validate_on_submit():
        if form.acao.data == 'aprovar':
            trabalho.aprovado = True
            flash('Trabalho aprovado com sucesso!', 'success')
        else:
            # Aqui você poderia adicionar uma mensagem de motivo para rejeição
            db.session.delete(trabalho)
            flash('Trabalho rejeitado e removido do sistema', 'info')
        
        db.session.commit()
        return redirect(url_for('admin.trabalhos_pendentes'))
    
    return render_template('admin/aprovar_trabalho.html', trabalho=trabalho, form=form)

@admin.route('/solicitacoes_upgrade')
def solicitacoes_upgrade():
    solicitacoes = SolicitacaoUpgrade.query.filter_by(aprovada=False).all()
    return render_template('admin/solicitacoes_upgrade.html', solicitacoes=solicitacoes)

@admin.route('/aprovar_upgrade/<int:solicitacao_id>', methods=['GET', 'POST'])
def aprovar_upgrade(solicitacao_id):
    solicitacao = SolicitacaoUpgrade.query.get_or_404(solicitacao_id)
    form = AprovarUpgradeForm()
    
    if form.validate_on_submit():
        if form.acao.data == 'aprovar':
            usuario = solicitacao.usuario
            usuario.plano = 'premium'
            solicitacao.aprovada = True
            solicitacao.data_aprovacao = datetime.utcnow()
            flash('Upgrade aprovado com sucesso!', 'success')
        else:
            flash('Solicitação de upgrade rejeitada', 'info')
        
        db.session.commit()
        return redirect(url_for('admin.solicitacoes_upgrade'))
    
    return render_template('admin/aprovar_upgrade.html', solicitacao=solicitacao, form=form)

@admin.route('/criar_admin', methods=['POST'])
def criar_admin():
    # Esta rota seria protegida por algum mecanismo adicional
    # como um token secreto ou acesso apenas via linha de comando
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    if not email or not senha:
        flash('Email e senha são obrigatórios', 'danger')
        return redirect(url_for('admin.painel'))
    
    # Verificar se já existe um admin com este email
    if Usuario.query.filter_by(email=email, is_admin=True).first():
        flash('Já existe um administrador com este email', 'warning')
        return redirect(url_for('admin.painel'))
    
    # Criar novo admin
    hashed_senha = bcrypt.generate_password_hash(senha).decode('utf-8')
    admin = Usuario(
        nome='Administrador',
        email=email,
        senha_hash=hashed_senha,
        plano='premium',
        is_admin=True,
        email_confirmado=True
    )
    db.session.add(admin)
    db.session.commit()
    
    flash('Novo administrador criado com sucesso!', 'success')
    return redirect(url_for('admin.painel'))