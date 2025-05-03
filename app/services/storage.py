import os
import json
from datetime import datetime

class DatabaseManager:
    """
    Gestor de base de datos para almacenar sesiones y RFIs
    En esta implementación se usa JSON como almacenamiento persistente
    para facilitar el desarrollo, pero en producción deberías usar 
    una base de datos real como PostgreSQL o DynamoDB.
    """
    def __init__(self):
        self.sessions_file = os.path.join(os.getcwd(), "data", "sessions.json")
        self.rfis_file = os.path.join(os.getcwd(), "data", "rfis.json")
        
        # Crear directorios si no existen
        os.makedirs(os.path.dirname(self.sessions_file), exist_ok=True)
        
        # Inicializar archivos si no existen
        if not os.path.exists(self.sessions_file):
            with open(self.sessions_file, "w") as f:
                json.dump({}, f)
        
        if not os.path.exists(self.rfis_file):
            with open(self.rfis_file, "w") as f:
                json.dump({}, f)
    
    def get_session(self, phone_number):
        """
        Recupera la sesión de un usuario por su número de teléfono
        
        Args:
            phone_number: Número de teléfono del usuario
            
        Returns:
            dict: Datos de la sesión o None si no existe
        """
        try:
            with open(self.sessions_file, "r") as f:
                sessions = json.load(f)
                return sessions.get(phone_number)
        except Exception as e:
            print(f"Error al recuperar sesión: {e}")
            return None
    
    def save_session(self, phone_number, session_data):
        """
        Guarda o actualiza la sesión de un usuario
        
        Args:
            phone_number: Número de teléfono del usuario
            session_data: Datos de la sesión a guardar
        """
        try:
            with open(self.sessions_file, "r") as f:
                sessions = json.load(f)
            
            sessions[phone_number] = session_data
            
            with open(self.sessions_file, "w") as f:
                json.dump(sessions, f, indent=2)
        except Exception as e:
            print(f"Error al guardar sesión: {e}")
    
    def delete_session(self, phone_number):
        """
        Elimina la sesión de un usuario
        
        Args:
            phone_number: Número de teléfono del usuario
        """
        try:
            with open(self.sessions_file, "r") as f:
                sessions = json.load(f)
            
            if phone_number in sessions:
                del sessions[phone_number]
            
            with open(self.sessions_file, "w") as f:
                json.dump(sessions, f, indent=2)
        except Exception as e:
            print(f"Error al eliminar sesión: {e}")
    
    def save_rfi(self, rfi_data):
        """
        Guarda un RFI completado
        
        Args:
            rfi_data: Datos del RFI a guardar
        """
        try:
            with open(self.rfis_file, "r") as f:
                rfis = json.load(f)
            
            # Añadir fecha de creación
            rfi_data['created_at'] = datetime.now().isoformat()
            
            # Guardar por ID
            rfis[rfi_data['rfi_id']] = rfi_data
            
            with open(self.rfis_file, "w") as f:
                json.dump(rfis, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error al guardar RFI: {e}")
            return False
    
    def get_rfi(self, rfi_id):
        """
        Recupera un RFI por su ID
        
        Args:
            rfi_id: ID del RFI
            
        Returns:
            dict: Datos del RFI o None si no existe
        """
        try:
            with open(self.rfis_file, "r") as f:
                rfis = json.load(f)
                return rfis.get(rfi_id)
        except Exception as e:
            print(f"Error al recuperar RFI: {e}")
            return None