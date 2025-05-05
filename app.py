from flask import Flask
from dotenv import load_dotenv
from app.routes import configure_routes
import os

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask app
app = Flask(__name__)

# Verificar credenciales críticas
if not os.getenv("TWILIO_ACCOUNT_SID") or not os.getenv("TWILIO_AUTH_TOKEN"):
    raise EnvironmentError("Credenciales de Twilio no definidas en el archivo .env")

if not os.getenv("ANY_SCALE_API_KEY"):
    raise EnvironmentError("API Key de AnyScale no definida en el archivo .env")

# Cargar configuraciones
from config import Config
app.config.from_object(Config)

# Configurar rutas
configure_routes(app)

# Ejecutar la app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)  