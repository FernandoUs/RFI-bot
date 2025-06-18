"""
Manejador de navegación hacia atrás en el flujo RFI
"""
import traceback
from app.services.prompt_generator import PromptGenerator

class BackNavigationHandler:
    """Maneja la navegación hacia atrás en el flujo de creación de RFI"""
    
    # Mapeo de pasos anteriores
    BACK_STEPS = {
        1.1: 1,
        1.2: 1.1,
        1.3: 1.2,
        1.4: 1.3,
        2: None,  # Se calcula dinámicamente
        2.1: 2,
        3: None,  # Se calcula dinámicamente
        4: 3,
        4.1: 4,
        5: None,  # Se calcula dinámicamente
        6: 5,
        7: 6,
        8: 7,
        8.1: 8,
        8.2: 8.1
    }
    
    @staticmethod
    def can_go_back(step):
        """
        Verifica si se puede ir hacia atrás desde el paso actual
        
        Args:
            step (int): Paso actual
            
        Returns:
            bool: True si se puede ir hacia atrás
        """
        return step in [1, 1.1, 1.2, 1.3, 1.4, 2, 2.1, 3, 4, 4.1, 5, 6, 7, 8]
    
    @staticmethod
    def get_previous_step(session, current_step):
        """
        Obtiene el paso anterior basado en el flujo y la sesión
        
        Args:
            session (dict): Sesión actual
            current_step (int): Paso actual
            
        Returns:
            int or None: Paso anterior o None si no se puede ir atrás
        """
        try:
            # Casos especiales que dependen del estado de la sesión
            if current_step == 2:
                # Volver a 1.4 si hay documentos, sino a 1.3
                if session.get('data', {}).get('num_documentos_referencia', 0) > 0:
                    return 1.4
                else:
                    return 1.3
            
            elif current_step == 3:
                # Volver a 2.1 si se pasó por especialidad personalizada, sino a 2
                if BackNavigationHandler._passed_through_step(session, 2.1):
                    return 2.1
                else:
                    return 2
            
            elif current_step == 5:
                # Volver a 4.1 si se pasó por incompatibilidad personalizada,
                # sino a 4 si hay incompatibilidad, sino a 3
                if BackNavigationHandler._passed_through_step(session, 4.1):
                    return 4.1
                elif session.get('data', {}).get('incompatibilidad'):
                    return 4
                else:
                    return 3
            
            # Casos normales
            return BackNavigationHandler.BACK_STEPS.get(current_step)
            
        except Exception as e:
            print(f"Error al calcular paso anterior: {e}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def _passed_through_step(session, step):
        """
        Verifica si se pasó por un paso específico en el historial
        
        Args:
            session (dict): Sesión actual
            step (int): Paso a verificar
            
        Returns:
            bool: True si se pasó por el paso
        """
        try:
            step_history = session.get('step_history', [])
            return step_history.count(step) > 0
        except Exception as e:
            print(f"Error al verificar historial de pasos: {e}")
            traceback.print_exc()
            return False
    
    @staticmethod
    def handle_back_command(session, msg_response):
        """
        Maneja el comando 'volver' con manejo de errores
        
        Args:
            session (dict): Sesión actual
            msg_response: Objeto de respuesta de mensaje
            
        Returns:
            bool: True si se pudo ir hacia atrás, False en caso contrario
        """
        try:
            current_step = session.get('step', 1)
            
            # Verificar si se puede ir hacia atrás
            if not BackNavigationHandler.can_go_back(current_step):
                msg_response.body("❌ No puedes volver en este punto del proceso.")
                return False
            
            # Obtener paso anterior
            previous_step = BackNavigationHandler.get_previous_step(session, current_step)
            
            if previous_step is not None:
                # Actualizar step en la sesión
                session['step'] = previous_step
                
                # Enviar prompt del paso anterior
                prompt = PromptGenerator.get_step_prompt(session, previous_step)
                msg_response.body(prompt)
                
                return True
            else:
                msg_response.body("❌ No puedes volver más atrás.")
                return False
                
        except Exception as e:
            print(f"Error en handle_back_command: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar comando 'volver'.")
            return False
    
    @staticmethod
    def is_back_command(message):
        """
        Verifica si el mensaje es un comando para ir hacia atrás
        
        Args:
            message (str): Mensaje del usuario
            
        Returns:
            bool: True si es un comando de ir hacia atrás
        """
        if not message:
            return False
        
        back_commands = ['volver', 'atras', 'atrás', 'back']
        return message.lower() in back_commands
