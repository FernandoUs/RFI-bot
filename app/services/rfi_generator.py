import os
import google.generativeai as genai
import time
import requests
import threading
import traceback
from fpdf import FPDF as FPDF2
from datetime import datetime
from app.utils.config import get_config as get_config_func
from app.utils.config import get_config
from app.services.s3_service import upload_file_to_s3

class CustomPDF(FPDF2):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No font customization needed - will use default fonts

def improve_description(description):
    """
    Mejora la descripción usando Google Gemini API
    """
    config = get_config()
    
    try:
        # Verificar si existe la API key de Google
        google_api_key = config.GOOGLE_API_KEY
        
        if not google_api_key:
            print("ERROR: No se ha configurado la API key de Google")
            return description
        
        print("Usando Gemini API para mejorar la descripción...")
        
        # Configurar la API
        genai.configure(api_key=google_api_key)
        
        # Crear un modelo
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        # Crear prompt de sistema más específico y acotado
        prompt = f"""Como ingeniero de construcción, mejora ÚNICAMENTE la siguiente descripción técnica del PROBLEMA para que este dentro de un RFI, 
        haciéndola más profesional y un pocoo más detallada pero no tan extensa. NO generes un RFI completo, NO agregues campos adicionales,
        NO incluyas "Detalles Específicos", "Adjuntos", ni otros elementos de formato, NO inventes ejes ni datos adicionales. NO agregues ningun requerimiento o relacionado a eso
        solamente centrate en la problematica
        
        SOLO mejora el texto de la descripción del problema original manteniendo su extensión similar (máximo 1-2 párrafos).
        NO incluyas "Asunto:", "Descripción:", ni otras etiquetas o títulos.
        
        Descripción original:
        {description}
        
        Descripción mejorada (solo el texto, sin añadir estructura de RFI):"""
        
        # Generar respuesta
        response = model.generate_content(prompt)
        
        # Verificar si hay respuesta válida
        if response.text:
            improved_text = response.text.strip()
            
            # Eliminar posibles etiquetas o títulos que el modelo podría haber generado
            lines = improved_text.split('\n')
            cleaned_lines = []
            for line in lines:
                # Eliminar líneas que contengan patrones de títulos o etiquetas
                if not line.strip().startswith(('**', '* ', 'Descripción:', 'Asunto:', 'Detalles:', 'Adjuntos:')):
                    cleaned_lines.append(line)
            
            improved_text = '\n'.join(cleaned_lines).strip()
            
            # Comprobar si la respuesta tiene suficiente contenido
            if len(improved_text) < len(description) * 0.5 or len(improved_text) < 20:
                print("La respuesta generada fue demasiado corta")
                return description
            
            print("Descripción mejorada exitosamente con Gemini")
            return improved_text
        else:
            print("No se obtuvo respuesta de Gemini")
            return description
        
    except Exception as e:
        print(f"Error al mejorar la descripción: {e}")
        print(traceback.format_exc())
        return description


