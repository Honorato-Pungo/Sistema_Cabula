# Makefile para gerenciar o projeto Flask e limpar arquivos __pycache__

# Variável de ambiente para o Flask
FLASK_APP=wsgi.py

# Caminho do ambiente virtual (modifique se necessário)
VENV_DIR=venv
CERT_DIR=certs
CERT_FILE=$(CERT_DIR)/cert.pem
KEY_FILE=$(CERT_DIR)/privkey.pem

# Detectando o sistema operacional
ifeq ($(OS),Windows_NT)
    # Variáveis para Windows
    PYTHON=python
    VENV_ACTIVATE=$(VENV_DIR)\\Scripts\\activate.bat
    FLASK=$(VENV_DIR)\\Scripts\\flask.exe
else
    # Variáveis para Linux/Mac
    PYTHON=python3
    VENV_ACTIVATE=source $(VENV_DIR)/bin/activate
    FLASK=$(VENV_DIR)/bin/flask
endif

# Comando para instalar o python3-venv no Linux (caso não esteja instalado)
install-venv-dependencies:
ifeq ($(shell uname), Linux)
	@echo "Verificando e instalando o pacote python3-venv..."
	@sudo apt-get update
	@sudo apt-get install -y python3-venv
else
	@echo "Pacote python3-venv não necessário no Windows/Mac."
endif

# Alvo para criar o venv
create-venv: install-venv-dependencies
ifeq ($(OS),Windows_NT)
	@echo "Criando o ambiente virtual no Windows..."
	@$(PYTHON) -m venv $(VENV_DIR)
else
	@echo "Criando o ambiente virtual no Linux/Mac..."
	@$(PYTHON) -m venv $(VENV_DIR) || (echo "Erro: python3-venv não encontrado. Instale com sudo apt install python3-venv" && exit 1)
endif
	@echo "Ambiente virtual criado em $(VENV_DIR)."

# Alvo para criar os certificados SSL
create-ssl-certs:
	@echo "Criando certificados SSL autoassinados..."
	@mkdir -p $(CERT_DIR)
	@openssl genpkey -algorithm RSA -out $(KEY_FILE)
	@openssl req -new -key $(KEY_FILE) -out $(CERT_DIR)/cert.csr -subj "/CN=localhost"
	@openssl x509 -req -days 365 -in $(CERT_DIR)/cert.csr -signkey $(KEY_FILE) -out $(CERT_FILE)
	@echo "Certificados SSL criados com sucesso!"

# Alvo para instalar as dependências (dentro do venv já ativado)
install: create-venv
	@echo "Instalando dependências do requirements.txt..."
ifeq ($(OS),Windows_NT)
	@$(VENV_DIR)\\Scripts\\pip install -r requirements.txt
else
	@$(VENV_DIR)/bin/pip install -r requirements.txt
endif

# Alvo para rodar a aplicação (dentro do venv já ativado)
# Adicionando a opção para rodar com HTTP ou HTTPS e ativando o modo de desenvolvimento
run:
ifeq ($(OS),Windows_NT)
	# No Windows, podemos rodar com HTTP ou HTTPS
	@if [ "$(USE_HTTPS)" = "true" ]; then \
		echo "Rodando o servidor Flask com HTTPS no Windows..."; \
		@set FLASK_ENV=development && set FLASK_DEBUG=1 && $(FLASK) run --host=0.0.0.0 --port=5000 --cert=$(CERT_FILE) --key=$(KEY_FILE); \
	else \
		echo "Rodando o servidor Flask com HTTP no Windows..."; \
		@set FLASK_ENV=development && set FLASK_DEBUG=1 && $(FLASK) run --host=0.0.0.0 --port=5000; \
	fi
else
	# No Linux/Mac, podemos usar o parâmetro USE_HTTPS para decidir se usamos HTTP ou HTTPS
	@if [ "$(USE_HTTPS)" = "true" ]; then \
		echo "Rodando o servidor Flask com HTTPS..."; \
		FLASK_ENV=development FLASK_DEBUG=1 sudo $(FLASK) run --host=0.0.0.0 --port=443 --cert=$(CERT_FILE) --key=$(KEY_FILE); \
	else \
		echo "Rodando o servidor Flask com HTTP..."; \
		FLASK_ENV=development FLASK_DEBUG=1 $(FLASK) run --host=0.0.0.0 --port=5001; \
	fi
