import os
import re
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import uuid
from app.utils.config import get_config
from app.services.storage import DatabaseManager
from app.services.rfi_generator import generate_rfi_pdf

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
    
    if message and message.lower() in ['join', 'join light-speech']:
        msg.body("¡Bienvenido al asistente de RFI! Estás conectado al sandbox de Twilio.")
        return str(resp), {'step': 0}

    # Obtener sesión desde almacenamiento persistente
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
        msg.body("¡Bienvenido al asistente de RFI! Vamos a ayudarte un RFI según tus necesdidades")
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
    
    if session['step'] == 7.6 and media_urls:
        # Guardar las URLs de las imágenes
        if 'images' not in session['data']:
            session['data']['images'] = []
        
        session['data']['images'].extend(media_urls)
        session['step'] = 8  # Avanzar al paso final
        
        msg.body("Imagen recibida correctamente. Generando archivo RFI...")
        db.save_session(sender, session)
        return str(resp), session
    
    
    # Si estamos esperando una imagen pero no se recibió
    if session['step'] == 7.6 and not media_urls:
        if message and message.lower() in ['saltar', 'continuar', 'skip']:
            # El usuario quiere saltar el paso de la imagen
            session['step'] = 8
            db.save_session(sender, session)
            msg.body("Generando archivo RFI sin imágenes...")
            return str(resp), session
        else:
            msg.body("No se detectó ninguna imagen. Por favor, envía una imagen o escribe 'saltar' para continuar sin imagen.")
            return str(resp), session
    
    # Procesar el mensaje según el paso actual
    handle_step(session, message, msg)
    
    # Si es necesario enviar un PDF, indicarlo en la sesión
    if session.get('step') == 8:  # Paso final
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
        elif message.startswith("5:"):
            otra = message[2:].strip()
            if otra:
                session['data']['especialidad'] = otra
                session['step'] = 2
            else:
                msg_response.body("Por favor, describe la otra especialidad.")
                return
        send_step_prompt(session, msg_response)
        return

    elif step == 2:
        if message == "1":
            session['data']['incompatibilidad'] = True
            session['step'] = 3
            send_step_prompt(session, msg_response)
        elif message == "2":
            session['data']['incompatibilidad'] = False
            session['step'] = 4
            send_step_prompt(session, msg_response)
        else:
            send_step_prompt(session, msg_response)
            return

    elif step == 3:
        actual = session['data'].get('especialidad')
        if message in map(str, range(1, 5)):
            seleccionada = ESPECIALIDADES[int(message) - 1]
            if seleccionada != actual:
                session['data']['incompatibilidad_con'] = seleccionada
                session['step'] = 4
            else:
                msg_response.body("Selecciona una especialidad distinta a la original.")
                return
        elif message.startswith("5:"):
            otra = message[2:].strip()
            if otra and otra != actual:
                session['data']['incompatibilidad_con'] = otra
                session['step'] = 4
            else:
                msg_response.body("La especialidad debe ser distinta a la seleccionada inicialmente.")
                return
        else:
            send_step_prompt(session, msg_response)
            return

    elif step == 4:
        if re.match(r'^\d+$', message):
            session['data']['piso'] = message
            session['step'] = 5
        else:
            msg_response.body("Por favor, ingresa un número válido para el piso.")
            return

    elif step == 5:
        session['data']['sector'] = message
        session['step'] = 6

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
            msg_response.body("Generando archivo RFI sin imágenes...")
        else:
            msg_response.body("Selecciona una opción válida:\n1. Sí\n2. No")
        return

    if session['step'] != 8:
        send_step_prompt(session, msg_response)


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
        especialidad_actual = session['data'].get('especialidad')
        options = []
        
        for i, esp in enumerate(ESPECIALIDADES, 1):
            if esp != especialidad_actual:
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
    
    Args:
        phone_number: Número de teléfono del destinatario
        pdf_tuple: Tupla con (pdf_path, pdf_url)
        rfi_id: ID del RFI generado
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    config = get_config()
    
    # Desempaquetar la tupla
    pdf_path, pdf_url = pdf_tuple
    
    if pdf_url.startswith("ERROR:"):
        pdf_url = None
    
    # Limpiar el número de teléfono para prevenir errores
    clean_phone = phone_number.replace(' ', '').replace('\u200e', '')
    if "whatsapp:" in clean_phone:
        clean_phone = clean_phone.replace("whatsapp:", "")
    # Inicializar cliente de Twilio
    
    try:
        # Inicializar cliente de Twilio
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        
        # Preparar mensaje
        message = client.messages.create(
            body=f"Aquí está tu RFI #{rfi_id}. Por favor revisa el documento adjunto.",
            from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
            to=f"whatsapp:{clean_phone}"
        )
        
        # Añadir URL del PDF si está disponible
        if pdf_url:
            message['media_url'] = [pdf_url]
        else:
            message['body'] += "\n\nNo se pudo generar el PDF. Por favor, intenta nuevamente más tarde."
        
        # Enviar mensaje
        message = client.messages.create(**message)
        
        print(f"Mensaje enviado con ID: {message.sid}")

        client.messages.create(
            body="Tu RFI ha sido procesado exitosamente'.",
            from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}", 
            to=f"whatsapp:{clean_phone}"
        )
        
        # Eliminar la sesión para permitir empezar de nuevo
        db.delete_session(phone_number)
        return True
    except Exception as e:
        print(f"Error al enviar PDF:\n{e}")
        return False