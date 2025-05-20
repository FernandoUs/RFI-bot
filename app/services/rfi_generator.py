import os
from fpdf import FPDF as FPDF2
from datetime import datetime
from app.utils.config import get_config
import google.generativeai as genai
from PIL import Image
import uuid
import time
import requests
import threading
import traceback
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
        prompt = f"""Como ingeniero de construcción, mejora ÚNICAMENTE la siguiente descripción técnica para que este dentro de un RFI, 
        haciéndola más profesional y un pocoo más detallada pero no tan extensa. NO generes un RFI completo, NO agregues campos adicionales,
        NO incluyas "Detalles Específicos", "Adjuntos", ni otros elementos de formato, NO inventes ejes ni datos adicionales.
        
        SOLO mejora el texto de la descripción original manteniendo su extensión similar (máximo 1-2 párrafos).
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
    """
    Genera un PDF con formato RFI y los datos recopilados, similar al formato estándar de la industria
    """
    config = get_config()
    
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
    pdf.cell(190, 7, "Contratista:", 1, 1, "L", True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font("Arial", "", 9)
    pdf.cell(70, 7, "Compañía:", 1, 0)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(70, 7, data.get("empresa", ""), 1, 0)
    pdf.set_font("Arial", "", 9)
    pdf.cell(20, 7, "Fecha:", 1, 0)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(30, 7, datetime.now().strftime('%d/%m/%Y'), 1, 1)
    
    pdf.set_font("Arial", "", 9)
    pdf.cell(70, 7, "Disciplina:", 1, 0)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(120, 7, data.get("especialidad", "OBRAS CIVILES"), 1, 1)
    
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
    pdf.cell(190, 8, "Información Requerida (indicar detalle):", 1, 1, "L", True)
    pdf.set_text_color(0, 0, 0)
    
    # Descripción del problema
    pdf.set_font("Arial", "B", 9)
    # Usar descripción mejorada si existe, si no la original
    descripcion = data.get("descripcion_mejorada", data.get("descripcion_original", ""))
    
    # Marco para la descripción - Update the multi_cell parameters
    pdf.multi_cell(w=190, h=7, txt=descripcion, border=1, align="L")
    
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
        if num_images <= 3:
            # Mostrar imágenes en una fila
            img_width = 190 / num_images - 10
            for i, image_url in enumerate(data["images"]):
                try:
                    # Descargar imagen
                    response = requests.get(image_url)
                    
                    if response.status_code == 200:
                        # Guardar temporalmente
                        temp_file_id = str(uuid.uuid4())[:8]
                        temp_img_path = os.path.join(config.TEMP_FOLDER, f"temp_image_{temp_file_id}.jpg")
                        with open(temp_img_path, "wb") as f:
                            f.write(response.content)
                        
                        temp_files.append(temp_img_path)
                        
                        # Calcular dimensiones
                        img = Image.open(temp_img_path)
                        img_w, img_h = img.size
                        ratio = min(img_width/img_w, 50/img_h)
                        final_width = img_w * ratio
                        final_height = img_h * ratio
                        
                        # Posicionar imagen
                        x_position = 10 + i * (img_width + 10)
                        pdf.image(temp_img_path, x=x_position, y=pdf.get_y(), w=final_width, h=final_height)
                except Exception as e:
                    print(f"Error al procesar imagen {i+1}: {e}")
            
            # Movernos abajo de las imágenes
            pdf.ln(60)  # Espacio para imágenes
        else:
            # Mostrar imágenes en grid si hay más de 3
            for i, image_url in enumerate(data["images"][:6]):  # Limitamos a 6 imágenes máximo
                try:
                    # Lógica similar a la anterior, pero en grid 2x3
                    # ... código para procesar imágenes ...
                    pass
                except Exception as e:
                    print(f"Error al procesar imagen {i+1}: {e}")
    
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