endif


# Alvo para inicializar o diretório de migração
init-db:
ifeq ($(OS),Windows_NT)
	@echo "Inicializando o banco de dados no Windows..."
	@$(FLASK) db init
else
	@echo "Inicializando o banco de dados no Linux/Mac..."
	@$(FLASK) db init
endif

# Alvo para criar uma nova migração
migrate:
ifeq ($(OS),Windows_NT)
	@echo "Criando migração no Windows..."
	@$(FLASK) db migrate
else
	@echo "Criando migração no Linux/Mac..."
	@$(FLASK) db migrate
endif

# Alvo para aplicar as migrações ao banco
upgrade-db:
ifeq ($(OS),Windows_NT)
	@echo "Aplicando migrações no Windows..."
	@$(FLASK) db upgrade
else
	@echo "Aplicando migrações no Linux/Mac..."
	@$(FLASK) db upgrade
endif

# Reverter a migração
downgrade-db:
ifeq ($(OS),Windows_NT)
	@echo "Revertendo migração no Windows..."
	@$(FLASK) db downgrade
else
	@echo "Revertendo migração no Linux/Mac..."
	@$(FLASK) db downgrade
endif

# Resetar migrações e banco de dados
fresh-db:
ifeq ($(OS),Windows_NT)
	@echo "Resetando migrações e banco de dados no Windows..."
	@del /f /q migrations\*
	@del /f /q instance\*
	@$(FLASK) db init
	@$(FLASK) db migrate
	@$(FLASK) db upgrade
else
	@echo "Resetando migrações e banco de dados no Linux/Mac..."
	@rm -rf migrations/*
	@rm -rf instance/*
	@$(FLASK) db init
	@$(FLASK) db migrate
	@$(FLASK) db upgrade
endif


# Alvo de limpeza
clean:
	# Encontra e remove todos os diretórios __pycache__
ifeq ($(OS),Windows_NT)
	@echo "Limpando __pycache__ no Windows..."
	@del /s /q __pycache__
else
	@find . -type d -name "__pycache__" -exec rm -r {} + && echo "Diretórios __pycache__ removidos."
	@find . -type f -name "*.pyc" -exec rm -f {} + && echo "Arquivos .pyc removidos."
endif

# Gera uma nova SECRET_KEY segura e grava no .env
gen-secret:
	@echo "Gerando nova SECRET_KEY..."
	@KEY=$$(python3 -c 'import secrets; print(secrets.token_hex(32))'); \
	if [ -f .env ]; then \
		if grep -q '^SECRET_KEY=' .env; then \
			sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$$KEY/" .env; \
		else \
			echo "SECRET_KEY=$$KEY" >> .env; \
		fi; \
	else \
		echo "SECRET_KEY=$$KEY" > .env; \
	fi; \
	echo "SECRET_KEY gerada e salva no .env."

# Cria um admin padrão dentro do ambiente virtual
create-admin:
	@echo "Criando admin padrão dentro do ambiente virtual..."
ifeq ($(OS),Windows_NT)
	@$(VENV_DIR)\\Scripts\\python create_admin.py
else
	@$(VENV_DIR)/bin/python create_admin.py
endif

# Alvo de ajuda
help:
	@echo "Comandos disponíveis no Makefile:"
	@echo "  run          - Inicia o servidor Flask com HTTP ou HTTPS"
	@echo "  init-db      - Inicializa as migrações do banco de dados"
	@echo "  migrate      - Cria uma nova migração com base nas alterações do modelo"
	@echo "  upgrade-db   - Aplica as migrações ao banco de dados"
	@echo "  clean        - Remove todos os diretórios __pycache__ e arquivos .pyc"
	@echo "  create-ssl-certs - Cria certificados SSL autoassinados"
	@echo "  install      - Cria o ambiente virtual (se necessário) e instala as dependências"
	@echo "  create-venv  - Cria o ambiente virtual"
	@echo "  install-dependencies - Instala dependências do requirements.txt"
