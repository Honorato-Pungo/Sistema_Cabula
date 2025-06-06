# **Cabula**

Este projeto permite o **registro e consulta de provas acadêmicas** e outros materiais de estudo de universidades. Ele inclui funcionalidades como o upload de provas passadas, consulta por filtros (universidade, disciplina, etc.), e visualização das soluções.

## **Descrição**

A plataforma foi desenvolvida para ajudar estudantes universitários a acessarem provas anteriores e suas soluções. O sistema permite aos usuários registrar, consultar e fazer o upload de provas passadas.

## **Funcionalidades:**
- **Administração:** Possui uma interface de administração para gerenciar provas e solicitações.
- **Autenticação:** Sistema de login e autenticação com **Multi-Factor Authentication (MFA)**.
- **Registro de Provas:** Permite registrar novas provas com enunciados e resoluções.
- **Consulta de Provas:** Usuários podem buscar provas passadas de acordo com critérios como universidade, disciplina ou ano.
- **Upload de Provas e Trabalhos:** Permite o envio de provas em formato PDF para facilitar o estudo.
  
## **Tecnologias Utilizadas**

- **Flask:** Framework web para o backend.
- **SQLite (ou PostgreSQL, dependendo da configuração):** Banco de dados para armazenar as provas e suas resoluções.
- **HTML/CSS/JavaScript:** Para construção do frontend.
- **Bootstrap:** Para design responsivo.
- **SQLAlchemy/Alembic:** ORM e migrações de banco de dados.
- **MFA (Multi-Factor Authentication):** Para segurança adicional no login.

## **Estrutura do Projeto**

Abaixo está uma visão geral da estrutura do projeto:

```

├── Makefile               # Arquivo para automação de tarefas (ex: limpeza, migração)
├── app/
│   ├── **init**.py        # Inicialização da aplicação Flask
│   ├── admin/             # Módulo de administração
│   │   ├── forms.py       # Formulários de administração
│   │   └── routes.py      # Rotas de administração
│   ├── auth/              # Módulo de autenticação
│   │   ├── forms.py       # Formulários de login e registro
│   │   ├── routes.py      # Rotas de login, registro, MFA
│   │   └── utils.py       # Funções auxiliares (ex: validação de MFA)
│   ├── main/              # Módulo principal do site (ex: Dashboard, Provas)
│   │   ├── forms.py       # Formulários principais
│   │   └── routes.py      # Rotas principais
│   ├── models.py          # Definições das tabelas do banco de dados
│   ├── prod.db            # Banco de dados de produção
│   ├── site.db            # Banco de dados de desenvolvimento
│   ├── site copy.db       # Cópia do banco de dados
│   ├── static/            # Arquivos estáticos (CSS, JS)
│   ├── templates/         # Templates HTML
│   └── utils.py           # Funções auxiliares
├── config.py              # Arquivo de configurações da aplicação
├── create\_admin.py        # Script para criar usuário administrador
├── instance/              # Instância da aplicação (bancos de dados)
│   ├── prod.db            # Banco de dados de produção
│   └── site.db            # Banco de dados de desenvolvimento
├── migrations/            # Migrações do banco de dados (Alembic)
│   ├── alembic.ini        # Arquivo de configuração do Alembic
│   └── versions/          # Arquivos de versão das migrações
├── requirements.txt       # Dependências do projeto
├── run.py                 # Arquivo para rodar a aplicação Flask
├── uploads/               # Diretório para upload de provas e trabalhos
│   ├── provas/            # Provas enviadas pelos usuários
│   └── trabalhos/         # Trabalhos enviados pelos usuários
└── wsgi.py                # Arquivo para execução no servidor WSGI (como Gunicorn)

```

## **Instalação e Configuração**

### **Pré-requisitos**

Antes de começar, você precisa garantir que tem as seguintes ferramentas instaladas:

