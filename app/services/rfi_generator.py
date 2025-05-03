import os
from fpdf import FPDF
from datetime import datetime
from app.utils.config import get_config
import requests


def improve_description(description):
    """
    Mejora la descripción del problema usando Hugging Face
    """
    config = get_config()
    try:
        
        huggingface_token = config.HUGGINGFACE_API_KEY
        
        if not huggingface_token or huggingface_token == "tu_token_copiado_aquí":
            print("ERROR: No se ha configurado el token de Hugging Face correctamente")
            return f"Se ha identificado un problema de construcción donde {description}"
        
        API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        
        headers = {
            "Authorization": f"Bearer {huggingface_token}",
            "Content-Type": "application/json"
        }
        
        prompt = (
            "Eres un asistente especializado en ingeniería y construcción. "
            f"Mejora esta descripción técnica para un RFI: '{description}'"
        )
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 300, "temperature": 0.7}
        }

        
        # Hacer la solicitud
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        # Procesar respuesta
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
                
                # Extraer solo la respuesta (eliminar el prompt)
                if "[/INST]" in generated_text:
                    improved_text = generated_text.split("[/INST]</s>")[-1].strip()
                else:
                    improved_text = generated_text.replace(payload["inputs"], "").strip()
                
                # Verificar calidad
                if improved_text and len(improved_text) > len(description):
                    return improved_text
                else:
                    print("La API devolvió un texto demasiado corto, usando fallback")
        else:
            error_msg = f"Error {response.status_code}: {response.text}"
            print(f"Error con Hugging Face API: {error_msg}")
        
        # Si llegamos aquí, algo falló, usar fallback
        return f"Se ha identificado el siguiente problema en la construcción: {description}"
    
    except Exception as e:
        print(f"Error al mejorar la descripción: {e}")
        return f"Se ha identificado el siguiente problema en la construcción: {description}"

def generate_rfi_pdf(data, rfi_id):
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
    pdf.cell(95, 10, f"RFI #: {rfi_id}", 0, 0)
    pdf.cell(95, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", 0, 1)
    pdf.ln(5)
    
    # Datos recopilados
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Información del Problema:", 0, 1)
    pdf.set_font("Arial", "", 12)
    
    pdf.cell(190, 10, f"Especialidad: {data.get('especialidad', 'No especificado')}", 0, 1)
    
    if data.get('incompatibilidad', False):
        pdf.cell(190, 10, f"Incompatibilidad con: {data.get('incompatibilidad_con', 'No especificado')}", 0, 1)
    else:
        pdf.cell(190, 10, "No presenta incompatibilidad con otras especialidades", 0, 1)
    
    pdf.cell(190, 10, f"Piso: {data.get('piso', 'No especificado')}", 0, 1)
    pdf.cell(190, 10, f"Sector: {data.get('sector', 'No especificado')}", 0, 1)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Descripción del Problema:", 0, 1)
    pdf.set_font("Arial", "", 12)
    
    # Descripción mejorada con saltos de línea
    description = data.get('descripcion_mejorada', 'No especificado')
    pdf.multi_cell(190, 10, description)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Espacio para Respuesta:", 0, 1)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(190, 10, "_" * 50)
    
    # Guardar el PDF
    pdf_filename = f"RFI_{rfi_id}.pdf"
    pdf_path = os.path.join(config.TEMP_FOLDER, pdf_filename)
    
    pdf.output(pdf_path)
    from app.services.s3_service import upload_file_to_s3
    pdf_url = upload_file_to_s3(pdf_path, folder="pdfs", object_name=pdf_filename)
    
    return pdf_path, pdf_url

def analyze_plan_image(image_path):
    """
    Función para futura implementación: Analiza una imagen de plano
    usando IA para detectar ejes y problemas
    """
    # Implementación futura para análisis de planos
    # Podría usar OpenAI Vision API o bibliotecas como OpenCV
    pass