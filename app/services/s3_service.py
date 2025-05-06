import boto3
import os
import mimetypes
from app.utils.config import get_config
from app.services.media_utils import download_media_from_whatsapp
import requests
import hashlib
temp_dir = os.path.join(os.getcwd(), 'temp')
os.makedirs(temp_dir, exist_ok=True)

def hash_phone_number(phone_number):
    """
    Genera un hash del número de teléfono para usarlo como nombre de carpeta seguro
    
    Args:
        phone_number: Número de teléfono del usuario (ejemplo: 'whatsapp:+51973592880')
        
    Returns:
        str: Hash hexadecimal del número de teléfono
    """
    # Limpiar el número de teléfono (quitar 'whatsapp:' y otros caracteres especiales)
    clean_number = phone_number.replace('whatsapp:', '').replace('+', '').replace(' ', '')
    
    # Crear hash md5 del número limpio
    return hashlib.md5(clean_number.encode()).hexdigest()

def upload_file_to_s3(file_path, phone_number=None, file_type="pdf", object_name=None):
    """
    Sube un archivo a S3 y devuelve la URL
    
    Args:
        file_path: Ruta del archivo a subir
        phone_number: Número de teléfono del usuario para crear su carpeta
        file_type: Tipo de archivo (pdf o image)
        object_name: Nombre personalizado del objeto en S3
        
    Returns:
        str: URL del archivo subido o None si hay error
    """
    if object_name is None:
        object_name = os.path.basename(file_path)
    
    config = get_config()
    
    try:
        # Inicializar cliente S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY,
            aws_secret_access_key=config.AWS_SECRET_KEY
        )
        
        # Establecer la estructura de carpetas
        base_folder = "rfi-bot"
        
        if phone_number:
            # Usar hash del número de teléfono como nombre de carpeta
            user_folder = hash_phone_number(phone_number)
            if file_type == "pdf":
                object_path = f"{base_folder}/users/{user_folder}/pdfs/{object_name}"
            elif file_type == "image":
                object_path = f"{base_folder}/users/{user_folder}/images/{object_name}"
            else:
                object_path = f"{base_folder}/users/{user_folder}/{object_name}"
        else:
            if file_type == "pdf":
                object_path = f"{base_folder}/general/pdfs/{object_name}"
            elif file_type == "image":
                object_path = f"{base_folder}/general/images/{object_name}"
            else:
                object_path = f"{base_folder}/general/{object_name}"
        
        # Determinar el tipo MIME automáticamente
        content_type = mimetypes.guess_type(file_path)[0]
        if not content_type:
            # Valores por defecto basados en file_type
            if file_type == "pdf":
                content_type = 'application/pdf'
            elif file_type in ["image", "jpg", "jpeg", "png"]:
                content_type = 'image/jpeg'  # o determinar basado en la extensión
            else:
                content_type = 'application/octet-stream'
        
        # Subir archivo
        s3_client.upload_file(
            file_path, 
            'anyscale-production-data-cld-2s5xxprx3uhiearmm2mqapkg85', 
            object_path,
            ExtraArgs={
                'ContentType': content_type
            }
        )
        
        # Generar URL con tiempo de expiración más largo (1 semana)
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': 'anyscale-production-data-cld-2s5xxprx3uhiearmm2mqapkg85',
                'Key': object_path
            },
            ExpiresIn=604800  # 7 días en segundos
        )
        
        print(f"Archivo subido correctamente a: {url}")
        return url
        
    except Exception as e:
        print(f"Error al subir archivo a S3: {e}")
        return None

def save_image_from_url(media_url, phone_number, image_index, rfi_id):
    """
    Descarga una imagen desde una URL y la sube a S3
    """
    config = get_config()
    try:
        # Intentar descargar la imagen
        image_content = download_media_from_whatsapp(media_url)
        
        # Generar nombre de archivo
        filename = f"image_{rfi_id}_{image_index}.jpg"
        temp_path = os.path.join(config.TEMP_FOLDER, filename)
        
        # Crear directorio si no existe
        os.makedirs(config.TEMP_FOLDER, exist_ok=True)
        
        if image_content:
            # Si se pudo descargar, guardar la imagen real
            with open(temp_path, "wb") as f:
                f.write(image_content)
            print(f"Imagen guardada en: {temp_path}")
        else:
            # Si no se pudo descargar, crear una imagen de marcador de posición
            print("Creando imagen de marcador de posición")
            try:
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new('RGB', (800, 600), color=(255, 255, 255))
                d = ImageDraw.Draw(img)
                d.text((10, 10), f"Imagen {image_index} no disponible", fill=(0, 0, 0))
                d.text((10, 30), "Error al descargar desde WhatsApp", fill=(255, 0, 0))
                d.text((10, 50), f"RFI #{rfi_id}", fill=(0, 0, 0))
                img.save(temp_path)
                print(f"Imagen de marcador guardada en: {temp_path}")
            except Exception as e:
                print(f"Error al crear imagen de marcador: {e}")
                return None
        
        # Subir a S3
        s3_url = upload_file_to_s3(temp_path, phone_number=phone_number, file_type="image", object_name=filename)
    
        
        return s3_url
    except Exception as e:
        print(f"Error al procesar imagen desde URL: {e}")
        import traceback
        print(traceback.format_exc())
        return None