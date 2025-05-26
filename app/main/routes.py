from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models import Usuario, Trabalho, Prova, SolicitacaoUpgrade
from app.main.forms import TrabalhoForm, ProvaForm, UpgradeForm
from app import db
import os
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('main/dashboard.html')

@main.route('/trabalhos')
@login_required
def trabalhos():
    if current_user.plano == 'premium':
        trabalhos = Trabalho.query.filter(
            (Trabalho.usuario_id == current_user.id) | 
            (Trabalho.aprovado == True)
        ).all()
    else:
        trabalhos = Trabalho.query.filter_by(aprovado=True).all()
    
    return render_template('main/trabalhos.html', trabalhos=trabalhos)

@main.route('/trabalho/novo', methods=['GET', 'POST'])
@login_required
def novo_trabalho():
    if current_user.plano != 'premium':
        flash('Você precisa ter um plano premium para submeter trabalhos', 'warning')
        return redirect(url_for('main.trabalhos'))
    
    form = TrabalhoForm()
    if form.validate_on_submit():
        arquivo = form.arquivo.data
        if arquivo and allowed_file(arquivo.filename):
            filename = secure_filename(arquivo.filename)
            arquivo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'trabalhos', filename)
            arquivo.save(arquivo_path)
            
            trabalho = Trabalho(
                titulo=form.titulo.data,
                autores=form.autores.data,
                disciplina=form.disciplina.data,
                periodo=form.periodo.data,
                tipo=form.tipo.data,
                palavras_chave=form.palavras_chave.data,
                nivel_acesso=form.nivel_acesso.data,
                arquivo=filename,
                aprovado=False,
                usuario_id=current_user.id
            )
            db.session.add(trabalho)
            db.session.commit()
            flash('Seu trabalho foi submetido para aprovação!', 'success')
            return redirect(url_for('main.trabalhos'))
        else:
            flash('Tipo de arquivo não permitido. Apenas PDF e DOCX são aceitos.', 'danger')
    
    return render_template('main/novo_trabalho.html', form=form)

@main.route('/provas')
@login_required
def provas():
    provas = Prova.query.filter_by(aprovado=True).all()
    return render_template('main/provas.html', provas=provas)

@main.route('/prova/nova', methods=['GET', 'POST'])
@login_required
def nova_prova():
    if current_user.plano != 'premium':
        flash('Você precisa ter um plano premium para submeter provas', 'warning')
        return redirect(url_for('main.provas'))
    
    form = ProvaForm()
    if form.validate_on_submit():
        # Processar arquivo de enunciado
        arquivo_enunciado = form.arquivo_enunciado.data
        if arquivo_enunciado and allowed_file(arquivo_enunciado.filename):
            filename_enunciado = secure_filename(arquivo_enunciado.filename)
            arquivo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'provas', filename_enunciado)
            arquivo_enunciado.save(arquivo_path)
            
            # Processar arquivo de resolução (se fornecido)
            filename_resolucao = None
            arquivo_resolucao = form.arquivo_resolucao.data
            if arquivo_resolucao and allowed_file(arquivo_resolucao.filename):
                filename_resolucao = secure_filename(arquivo_resolucao.filename)
                arquivo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'provas', filename_resolucao)
                arquivo_resolucao.save(arquivo_path)
            
            prova = Prova(
                disciplina=form.disciplina.data,
                professor=form.professor.data,
                data_prova=form.data_prova.data,
                arquivo_enunciado=filename_enunciado,
                arquivo_resolucao=filename_resolucao,
                aprovado=True,  # Provas são aprovadas automaticamente
                usuario_id=current_user.id
            )
            db.session.add(prova)
            db.session.commit()
            flash('Sua prova foi submetida com sucesso!', 'success')
            return redirect(url_for('main.provas'))
        else:
            flash('Tipo de arquivo não permitido. Apenas PDF e DOCX são aceitos.', 'danger')
    
    return render_template('main/nova_prova.html', form=form)

@main.route('/upgrade', methods=['GET', 'POST'])
@login_required
def solicitar_upgrade():
    if current_user.plano == 'premium':
        flash('Você já possui um plano premium!', 'info')
        return redirect(url_for('main.dashboard'))
    
    # Verificar se já existe uma solicitação pendente
    solicitacao_pendente = SolicitacaoUpgrade.query.filter_by(
        usuario_id=current_user.id,
        aprovada=False
    ).first()
    
    if solicitacao_pendente:
        flash('Você já tem uma solicitação de upgrade pendente', 'info')
        return redirect(url_for('main.dashboard'))
    
    form = UpgradeForm()
    if form.validate_on_submit():
        # Simular processo de pagamento
        # Na implementação real, integrar com um gateway de pagamento
        
        # Criar solicitação de upgrade
        solicitacao = SolicitacaoUpgrade(
            usuario_id=current_user.id
        )
        db.session.add(solicitacao)
        db.session.commit()
        
        flash('Sua solicitação de upgrade foi enviada para aprovação!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('main/solicitar_upgrade.html', form=form)