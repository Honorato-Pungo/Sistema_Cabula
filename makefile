# Makefile para gerenciar o projeto Flask e limpar arquivos __pycache__

# Variável de ambiente para o Flask
FLASK_APP=wsgi.py

# Alvo para rodar a aplicação
run:
	FLASK_APP=$(FLASK_APP) flask run

# Alvo para inicializar o diretório de migração
init-db:
	FLASK_APP=$(FLASK_APP) flask db init

# Alvo para criar uma nova migração
migrate:
	FLASK_APP=$(FLASK_APP) flask db migrate

# Alvo para aplicar as migrações ao banco
upgrade:
	FLASK_APP=$(FLASK_APP) flask db upgrade

# Alvo de limpeza
clean:
	# Encontra e remove todos os diretórios __pycache__
	@find . -type d -name "__pycache__" -exec rm -r {} + && echo "Diretórios __pycache__ removidos."
	# Encontra e remove todos os arquivos .pyc
	@find . -type f -name "*.pyc" -exec rm -f {} + && echo "Arquivos .pyc removidos."

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

# Alvo de ajuda
help:
	@echo "Comandos disponíveis no Makefile:"
	@echo "  run      - Inicia o servidor Flask"
	@echo "  init-db  - Inicializa as migrações do banco de dados"
	@echo "  migrate  - Cria uma nova migração com base nas alterações do modelo"
	@echo "  upgrade  - Aplica as migrações ao banco de dados"
	@echo "  clean    - Remove todos os diretórios __pycache__ e arquivos .pyc"

