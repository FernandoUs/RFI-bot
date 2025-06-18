import boto3
import os
import mimetypes
import time
import traceback
import hashlib
import requests
from app.utils.config import get_config
from app.services.media_utils import download_media_from_whatsapp
from PIL import Image, ImageDraw

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
    
    # Validar credenciales
    if not config.AWS_ACCESS_KEY or not config.AWS_SECRET_KEY:
        print("Error: Credenciales de AWS no configuradas")
        return None
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY,
            aws_secret_access_key=config.AWS_SECRET_KEY,
            region_name=getattr(config, 'AWS_REGION', 'us-west-1')
        )
    except Exception as e:
        print(f"Error al inicializar cliente S3: {e}")
        return None
    
    try:
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
        
        bucket_name = config.AWS_S3_BUCKET
        aws_region = config.AWS_REGION or 'us-west-1'

        s3_client = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY,
            aws_secret_access_key=config.AWS_SECRET_KEY,
            region_name=aws_region
        )
        
        s3_client.upload_file(
            file_path, 
            bucket_name, 
            object_path,
            ExtraArgs={
                'ContentType': content_type
            }
        )
        
        fixed_region = 'us-west-1' 

        # URL con tiempo de expiración
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_path
            },
            ExpiresIn=604800  # 7 días en segundos
        )

        # URL directa con la misma región consistente
        direct_url = f"https://{bucket_name}.s3.{fixed_region}.amazonaws.com/{object_path}"
        
        print(f"Archivo subido correctamente a: {url}")
        return url  

        
    except Exception as e:
        print(f"Error al subir archivo a S3: {e}")
        return None

def save_image_from_url(media_url, phone_number, image_index=None, rfi_id=None):
    """
    Descarga una imagen desde una URL y la sube a S3
    
    Args:
        media_url: URL de la imagen de WhatsApp
        phone_number: Número de teléfono del usuario
        image_index: Índice de la imagen (se genera automáticamente si no se proporciona)
        rfi_id: ID del RFI (se genera automáticamente si no se proporciona)
    """
    config = get_config()
    temp_path = None
    
    try:
        # Si no se proporciona rfi_id, generar uno temporal basado en timestamp
        if not rfi_id:
            rfi_id = str(int(time.time()))
        
        # Si no se proporciona image_index, generar uno secuencial
        if image_index is None:
            # Generar un índice basado en el timestamp para evitar conflictos
            image_index = int(str(int(time.time()))[-3:])  # Últimos 3 dígitos del timestamp
        
        # Intentar descargar la imagen
        image_content = download_media_from_whatsapp(media_url)
        
        # Generar nombre de archivo único
        timestamp = int(time.time())
        filename = f"image_{rfi_id}_{image_index}_{timestamp}.jpg"
        temp_path = os.path.join(config.TEMP_FOLDER, filename)
        
        # También guardar una copia en static/images
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "images")
        os.makedirs(static_dir, exist_ok=True)
        static_path = os.path.join(static_dir, filename)
        
        # Crear directorio temporal si no existe
        os.makedirs(config.TEMP_FOLDER, exist_ok=True)
        
        if image_content:
            # Si se pudo descargar, guardar la imagen real
            with open(temp_path, "wb") as f:
                f.write(image_content)
            print(f"Imagen guardada en: {temp_path}")
            
            # Guardar también en static
            with open(static_path, "wb") as f:
                f.write(image_content)
            print(f"Copia de imagen guardada en: {static_path}")
        else:
            # Si no se pudo descargar, crear una imagen de marcador de posición
            print("Creando imagen de marcador de posición")
            try:
                img = Image.new('RGB', (800, 600), color=(255, 255, 255))
                d = ImageDraw.Draw(img)
                d.text((10, 10), f"Imagen {image_index} no disponible", fill=(0, 0, 0))
                d.text((10, 30), "Error al descargar desde WhatsApp", fill=(255, 0, 0))
                d.text((10, 50), f"RFI #{rfi_id}", fill=(0, 0, 0))
                d.text((10, 70), f"Timestamp: {timestamp}", fill=(128, 128, 128))
                img.save(temp_path)
                img.save(static_path)  # También guardar en static
                print(f"Imagen de marcador guardada en: {temp_path}")
            except Exception as e:
                print(f"Error al crear imagen de marcador: {e}")
                return None
        
        # Subir a S3
        s3_result = upload_file_to_s3(temp_path, phone_number=phone_number, file_type="image", object_name=filename)

        if s3_result:
            # Como upload_file_to_s3 ahora devuelve solo un string (URL), no un diccionario
            return s3_result
        else:
            # Si S3 falla, devolver la ruta local como fallback
            local_url = f"file://{static_path}" if os.path.exists(static_path) else None
            print(f"S3 falló, usando archivo local: {local_url}")
            return static_path  
            
    except Exception as e:
        print(f"Error al procesar imagen desde URL: {e}")
        print(traceback.format_exc())
        return None
    finally: 
        # Limpiar archivo temporal pero mantener el de static
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print(f"Archivo temporal eliminado: {temp_path}")
            except Exception as e:
                print(f"Error al eliminar archivo temporal: {e}")

