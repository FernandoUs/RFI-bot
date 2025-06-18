"""
Gestión de sesiones de usuario para el bot de WhatsApp
"""
import time
import traceback
from app.services.storage import DatabaseManager

db = DatabaseManager()

class SessionManager:
    """Maneja todas las operaciones relacionadas con sesiones de usuario"""
    
    @staticmethod
    def get_user_session(clean_sender):
        """
        Obtiene la sesión actual del usuario
        
        Args:
            clean_sender (str): Número del usuario limpio
            
        Returns:
            dict: Sesión del usuario o None si no existe
        """
        try:
            return db.get_session(clean_sender)
        except Exception as e:
            print(f"Error al recuperar sesión para {clean_sender}: {e}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def create_new_session(clean_sender, twilio_limit_reached=False):
        """
        Crea una nueva sesión para el usuario
        
        Args:
            clean_sender (str): Número del usuario limpio
            twilio_limit_reached (bool): Si se alcanzó el límite de Twilio
            
        Returns:
            dict: Nueva sesión creada
        """
        try:
            session = {
                'step': 0,
                'menu_state': 'main_menu',
                'data': {'images': []},
                'rfi_id': None,
                'send_pdf': False,
                'pdf_sent': False,
                'twilio_limit_reached': twilio_limit_reached,
                'creation_time': time.time()
            }
            
            db.save_session(clean_sender, session)
            return session
        except Exception as e:
            print(f"Error al crear sesión para {clean_sender}: {e}")
            traceback.print_exc()
            raise
    
    @staticmethod
    def create_rfi_session(clean_sender, twilio_limit_reached=False):
        """
        Crea una nueva sesión para crear un RFI
        
        Args:
            clean_sender (str): Número del usuario limpio
            twilio_limit_reached (bool): Si se alcanzó el límite de Twilio
            
        Returns:
            dict: Nueva sesión para RFI
        """
        try:
            user_rfi_count = db.get_user_rfi_count(clean_sender)
            
            session = {
                'step': 1,
                'data': {'images': []},
                'rfi_id': user_rfi_count + 1,
                'send_pdf': False,
                'pdf_sent': False,
                'twilio_limit_reached': twilio_limit_reached,
                'creation_time': time.time()
            }
            
            db.save_session(clean_sender, session)
            return session
        except Exception as e:
            print(f"Error al crear sesión RFI para {clean_sender}: {e}")
            traceback.print_exc()
            raise
    
    @staticmethod
    def reset_session(clean_sender):
        """
        Reinicia la sesión del usuario eliminando la anterior
        
        Args:
            clean_sender (str): Número del usuario limpio
            
        Returns:
            dict: Nueva sesión creada
        """
        try:
            # Eliminar sesión anterior
            try:
                db.delete_session(clean_sender)
                print(f"Sesión anterior eliminada para {clean_sender}")
            except Exception as e:
                print(f"Error al eliminar sesión anterior: {e}")
                traceback.print_exc()
            
            # Crear nueva sesión
            return SessionManager.create_rfi_session(clean_sender)
        except Exception as e:
            print(f"Error al reiniciar sesión para {clean_sender}: {e}")
            traceback.print_exc()
            raise
    
    @staticmethod
    def save_session(clean_sender, session):
        """
        Guarda la sesión del usuario
        
        Args:
            clean_sender (str): Número del usuario limpio
            session (dict): Datos de la sesión
        """
        try:
            db.save_session(clean_sender, session)
        except Exception as e:
            print(f"Error al guardar sesión para {clean_sender}: {e}")
            traceback.print_exc()
            raise
    
    @staticmethod
    def update_session_for_menu(session):
        """
        Actualiza la sesión para regresar al menú principal
        
        Args:
            session (dict): Sesión actual
        """
        try:
            session['step'] = 0
            session['menu_state'] = 'main_menu'
            # No resetear pdf_sent si ya está en True (evita bucles después de enviar PDF desde historial)
            if not session.get('pdf_sent', False):
                session['pdf_sent'] = False
        except Exception as e:
            print(f"Error al actualizar sesión para menú: {e}")
            traceback.print_exc()
            raise
    
    @staticmethod
    def update_session_for_history(session):
        """
        Actualiza la sesión para mostrar historial
        
        Args:
            session (dict): Sesión actual
        """
        try:
            session['step'] = 0
            session['menu_state'] = 'viewing_history'
            # No resetear pdf_sent si ya está en True (evita bucles después de enviar PDF desde historial)
            if not session.get('pdf_sent', False):
                session['pdf_sent'] = False
        except Exception as e:
            print(f"Error al actualizar sesión para historial: {e}")
            traceback.print_exc()
            raise
