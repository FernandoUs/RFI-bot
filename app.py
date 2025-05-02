import os
from flask import Flask
from dotenv import load_dotenv
from app.utils.config import Config
from app.routes import configure_routes

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask app
app = Flask(__name__)

# Cargar configuraciones desde Config
app.config.from_object(Config)

# Configurar rutas
configure_routes(app)

# Ejecutar la app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
