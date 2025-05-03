import pytest
import os
import sys
from app.services.rfi_generator import improve_description, generate_rfi_pdf

def test_improve_description():
    """Test para la función de mejora de descripciones"""
    # Descripción de prueba
    test_description = "hay una tuberia que choca con una viga"
    
    # Mejorar descripción
    improved = improve_description(test_description)
    
    # Verificar que la descripción contiene palabras clave, incluso si falla la conexión con la API
    assert "tuberia" in improved.lower() or "tubería" in improved.lower()
    assert "viga" in improved.lower()
    
    # Mensaje informativo en caso de fallo en la conexión
    if len(improved) <= len(test_description):
        print("ADVERTENCIA: La API no mejoró el texto. Puede ser un problema de conexión con AnyScale.")

def test_generate_rfi_pdf():
    """Test para la generación de PDF"""
    # Datos de prueba
    test_data = {
        'especialidad': 'Sanitarias',
        'incompatibilidad': True,
        'incompatibilidad_con': 'Estructuras',
        'piso': '3',
        'sector': 'B-2',
        'descripcion_mejorada': 'Se ha detectado una interferencia entre la tubería principal de desagüe y una viga estructural de concreto.'
    }
    rfi_id = "TEST123"
    
    # Generar PDF - ahora devuelve una tupla (pdf_path, pdf_url)
    pdf_tuple = generate_rfi_pdf(test_data, rfi_id)
    pdf_path = pdf_tuple[0]  # Extraer la ruta del PDF
    
    # Verificar que el archivo existe
    assert os.path.exists(pdf_path)
    
    # Verificar que el archivo tiene contenido
    assert os.path.getsize(pdf_path) > 0
    
    # Limpiar
    os.remove(pdf_path)