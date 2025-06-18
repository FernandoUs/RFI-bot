"""
Servicio de WhatsApp API para el bot RFI con modularización
"""
import traceback
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from config import Config
from app.services.session_manager import SessionManager
from app.services.command_handler import CommandHandler
from app.services.step_processor import StepProcessor
from app.services.prompt_generator import PromptGenerator
from app.services.back_navigation import BackNavigationHandler
from app.services.menu_manager import show_main_menu

def process_incoming_message(sender, message, media_urls=None):
    """
    Procesa mensajes entrantes y gestiona la conversación
    
    Args:
        sender: Número del remitente
        message: Texto del mensaje recibido
        media_urls: Lista de URLs de medios adjuntos (imágenes, etc.)
    """
    try:
        # Inicializar respuesta
        resp = MessagingResponse()
        msg = resp.message()
        
        # Limpiar sender para búsqueda y almacenamiento consistente en DB
        clean_sender = sender.replace('whatsapp:', '') if sender else ""
        
        # Registrar la actividad para depuración
        print(f"Mensaje recibido de {clean_sender}: {message if message else '[sin texto]'}")
        if media_urls:
            print(f"URLs de medios adjuntos: {media_urls}")
        
        # Obtener sesión actual
        session = SessionManager.get_user_session(clean_sender)
        
        # Verificar si ya se alcanzó el límite diario de Twilio
        if session and session.get('twilio_limit_reached'):
            msg.body("Lo sentimos, hemos alcanzado nuestro límite diario de mensajes. Por favor, intenta nuevamente mañana.")
            return str(resp), session
        
        # Manejar comandos post-PDF
        if session and session.get('pdf_sent'):
            try:
                response_text, updated_session = CommandHandler.handle_post_pdf_commands(session, message, clean_sender)
                msg.body(response_text)
                # SIEMPRE guardar la sesión actualizada (aunque sea la misma referencia)
                SessionManager.save_session(clean_sender, updated_session)
                return str(resp), updated_session
            except Exception as e:
                print(f"Error al manejar comando post-PDF: {e}")
                traceback.print_exc()
                msg.body("❌ Error al procesar el comando. Escribe 'menu' para continuar.")
                return str(resp), session
        
        # Manejar comando de reinicio explícito
        if message and message.lower() in ['reiniciar', 'reset', 'nuevo']:
            try:
                response_text, updated_session = CommandHandler.handle_reset_command(session, clean_sender)
                msg.body(response_text)
                if response_text.startswith("Proceso reiniciado"):
                    prompt = PromptGenerator.get_step_prompt(updated_session)
                    msg.body(prompt)
                return str(resp), updated_session
            except Exception as e:
                print(f"Error en reinicio: {e}")
                traceback.print_exc()
                msg.body("❌ Error al reiniciar el proceso. Por favor, intenta nuevamente.")
                return str(resp), session

        # Crear sesión inicial si no existe
        if not session:
            try:
                session = SessionManager.create_new_session(clean_sender)
                msg.body(show_main_menu())
                return str(resp), session
            except Exception as e:
                print(f"Error al crear sesión inicial: {e}")
                traceback.print_exc()
                msg.body("❌ Error al inicializar la sesión. Por favor, intenta nuevamente.")
                return str(resp), None

        # Manejar navegación en menú (step = 0)
        if session.get('step') == 0:
            try:
                # CASO ESPECIAL: Si el PDF ya fue enviado y estamos en step = 0,
                # usar el manejador post-PDF en lugar de navegación normal
                if session.get('pdf_sent'):
                    response_text, updated_session = CommandHandler.handle_post_pdf_commands(session, message, clean_sender)
                    msg.body(response_text)
                    # SIEMPRE guardar la sesión actualizada
                    SessionManager.save_session(clean_sender, updated_session)
                    return str(resp), updated_session
                else:
                    # Navegación normal de menú (sin PDF enviado)
                    response_text, updated_session = CommandHandler.handle_menu_navigation(session, message, clean_sender)
                    msg.body(response_text)
                    
                    # Si cambió a creación de RFI, enviar prompt del primer paso
                    if updated_session.get('step') == 1:
                        prompt = PromptGenerator.get_step_prompt(updated_session)
                        msg.body(prompt)
                    
                    SessionManager.save_session(clean_sender, updated_session)
                    return str(resp), updated_session
                    
            except Exception as e:
                print(f"Error en navegación de menú: {e}")
                traceback.print_exc()
                msg.body("❌ Error en el menú. Escribe 'menu' para regresar al inicio.")
                return str(resp), session
        
        # Procesar pasos del flujo RFI
        try:
            success = handle_step(session, message, msg, media_urls, clean_sender)
            if success:
                SessionManager.save_session(clean_sender, session)
        except Exception as e:
            print(f"Error al procesar paso {session.get('step', 'desconocido')}: {e}")
            traceback.print_exc()
            msg.body("❌ Error al procesar tu mensaje. Por favor, intenta nuevamente o escribe 'menu' para regresar al inicio.")
            
        # Devolver la respuesta y la sesión actualizada
        return str(resp), session
        
    except Exception as e:
        print(f"Error crítico en process_incoming_message: {e}")
        traceback.print_exc()
        
        # Respuesta de emergencia
        try:
            resp = MessagingResponse()
            msg = resp.message()
            msg.body("❌ Error inesperado del sistema. Por favor, contacta al administrador o intenta nuevamente más tarde.")
            return str(resp), None
        except Exception as critical_error:
            print(f"Error crítico al generar respuesta de emergencia: {critical_error}")
            traceback.print_exc()
            return "", None


