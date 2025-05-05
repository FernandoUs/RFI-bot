import os
from fpdf import FPDF
from datetime import datetime
from app.utils.config import get_config
import requests
import random
from openai import OpenAI
import traceback
from app.services.s3_service import upload_file_to_s3

def improve_description(description):
    """
    Mejora la descripción del problema usando múltiples modelos con sistema de respaldo
    """
    config = get_config()
    
    # Primero intentar con AnyScale (si está configurado)
    if hasattr(config, 'ANY_SCALE_API_KEY') and config.ANY_SCALE_API_KEY:
        try:
            
            print("Intentando mejorar descripción con AnyScale...")
            client = OpenAI(
                api_key=config.ANY_SCALE_API_KEY,
                base_url=config.ANY_SCALE_API_BASE
            )
            
            response = client.chat.completions.create(
                model="meta-llama/Llama-3-8b-chat-hf",
                messages=[
                    {"role": "system", "content": "Eres un experto en construcción que responde en español. Mejora descripciones técnicas para RFIs manteniendo un tono profesional y preciso."},
                    {"role": "user", "content": f"Mejora esta descripción técnica para un RFI de construcción, haciéndola más profesional y detallada. Responde SOLO en español: {description}"}
                ],
                temperature=0.5,
                max_tokens=300
            )
            
            improved_text = response.choices[0].message.content.strip()
            
            if improved_text and len(improved_text) > 20 and contains_spanish(improved_text):
                print("Descripción mejorada exitosamente con AnyScale")
                return improved_text
            
            print("AnyScale devolvió texto inadecuado, probando con Hugging Face")
        except Exception as e:
            print(f"Error al usar AnyScale: {e}")
    
    # Si llegamos aquí, AnyScale falló o no está configurado, intentar con Hugging Face
    try:
        huggingface_token = config.HUGGINGFACE_API_KEY
        
        if not huggingface_token or huggingface_token == "tu_token_copiado_aquí":
            print("ERROR: No se ha configurado el token de Hugging Face correctamente")
            return enhance_description_locally(description)
        
        # Definir varios modelos a probar en orden
        models = [
            {
                "name": "GPT-2 en Español",
                "url": "https://api-inference.huggingface.co/models/PlanTL-GOB-ES/gpt2-large-bne",
                "type": "text-generation",
                "prompt": f"Mejora esta descripción para un RFI de construcción: {description}\n\nDescripción mejorada:"
            },
            {
                "name": "mT5 Pequeño",
                "url": "https://api-inference.huggingface.co/models/google/mt5-small",
                "type": "text2text-generation",
                "prompt": f"Mejora esta descripción técnica para un RFI de construcción en español: {description}"
            },
            {
                "name": "MBart Multilingüe",
                "url": "https://api-inference.huggingface.co/models/facebook/mbart-large-50-many-to-many-mmt",
                "type": "translation",
                "prompt": description,
                "params": {
                    "src_lang": "es_XX",
                    "tgt_lang": "es_XX"
                }
            }
        ]
        
        headers = {
            "Authorization": f"Bearer {huggingface_token}",
            "Content-Type": "application/json"
        }
        
        # Intentar cada modelo secuencialmente
        for model in models:
            try:
                print(f"Intentando mejorar descripción con {model['name']}...")
                
                # Configurar payload según el tipo de modelo
                if model["type"] == "translation":
                    payload = {
                        "inputs": model["prompt"],
                        "parameters": {
                            "max_length": 300,
                            "temperature": 0.7,
                            "top_p": 0.85,
                            "do_sample": True,
                            "src_lang": model["params"]["src_lang"],
                            "tgt_lang": model["params"]["tgt_lang"]
                        }
                    }
                else:
                    payload = {
                        "inputs": model["prompt"],
                        "parameters": {
                            "max_length": 300,
                            "temperature": 0.7,
                            "top_p": 0.85,
                            "do_sample": True,
                            "return_full_text": False
                        }
                    }
                
                # Hacer la solicitud con timeout
                response = requests.post(model["url"], headers=headers, json=payload, timeout=15)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extraer texto según el tipo de modelo
                    if model["type"] == "translation":
                        field_name = "translation_text"
                    else:
                        field_name = "generated_text"
                    
                    # Intentar extraer el texto generado
                    if isinstance(result, list) and len(result) > 0:
                        improved_text = result[0].get(field_name, "")
                    else:
                        improved_text = result.get(field_name, "")
                    
                    # Verificar calidad del texto generado
                    if improved_text and len(improved_text) > 20 and contains_spanish(improved_text):
                        print(f"Descripción mejorada exitosamente con {model['name']}")
                        return improved_text
                    else:
                        print(f"El modelo {model['name']} devolvió texto inadecuado: {improved_text}")
                
                else:
                    error_msg = f"Error {response.status_code}: {response.text}"
                    print(f"Error con modelo {model['name']}: {error_msg}")
                
            except requests.exceptions.Timeout:
                print(f"Timeout al consultar el modelo {model['name']}")
            except Exception as e:
                print(f"Error al probar modelo {model['name']}: {e}")
                print(traceback.format_exc())
        
        # Si llegamos aquí, todos los modelos fallaron
        print("Todos los modelos fallaron, usando fallback local")
        return enhance_description_locally(description)
    
    except Exception as e:
        print(f"Error general al mejorar la descripción: {e}")
        return enhance_description_locally(description)

def contains_spanish(text):
    """Verifica si el texto contiene caracteres típicos del español"""
    spanish_chars = ['á', 'é', 'í', 'ó', 'ú', 'ñ', 'ü', '¿', '¡']
    spanish_words = ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'pero', 'porque', 'que', 'con']
    
    # Verificar caracteres especiales
    for char in spanish_chars:
        if char in text.lower():
            return True
    
    # Verificar palabras comunes
    for word in spanish_words:
        if f" {word} " in f" {text.lower()} ":
            return True
    
    return False

def enhance_description_locally(description):
    """
    Fallback local para mejorar descripciones cuando la API no está disponible
    """
    # Lista de prefijos profesionales en español
    prefixes = [
        "Se ha identificado una discrepancia técnica donde ",
        "Se ha detectado un problema de construcción en el que ",
        "Durante la inspección se observó que ",
        "Se requiere información adicional debido a que ",
        "El equipo técnico ha encontrado que ",
        "La revisión del proyecto ha revelado que ",
        "Es necesario aclarar la especificación técnica porque "
    ]
    
    prefix = random.choice(prefixes)
    
    # Evitar duplicación si ya tiene un prefijo similar
    for p in prefixes:
        if description.lower().startswith(p.lower()):
            return description
    
    # Mejorar formato
    enhanced = description.strip()
    if not enhanced.endswith("."):
        enhanced += "."
    
    # Capitalizar primera letra si es necesario
    if enhanced and enhanced[0].islower():
        enhanced = enhanced[0].upper() + enhanced[1:]
    
    return f"{prefix}{enhanced}"

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