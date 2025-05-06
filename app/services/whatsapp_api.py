import os
import re
import requests
import uuid
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from app.utils.config import get_config
from app.services.storage import DatabaseManager
from app.services.rfi_generator import generate_rfi_pdf
from app.services.s3_service import save_image_from_url


# Especialidades disponibles
ESPECIALIDADES = ["Estructuras", "Arquitectura", "Sanitarias", "Eléctricas"]

# Inicializar almacenamiento
db = DatabaseManager()

def process_incoming_message(sender, message, media_urls=None):
    """
    Procesa mensajes entrantes y gestiona la conversación
    
    Args:
        sender: Número del remitente
        message: Texto del mensaje recibido
        media_urls: Lista de URLs de medios adjuntos (imágenes, etc.)
    """
    # Inicializar respuesta
    resp = MessagingResponse()
    msg = resp.message()
    
    session = db.get_session(sender)
    
    # Si no existe sesión, crear una nueva
    if not session:
        session = {
            'step': 1,
            'data': {
                'images': []
            },
            'rfi_id': str(uuid.uuid4())[:8], 
            'send_pdf': False
        }
        msg.body("¡Bienvenido al asistente de RFI! Vamos a ayudarte un RFI según tus necesidades.")
        send_step_prompt(session, msg)
        db.save_session(sender, session)
        return str(resp), session
    
    # Verificar si el usuario quiere reiniciar
    if message and message.lower() in ['reiniciar', 'reset', 'nuevo']:
        # Eliminar sesión anterior
        db.delete_session(sender)
        
        # Crear nueva sesión
        session = {
            'step': 1,
            'data': {
                'images': []
            },
            'rfi_id': str(uuid.uuid4())[:8],
            'send_pdf': False
        }
        db.save_session(sender, session)
        msg.body("Proceso reiniciado. Vamos a crear un nuevo RFI.")
        send_step_prompt(session, msg)
        return str(resp), session

    if message and message.lower() in ['volver', 'atrás', 'regresar']:
        if session['step'] > 1:
            # Retroceder un paso
            session['step'] -= 1
            msg.body("Volviendo al paso anterior.")
            send_step_prompt(session, msg)
            db.save_session(sender, session)
            return str(resp), session
        else:
            msg.body("Ya estás en el primer paso.")
            send_step_prompt(session, msg)
            return str(resp), session
    
    if session['step'] == 7.6:
        if media_urls and media_urls[0]:
            # Guardar las URLs de las imágenes
            if 'images' not in session['data']:
                session['data']['images'] = []
            
            s3_image_urls = []
            for i, media_url in enumerate(media_urls):
                s3_url = save_image_from_url(media_url, sender, len(session['data']['images']) + i + 1, session['rfi_id'])
                if s3_url:
                    s3_image_urls.append(s3_url)
                    print(f"Imagen {i+1} guardada correctamente en S3: {s3_url}")
                else:
                    print(f"No se pudo guardar la imagen {i+1} de {media_url}")
            
            if s3_image_urls:
                session['data']['images'].extend(s3_image_urls)
                session['step'] = 8
                session['send_pdf'] = True
                msg.body("Imagen recibida correctamente. Generando archivo RFI con la imagen...")
            else:
                msg.body("Hubo problemas al procesar la imagen. Generando RFI sin imágenes...")
                session['step'] = 8
                session['send_pdf'] = True
            
            db.save_session(sender, session)
            return str(resp), session
        elif message and message.lower() == "saltar":
            session['step'] = 8
            session['send_pdf'] = True
            msg.body("Generando RFI sin imágenes...")
            db.save_session(sender, session)
            return str(resp), session
        else:
            msg.body("No se detectó ninguna imagen. Por favor, envía una imagen o escribe 'saltar' para continuar sin imágenes.")
            db.save_session(sender, session)
            return str(resp), session
    
    # Procesar el mensaje según el paso actual
    handle_step(session, message, msg)
    
    # Si es necesario enviar un PDF, indicarlo en la sesión
    if session.get('step') == 8 and not session.get('send_pdf'):  # Paso final y aún no marcado para enviar PDF
        session['send_pdf'] = True
        session['delete_after_pdf'] = True
        msg.body("Procesando tu RFI... Recibirás el documento en breve.")
        
    db.save_session(sender, session)
        
    # Devolver la respuesta y la sesión actualizada
    return str(resp), session


