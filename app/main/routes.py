from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models import Usuario, Trabalho, Prova, SolicitacaoUpgrade
from app.main.forms import TrabalhoForm, ProvaForm, UpgradeForm
from app import db
import os
from werkzeug.utils import secure_filename
import random
import pdb
from sqlalchemy import desc

main = Blueprint('main', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Função para salvar os arquivos com nomes únicos
def salvar_arquivo(arquivo, pasta_destino):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filename = secure_filename(arquivo.filename)
    nome, extensao = os.path.splitext(filename)
    numero_aleatorio = random.randint(1000, 9999)
    novo_nome = f"{nome}_{numero_aleatorio}{extensao}"
    caminho_destino = os.path.join(upload_folder, pasta_destino, novo_nome)
    
    if not os.path.exists(os.path.dirname(caminho_destino)):
        os.makedirs(os.path.dirname(caminho_destino))
    
    arquivo.save(caminho_destino)
    return novo_nome

@main.route('/')
def index():
    print("Entrando na rota '/index'")
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    print(f"Usuário logado: {current_user.nome}")
    return render_template('main/dashboard.html')

@main.route('/trabalhos')
@login_required
def trabalhos():
    # Verificar se o usuário tem plano premium
    if current_user.plano == 'premium':
        # Usuários premium podem ver todos os trabalhos, seus e aprovados
        trabalhos = Trabalho.query.filter(
            (Trabalho.usuario_id == current_user.id) | 
            (Trabalho.aprovado == True)
        ).all()
    else:
        # Usuários não premium apenas veem os trabalhos aprovados, ordenados de forma decrescente pela data de submissão
        trabalhos = Trabalho.query.filter_by(aprovado=True).order_by(desc(Trabalho.data_submissao)).all()

    # Depuração: Imprimindo os trabalhos encontrados
    print(f"Trabalhos encontrados: {len(trabalhos)}")
    for trabalho in trabalhos:
        print(f"Trabalho: {trabalho.titulo}, Aprovado: {trabalho.aprovado}")
    
    # Renderizando a página e passando os trabalhos
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
            # Usando a função salvar_arquivo para salvar o arquivo com um nome único
            arquivo_path = salvar_arquivo(arquivo, "trabalhos")
            
            trabalho = Trabalho(
                titulo=form.titulo.data,
                autores=form.autores.data,
                disciplina=form.disciplina.data,
                periodo=form.periodo.data,
                tipo=form.tipo.data,
                palavras_chave=form.palavras_chave.data,
                nivel_acesso=form.nivel_acesso.data,
                arquivo=arquivo_path,  # Salva o caminho completo
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
    print(f"Provas encontradas: {len(provas)}")
    for prova in provas:
        print(f"Prova: {prova.disciplina}, Aprovada: {prova.aprovado}")
    
    return render_template('main/provas.html', provas=provas)

@main.route('/prova/nova', methods=['GET', 'POST'])
@login_required
def nova_prova():
    if current_user.plano != 'premium':
        flash('Você precisa ter um plano premium para submeter provas', 'warning')
        return redirect(url_for('main.provas'))
    
    form = ProvaForm()
    
    if form.validate_on_submit():
        arquivo_enunciado = form.arquivo_enunciado.data
        if arquivo_enunciado and allowed_file(arquivo_enunciado.filename):
            caminho_enunciado = salvar_arquivo(arquivo_enunciado, "provas")
            
            arquivo_resolucao = form.arquivo_resolucao.data
            caminho_resolucao = None
            if arquivo_resolucao and allowed_file(arquivo_resolucao.filename):
                caminho_resolucao = salvar_arquivo(arquivo_resolucao, "provas")
            
            pdb.set_trace()

            prova = Prova(
                disciplina=form.disciplina.data,
                professor=form.professor.data,
                data_prova=form.data_prova.data,
                arquivo_enunciado=caminho_enunciado,
                arquivo_resolucao=caminho_resolucao,
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
    
    solicitacao_pendente = SolicitacaoUpgrade.query.filter_by(
        usuario_id=current_user.id,
        aprovada=False
    ).first()
    
    print(f"Solicitação pendente encontrada? {solicitacao_pendente is not None}")
    
    if solicitacao_pendente:
        flash('Você já tem uma solicitação de upgrade pendente', 'info')
        return redirect(url_for('main.dashboard'))
    
    form = UpgradeForm()
    if form.validate_on_submit():
        solicitacao = SolicitacaoUpgrade(
            usuario_id=current_user.id
        )
        db.session.add(solicitacao)
        db.session.commit()
        
        flash('Sua solicitação de upgrade foi enviada para aprovação!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('main/solicitar_upgrade.html', form=form)