def upload_file_from_memory_to_s3(file_buffer, phone_number=None, file_type="pdf", object_name=None):
    """
    Sube un archivo desde memoria (BytesIO) a S3 y devuelve la URL
    
    Args:
        file_buffer: Buffer de memoria (BytesIO) con el contenido del archivo
        phone_number: Número de teléfono del usuario para crear su carpeta
        file_type: Tipo de archivo (pdf o image)
        object_name: Nombre personalizado del objeto en S3
        
    Returns:
        str: URL del archivo subido o None si hay error
    """
    config = get_config()
    
    # Validar credenciales
    if not config.AWS_ACCESS_KEY or not config.AWS_SECRET_KEY:
        print("Error: Credenciales de AWS no configuradas")
        return None
    
    try:
        # Configurar cliente S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY,
            aws_secret_access_key=config.AWS_SECRET_KEY,
            region_name=config.AWS_REGION
        )
        
        # Construir la ruta del objeto en S3
        folder_path = "rfi-bot"
        if phone_number:
            phone_hash = hash_phone_number(phone_number)
            if file_type == "pdf":
                folder_path += f"/users/{phone_hash}/pdfs"
            elif file_type == "image":
                folder_path += f"/users/{phone_hash}/images"
        
        s3_key = f"{folder_path}/{object_name}"
        
        # Determinar el tipo de contenido
        if file_type == "pdf":
            content_type = "application/pdf"
        elif file_type == "image":
            content_type = "image/jpeg"
        else:
            content_type = "application/octet-stream"
        
        # Resetear el buffer al inicio
        file_buffer.seek(0)
        
        # Subir el archivo desde memoria
        s3_client.upload_fileobj(
            file_buffer,
            config.S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={'ContentType': content_type}
        )
        
        # Generar URL firmada válida por 24 horas
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': config.S3_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=86400  # 24 horas
        )
        
        print(f"Archivo subido desde memoria a S3: {presigned_url}")
        return presigned_url
        
    except Exception as e:
        print(f"Error al subir archivo desde memoria a S3: {e}")
        traceback.print_exc()
        return None

def test_s3_public_access():
    """Test if S3 files can be accessed publicly"""
    test_file = os.path.join(get_config().TEMP_FOLDER, "test_public.txt")
    
    # Create test file
    with open(test_file, "w") as f:
        f.write("Test public access " + str(time.time()))
    
    # Upload with public-read ACL
    result = upload_file_to_s3(test_file, file_type="text", object_name="test_public.txt")
    
    if not result:
        print("Upload failed")
        return False
    
    # Try both URLs
    presigned_url = result["presigned_url"]
    direct_url = result["direct_url"]
    
    print(f"Testing presigned URL: {presigned_url}")
    resp1 = requests.get(presigned_url)
    print(f"Presigned URL status: {resp1.status_code}")
    
    print(f"Testing direct URL: {direct_url}")
    resp2 = requests.get(direct_url)
    print(f"Direct URL status: {resp2.status_code}")
    
    return resp1.status_code == 200 or resp2.status_code == 200