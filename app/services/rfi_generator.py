import os
from fpdf import FPDF
from datetime import datetime
from app.utils.config import get_config
import google.generativeai as genai
from PIL import Image
import uuid
import time
import requests
import threading
from app.services.s3_service import upload_file_to_s3

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
        model = genai.GenerativeModel('gemini-1.5-pro')
        
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
        import traceback
        print(traceback.format_exc())
        return description


def generate_rfi_pdf(data, rfi_id, phone_number=None):
    """
    Genera un PDF con formato RFI y los datos recopilados
    """
    config = get_config()
    
    # Crear objeto PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Configuración de fuentes
    pdf.set_font("Arial", "B", 16)
    
    # Título
    pdf.cell(190, 10, "SOLICITUD DE INFORMACIÓN (RFI)", 0, 1, "C")
    pdf.line(10, 25, 200, 25)
    pdf.ln(5)
    
    # Información del RFI
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, f"ID de RFI: {rfi_id}", 0, 1)
    pdf.cell(50, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", 0, 1)
    pdf.ln(5)
    
    # Detalles
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Detalles de la Solicitud", 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Información detallada
    pdf.set_font("Arial", "", 11)
    
    if "especialidad" in data:
        pdf.set_font("Arial", "B", 11)
        pdf.cell(50, 10, "Especialidad:", 0, 0)
        pdf.set_font("Arial", "", 11)
        pdf.cell(140, 10, data.get("especialidad", ""), 0, 1)
    
    # Incompatibilidad
    if "incompatibilidad" in data:
        incompatibilidad = data.get("incompatibilidad")
        
        pdf.set_font("Arial", "B", 11)
        pdf.cell(80, 10, "¿Presenta incompatibilidad?:", 0, 0)
        pdf.set_font("Arial", "", 11)
        pdf.cell(110, 10, "Sí" if incompatibilidad else "No", 0, 1)
        
        if incompatibilidad and "incompatibilidad_con" in data:
            pdf.set_font("Arial", "B", 11)
            pdf.cell(80, 10, "Incompatibilidad con:", 0, 0)
            pdf.set_font("Arial", "", 11)
            pdf.cell(110, 10, data.get("incompatibilidad_con", ""), 0, 1)
    
    if "piso" in data:
        pdf.set_font("Arial", "B", 11)
        pdf.cell(50, 10, "Piso:", 0, 0)
        pdf.set_font("Arial", "", 11)
        pdf.cell(140, 10, data.get("piso", ""), 0, 1)
    
    if "sector" in data:
        pdf.set_font("Arial", "B", 11)
        pdf.cell(50, 10, "Sector:", 0, 0)
        pdf.set_font("Arial", "", 11)
        pdf.cell(140, 10, data.get("sector", ""), 0, 1)
    
    # Descripción del problema
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Descripción del Problema", 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Usar descripción mejorada si existe, si no la original
    descripcion = data.get("descripcion_mejorada", data.get("descripcion_original", ""))
    
    pdf.set_font("Arial", "", 11)
    
    # Procesar texto largo con múltiples líneas
    pdf.multi_cell(0, 7, descripcion)
    pdf.ln(5)
    
    temp_files = []
    
    # NUEVO: Agregar imágenes si existen
    if "images" in data and data["images"]:
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "Imágenes Adjuntas", 0, 1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        # Iterar por cada imagen
        for i, image_url in enumerate(data["images"]):
            try:
                # Descargar imagen de S3
                print(f"Descargando imagen {i+1} desde: {image_url}")
                response = requests.get(image_url)
                
                if response.status_code == 200:
                    # Guardar temporalmente
                    temp_file_id = str(uuid.uuid4())[:8]
                    temp_img_path = os.path.join(config.TEMP_FOLDER, f"temp_image_{temp_file_id}.jpg")
                    with open(temp_img_path, "wb") as f:
                        f.write(response.content)
                    
                    temp_files.append(temp_img_path)
                    
                    # Añadir leyenda
                    pdf.set_font("Arial", "I", 10)
                    pdf.cell(0, 10, f"Imagen {i+1}:", 0, 1)
                    
                    try:
                    # Calcular dimensiones para mantenerla dentro de los márgenes
                        img_width = 180  # ancho máximo (en mm)
                        img_height = 120  # alto máximo (en mm)
                        img = Image.open(temp_img_path)
                        img_w, img_h = img.size
                        ratio = min(img_width/img_w, img_height/img_h)
                        final_width = img_w * ratio
                        final_height = img_h * ratio
                        pdf.image(temp_img_path, x=15, y=pdf.get_y(), w=final_width, h=final_height)
                        pdf.ln(final_height + 10)
                    except Exception as e:
                        print(f"Error al procesar imagen {i+1} con PIL: {e}")
                        pdf.set_text_color(255, 0, 0)
                        pdf.multi_cell(0, 7, f"Error al procesar imagen {i+1}: {str(e)}")
                        pdf.set_text_color(0, 0, 0)
                else:
                    pdf.set_text_color(255, 0, 0)
                    pdf.multi_cell(0, 7, f"Error al cargar imagen {i+1}: Error {response.status_code}")
                    pdf.set_text_color(0, 0, 0)
            except Exception as e:
                pdf.set_text_color(255, 0, 0)
                pdf.multi_cell(0, 7, f"Error al procesar imagen {i+1}: {str(e)}")
                pdf.set_text_color(0, 0, 0)
    
    # Espacio para firmas
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Firmas", 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(20)
    
    pdf.line(30, pdf.get_y(), 90, pdf.get_y())
    pdf.line(110, pdf.get_y(), 170, pdf.get_y())
    
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    pdf.cell(90, 5, "Solicitante", 0, 0, "C")
    pdf.cell(90, 5, "Responsable", 0, 1, "C")
    
    # Generar nombre de archivo
    pdf_filename = f"RFI_{rfi_id}.pdf"
    pdf_path = os.path.join(config.TEMP_FOLDER, pdf_filename)
    
    # Asegurarse de que exista la carpeta temporal
    os.makedirs(config.TEMP_FOLDER, exist_ok=True)
    
    try:
        pdf.output(pdf_path)
        print(f"PDF generado exitosamente: {pdf_path}")
        
        # Eliminar archivos temporales DESPUÉS de que el PDF se ha guardado
        if temp_files:
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