import os
import json
from datetime import datetime
import time

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
    
    def save_rfi(self, rfi_data, phone_number):
        """
        Guarda un RFI completado en archivo JSON
        
        Args:
            rfi_data: Datos del RFI a guardar
            phone_number: Número de teléfono del usuario
        """
        try:
            # Leer RFIs existentes
            with open(self.rfis_file, "r") as f:
                rfis = json.load(f)
            
            # Crear ID único para el RFI
            rfi_id = str(rfi_data.get('rfi_id'))
            rfi_key = f"{phone_number}_{rfi_id}"
            
            # Guardar el RFI
            rfis[rfi_key] = {
                'rfi_id': rfi_id,
                'phone_number': phone_number,
                'data': rfi_data.get('data', {}),
                'pdf_path': rfi_data.get('pdf_path'),
                'pdf_url': rfi_data.get('pdf_url'),
                'creation_time': rfi_data.get('creation_time', time.time()),
                'created_at': datetime.now().isoformat()
            }
            
            # Guardar archivo
            with open(self.rfis_file, "w") as f:
                json.dump(rfis, f, indent=2)
            
            print(f"RFI #{rfi_id} guardado correctamente para {phone_number}")
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
    
    def get_user_rfis(self, phone_number):
        """
        Recupera todos los RFIs de un usuario por su número de teléfono
        
        Args:
            phone_number: Número de teléfono del usuario
            
        Returns:
            list: Lista de RFIs del usuario ordenados por fecha de creación
        """
        try:
            with open(self.rfis_file, "r") as f:
                rfis = json.load(f)
                user_rfis = [rfi for rfi in rfis.values() if rfi.get('phone_number') == phone_number]
                # Ordenar por fecha de creación (más reciente primero)
                user_rfis.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                return user_rfis
        except Exception as e:
            print(f"Error al recuperar RFIs del usuario: {e}")
            return []

    def get_user_rfi_count(self, phone_number):
        """
        Recupera el número de RFIs completados por un usuario
        
        Args:
            phone_number: Número de teléfono del usuario
            
        Returns:
            int: Número de RFIs completados por el usuario
        """
        try:
            rfis = self.get_user_rfis(phone_number)
            return len(rfis)
        except Exception as e:
            print(f"Error al contar RFIs del usuario: {e}")
            return 0