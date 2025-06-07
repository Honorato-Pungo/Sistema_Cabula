from app import create_app, db
from flask_migrate import Migrate
import pdb

# Criação do aplicativo e configuração do Flask-Migrate
app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    # Inicia o servidor Flask
     app.run(
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile='certs/cert.pem', keyfile='certs/privkey.pem')
        host='0.0.0.0',
        port=443,  # Usar a porta padrão do HTTPS
        ssl_context=('cert.pem', 'privkey.pem'),  # Referência aos arquivos do certificado SSL
        debug=True
    )

