from app import create_app, db
from flask_migrate import Migrate

# Criação do aplicativo e configuração do Flask-Migrate
app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    # Inicia o servidor Flask
    app.run(host='0.0.0.0', port=5000, debug=True)