def generate_rfi_pdf(data, rfi_id, phone_number=None):
    config = get_config_func()  # Esto funciona porque get_config está importado al inicio del archivo
    
    # Crear objeto PDF (orientación horizontal para mayor espacio)
    pdf = CustomPDF()
    pdf.add_page()
    
    # Definir colores
    header_bg_color = (50, 61, 96)  # Color azul oscuro para encabezados
    subheader_bg_color = (230, 230, 240)  # Color gris claro para sub-encabezados
    
    # --- ENCABEZADO DEL DOCUMENTO ---
    
    # Logos (si existen)
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'static', 'img', 'logo.png')
    client_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'static', 'img', 'client_logo.png')
    
    # Verificar si existen los logos
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=50)
    else:
        # Si no hay logo, añadir texto en su lugar
        pdf.set_font("Arial", "B", 16)
        pdf.cell(50, 20, "EMPRESA", 0, 0, 'L')
    
    # Título principal centrado
    pdf.set_font("Arial", "B", 14)
    pdf.cell(90, 10, "Request For Information (RFI) N°" + rfi_id, 0, 0, "C")
    
    # Cliente logo (lado derecho)
    if os.path.exists(client_logo_path):
        pdf.image(client_logo_path, x=160, y=8, w=40)
    
    pdf.ln(20)
      # --- TABLA DE INFORMACIÓN DEL PROYECTO ---
    # Primera fila con información del proyecto
    pdf.set_fill_color(*header_bg_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(190, 8, "Información General:", 1, 1, "L", True)
    pdf.set_text_color(0, 0, 0)
    
    # Información del proyecto
    pdf.set_font("Arial", "", 9)
    pdf.cell(70, 7, "Nombre del Proyecto:", 1, 0, "L")
    pdf.set_font("Arial", "B", 9)
    pdf.cell(120, 7, data.get("proyecto", "CONSTRUCCIÓN DE OBRAS CIVILES"), 1, 1)
    
    pdf.set_font("Arial", "", 9)
    pdf.cell(70, 7, "Contrato:", 1, 0, "L")
    pdf.set_font("Arial", "B", 9)
    pdf.cell(120, 7, data.get("contrato", "Servicios varios para levantamiento de observaciones"), 1, 1)
    
    # Arreglar la alineación del código de documento y número de registro
    pdf.set_font("Arial", "", 9)
    pdf.cell(70, 7, "Código de documento:", 1, 0, "L")
    pdf.set_font("Arial", "", 9)
    pdf.cell(90, 7, data.get("codigo", ""), 1, 0)  # Ampliamos el espacio para el código
    pdf.cell(15, 7, "N° RFI:", 1, 0)  # Reducimos el texto y el tamaño de la celda
    pdf.set_font("Arial", "B", 8)  # Fuente más pequeña
    pdf.cell(15, 7, f"{rfi_id}", 1, 1)  # Celda más pequeña para el número de registro
    
    # Compañía, disciplina y fecha
    pdf.set_fill_color(*header_bg_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(190, 7, "Información del Solicitante:", 1, 1, "L", True)
    pdf.set_text_color(0, 0, 0)
      # NUEVOS CAMPOS - Información del solicitante
    pdf.set_font("Arial", "", 9)
    pdf.cell(70, 7, "Nombre del Solicitante:", 1, 0)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(120, 7, data.get("nombre_usuario", ""), 1, 1)
    
    pdf.set_font("Arial", "", 9)
    pdf.cell(70, 7, "Cargo:", 1, 0)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(120, 7, data.get("cargo_usuario", ""), 1, 1)
    
    pdf.set_font("Arial", "", 9)
    pdf.cell(70, 7, "Compañía:", 1, 0)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(70, 7, data.get("empresa", ""), 1, 0)
    pdf.set_font("Arial", "", 9)
    pdf.cell(20, 7, "Fecha:", 1, 0)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(30, 7, datetime.now().strftime('%d/%m/%Y'), 1, 1)
      # Fecha de respuesta requerida
    pdf.set_font("Arial", "", 9)
    pdf.cell(70, 7, "Fecha de Respuesta Requerida:", 1, 0)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(120, 7, data.get("fecha_respuesta", ""), 1, 1)

    # Documentos de referencia
    if 'documentos_referencia' in data and data['documentos_referencia']:
        pdf.set_fill_color(240, 240, 240)  # Color gris muy claro para subtítulos
        pdf.set_font("Arial", "B", 9)
        pdf.cell(190, 7, "Documentos de Referencia:", 1, 1, "L", True)
        pdf.set_font("Arial", "", 9)
        
        # Numerar los documentos de referencia
        for i, doc in enumerate(data['documentos_referencia'], 1):
            pdf.set_font("Arial", "", 9)
            pdf.cell(10, 7, f"{i}.", 1, 0, "C")
            pdf.set_font("Arial", "B", 9)
            pdf.cell(180, 7, doc, 1, 1)
    
    pdf.set_font("Arial", "", 9)
    pdf.cell(70, 7, "Sector del problema:", 1, 0)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(120, 7, data.get("sector", ""), 1, 1)
    
    pdf.set_font("Arial", "", 9)
    pdf.cell(70, 7, "Disciplina:", 1, 0)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(120, 7, data.get("especialidad", "OBRAS CIVILES"), 1, 1)
    
    # Verificar si hay incompatibilidad con otra especialidad
    if data.get("incompatibilidad") == True:
        pdf.set_font("Arial", "", 9)
        pdf.cell(70, 7, "Incompatibilidad con:", 1, 0)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(120, 7, data.get("incompatibilidad_con", ""), 1, 1)
    
    pdf.set_font("Arial", "", 9)
    pdf.cell(70, 7, "Asunto:", 1, 0)
    pdf.set_font("Arial", "B", 9)
    # Fixed multi_cell call to be compatible with fpdf2
    pdf.multi_cell(w=120, h=7, txt=data.get("asunto", "SOLICITUD PLANOS DE INGENIERÍA MODIFICADOS"), border=1, align="L")
    # Sección de detalles de la solicitud
    pdf.ln(5)
    pdf.set_fill_color(*header_bg_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(190, 8, "Información Requerida:", 1, 1, "L", True)
    pdf.set_text_color(0, 0, 0)
    
    # Descripción del problema
    # Usar descripción mejorada si existe, si no la original
    descripcion = data.get("descripcion_mejorada", data.get("descripcion_original", ""))
    
    # Dividir en dos secciones: Problemática y Requerimientos
    pdf.set_fill_color(240, 240, 240)  # Color gris muy claro para subtítulos
    pdf.set_font("Arial", "B", 9)
    pdf.cell(190, 7, "Problemática:", 1, 1, "L", True)
    
    # Marco para la descripción del problema
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(w=190, h=7, txt=descripcion, border=1, align="L")
    
    # Sección de requerimientos
    pdf.ln(3)
    pdf.set_fill_color(240, 240, 240)  # Color gris muy claro para subtítulos
    pdf.set_font("Arial", "B", 9)
    pdf.cell(190, 7, "Requerimientos:", 1, 1, "L", True)
      # Marco para los requerimientos
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(w=190, h=7, txt=generate_requeriment(data.get("descripcion_mejorada")), border=1, align="L")
    
    # Sección de imágenes
    if "images" in data and data["images"]:
        pdf.ln(5)
        pdf.set_fill_color(*header_bg_color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(190, 8, "Reason Request / Razón de la solicitud:", 1, 1, "L", True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

        # Añadimos un texto corto
        pdf.set_font("Arial", "I", 9)
        pdf.multi_cell(w=190, h=7, txt="Las imágenes/planos presentados a continuación muestran la incompatibilidad encontrada en el proyecto:", border=0, align="L")
        
        temp_files = []
        
        # Definir layout para imágenes
        num_images = len(data["images"])
        
        # SOLUCIÓN: Implementar múltiples métodos para descargar imágenes
        if num_images > 0:
            # Mostrar imágenes en una fila
            img_width = 190 / num_images - 10
            
            # Guardar posición Y actual para mantener alineación
            current_y = pdf.get_y()
            max_height = 0
            
            for i, image_data in enumerate(data["images"]):
                print(f"Procesando imagen {i+1} de {num_images}")
                success = False
                image_content = None
                
                try:
                    # MÉTODO 1: Extraer URL desde el diccionario o string
                    urls_to_try = []
                    
                    if isinstance(image_data, dict):
                        # Primero intentar con URL presignada (más permisos)
                        if "presigned_url" in image_data:
                            urls_to_try.append(("presigned_url", image_data["presigned_url"]))
                        
                        # Luego con URL directa
                        if "direct_url" in image_data:
                            # Intentar con diferentes variantes de región
                            direct_url = image_data["direct_url"]
                            urls_to_try.append(("direct_url", direct_url))
                            
                            # Probar con variaciones de URL
                            if "us-west-1" in direct_url:
                                alt_url = direct_url.replace("us-west-1", "us-east-1")
                                urls_to_try.append(("us-east-1", alt_url))
                            elif "us-east-1" in direct_url:
                                alt_url = direct_url.replace("us-east-1", "us-west-1")
                                urls_to_try.append(("us-west-1", alt_url))
                    elif isinstance(image_data, str):
                        urls_to_try.append(("string_url", image_data))
                    
                    # Intentar con cada URL disponible
                    for url_type, url in urls_to_try:
                        if success:
                            break
                            
                        try:
                            print(f"Intentando descarga con {url_type}: {url}")
                            
                            # Configurar una sesión con timeout más largo
                            session = requests.Session()
                            response = session.get(url, timeout=30)
                            
                            if response.status_code == 200:
                                print(f"Descarga exitosa con {url_type}")
                                image_content = response.content
                                success = True
                                break
                            else:
                                print(f"Error con {url_type}: Status {response.status_code}")
                        except Exception as e:
                            print(f"Error al descargar con {url_type}: {e}")
                    
                    # MÉTODO 2: Intentar con boto3 directamente si falla el método anterior
                    if not success:
                        try:
                            import boto3
                            from app.utils.config import get_config
                            config = get_config()
                            
                            # Extraer bucket y key de la primera URL válida
                            for _, url in urls_to_try:
                                try:
                                    # Parsear URL para obtener bucket y key
                                    from urllib.parse import urlparse
                                    parsed = urlparse(url)
                                    path = parsed.path.lstrip('/')
                                    
                                    # Configurar cliente S3 con credenciales explícitas
                                    s3_client = boto3.client(
                                        's3',
                                        aws_access_key_id=config.AWS_ACCESS_KEY,
                                        aws_secret_access_key=config.AWS_SECRET_KEY,
                                        region_name='us-west-1'  # Especificar región
                                    )
                                    
                                    # Determinar bucket_name y object_key
                                    if '.s3.' in parsed.netloc:
                                        bucket_name = parsed.netloc.split('.')[0]
                                        object_key = path
                                    else:
                                        parts = path.split('/', 1)
                                        if len(parts) >= 2:
                                            bucket_name, object_key = parts
                                        else:
                                            continue
                                    
                                    print(f"Intentando con boto3: bucket={bucket_name}, key={object_key}")
                                    
                                    # Descargar a un archivo temporal
                                    temp_file_path = os.path.join(config.TEMP_FOLDER, f"temp_img_{rfi_id}_{i}.jpg")
                                    s3_client.download_file(bucket_name, object_key, temp_file_path)
                                    
                                    # Leer como bytes
                                    with open(temp_file_path, 'rb') as f:
                                        image_content = f.read()
                                    
                                    os.unlink(temp_file_path)  # Eliminar archivo temporal
                                    success = True
                                    print(f"Descarga exitosa con boto3: {len(image_content)} bytes")
                                    break
                                except Exception as s3_error:
                                    print(f"Error con boto3 para {url}: {s3_error}")
                        except Exception as boto3_error:
                            print(f"Error general con boto3: {boto3_error}")
                    
                    # MÉTODO 3: Usar la copia local guardada si existe
                    if not success:
                        try:
                            local_path = os.path.join(
                                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                "static", "images", f"image_{rfi_id}_{i+1}.jpg"
                            )
                            
                            if os.path.exists(local_path):
                                print(f"Usando imagen local: {local_path}")
                                with open(local_path, 'rb') as f:
                                    image_content = f.read()
                                success = True
                        except Exception as local_error:
                            print(f"Error al usar imagen local: {local_error}")
                    
                    # Si no hay imagen, crear una imagen de marcador
                    if not success:
                        print("Creando imagen de marcador para el PDF")
                        from PIL import Image, ImageDraw, ImageFont
                        import io
                        
                        # Crear imagen con texto
                        img = Image.new('RGB', (800, 600), color=(240, 240, 240))
                        draw = ImageDraw.Draw(img)
                        
                        # Añadir texto indicando el problema
                        draw.text((20, 20), f"Imagen {i+1}", fill=(0, 0, 0))
                        draw.text((20, 60), "No se pudo cargar la imagen", fill=(255, 0, 0))
                        draw.text((20, 100), "Verifique la imagen original en WhatsApp", fill=(0, 0, 255))
                        
                        # Convertir a bytes
                        img_byte_array = io.BytesIO()
                        img.save(img_byte_array, format='JPEG')
                        image_content = img_byte_array.getvalue()
                        success = True
                    
                    # Procesar la imagen
                    if success and image_content:
                        # Guardar temporalmente
                        temp_file = os.path.join(config.TEMP_FOLDER, f"temp_img_{rfi_id}_{i}.jpg")
                        with open(temp_file, 'wb') as f:
                            f.write(image_content)
                        temp_files.append(temp_file)
                        
                        # Calcular dimensiones para el PDF
                        from PIL import Image
                        img = Image.open(temp_file)
                        img_w, img_h = img.size
                        
                        # Limitar altura máxima a 60% de la página
                        max_h = 120  # Altura máxima en mm
                        
                        # Mantener relación de aspecto
                        ratio = min(img_width/img_w, max_h/img_h)
                        final_w = img_w * ratio
                        final_h = img_h * ratio
                        
                        # Actualizar altura máxima para alineación
                        if final_h > max_height:
                            max_height = final_h
                        
                        # Posicionar imagen en PDF
                        x_pos = 10 + i * (img_width + 10)
                        pdf.image(temp_file, x=x_pos, y=current_y, w=final_w, h=final_h)
                        
                        print(f"Imagen {i+1} añadida al PDF correctamente")
                
                except Exception as e:
                    print(f"Error general al procesar imagen {i+1}: {e}")
                    import traceback
                    print(traceback.format_exc())
            
            # Avanzar después de todas las imágenes
            pdf.ln(max_height + 20)  # Espacio adicional después de las imágenes
        
        # Limpiar archivos temporales al finalizar
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass

    # Sección para firmas
    pdf.ln(5)
    pdf.set_fill_color(*header_bg_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(190, 8, "Fecha requerida de respuesta:", 1, 1, "L", True)
    pdf.set_text_color(0, 0, 0)
    
    # Fecha requerida - casilla vacía para llenar manualmente
    pdf.set_font("Arial", "", 9)
    pdf.cell(60, 7, "Preparado por:", 1, 0)
    pdf.cell(70, 7, "", 1, 0)  # Espacio para firma
    pdf.cell(30, 7, "Fecha:", 1, 0)
    pdf.cell(30, 7, "", 1, 1)  # Espacio para fecha
    
    # Firma 2
    pdf.set_font("Arial", "", 9)
    pdf.cell(60, 7, "Enviado por (Representante Supervisor):", 1, 0)
    pdf.cell(70, 7, "", 1, 0)  # Espacio para firma
    pdf.cell(30, 7, "Fecha:", 1, 0)
    pdf.cell(30, 7, "", 1, 1)  # Espacio para fecha
    
    # Nombre y firma final
    pdf.ln(5)
    pdf.set_font("Arial", "", 9)
    pdf.cell(30, 7, "Nombre:", 1, 0)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(80, 7, data.get("nombre", ""), 1, 0)
    pdf.set_font("Arial", "", 9)
    pdf.cell(30, 7, "Cargo:", 1, 0)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(50, 7, data.get("cargo", "RESIDENTE"), 1, 1)
    
    # Reemplazar la sección de información por firmas del solicitante y responsable
    pdf.ln(5)
    pdf.set_fill_color(*header_bg_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(190, 8, "Firmas:", 1, 1, "L", True)
    pdf.set_text_color(0, 0, 0)
    
    # Tabla de firmas
    pdf.cell(95, 10, "Firma del Solicitante:", 1, 0, "C")
    pdf.cell(95, 10, "Firma del Responsable:", 1, 1, "C")
    pdf.cell(95, 30, "", 1, 0, "C")  # Espacio para firma
    pdf.cell(95, 30, "", 1, 1, "C")  # Espacio para firma
    pdf.cell(95, 7, "Nombre: _________________________", 1, 0, "C")
    pdf.cell(95, 7, "Nombre: _________________________", 1, 1, "C")
    
    # Eliminar la sección "Information or Information Response" y el resto de verificaciones
    
    pdf_filename = f"RFI_{rfi_id}.pdf"
    pdf_path = os.path.join(config.TEMP_FOLDER, pdf_filename)
    
    # Asegurarse de que exista la carpeta temporal
    os.makedirs(config.TEMP_FOLDER, exist_ok=True)
    
    try:
        pdf.output(pdf_path)
        print(f"PDF generado exitosamente: {pdf_path}")
        
        # Eliminar archivos temporales DESPUÉS de que el PDF se ha guardado
        if 'temp_files' in locals() and temp_files:
            time.sleep(3)  # Pequeña pausa para asegurar que el PDF ha liberado los archivos
            
            # Definir una función para limpiar archivos temporales
            def cleanup_files():
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        try:
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                                print(f"Archivo temporal eliminado: {temp_file}")
                        except Exception as del_error:
                            print(f"No se pudo eliminar archivo temporal {temp_file}: {del_error}")
            
            # Crear y lanzar hilo para limpieza
            cleanup_thread = threading.Thread(target=cleanup_files)
            cleanup_thread.daemon = True
            cleanup_thread.start()
    except Exception as pdf_error:
        print(f"Error al guardar el PDF: {pdf_error}")
    
    # Intentar subir a S3 si está disponible
    try:
        # Verificar si está disponible la función de S3
        if hasattr(config, 'S3_UPLOAD_ENABLED') and config.S3_UPLOAD_ENABLED:
            s3_url = upload_file_to_s3(pdf_path, phone_number=phone_number, file_type="pdf", object_name=pdf_filename)
            print(f"PDF subido a S3: {s3_url}")
            return pdf_path, s3_url
        else:
            # S3 no está habilitado, usar un archivo local
            local_url = f"file://{pdf_path}"
            print(f"S3 no está habilitado. Usando archivo local: {local_url}")
            return pdf_path, local_url
    except Exception as e:
        # Error al subir a S3, devolver ruta local
        print(f"Error al subir PDF a S3: {e}")
        return pdf_path, f"file://{pdf_path}"

def analyze_plan_image(image_path):
    """
    Función para futura implementación: Analiza una imagen de plano
    usando IA para detectar ejes y problemas
    """
    # Implementación futura para análisis de planos
    # Podría usar OpenAI Vision API o bibliotecas como OpenCV
    pass

def generate_requeriment(description):
    """
    Genera un requerimiento técnico basado en la descripción proporcionada
    usando Google Gemini API o un algoritmo de respaldo si falla
    
    Args:
        description: La descripción mejorada del problema
        
    Returns:
        str: Un requerimiento técnico conciso y relevante
    """
    config = get_config()
    
    try:
        # Verificar si existe la API key de Google
        google_api_key = config.GOOGLE_API_KEY
        
        if not google_api_key:
            print("ERROR: No se ha configurado la API key de Google")
            return "REQUIERE REVISIÓN TÉCNICA"
        
        print("Usando Gemini API para generar requerimiento...")
        
        # Configurar la API
        genai.configure(api_key=google_api_key)
        
        # Crear un modelo
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        # Crear prompt específico para generar el requerimiento
        prompt = f"""Genera un requerimiento técnico conciso y claro para un Request For Information (RFI) 
        en un proyecto de construcción basado en esta descripción. El requerimiento debe ser específico, 
        relacionado a la descripción, y no debe incluir "Requerimiento:", "Descripción:", ni otras etiquetas o títulos.
        
        Descripción: {description}
        
        Requerimiento:"""
        
        # Generar respuesta
        response = model.generate_content(prompt)
        
        # Verificar si hay respuesta válida
        if response.text:
            requeriment = response.text.strip()
            
            # Limpiar el texto de posibles marcadores o prefijos
            requeriment = requeriment.replace("Requerimiento:", "").replace(":", "").strip()
            
            # Asegurar formato de capitalización adecuado (primera letra mayúscula)
            if requeriment and len(requeriment) > 1:
                # Primera letra mayúscula
                requeriment = requeriment[0].upper() + requeriment[1:]
            
            # Ya no recortamos el requerimiento para mostrarlo completo en el PDF
            print(f"Requerimiento generado: {requeriment}")
            return requeriment
        else:
            print("No se obtuvo respuesta al generar el requerimiento")
            return "REQUIERE REVISIÓN TÉCNICA"
    except Exception as e:
        print(f"Error al generar requerimiento: {e}")
        words = description.split()
        if len(words) >= 5:
            backup_requeriment = " ".join(words[:5]).upper() + "..."
            return backup_requeriment
        else:
            return "REQUIERE REVISIÓN TÉCNICA"


def generate_subject(description):
    """
    Genera un asunto relevante basado en la descripción proporcionada
    usando Google Gemini API o un algoritmo de respaldo si falla
    
    Args:
        description: La descripción mejorada del problema
        
    Returns:
        str: Un asunto conciso y relevante para el RFI
    """
    config = get_config()
    
    try:
        # Verificar si existe la API key de Google
        google_api_key = config.GOOGLE_API_KEY
        
        if not google_api_key:
            print("ERROR: No se ha configurado la API key de Google")
            return "SOLICITUD DE INFORMACIÓN"
        
        print("Usando Gemini API para generar asunto...")
        
        # Configurar la API
        genai.configure(api_key=google_api_key)
        
        # Crear un modelo
        model = genai.GenerativeModel('models/gemini-1.5-flash')
          # Crear prompt específico para generar el asunto
        prompt = f"""Genera un asunto técnico conciso para un Request For Information (RFI) 
        en un proyecto de construcción basado en esta descripción. El asunto debe tener formato
        de oración natural, que sea corto de maximo 10 palabras y relacionados a la descripción.
        NO incluyas "Asunto:", "Descripción:" "RFI Verificación", ni otras etiquetas o títulos.
        
        Descripción: {description}
        
        Asunto:"""
        
        # Generar respuesta
        response = model.generate_content(prompt)
          # Verificar si hay respuesta válida
        if response.text:
            subject = response.text.strip()
            
            # Limpiar el texto de posibles marcadores o prefijos
            subject = subject.replace("Asunto:", "").replace(":", "").strip()
            
            # Asegurar formato de capitalización adecuado (primera letra mayúscula)
            if subject and len(subject) > 1:
                # Primera letra mayúscula
                subject = subject[0].upper() + subject[1:]
            
            # Si el asunto es demasiado largo, recortarlo
            if len(subject) > 70:
                subject = subject[:67] + "..."
            
            print(f"Asunto generado: {subject}")
            return subject
        else:
            print("No se obtuvo respuesta al generar el asunto")
            return "SOLICITUD DE INFORMACIÓN"
        
    except Exception as e:
        print(f"Error al generar asunto: {e}")
        
        # Algoritmo de respaldo:
        # Si falla la IA, generar un asunto basado en las primeras palabras de la descripción
        words = description.split()
        if len(words) >= 5:
            backup_subject = " ".join(words[:5]).upper() + "..."
            return backup_subject if len(backup_subject) <= 70 else backup_subject[:67] + "..."
        else:
            return "SOLICITUD DE INFORMACIÓN"