import boto3
import logging
import os
import mimetypes
from botocore.exceptions import NoCredentialsError
from app.utils.config import get_config
temp_dir = os.path.join(os.getcwd(), 'temp')
os.makedirs(temp_dir, exist_ok=True)

def upload_file_to_s3(file_path, folder="uploads", object_name=None):
    """
    Sube un archivo a S3 y devuelve la URL
    """
    if object_name is None:
        object_name = os.path.basename(file_path)
    
    # Agregar la carpeta al nombre del objeto
    if folder:
        object_name = f"{folder}/{object_name}"
    
    config = get_config()
    
    try:
        # Inicializar cliente S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY,
            aws_secret_access_key=config.AWS_SECRET_KEY
        )
        
        # Subir archivo sin especificar ACL
        s3_client.upload_file(
            file_path, 
            'anyscale-production-data-cld-2s5xxprx3uhiearmm2mqapkg85', 
            object_name,
            ExtraArgs={
                'ContentType': 'application/pdf'  # Quitar ACL
            }
        )
        
        # Generar URL con tiempo de expiración más largo (1 semana)
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': 'anyscale-production-data-cld-2s5xxprx3uhiearmm2mqapkg85',
                'Key': object_name
            },
            ExpiresIn=604800  # 7 días en segundos
        )
        
        print(f"Archivo subido correctamente a: {url}")
        return url
        
    except Exception as e:
        print(f"Error al subir archivo a S3: {e}")
        return None
