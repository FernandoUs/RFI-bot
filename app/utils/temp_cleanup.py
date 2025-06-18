"""
Utilidad para limpiar archivos temporales obsoletos del bot RFI
"""
import os
import time
import glob
from config import Config

def cleanup_old_temp_files(max_age_hours=24):
    """
    Limpia archivos temporales más antiguos que max_age_hours
    
    Args:
        max_age_hours (int): Edad máxima en horas antes de eliminar archivos
    """
    try:
        temp_folder = getattr(Config, 'TEMP_FOLDER', 'temp')
        
        if not os.path.exists(temp_folder):
            print(f"Carpeta temporal no existe: {temp_folder}")
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        files_deleted = 0
        
        # Buscar archivos PDF y de imagen temporales
        patterns = [
            os.path.join(temp_folder, "RFI_*.pdf"),
            os.path.join(temp_folder, "temp_img_*.jpg"),
            os.path.join(temp_folder, "temp_image_*.jpg"),
            os.path.join(temp_folder, "image_*.jpg")
        ]
        
        for pattern in patterns:
            for file_path in glob.glob(pattern):
                try:
                    # Verificar la edad del archivo
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        files_deleted += 1
                        print(f"Archivo temporal eliminado (antiguo): {file_path}")
                        
                except Exception as e:
                    print(f"No se pudo eliminar {file_path}: {e}")
        
        print(f"Limpieza completada: {files_deleted} archivos eliminados")
        return files_deleted
        
    except Exception as e:
        print(f"Error en limpieza de archivos temporales: {e}")
        return 0

def get_temp_folder_size():
    """
    Calcula el tamaño total de la carpeta temporal
    
    Returns:
        tuple: (cantidad_archivos, tamaño_MB)
    """
    try:
        temp_folder = getattr(Config, 'TEMP_FOLDER', 'temp')
        
        if not os.path.exists(temp_folder):
            return 0, 0.0
        
        total_size = 0
        file_count = 0
        
        for file_path in glob.glob(os.path.join(temp_folder, "*")):
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
                file_count += 1
        
        size_mb = total_size / (1024 * 1024)  # Convertir a MB
        return file_count, round(size_mb, 2)
        
    except Exception as e:
        print(f"Error al calcular tamaño de carpeta temporal: {e}")
        return 0, 0.0

if __name__ == "__main__":
    print("🧹 LIMPIEZA DE ARCHIVOS TEMPORALES")
    print("=" * 40)
    
    # Mostrar estado actual
    count, size = get_temp_folder_size()
    print(f"Estado actual: {count} archivos, {size} MB")
    
    # Limpiar archivos antiguos (más de 24 horas)
    deleted = cleanup_old_temp_files(24)
    
    # Mostrar estado después de la limpieza
    count_after, size_after = get_temp_folder_size()
    print(f"Después de limpieza: {count_after} archivos, {size_after} MB")
    print(f"Espacio liberado: {round(size - size_after, 2)} MB")
