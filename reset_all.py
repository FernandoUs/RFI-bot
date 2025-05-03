from app.services.storage import DatabaseManager

def reset_all_sessions():
    """
    Elimina todas las sesiones de la base de datos
    """
    db = DatabaseManager()
    
    # Limpiar archivo JSON si está usando almacenamiento de archivos
    try:
        import os
        import json
        
        # Ubicación probable del archivo de sesiones
        session_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   'app', 'data', 'sessions.json')
        
        if os.path.exists(session_file):
            with open(session_file, 'w') as f:
                json.dump({}, f)
            print(f"Archivo de sesiones limpiado: {session_file}")
        else:
            print(f"Archivo de sesiones no encontrado en: {session_file}")
        
        # Buscar otros posibles archivos JSON
        for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):
            for file in files:
                if file.endswith('.json') and 'session' in file.lower():
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'w') as f:
                            json.dump({}, f)
                        print(f"Archivo limpiado: {path}")
                    except:
                        pass
        
    except Exception as e:
        print(f"Error al limpiar archivos: {e}")
    
    # Si está usando un método específico
    try:
        # Para la implementación DatabaseManager básica
        db._sessions = {}
        db._save_sessions()
        print("Sesiones limpiadas en memoria y guardadas")
    except:
        pass

if __name__ == "__main__":
    reset_all_sessions()
    print("Proceso de limpieza completado. Reinicia el servidor.")