def handle_step(session, message, msg_response, media_urls=None, sender=None):
    """Maneja el procesamiento de cada paso con manejo de errores"""
    try:
        step = session.get('step', 1)
        
        # Verificar comando "volver" ANTES de procesar el paso
        if BackNavigationHandler.is_back_command(message):
            try:
                # Solo permitir volver en pasos específicos (no en procesamiento final)
                if BackNavigationHandler.can_go_back(step):
                    if BackNavigationHandler.handle_back_command(session, msg_response):
                        return True  # Salir de la función después de manejar "volver"
                else:
                    msg_response.body("❌ No puedes volver en este punto del proceso.")
                    return False
            except Exception as e:
                print(f"Error al manejar comando 'volver': {e}")
                traceback.print_exc()
                msg_response.body("❌ Error al procesar comando. Por favor, intenta nuevamente.")
                return False
        
        # Mapeo de procesadores por paso
        step_processors = {
            1: StepProcessor.process_step_1,
            1.1: StepProcessor.process_step_1_1,
            1.2: StepProcessor.process_step_1_2,
            1.3: StepProcessor.process_step_1_3,
            1.4: StepProcessor.process_step_1_4,
            2: StepProcessor.process_step_2,
            2.1: StepProcessor.process_step_2_1,
            3: StepProcessor.process_step_3,
            4: StepProcessor.process_step_4,
            4.1: StepProcessor.process_step_4_1,
            5: StepProcessor.process_step_5,
            6: StepProcessor.process_step_6,
            7: StepProcessor.process_step_7,
            8: StepProcessor.process_step_8,
            8.1: StepProcessor.process_step_8_1,
            8.2: StepProcessor.process_step_8_2,
            8.5: StepProcessor.process_step_8_5,
            8.6: lambda s, m, mr: StepProcessor.process_step_8_6(s, m, mr, media_urls, sender)
        }
        
        # Obtener el procesador para el paso actual
        processor = step_processors.get(step)
        
        if processor:
            try:
                success = processor(session, message, msg_response)
                
                # Si el procesamiento fue exitoso, verificar si necesita enviar prompt del siguiente paso
                if success and session['step'] != 9 and not session.get('send_pdf', False):
                    current_step = session.get('step')
                    
                    # Determinar si necesita prompt automático
                    needs_prompt = StepProcessor._needs_auto_prompt(step, current_step)
                    
                    if needs_prompt:
                        try:
                            prompt = PromptGenerator.get_step_prompt(session)
                            msg_response.body(prompt)
                            print(f"Enviando prompt automático para step {current_step}: {prompt[:50]}...")
                        except Exception as prompt_error:
                            print(f"Error al enviar prompt: {prompt_error}")
                            traceback.print_exc()
                
                return success
            except Exception as e:
                print(f"Error al procesar paso {step}: {e}")
                traceback.print_exc()
                msg_response.body("❌ Error al procesar tu mensaje. Por favor, intenta nuevamente.")
                return False
        else:
            # Paso no reconocido
            msg_response.body("❌ Paso no reconocido. Escribe 'menu' para regresar al inicio.")
            return False
            
    except Exception as e:
        print(f"Error general en handle_step: {e}")
        traceback.print_exc()
        msg_response.body("❌ Error inesperado. Por favor, intenta nuevamente o escribe 'menu' para regresar al inicio.")
        return False


def send_step_prompt(session, msg_response):
    """
    Envía el mensaje correspondiente al paso actual usando PromptGenerator
    """
    try:
        prompt = PromptGenerator.get_step_prompt(session)
        msg_response.body(prompt)
    except Exception as e:
        print(f"Error en send_step_prompt: {e}")
        traceback.print_exc()
        msg_response.body("❌ Error al generar el mensaje. Por favor, intenta nuevamente.")


def send_historical_pdf(sender, rfi_data, msg_response):
    """Envía PDF histórico con manejo de errores"""
    try:
        # Implementación del envío de PDF histórico
        # (Agregar la lógica específica aquí)
        pass
    except Exception as e:
        print(f"Error al enviar PDF histórico: {e}")
        traceback.print_exc()
        msg_response.body("❌ Error al enviar el documento histórico.")