def handle_step(session, message, msg_response):
    step = session.get('step', 1)

    if step == 1:
        # Elegir especialidad
        if message in map(str, range(1, 5)):
            session['data']['especialidad'] = ESPECIALIDADES[int(message) - 1]
            session['step'] = 2
            send_step_prompt(session, msg_response)
            return
        elif message.startswith("5:"):
            otra = message[2:].strip()
            if otra:
                session['data']['especialidad'] = otra
                session['step'] = 2
                send_step_prompt(session, msg_response)
                return
            else:
                msg_response.body("Por favor, describe la otra especialidad.")
                return
        else:
            msg_response.body("Selecciona una opción válida")
            return

    elif step == 2:
        if message == "1":
            session['data']['incompatibilidad'] = True
            session['step'] = 3
            send_step_prompt(session, msg_response)
            return
        elif message == "2":
            session['data']['incompatibilidad'] = False
            session['step'] = 4
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("Selecciona una opción válida:\n1. Sí\n2. No")
            return

    elif step == 3:
        if message in map(str, range(1, 5)):
            seleccionada = ESPECIALIDADES[int(message)-1]
            session['data']['incompatibilidad_con'] = seleccionada
            session['step'] = 4
            send_step_prompt(session, msg_response)
            return
        elif message.startswith("5:"):
            otra = message[2:].strip()
            session['data']['incompatibilidad_con'] = otra
            session['step'] = 4
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("Selecciona una opción válida")
            return


    elif step == 4:
        if re.match(r'^\d+$', message):
            session['data']['piso'] = message
            session['step'] = 5
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("Por favor, ingresa un número válido para el piso.")
            return


    elif step == 5:
        session['data']['sector'] = message
        session['step'] = 6
        send_step_prompt(session, msg_response)
        return

    elif step == 6:
        if len(message.strip()) < 10:
            msg_response.body("Describe el problema con más detalle (mínimo 10 caracteres).")
            return
        from app.services.rfi_generator import improve_description
        session['data']['descripcion_original'] = message
        try:
            mejorada = improve_description(message)
            session['data']['descripcion_mejorada'] = mejorada
            msg_response.body(f"Hemos mejorado tu descripción:\n\n{mejorada}\n\n¿Está bien?\n1. Sí\n2. No, modificar")
        except Exception as e:
            print(f"Error al mejorar descripción: {e}")
            session['data']['descripcion_mejorada'] = message
            msg_response.body("Ocurrió un error. Usaremos tu descripción original.\n¿Está bien?\n1. Sí\n2. No, modificar")
        session['step'] = 7
        return

    elif step == 7:
        if message == "1":
            session['step'] = 7.5
            msg_response.body("¿Deseas adjuntar una imagen del problema?\n1. Sí\n2. No, continuar sin imagen")
        elif message == "2":
            session['step'] = 6
            msg_response.body("Describe nuevamente el problema encontrado:")
        else:
            msg_response.body("Selecciona una opción válida:\n1. Sí\n2. No, modificar")
        return

    elif step == 7.5:
        if message == "1":
            session['step'] = 7.6
            msg_response.body("Envía la imagen del problema ahora.")
        elif message == "2":
            session['step'] = 8
            session['send_pdf'] = True
            msg_response.body("Generando archivo RFI sin imágenes...")
        else:
            msg_response.body("Selecciona una opción válida:\n1. Sí\n2. No")
        return

    if session['step'] != 8 and not session.get('send_pdf', False):
        if not msg_response.body: 
            send_step_prompt(session, msg_response)
        return