- [Python](https://www.python.org/downloads/) (versão 3.x)
- [pip](https://pip.pypa.io/en/stable/)
- Banco de dados (SQLite para desenvolvimento, ou PostgreSQL para produção)

### **Passos para Instalar e Rodar o Projeto**

1. **Clone o repositório:**
   Primeiro, clone este repositório para o seu diretório local:
   ```bash
   git clone https://github.com/username/provas-academicas.git
   cd provas-academicas
    ```

2. **Crie um ambiente virtual:**
   É recomendado criar um ambiente virtual para isolar as dependências do seu projeto.

   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows use venv\Scripts\activate
   ```

3. **Instale as dependências do projeto:**
   Instale as dependências do projeto com o `pip`:

   ```bash
   pip install -r requirements.txt
   ```

4. **Crie o banco de dados:**
   Para criar o banco de dados e inicializar a aplicação, execute o script de migrações:

   ```bash
   flask db upgrade
   ```

5. **Crie um administrador (caso esteja configurado):**
   Você pode criar um usuário administrador com o seguinte comando:

   ```bash
   python create_admin.py
   ```

6. **Rodando a aplicação localmente:**
   Execute o servidor Flask:

   ```bash
   python run.py
   ```

### 4. Inicializar o Banco de Dados

Execute o seguinte comando para **inicializar as migrações** (se ainda não tiver rodado anteriormente):

```bash
flask db init
```

Esse comando irá criar o diretório `migrations` e os arquivos necessários para o gerenciamento de migrações.

### 5. Gerar as Migrações

Após ter configurado o banco de dados e criado as tabelas no código, gere as migrações:

```bash
flask db migrate -m "Initial migration"
```

Esse comando irá gerar um arquivo de migração no diretório `migrations/versions/`.

### 6. Rodar as Migrações

Para aplicar as migrações e criar as tabelas no banco de dados, execute:

```bash
flask db upgrade
```

Esse comando irá aplicar a migração gerada no passo anterior e criar as tabelas definidas nos seus modelos.

### 7. Verificar as Tabelas Criadas

Após rodar as migrações, você pode verificar se as tabelas foram criadas corretamente no banco de dados. Para isso, você pode usar:

* **SQLite Command Line**:

  ```bash
  cd instance
  sqlite3 site.db
  .tables
  ```

* **Flask Shell**:

  ```bash
  flask shell
  from app import db
  db.engine.table_names()  # Lista todas as tabelas
  ```

* **Ferramentas Gráficas** como [DB Browser for SQLite](https://sqlitebrowser.org/), [DBeaver](https://dbeaver.io/), ou [SQLiteStudio](https://sqlitestudio.pl/).

### 8. Reverter as Migrações (se necessário)

Se você precisar reverter uma migração, utilize:

```bash
flask db downgrade
```



7. **Acesse a aplicação:**
   Abra o navegador e vá para `http://127.0.0.1:5000/` para acessar a aplicação localmente.

---

## **Uso**

### **Registrar uma Prova**

1. Acesse a página de **Cadastro de Provas**.
2. Preencha os campos:

   * **Universidade**
   * **Disciplina**
   * **Ano da Prova**
   * **Enunciado** (Texto ou PDF)
   * **Resolução** (Texto ou PDF)
3. Clique em **Registrar Prova** para armazená-la no sistema.

### **Consultar Provas**

1. Vá para a página de **Consulta de Provas**.
2. Utilize os filtros:

   * **Universidade**
   * **Disciplina**
   * **Ano da Prova**
3. Clique em **Buscar** para visualizar a lista de provas correspondentes aos critérios selecionados.

### **Autenticação e Administração**

* **Login:** Faça login utilizando as credenciais cadastradas.
* **Administração:** A interface de administração permite gerenciar provas e solicitações.

---

## **Makefile**

## 📄 Makefile do Projeto Flask

Este `Makefile` automatiza tarefas comuns no desenvolvimento com Flask, como rodar o servidor, gerenciar migrações com Flask-Migrate e limpar arquivos desnecessários do Python.

### 🔧 Comandos disponíveis

| Comando         | Descrição                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| `make run`      | Inicia o servidor Flask usando o arquivo `wsgi.py` como ponto de entrada.  |
| `make init-db`  | Inicializa a estrutura de migrações com `flask db init`.                   |
| `make migrate`  | Gera uma nova migração com base nas alterações feitas nos modelos.         |
| `make upgrade`  | Aplica as migrações pendentes ao banco de dados.                           |
| `make clean`    | Remove todos os diretórios `__pycache__` e arquivos `.pyc` do projeto.     |
| `make help`     | Exibe a lista de comandos disponíveis com suas descrições.                 |

### 🧩 Requisitos

- Python 3.x
- Flask com suporte ao padrão **application factory**
- Flask-Migrate configurado no projeto
- Um arquivo `wsgi.py` na raiz do projeto
- (Opcional) [`python-dotenv`](https://pypi.org/project/python-dotenv/) para carregar variáveis de ambiente automaticamente

### 📌 Observações

- Todos os comandos usam `FLASK_APP=wsgi.py`, então você **não precisa exportar essa variável** manualmente no terminal.
- Ideal para uso em ambientes Unix/Linux e WSL. Para Windows, recomenda-se usar scripts `.bat` ou PowerShell equivalentes.



## **Contribuindo para o Projeto**

1. Faça um **fork** do repositório.
2. Crie uma **branch** com a sua feature (`git checkout -b feature/nova-feature`).
3. Faça suas alterações e comite-as (`git commit -m 'Adiciona nova funcionalidade'`).
4. Envie suas alterações para o repositório remoto (`git push origin feature/nova-feature`).
5. Abra um **pull request** com uma descrição clara das alterações.

---

## **Licença**

Este projeto está licenciado sob a [MIT License](LICENSE).


