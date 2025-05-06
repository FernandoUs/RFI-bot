import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')

    # Twilio
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise ValueError("Twilio credentials are not set in the environment variables.")

    # AnyScale (en lugar de OpenAI)
    ANY_SCALE_API_KEY = os.getenv('ANY_SCALE_API_KEY')
    ANY_SCALE_API_BASE = os.getenv('ANY_SCALE_API_BASE', 'https://api.endpoints.anyscale.com/v1')
    if not ANY_SCALE_API_KEY:
        raise ValueError("AnyScale API Key is not set in the environment variables.")
    
    # Mantener compatibilidad con código que espera OPENAI_API_KEY 
    OPEN_IA_KEY = os.getenv('OPEN_IA_KEY')


    HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", "")
    
    # AWS S3
    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
    AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY or not S3_BUCKET_NAME:
        raise ValueError("AWS credentials or bucket name are not set in the environment variables.")

    # Almacenamiento
    TEMP_FOLDER = os.path.join(os.getcwd(), 'temp')
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    # WhatsApp Business API (futuro)
    # WHATSAPP_API_TOKEN = os.getenv('WHATSAPP_API_TOKEN')
    # WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    # WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')