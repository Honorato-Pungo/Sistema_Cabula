import os
from app import create_app, db, bcrypt
from app.models import Usuario

# Configurar o aplicativo Flask
app = create_app()

with app.app_context():
    # 1. Verificar se o banco de dados existe, se não, criar
    db_file = 'instance/site.db'
    if not os.path.exists(db_file):
        print("Criando banco de dados e tabelas...")
        db.create_all()
    
    # 2. Dados do administrador
    email_admin = "admin@example.com"
    senha_admin = "senha_segura123"
    
    # 3. Verificar se o admin já existe
    admin_existente = Usuario.query.filter_by(email=email_admin, is_admin=True).first()
    
    if admin_existente:
        print(f"Administrador já existe: {email_admin}")
    else:
        # 4. Criar novo admin
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