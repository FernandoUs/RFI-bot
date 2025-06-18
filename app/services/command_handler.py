"""
Manejador de comandos de WhatsApp
"""
import traceback
from app.services.session_manager import SessionManager
from app.services.menu_manager import (
    show_main_menu, 
    handle_menu_selection, 
    show_rfi_history, 
    handle_rfi_selection,
    handle_navigation_command
)

class CommandHandler:
    """Maneja los diferentes comandos y acciones del usuario"""
    
    @staticmethod
    def handle_post_pdf_commands(session, message, clean_sender):
        """
        Maneja comandos después de que se envió un PDF
        
        Args:
            session (dict): Sesión actual
            message (str): Mensaje del usuario
            clean_sender (str): Número del usuario limpio
            
        Returns:
            tuple: (response_text, updated_session)
        """
        try:
            # Verificar si hay límite de Twilio alcanzado
            if session.get('twilio_limit_reached'):
                if message and message.lower() in ['enlace', 'link', 'pdf', 'documento']:
                    # Proporcionar enlace al PDF pendiente
                    pdf_url = session.get('pending_pdf_url')
                    rfi_id = session.get('pending_pdf_rfi_id', 'N/A')
                    
                    if pdf_url:
                        response = f"📄 *RFI #{rfi_id} - Documento Generado*\n\n"
                        response += "✅ Tu RFI fue procesado exitosamente.\n"
                        response += "⚠️ No se pudo enviar por WhatsApp debido al límite diario de mensajes.\n\n"
                        response += f"🔗 **Descarga tu PDF aquí:**\n{pdf_url}\n\n"
                        response += "💡 *Opciones:*\n"
                        response += "• Escribe 'menu' para ir al menú principal\n"
                        response += "• Escribe 'nuevo' para crear otro RFI\n"
                        response += "• Escribe 'historial' para ver RFIs anteriores"
                        return response, session
                    else:
                        return "❌ No se encontró el enlace del PDF. Por favor contacta al administrador.", session
                
                elif message and message.lower() in ['menu', 'menú']:
                    # Regresar al menú principal pero mantener info del límite
                    SessionManager.update_session_for_menu(session)
                    response = "⚠️ *Límite diario de WhatsApp alcanzado*\n\n"
                    response += "El servicio ha alcanzado el límite de mensajes diarios.\n"
                    response += "Los PDFs se generan correctamente pero no se pueden enviar automáticamente.\n\n"
                    response += "💡 Escribe 'enlace' para obtener el link de descarga de tu último RFI.\n\n"
                    response += show_main_menu()
                    return response, session
                
                # Mensaje por defecto cuando hay límite alcanzado
                response = "⚠️ *Límite diario de WhatsApp alcanzado*\n\n"
                response += "El servicio ha alcanzado el límite de 9 mensajes diarios de la cuenta trial.\n"
                response += "Tu RFI fue procesado correctamente pero no se pudo enviar automáticamente.\n\n"
                response += "💡 *Opciones disponibles:*\n"
                response += "• Escribe 'enlace' para obtener el link de descarga\n"
                response += "• Escribe 'menu' para ir al menú principal\n"
                response += "• Escribe 'nuevo' para crear otro RFI\n\n"
                response += "🔄 El límite se reinicia cada 24 horas."
                return response, session            # PRIORIDAD 1: Manejo de números para historial cuando ya estamos viendo el historial
            if message and session.get('menu_state') == 'viewing_history' and message.isdigit():
                return CommandHandler.handle_menu_navigation(session, message, clean_sender)
            
            # PRIORIDAD 2: Opciones del menú principal (después de PDF)
            # Cuando el usuario envía '1' o '2' después de recibir el PDF
            # IMPORTANTE: Solo procesar esto si NO estamos en viewing_history
            if message and message.strip() in ['1', '2'] and session.get('menu_state') != 'viewing_history':
                if message == '1':
                    # Ver historial
                    try:
                        SessionManager.update_session_for_history(session)
                        SessionManager.save_session(clean_sender, session)
                        return show_rfi_history(clean_sender), session
                    except Exception as e:
                        print(f"Error al mostrar historial: {e}")
                        traceback.print_exc()
                        return "❌ Error al cargar el historial. Por favor, intenta nuevamente.", session
                
                elif message == '2':
                    # Crear nuevo RFI
                    try:
                        new_session = SessionManager.reset_session(clean_sender)
                        from app.services.prompt_generator import PromptGenerator
                        prompt = PromptGenerator.get_step_prompt(new_session)
                        response = "🆕 *Nuevo RFI*\n\nPerfecto! Vamos a crear un nuevo RFI.\n\n" + prompt
                        return response, new_session
                    except Exception as e:
                        print(f"Error al crear nueva sesión: {e}")
                        traceback.print_exc()
                        return "❌ Error al reiniciar el proceso. Por favor, intenta nuevamente.", session
            
            # PRIORIDAD 3: Comandos específicos por texto
            if message and message.lower() in ['menu', 'menú']:
                # Mostrar menú principal
                SessionManager.update_session_for_menu(session)
                response = "✅ *RFI Completado Exitosamente*\n\n" + show_main_menu()
                return response, session
                
            elif message and message.lower() in ['nuevo', 'reiniciar', 'reset', '2']:
                # Crear nuevo RFI
                try:
                    new_session = SessionManager.reset_session(clean_sender)
                    from app.services.prompt_generator import PromptGenerator
                    prompt = PromptGenerator.get_step_prompt(new_session)
                    response = "🔄 *Proceso Reiniciado*\n\nPerfecto! Vamos a crear un nuevo RFI.\n\n" + prompt
                    return response, new_session
                except Exception as e:
                    print(f"Error al crear nueva sesión: {e}")
                    traceback.print_exc()
                    return "❌ Error al reiniciar el proceso. Por favor, intenta nuevamente.", session
                    
            elif message and message.lower() in ['historial', '1']:
                # Mostrar historial de RFIs
                try:
                    SessionManager.update_session_for_history(session)
                    SessionManager.save_session(clean_sender, session)
                    return show_rfi_history(clean_sender), session
                except Exception as e:
                    print(f"Error al mostrar historial: {e}")
                    traceback.print_exc()
                    return "❌ Error al cargar el historial. Por favor, intenta nuevamente.", session
            
            # PRIORIDAD 4: Mensaje por defecto con opciones claras
            else:
                # Para cualquier otro mensaje, mostrar opciones disponibles de forma clara
                response = "✅ *RFI Completado Exitosamente*\n\n"
                response += "Tu RFI anterior fue procesado y enviado correctamente.\n\n"
                response += "*¿Qué te gustaría hacer ahora?*\n\n"
                response += "1️⃣ Ver historial de RFIs\n"
                response += "2️⃣ Crear un nuevo RFI\n\n"
                response += "� También puedes escribir:\n"
                response += "• 'menu' para ver opciones\n"
                response += "• 'historial' para ver tus RFIs\n"
                response += "• 'nuevo' para crear otro RFI"
                return response, session
                       
        except Exception as e:
            print(f"Error al manejar comando post-PDF: {e}")
            traceback.print_exc()
            return "❌ Error al procesar el comando. Escribe 'menu' para continuar.", session
    
    @staticmethod
    def handle_reset_command(session, clean_sender):
        """
        Maneja el comando de reinicio explícito
        
        Args:
            session (dict): Sesión actual
            clean_sender (str): Número del usuario limpio
            
        Returns:
            tuple: (response_text, updated_session)
        """
        try:
            # Si hay una sesión previa, guardar algunos datos relevantes
            twilio_limit_reached = session.get('twilio_limit_reached', False) if session else False
            
            # Crear nueva sesión con ID único
            try:
                new_session = SessionManager.reset_session(clean_sender)
                new_session['twilio_limit_reached'] = twilio_limit_reached
                SessionManager.save_session(clean_sender, new_session)
                
                # Agregar prompt inicial para que el usuario sepa qué hacer
                from app.services.prompt_generator import PromptGenerator
                prompt = PromptGenerator.get_step_prompt(1, new_session.get('data', {}))
                response = "🔄 *Proceso Reiniciado*\n\n" + \
                         "Perfecto! Vamos a crear un nuevo RFI.\n\n" + \
                         prompt
                return response, new_session
            except Exception as e:
                print(f"Error al crear nueva sesión después del reinicio: {e}")
                traceback.print_exc()
                return "❌ Error al reiniciar. Por favor, intenta nuevamente.", session
                
        except Exception as e:
            print(f"Error general en reinicio: {e}")
            traceback.print_exc()
            return "❌ Error al reiniciar el proceso. Por favor, intenta nuevamente.", session
    
    @staticmethod
    def handle_menu_navigation(session, message, clean_sender):
        """
        Maneja la navegación en el menú
        
        Args:
            session (dict): Sesión actual
            message (str): Mensaje del usuario
            clean_sender (str): Número del usuario limpio
            
        Returns:
            tuple: (response_text, updated_session)
        """
        try:
            # Verificar comandos de navegación
            action, nav_message = handle_navigation_command(message)
            
            if action == "show_menu":
                session['menu_state'] = 'main_menu'
                return nav_message, session
                
            elif action == "show_history":
                session['menu_state'] = 'viewing_history'
                return show_rfi_history(clean_sender), session
                
            elif action == "create_new":
                # Cambiar a modo creación de RFI
                try:
                    from app.services.storage import DatabaseManager
                    db = DatabaseManager()
                    
                    session['step'] = 1
                    user_rfi_count = db.get_user_rfi_count(clean_sender)
                    session['rfi_id'] = user_rfi_count + 1
                    session['data']['images'] = []
                    return "¡Bienvenido al asistente de RFI! Vamos a ayudarte a crear un RFI según tus necesidades.", session
                except Exception as e:
                    print(f"Error al iniciar creación de RFI: {e}")
                    traceback.print_exc()
                    return "❌ Error al iniciar la creación del RFI. Por favor, intenta nuevamente.", session
            else:
                # Manejar selección según estado del menú
                try:
                    if session.get('menu_state') == 'main_menu':
                        response, new_state = handle_menu_selection(clean_sender, message)
                        session['menu_state'] = new_state
                        
                        if new_state == "creating_rfi":
                            try:
                                from app.services.storage import DatabaseManager
                                db = DatabaseManager()                                
                                session['step'] = 1
                                user_rfi_count = db.get_user_rfi_count(clean_sender)
                                session['rfi_id'] = user_rfi_count + 1
                                session['data']['images'] = []
                            except Exception as e:
                                print(f"Error en transición a crear RFI: {e}")
                                traceback.print_exc()
                                return "❌ Error al iniciar creación de RFI.", session
                        
                        return response, session
                    
                    elif session.get('menu_state') == 'viewing_history':
                        response, selected_rfi = handle_rfi_selection(clean_sender, message)
                        
                        if selected_rfi:
                            # Mostrar información del RFI y enviar el PDF
                            try:
                                # Importar funciones necesarias
                                from app.services.whatsapp_api import send_pdf_to_whatsapp
                                
                                rfi_data = selected_rfi.get('data', {})
                                rfi_id = selected_rfi.get('rfi_id', 'N/A')
                                pdf_url = selected_rfi.get('pdf_url')
                                pdf_path = selected_rfi.get('pdf_path')
                                
                                # Preparar mensaje informativo
                                response_text = (f"📄 *RFI #{rfi_id} Seleccionado*\n\n" +
                                               f"*Asunto:* {rfi_data.get('asunto', 'N/A')}\n" +
                                               f"*Proyecto:* {rfi_data.get('proyecto', 'N/A')}\n" +
                                               f"*Empresa:* {rfi_data.get('empresa', 'N/A')}\n\n" +
                                               "📤 Enviando documento...")
                                
                                # Intentar enviar el PDF si tenemos URL
                                if pdf_url:
                                    # Crear tupla para send_pdf_to_whatsapp
                                    pdf_tuple = (pdf_path if pdf_path and pdf_path != "MEMORIA" else None, pdf_url)
                                    
                                    # Enviar PDF del historial
                                    success = send_pdf_to_whatsapp(f"whatsapp:{clean_sender}", pdf_tuple, rfi_id)
                                    
                                    if success:
                                        response_text += f"\n\n✅ *RFI #{rfi_id} Enviado*\n" + \
                                                       "Tu documento histórico ha sido enviado por WhatsApp."
                                    else:
                                        # Si falla el envío automático, ofrecer enlace
                                        response_text += "\n\n⚠️ *Envío Automático Falló*\n" + \
                                                       f"🔗 **Descarga directa:** {pdf_url}\n\n" + \
                                                       "💡 Puedes descargar el documento usando el enlace de arriba."
                                else:
                                    response_text += "\n\n❌ *PDF No Disponible*\n" + \
                                                   "No se encontró el enlace del documento para este RFI."
                                
                                # Marcar que se envió un PDF para usar handle_post_pdf_commands
                                session['pdf_sent'] = True
                                session['menu_state'] = 'main_menu'  # Resetear estado del menú
                                
                                # Guardar la sesión actualizada
                                from app.services.session_manager import SessionManager
                                SessionManager.save_session(clean_sender, session)
                                
                                response_text += "\n\n💡 *Opciones:*\n"
                                response_text += "• Escribe 'menu' para ir al menú principal\n"
                                response_text += "• Escribe 'historial' para ver más RFIs\n"
                                response_text += "• Escribe 'nuevo' para crear un RFI"
                                
                                return response_text, session
                                
                            except Exception as e:
                                print(f"Error al preparar envío de PDF histórico: {e}")
                                traceback.print_exc()
                                return "❌ Error al enviar el documento. Por favor, intenta nuevamente.", session
                        else:
                            return response, session
                            
                except Exception as e:
                    print(f"Error en manejo de menú: {e}")
                    traceback.print_exc()
                    return "❌ Error al procesar la selección. Por favor, intenta nuevamente.", session
                    
        except Exception as e:
            print(f"Error general en navegación de menú: {e}")
            traceback.print_exc()
            return "❌ Error en el menú. Escribe 'menu' para regresar al inicio.", session
