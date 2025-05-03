import boto3
import logging
import os
import mimetypes
from botocore.exceptions import NoCredentialsError
from app.utils.config import get_config
temp_dir = os.path.join(os.getcwd(), 'temp')
os.makedirs(temp_dir, exist_ok=True)

def upload_file_to_s3(file_path, folder="general", object_name=None):
    """
    Sube un archivo a S3 con estructura de carpetas.
    """
    config = get_config()
    
    try:

        # Configurar logging para ver errores detallados
        logging.basicConfig(level=logging.INFO)
        
        # Inicializar cliente S3
        s3 = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY,
            aws_secret_access_key=config.AWS_SECRET_KEY,
            region_name=config.AWS_REGION
        )
        
        # Construir la ruta en S3 (usa "rfi-bot" como prefijo para organización)
        if object_name is None:
            object_name = os.path.basename(file_path)
        
        # Agregar prefijo "rfi-bot/" para mantener organizado dentro del bucket de Anyscale
        s3_path = f"rfi-bot/{folder}/{object_name}"
        
        # Configuración adicional para archivos PDF
        extra_args = {}
        if file_path.lower().endswith('.pdf'):
            extra_args = {
                'ContentType': 'application/pdf',
            }
        
        # Subir el archivo
        s3.upload_file(file_path, config.S3_BUCKET_NAME, s3_path, ExtraArgs=extra_args)
        
        # Generar URL pública
        url = s3.generate_presigned_url('get_object',
            Params={'Bucket': config.S3_BUCKET_NAME, 'Key': s3_path},
            ExpiresIn=86400)  # 24 horas
        
        print(f"Archivo subido correctamente a: {url}")
        return url
        
    except Exception as e:
        print(f"Error al subir a S3: {e}")
        # En caso de error, devolver una URL local (sólo para testing)
        return f"file://{file_path}"
