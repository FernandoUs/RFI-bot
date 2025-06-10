import os
from types import SimpleNamespace
from dotenv import load_dotenv

# Asegurar que las variables de entorno estén cargadas
load_dotenv()

def get_config():
    """
    Obtener configuraciones desde variables de entorno
    Devuelve un SimpleNamespace que permite acceder a los valores como atributos
    """
    config = {
        # Configuración general
        'DEBUG': os.getenv('DEBUG', 'False').lower() == 'true',
        'SECRET_KEY': os.getenv('SECRET_KEY', 'default-secret-key'),
        
        # Configuración de Twilio
        'TWILIO_ACCOUNT_SID': os.getenv('TWILIO_ACCOUNT_SID'),
        'TWILIO_AUTH_TOKEN': os.getenv('TWILIO_AUTH_TOKEN'),
        'TWILIO_PHONE_NUMBER': os.getenv('TWILIO_PHONE_NUMBER'),
        
        # Configuración de AnyScale (en lugar de OpenAI)
        'ANY_SCALE_API_KEY': os.getenv('ANY_SCALE_API_KEY'),
        'ANY_SCALE_API_BASE': os.getenv('ANY_SCALE_API_BASE', 'https://api.endpoints.anyscale.com/v1'),
        
        # Mantener compatibilidad con el código que espera OPENAI_API_KEY
        'OPENAI_API_KEY': os.getenv('OPEN_IA_KEY'),

        'HUGGINGFACE_API_KEY' : os.getenv('HUGGINGFACE_API_KEY'),

        
        # Configuración de AWS
        'AWS_ACCESS_KEY': os.getenv('AWS_ACCESS_KEY'),
        'AWS_SECRET_KEY': os.getenv('AWS_SECRET_KEY'),
        'AWS_REGION': os.getenv('AWS_REGION', 'us-east-1'),
        'S3_BUCKET_NAME': os.getenv('S3_BUCKET_NAME'),
        
        # Configuración de almacenamiento local
        'TEMP_FOLDER': os.path.join(os.getcwd(), 'temp'),
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),

        
        # WhatsApp Business API (para futuro uso)
        'WHATSAPP_API_TOKEN': os.getenv('WHATSAPP_API_TOKEN'),
        'WHATSAPP_PHONE_NUMBER_ID': os.getenv('WHATSAPP_PHONE_NUMBER_ID'),
        'WHATSAPP_BUSINESS_ACCOUNT_ID': os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID'),
        "S3_UPLOAD_ENABLED": True,

        # Nuevas configuraciones de AWS S3
        'AWS_S3_BUCKET': os.getenv('S3_BUCKET_NAME', 'anyscale-production-data-cld-2s5xxprx3uhiearmm2mqapkg85'),
        'AWS_ACCESS_KEY': os.getenv('AWS_ACCESS_KEY'),
        'AWS_SECRET_KEY': os.getenv('AWS_SECRET_KEY'),
        'AWS_REGION': os.getenv('AWS_REGION', 'us-west-1'),
        
        # Otras configuraciones que puedan faltar
        'STATIC_FOLDER': os.getenv('STATIC_FOLDER', 'static'),
    }
    
    # Crear directorio temporal si no existe
    os.makedirs(config['TEMP_FOLDER'], exist_ok=True)
    
    return SimpleNamespace(**config)