def send_step_prompt(session, msg_response):
    """
    Envía el mensaje correspondiente al paso actual
    
    Args:
        session: Datos de la sesión del usuario
        msg_response: Objeto de respuesta para enviar mensajes
    """
    step = session.get('step', 1)
    
    if step == 1:
        msg_response.body("¿Cuál es tu especialidad?\n1. Estructuras\n2. Arquitectura\n3. Sanitarias\n4. Eléctricas\n5: Otra (especificar)")
    
    elif step == 2:
        msg_response.body("¿Presenta incompatibilidad con otra especialidad?\n1. Sí\n2. No\n\nEscribe 'volver' para regresar a la pregunta anterior.")
    
    elif step == 3:
        options = []
        
        for i, esp in enumerate(ESPECIALIDADES, 1):
                options.append(f"{i}. {esp}")
        
        options.append("5: Otra (especificar)")
        options.append("\nEscribe 'volver' para regresar a la pregunta anterior.")
        
        msg_response.body(f"¿Con qué especialidad encuentra la incompatibilidad?\n{chr(10).join(options)}")
    
    elif step == 4:
        msg_response.body("¿En qué piso se encontró el problema? (Ingresa un número)\n\nEscribe 'volver' para regresar a la pregunta anterior.")
    
    elif step == 5:
        msg_response.body("Según el plano, ¿en qué sector se encuentra el problema?\n\nEscribe 'volver' para regresar a la pregunta anterior.")
    
    elif step == 6:
        msg_response.body("Por favor, describe el problema que has encontrado con el mayor detalle posible:\n\nEscribe 'volver' para regresar a la pregunta anterior.")
    
    return msg_response


def send_pdf_to_whatsapp(phone_number, pdf_tuple, rfi_id):
    """
    Envía un PDF por WhatsApp usando Twilio
    """
    config = get_config()
    
    # Desempaquetar la tupla
    pdf_path, pdf_url = pdf_tuple
    
    if pdf_url and pdf_url.startswith("ERROR:"):
        pdf_url = None
    
    # Limpiar el número de teléfono para prevenir errores
    clean_phone = phone_number.replace(' ', '').replace('\u200e', '')
    if "whatsapp:" not in clean_phone:
        clean_phone = f"whatsapp:{clean_phone}"
    
    try:
        # Inicializar cliente de Twilio
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        
        # Enviar mensaje introductorio
        intro_message = client.messages.create(
            body=f"Tu RFI #{rfi_id} está listo. A continuación te envío el documento.",
            from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
            to=clean_phone
        )
        print(f"Mensaje introductorio enviado con ID: {intro_message.sid}")
        
        # Enviar el PDF como documento independiente
        if pdf_url:
            # IMPORTANTE: Verificar contenido del PDF y URL
            print(f"Enviando PDF desde URL: {pdf_url}")
            
            # Verificar que el archivo sea accesible
            test_response = requests.head(pdf_url)
            print(f"Verificación de URL: Status {test_response.status_code}, Content-Type: {test_response.headers.get('Content-Type', 'desconocido')}")
            
            # Enviar como media
            pdf_message = client.messages.create(
                body="Aquí está tu documento RFI:",
                from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                to=clean_phone,
                media_url=[pdf_url]
            )
            
            print(f"Mensaje con PDF adjunto enviado con ID: {pdf_message.sid}")
        else:
            # Error - no hay URL de PDF
            error_message = client.messages.create(
                body=f"Lo sentimos, hubo un problema al generar el PDF para tu RFI #{rfi_id}. Por favor, intenta nuevamente.",
                from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                to=clean_phone
            )
            print(f"Mensaje de error enviado con ID: {error_message.sid}")
        
        # Mensaje de cierre
        client.messages.create(
            body="Tu RFI ha sido procesado exitosamente. Si necesitas alguna otra cosa, estoy aquí para ayudarte.",
            from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}", 
            to=clean_phone
        )
        
        return True
    except Exception as e:
        import traceback
        print(f"Error al enviar PDF:\n{e}\n{traceback.format_exc()}")
        return False