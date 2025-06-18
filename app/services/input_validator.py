"""
Validadores de entrada para el bot de WhatsApp
"""
import re
import traceback

class InputValidator:
    """Validadores para diferentes tipos de entrada del usuario"""
    
    @staticmethod
    def validate_name(message):
        """
        Valida que el nombre tenga al menos 3 caracteres
        
        Args:
            message (str): Mensaje a validar
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            if not message or len(message.strip()) < 3:
                return False, "❌ *Nombre muy corto*\n\nPor favor, ingresa tu nombre completo (mínimo 3 caracteres).\n\n⬅️ Escribe 'volver' para regresar"
            return True, None
        except Exception as e:
            print(f"Error al validar nombre: {e}")
            traceback.print_exc()
            return False, "❌ Error al procesar el nombre. Por favor, intenta nuevamente."
    
    @staticmethod
    def validate_job_title(message):
        """
        Valida que el cargo tenga al menos 3 caracteres
        
        Args:
            message (str): Mensaje a validar
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            if not message or len(message.strip()) < 3:
                return False, "❌ *Cargo muy corto*\n\nPor favor, ingresa tu cargo (mínimo 3 caracteres).\n\n⬅️ Escribe 'volver' para regresar"
            return True, None
        except Exception as e:
            print(f"Error al validar cargo: {e}")
            traceback.print_exc()
            return False, "❌ Error al procesar el cargo. Por favor, intenta nuevamente."
    
    @staticmethod
    def validate_date(message):
        """
        Valida formato de fecha DD/MM/AA o DD/MM/AAAA
        
        Args:
            message (str): Mensaje a validar
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            if not message or not re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})$', message.strip()):
                return False, "❌ *Formato incorrecto*\n\nPor favor, ingresa la fecha en formato DD/MM/AA o DD/MM/AAAA.\n\n💡 Ejemplo: 15/12/24\n⬅️ Escribe 'volver' para regresar"
            return True, None
        except Exception as e:
            print(f"Error al validar fecha: {e}")
            traceback.print_exc()
            return False, "❌ Error al procesar la fecha. Por favor, intenta nuevamente."
    
    @staticmethod
    def validate_document_count(message):
        """
        Valida que el número de documentos esté entre 0 y 3
        
        Args:
            message (str): Mensaje a validar
            
        Returns:
            tuple: (is_valid, num_docs, error_message)
        """
        try:
            if not message:
                return False, None, "❌ *Número inválido*\n\nPor favor, ingresa un número válido entre 0 y 3.\n\n⬅️ Escribe 'volver' para regresar"
            
            try:
                num_docs = int(message.strip())
                if 0 <= num_docs <= 3:
                    return True, num_docs, None
                else:
                    return False, None, "❌ *Número inválido*\n\nPor favor, ingresa un número entre 0 y 3.\n\n⬅️ Escribe 'volver' para regresar"
            except ValueError:
                return False, None, "❌ *Número inválido*\n\nPor favor, ingresa un número válido entre 0 y 3.\n\n⬅️ Escribe 'volver' para regresar"
                
        except Exception as e:
            print(f"Error al validar número de documentos: {e}")
            traceback.print_exc()
            return False, None, "❌ Error al procesar el número de documentos. Por favor, intenta nuevamente."
    
    @staticmethod
    def validate_documents_list(message):
        """
        Valida que la lista de documentos no esté vacía
        
        Args:
            message (str): Mensaje a validar
            
        Returns:
            tuple: (is_valid, documents_list, error_message)
        """
        try:
            if not message or len(message.strip()) == 0:
                return False, None, "Por favor, ingresa al menos un documento de referencia.\n\n⬅️ Escribe 'volver' para regresar"
            
            docs = [doc.strip() for doc in message.split(',') if doc.strip()]
            return True, docs, None
            
        except Exception as e:
            print(f"Error al validar lista de documentos: {e}")
            traceback.print_exc()
            return False, None, "❌ Error al procesar los documentos. Por favor, intenta nuevamente."
    
    @staticmethod
    def validate_specialty_selection(message):
        """
        Valida la selección de especialidad (1-5)
        
        Args:
            message (str): Mensaje a validar
            
        Returns:
            tuple: (is_valid, selection, error_message)
        """
        try:
            if message in ['1', '2', '3', '4']:
                return True, int(message), None
            elif message == '5':
                return True, 5, None
            else:
                return False, None, "❌ *Opción inválida*\n\nSelecciona una opción válida (1-5)\n\n⬅️ Escribe 'volver' para regresar"
                
        except Exception as e:
            print(f"Error al validar selección de especialidad: {e}")
            traceback.print_exc()
            return False, None, "❌ Error al procesar la especialidad. Por favor, intenta nuevamente."
    
    @staticmethod
    def validate_custom_specialty(message):
        """
        Valida especialidad personalizada (mínimo 3 caracteres)
        
        Args:
            message (str): Mensaje a validar
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            if not message or len(message.strip()) < 3:
                return False, "❌ *Especialidad muy corta*\n\nPor favor, ingresa una especialidad válida (mínimo 3 caracteres):\n\n⬅️ Escribe 'volver' para regresar"
            return True, None
        except Exception as e:
            print(f"Error al validar especialidad personalizada: {e}")
            traceback.print_exc()
            return False, "❌ Error al procesar la especialidad personalizada. Por favor, intenta nuevamente."
    
    @staticmethod
    def validate_yes_no_selection(message):
        """
        Valida selección Sí/No (1/2)
        
        Args:
            message (str): Mensaje a validar
            
        Returns:
            tuple: (is_valid, selection, error_message)
        """
        try:
            if message == "1":
                return True, True, None
            elif message == "2":
                return True, False, None
            else:
                return False, None, "❌ *Opción inválida*\n\nSelecciona una opción válida:\n\n1️⃣ Sí\n2️⃣ No\n\n⬅️ Escribe 'volver' para regresar"
                
        except Exception as e:
            print(f"Error al validar selección Sí/No: {e}")
            traceback.print_exc()
            return False, None, "❌ Error al procesar la selección. Por favor, intenta nuevamente."
    
    @staticmethod
    def validate_floor_number(message):
        """
        Valida número de piso (solo números)
        
        Args:
            message (str): Mensaje a validar
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            if not message or not re.match(r'^\d+$', message):
                return False, "Por favor, ingresa un número válido para el piso.\n\n⬅️ Escribe 'volver' para regresar"
            return True, None
        except Exception as e:
            print(f"Error al validar número de piso: {e}")
            traceback.print_exc()
            return False, "❌ Error al procesar el piso. Por favor, intenta nuevamente."
    
    @staticmethod
    def validate_sector(message):
        """
        Valida que el sector no esté vacío
        
        Args:
            message (str): Mensaje a validar
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            if not message:
                return False, "Por favor, ingresa la ubicación del sector.\n\n⬅️ Escribe 'volver' para regresar"
            return True, None
        except Exception as e:
            print(f"Error al validar sector: {e}")
            traceback.print_exc()
            return False, "❌ Error al procesar el sector. Por favor, intenta nuevamente."
    
    @staticmethod
    def validate_description(message):
        """
        Valida descripción (mínimo 10 caracteres)
        
        Args:
            message (str): Mensaje a validar
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            if not message or len(message.strip()) < 10:
                return False, "❌ *Descripción muy corta*\n\nDescribe el problema con más detalle (mínimo 10 caracteres).\n\n⬅️ Escribe 'volver' para regresar"
            return True, None
        except Exception as e:
            print(f"Error al validar descripción: {e}")
            traceback.print_exc()
            return False, "❌ Error al procesar la descripción. Por favor, intenta nuevamente."
