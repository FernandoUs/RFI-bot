from flask import Flask
from dotenv import load_dotenv
from app.routes import configure_routes
from app.utils.config import get_config 
import os
import logging

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask app
app = Flask(__name__)

# Verificar credenciales críticas
if not os.getenv("TWILIO_ACCOUNT_SID") or not os.getenv("TWILIO_AUTH_TOKEN"):
    raise EnvironmentError("Credenciales de Twilio no definidas en el archivo .env")

if not os.getenv("GOOGLE_API_KEY"):
    raise EnvironmentError("API Key de Google Gemini no definida en el archivo .env")

# Verificar otras credenciales importantes
if not os.getenv("TWILIO_PHONE_NUMBER"):
    print("ADVERTENCIA: TWILIO_PHONE_NUMBER no definido")

# Verificar credenciales AWS (opcionales)
if not os.getenv("AWS_ACCESS_KEY") or not os.getenv("AWS_SECRET_KEY"):
    print("ADVERTENCIA: Credenciales AWS no definidas - S3 no funcionará")

if not os.getenv("AWS_S3_BUCKET"):
    print("ADVERTENCIA: AWS_S3_BUCKET no definido - usando bucket por defecto")

# CORREGIDO: Cargar configuraciones usando get_config()
config = get_config()
app.config.update({
    'SECRET_KEY': config.SECRET_KEY,
    'DEBUG': config.DEBUG,
})

# Configurar rutas
configure_routes(app)

# Configurar logging
if app.config.get('DEBUG', False):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.info("Aplicación RFI Bot iniciada")

# Ejecutar la app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)