def clean_phone_number(phone_number):
    """
    Limpia y formatea el número de teléfono para WhatsApp
    
    Args:
        phone_number (str): Número de teléfono con formato +51973592880 o similar
        
    Returns:
        str: Número limpio en formato internacional sin +
    """
    if not phone_number:
        return None
    
    # Remover espacios y caracteres especiales excepto +
    clean_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
    
    # Si comienza con +, removerlo
    if clean_number.startswith('+'):
        clean_number = clean_number[1:]
    
    # Validar que el número tenga longitud razonable (8-15 dígitos)
    if len(clean_number) < 8 or len(clean_number) > 15:
        print(f"Número de teléfono inválido: {phone_number} -> {clean_number}")
        return None
    
    return clean_number


def send_pdf_to_whatsapp(sender, pdf_tuple, rfi_id):
    """Envía un archivo PDF a través de WhatsApp usando el cliente de Twilio"""
    try:
        # Extraer la URL del PDF de la tupla
        if not pdf_tuple or len(pdf_tuple) < 2:
            print(f"PDF tuple inválida para RFI #{rfi_id}")
            return False
            
        pdf_path = pdf_tuple[0]  # Ruta local del PDF (puede ser None si está en memoria)
        pdf_url = pdf_tuple[1]   # URL de S3 del PDF
        
        # Verificar que tengamos la URL de S3 (lo más importante)
        if not pdf_url:
            print(f"No se encontró URL de S3 para RFI #{rfi_id}")
            return False
        
        # Si pdf_path es None, significa que el PDF se generó en memoria (nueva implementación)
        # Si pdf_path existe, verificar que el archivo exista (compatibilidad con implementación anterior)
        if pdf_path and pdf_path != "MEMORIA" and not os.path.exists(pdf_path):
            print(f"El archivo PDF no existe localmente: {pdf_path}")
            # No retornar False aquí, porque tenemos la URL de S3
        
        # Limpiar y formatear el número de teléfono
        clean_sender = clean_phone_number(sender)
        if not clean_sender:
            print(f"Número de teléfono inválido: {sender}")
            return False
        
        print(f"Enviando PDF a número limpio: {clean_sender} (original: {sender})")
        
        # Configurar el cliente de Twilio
        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        
        # Formatear números para WhatsApp
        # Para Twilio Sandbox, el formato debe ser exacto
        from_number = f"whatsapp:{Config.TWILIO_PHONE_NUMBER}"
        to_number = f"whatsapp:+{clean_sender}"
        
        print(f"From: {from_number}")
        print(f"To: {to_number}")
        print(f"PDF URL: {pdf_url}")
        
        # Enviar el PDF usando la URL de S3
        message = client.messages.create(
            media_url=[pdf_url],  # Usar la URL de S3
            from_=from_number,
            to=to_number,
            body=f"✅ *RFI #{rfi_id} Completado*\n\n" +
                 "Tu solicitud de información ha sido generada exitosamente.\n\n" +
                 "*¿Qué quieres hacer ahora?*\n\n" +
                 "1️⃣ Ver historial de RFIs\n" +
                 "2️⃣ Crear un nuevo RFI\n\n" +
                 "🔹 También puedes escribir:\n" +
                 "• 'menu' para ver opciones\n" +
                 "• 'historial' para ver tus RFIs\n" +
                 "• 'nuevo' para crear otro RFI"
        )
        
        print(f"PDF del RFI #{rfi_id} enviado con éxito a {sender}: {message.sid}")
        return True
        
    except Exception as e:
        print(f"Error al enviar PDF por WhatsApp para RFI #{rfi_id}: {e}")
        traceback.print_exc()
        
        # Manejar errores específicos de Twilio
        if hasattr(e, 'code'):
            if e.code == 63038:
                print("🚨 LÍMITE DIARIO DE TWILIO ALCANZADO")
                print("La cuenta trial ha alcanzado el límite de 9 mensajes diarios.")
                print("El PDF se ha generado y subido a S3, pero no se pudo enviar por WhatsApp.")
                print(f"PDF disponible en: {pdf_url}")
                
                # Marcar sesión con límite alcanzado
                try:
                    from app.services.session_manager import SessionManager
                    session = SessionManager.get_user_session(clean_sender)
                    if session:
                        session['twilio_limit_reached'] = True
                        session['pending_pdf_url'] = pdf_url
                        session['pending_pdf_rfi_id'] = rfi_id
                        SessionManager.save_user_session(clean_sender, session)
                except Exception as session_error:
                    print(f"Error al actualizar sesión con límite de Twilio: {session_error}")
                
                return False
            elif e.code == 21211:
                print("🚨 NÚMERO NO AUTORIZADO EN SANDBOX DE WHATSAPP")
                print("El número no está verificado en el Sandbox de WhatsApp.")
                print("Instrucciones: Envía 'join <sandbox-code>' al +1 415 523 8886 desde WhatsApp")
                return False
        
        return False