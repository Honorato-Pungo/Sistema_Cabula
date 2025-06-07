import os
from app import create_app, db, bcrypt
from app.models import Usuario

# Caminho do banco de dados
db_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'site.db')

# 1. Verificar se o banco de dados existe
if not os.path.exists(db_file):
    print("Banco de dados não encontrado, criando...")
    exit()  # Caso o banco não exista, o script é encerrado
else:
    print('Banco de dados encontrado.')

# Dados do administrador
email_admin = "admin@example.com"
senha_admin = "senha_segura123"

# Função para criar o admin
def create_admin():
    app = create_app()

    with app.app_context():
        # 2. Verificar se o administrador já existe
        admin_existente = Usuario.query.filter_by(email=email_admin, is_admin=True).first()

        if admin_existente:
            print(f"Administrador já existe: {email_admin}")
        else:
            # 3. Criar novo administrador
            try:
                hashed_senha = bcrypt.generate_password_hash(senha_admin).decode('utf-8')
                admin = Usuario(
                    nome="Administrador",
                    email=email_admin,
                    senha_hash=hashed_senha,
                    plano="premium",
                    is_admin=True,
                    email_confirmado=True
                )
                db.session.add(admin)
                db.session.commit()
                print(f"""
                ===========================================
                Administrador criado com sucesso!
                Email: {email_admin}
                Senha: {senha_admin}
                ===========================================
                """)
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao criar administrador: {str(e)}")

# Chama a função para criar o admin
if __name__ == '__main__':
    create_admin()

