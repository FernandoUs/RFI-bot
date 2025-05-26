import re
import requests
import uuid
import traceback
import boto3
import os
import time
from urllib.parse import urlparse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from app.utils.config import get_config
from app.services.storage import DatabaseManager
from app.services.s3_service import save_image_from_url
from app.services.rfi_generator import improve_description
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
    
    # Limpiar sender para búsqueda y almacenamiento consistente en DB
    clean_sender = sender.replace('whatsapp:', '')
    
    # Registrar la actividad para depuración
    print(f"Mensaje recibido de {clean_sender}: {message if message else '[sin texto]'}")
    if media_urls:
        print(f"URLs de medios adjuntos: {media_urls}")
    
    # Obtener sesión actual
    session = None
    try:
        session = db.get_session(clean_sender)
    except Exception as e:
        print(f"Error al recuperar sesión: {e}")
    
    # Verificar si ya se alcanzó el límite diario de Twilio
    if session and session.get('twilio_limit_reached'):
        msg.body("Lo sentimos, hemos alcanzado nuestro límite diario de mensajes. Por favor, intenta nuevamente mañana.")
        return str(resp), session
    
    # NUEVO: Verificar reinicio automático para cualquier mensaje inicial
    # Si la sesión existe y tiene un PDF enviado
    if session and session.get('pdf_sent'):
        # Si el mensaje NO es un comando específico del sistema
        if message and message.lower() not in ['reiniciar', 'reset', 'nuevo', 'volver', 'atrás', 'regresar', 'saltar']:
            # Para cualquier mensaje después de un RFI completado, solo mostrar el mensaje informativo
            msg.body("Tu RFI anterior ya fue procesado. Para crear un nuevo RFI, envía 'nuevo'.")
            return str(resp), session
    
    # Si llegamos aquí, continuar con el flujo normal
    
    # Verificar si el usuario quiere reiniciar explícitamente
    if message and message.lower() in ['reiniciar', 'reset', 'nuevo']:
        # Si hay una sesión previa, guardar algunos datos relevantes
        twilio_limit_reached = session.get('twilio_limit_reached', False) if session else False
        
        try:
            # Eliminar sesión anterior de manera segura
            if session:
                db.delete_session(clean_sender)
                print(f"Sesión anterior eliminada para {clean_sender}")
        except Exception as e:
            print(f"Error al eliminar sesión anterior: {e}")
        
        # Crear nueva sesión con ID único
        new_rfi_id = str(uuid.uuid4())[:8]
        print(f"Creando nuevo RFI con ID: {new_rfi_id}")
        
        # Crear nueva sesión
        session = {
            'step': 1,
            'data': {
                'images': []
            },
            'rfi_id': new_rfi_id,
            'send_pdf': False,
            'pdf_sent': False,
            'twilio_limit_reached': twilio_limit_reached,
            'creation_time': time.time()  # Añadir marca de tiempo
        }
        
        # Guardar la nueva sesión inmediatamente
        db.save_session(clean_sender, session)
        msg.body("Proceso reiniciado. Vamos a crear un nuevo RFI.")
        send_step_prompt(session, msg)
        return str(resp), session

    # Si no existe sesión, crear una nueva
    if not session:
        # Crear una nueva sesión
        session = {
            'step': 1,
            'data': {
                'images': []
            },
            'rfi_id': str(uuid.uuid4())[:8],
            'send_pdf': False,
            'pdf_sent': False,
            'creation_time': time.time()  # Añadir marca de tiempo
        }
        db.save_session(clean_sender, session)
        
        # Si es un primer mensaje, mostrar mensaje de bienvenida
        msg.body("¡Bienvenido al asistente de RFI! Vamos a ayudarte a crear un RFI según tus necesidades.")
        send_step_prompt(session, msg)
        db.save_session(clean_sender, session)
        return str(resp), session
    
    if message and message.lower() in ['volver', 'atrás', 'regresar']:
        if session['step'] > 1:
            # Retroceder un paso
            session['step'] -= 1
            msg.body("Volviendo al paso anterior.")
            send_step_prompt(session, msg)
            db.save_session(clean_sender, session)
            return str(resp), session
        else:
            msg.body("Ya estás en el primer paso.")
            send_step_prompt(session, msg)
            return str(resp), session
    
    # Manejar el paso de envío de imágenes (ahora con mejor detección)
    if session['step'] == 8.6:
        if media_urls and len(media_urls) > 0 and media_urls[0]:
            print(f"Procesando {len(media_urls)} imágenes recibidas")
            
            # Guardar las URLs de las imágenes
            if 'images' not in session['data']:
                session['data']['images'] = []
            
            s3_image_urls = []
            for i, media_url in enumerate(media_urls):
                if not media_url:
                    print(f"URL de imagen {i+1} está vacía, omitiendo")
                    continue
                    
                print(f"Guardando imagen {i+1} de URL: {media_url}")
                try:
                    # Guardar imagen en S3 y también localmente
                    s3_url = save_image_from_url(media_url, clean_sender, len(session['data']['images']) + i + 1, session['rfi_id'])
                    if s3_url:
                        # Asegurarse de guardar también la ruta local
                        static_path = os.path.join(
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "static", "images", f"image_{session['rfi_id']}_{len(session['data']['images']) + i + 1}.jpg"
                        )
                        if os.path.exists(static_path):
                            s3_url["local_path"] = static_path
                        
                        s3_image_urls.append(s3_url)
                        print(f"Imagen {i+1} guardada correctamente en S3: {s3_url}")
                    else:
                        print(f"No se pudo guardar la imagen {i+1} de {media_url}")
                except Exception as img_error:
                    print(f"Error al guardar imagen {i+1}: {img_error}")
            
            if s3_image_urls:
                session['data']['images'].extend(s3_image_urls)
                session['step'] = 9
                session['send_pdf'] = True
                msg.body("Imagen recibida correctamente. Generando archivo RFI con la imagen...")
            else:
                msg.body("Hubo problemas al procesar la imagen. Generando RFI sin imágenes...")
                session['step'] = 9
                session['send_pdf'] = True
            
            db.save_session(clean_sender, session)
            return str(resp), session
        elif message and message.lower() == "saltar":
            session['step'] = 8
            session['send_pdf'] = True
            msg.body("Generando RFI sin imágenes...")
            db.save_session(clean_sender, session)
            return str(resp), session
        else:
            # Verificar si hay alguna imagen adjunta pero no se detectó correctamente
            print("No se detectaron imágenes en el mensaje")
            msg.body("No se detectó ninguna imagen. Por favor, envía una imagen o escribe 'saltar' para continuar sin imágenes.")
            db.save_session(clean_sender, session)
            return str(resp), session
    
    # Procesar el mensaje según el paso actual
    handle_step(session, message, msg)
    
    # Si es necesario enviar un PDF, indicarlo en la sesión
    if session.get('step') == 9 and not session.get('send_pdf'):
        print(f"Preparando para generar PDF para RFI #{session['rfi_id']}")
        session['send_pdf'] = True
        session['delete_after_pdf'] = False  # No borrar la sesión para poder verificar el estado
        msg.body("Procesando tu RFI... Recibirás el documento en breve.")
        
    db.save_session(clean_sender, session)
        
    # Devolver la respuesta y la sesión actualizada
    return str(resp), session


def handle_step(session, message, msg_response):
    step = session.get('step', 1)

    # NUEVO PASO 1: Solicitar nombre del usuario
    if step == 1:
        # Validar que el nombre tenga al menos 3 caracteres
        if len(message.strip()) >= 3:
            session['data']['nombre_usuario'] = message.strip()
            session['step'] = 1.1
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("Por favor, ingresa tu nombre completo (mínimo 3 caracteres).")
            return
            
    # NUEVO PASO 1.1: Solicitar cargo del usuario
    elif step == 1.1:
        # Validar que el cargo tenga al menos 3 caracteres
        if len(message.strip()) >= 3:
            session['data']['cargo_usuario'] = message.strip()
            session['step'] = 1.2
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("Por favor, ingresa tu cargo (mínimo 3 caracteres).")
            return
            
    # NUEVO PASO 1.2: Solicitar fecha de respuesta requerida
    elif step == 1.2:
        # Validar formato de fecha DD/MM/AA o DD/MM/AAAA
        if re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})$', message.strip()):
            session['data']['fecha_respuesta'] = message.strip()
            session['step'] = 2
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("Por favor, ingresa la fecha en formato DD/MM/AA o DD/MM/AAAA.")
            return
            
    # PASO 2 (antiguo paso 1): Elegir especialidad
    elif step == 2:
        # Elegir especialidad
        if message in map(str, range(1, 5)):
            session['data']['especialidad'] = ESPECIALIDADES[int(message) - 1]
            session['step'] = 3
            send_step_prompt(session, msg_response)
            return
        elif message.startswith("5:"):
            otra = message[2:].strip()
            if otra:
                session['data']['especialidad'] = otra
                session['step'] = 3
                send_step_prompt(session, msg_response)
                return
            else:
                msg_response.body("Por favor, describe la otra especialidad.")
                return
        else:
            msg_response.body("Selecciona una opción válida")
            return

    elif step == 3:
        if message == "1":
            session['data']['incompatibilidad'] = True
            session['step'] = 4
            send_step_prompt(session, msg_response)
            return
        elif message == "2":
            session['data']['incompatibilidad'] = False
            session['step'] = 5
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("Selecciona una opción válida:\n1. Sí\n2. No")
            return

    elif step == 4:
        if message in map(str, range(1, 5)):
            seleccionada = ESPECIALIDADES[int(message)-1]
            session['data']['incompatibilidad_con'] = seleccionada
            session['step'] = 5
            send_step_prompt(session, msg_response)
            return
        elif message.startswith("5:"):
            otra = message[2:].strip()
            session['data']['incompatibilidad_con'] = otra
            session['step'] = 5
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("Selecciona una opción válida")
            return


    elif step == 5:
        if re.match(r'^\d+$', message):
            session['data']['piso'] = message
            session['step'] = 6
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("Por favor, ingresa un número válido para el piso.")
            return


    elif step == 6:
        session['data']['sector'] = message
        session['step'] = 7
        send_step_prompt(session, msg_response)
        return

    elif step == 7:
        if len(message.strip()) < 10:
            msg_response.body("Describe el problema con más detalle (mínimo 10 caracteres).")
            return
        session['data']['descripcion_original'] = message
        try:
            mejorada = improve_description(message)
            session['data']['descripcion_mejorada'] = mejorada
            
            # NUEVO: Generar automáticamente el asunto basado en la descripción
            try:
                from app.services.rfi_generator import generate_subject
                asunto = generate_subject(mejorada)
                session['data']['asunto'] = asunto
            except Exception as subject_error:
                print(f"Error al generar asunto: {subject_error}")
                session['data']['asunto'] = "SOLICITUD DE INFORMACIÓN"
            
            msg_response.body(f"Hemos mejorado tu descripción:\n\n{mejorada}\n\n¿Está bien?\n1. Sí\n2. No, modificar")
        except Exception as e:
            print(f"Error al mejorar descripción: {e}")
            session['data']['descripcion_mejorada'] = message
            session['data']['asunto'] = "SOLICITUD DE INFORMACIÓN"
            msg_response.body("Ocurrió un error. Usaremos tu descripción original.\n¿Está bien?\n1. Sí\n2. No, modificar")
        session['step'] = 8
        return

    elif step == 8:
        if message == "1":
            session['step'] = 8.5
            msg_response.body("¿Deseas adjuntar una imagen del problema?\n1. Sí\n2. No, continuar sin imagen")
        elif message == "2":
            session['step'] = 7
            msg_response.body("Describe nuevamente el problema encontrado:")
        else:
            msg_response.body("Selecciona una opción válida:\n1. Sí\n2. No, modificar")
        return

    elif step == 8.5:
        if message == "1":
            session['step'] = 8.6
            msg_response.body("Envía la imagen del problema ahora.")
        elif message == "2":
            session['step'] = 9
            session['send_pdf'] = True
            msg_response.body("Generando archivo RFI sin imágenes...")
        else:
            msg_response.body("Selecciona una opción válida:\n1. Sí\n2. No")
        return

    if session['step'] != 9 and not session.get('send_pdf', False):
        if not getattr(msg_response, 'body', None):  # Verificar si ya tiene un cuerpo de mensaje
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
    
    # NUEVOS PASOS
    if step == 1:
        msg_response.body("Por favor, ingresa tu nombre completo:")
    
    elif step == 1.1:
        msg_response.body(f"Gracias {session['data'].get('nombre_usuario')}. Por favor, ingresa tu cargo:")
    
    elif step == 1.2:
        msg_response.body("¿Para cuándo necesitas la respuesta del RFI? (Formato: DD/MM/AA)")
    
    # PASOS ACTUALIZADOS CON NUEVA NUMERACIÓN
    elif step == 2:
        msg_response.body("¿Cuál es tu especialidad?\n1. Estructuras\n2. Arquitectura\n3. Sanitarias\n4. Eléctricas\n5: Otra (especificar)")
    
    elif step == 3:
        msg_response.body("¿Presenta incompatibilidad con otra especialidad?\n1. Sí\n2. No\n\nEscribe 'volver' para regresar a la pregunta anterior.")
    
    elif step == 4:
        options = []
        
        for i, esp in enumerate(ESPECIALIDADES, 1):
                options.append(f"{i}. {esp}")
        
        options.append("5: Otra (especificar)")
        options.append("\nEscribe 'volver' para regresar a la pregunta anterior.")
        
        msg_response.body(f"¿Con qué especialidad encuentra la incompatibilidad?\n{chr(10).join(options)}")
    
    elif step == 5:
        msg_response.body("¿En qué piso se encontró el problema? (Ingresa un número)\n\nEscribe 'volver' para regresar a la pregunta anterior.")
    
    elif step == 6:
        msg_response.body("Según el plano, ¿en qué sector se encuentra el problema?\n\nEscribe 'volver' para regresar a la pregunta anterior.")
    
    elif step == 7:
        msg_response.body("Por favor, describe el problema que has encontrado con el mayor detalle posible:\n\nEscribe 'volver' para regresar a la pregunta anterior.")
    
    return msg_response

def send_pdf_to_whatsapp(phone_number, pdf_tuple, rfi_id):
    """
    Envía un PDF por WhatsApp usando Twilio
    
    Args:
        phone_number: Número de teléfono destinatario
        pdf_tuple: Tupla con (pdf_path, pdf_url)
        rfi_id: Identificador único del RFI
        
    Returns:
        bool: True si el envío fue exitoso, False en caso contrario
    """
    config = get_config()
    success = False
    status = 0
    clean_num = phone_number.replace('whatsapp:', '')
    
    # Desempaquetar la tupla y asegurarse que tenemos datos válidos
    if not pdf_tuple or len(pdf_tuple) != 2:
        print(f"Error: pdf_tuple inválido: {pdf_tuple}")
        return False
        
    pdf_path, pdf_url_data = pdf_tuple
    
    # Verificar que el archivo local realmente existe
    if not pdf_path or not os.path.exists(pdf_path):
        print(f"Error: Archivo local no encontrado: {pdf_path}")
        local_file_exists = False
    else:
        local_file_exists = True
        print(f"Archivo local verificado: {pdf_path}")
    
    # Validar y extraer la URL del PDF
    valid_url = None
    
    # Manejar el caso en que pdf_url_data sea un diccionario (nuevo formato)
    if isinstance(pdf_url_data, dict):
        # Usar la URL directa primero (usualmente más confiable)
        if "direct_url" in pdf_url_data and pdf_url_data["direct_url"]:
            valid_url = pdf_url_data["direct_url"]
            print(f"Usando URL directa: {valid_url}")
        elif "presigned_url" in pdf_url_data and pdf_url_data["presigned_url"]:
            valid_url = pdf_url_data["presigned_url"]
            print(f"Usando URL presigned: {valid_url}")
    elif isinstance(pdf_url_data, str) and not pdf_url_data.startswith("ERROR:"):
        valid_url = pdf_url_data
        print(f"Usando URL en formato string: {valid_url}")
    
    # Limpiar el número de teléfono para prevenir errores
    clean_phone = phone_number.replace(' ', '').replace('\u200e', '')
    if "whatsapp:" not in clean_phone:
        clean_phone = f"whatsapp:{clean_phone}"
    
    try:
        # Inicializar cliente de Twilio
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        
        # Verificar si ya hemos excedido el límite de mensajes diarios
        try:
            # Intentar enviar un mensaje de prueba primero para ver si tenemos disponibilidad
            test_status = client.messages.list(limit=1)
            print(f"Estado de mensajes Twilio: {len(test_status)} mensajes encontrados")
        except Exception as twilio_error:
            if "63038" in str(twilio_error):  # Código de error de límite diario
                print("ADVERTENCIA: Ya se ha excedido el límite diario de mensajes de Twilio")
                # Actualizar la sesión para no intentar enviar más mensajes hoy
                session = db.get_session(clean_num)
                if session:
                    session['twilio_limit_reached'] = True
                    db.save_session(clean_num, session)
                return False
        
        # Intentar con URL directa de S3 primero (si existe)
        if valid_url:
            try:
                print(f"Verificando URL del PDF: {valid_url}")
                # Verificar que el archivo sea accesible
                try:
                    test_response = requests.head(valid_url, timeout=10)
                    status = test_response.status_code
                    content_type = test_response.headers.get('Content-Type', 'desconocido')
                    print(f"Verificación de URL: Status {status}, Content-Type: {content_type}")
                    
                    # Si la URL es accesible, enviamos el PDF
                    if status == 200:
                        # Enviar mensaje introductorio primero
                        try:
                            intro_message = client.messages.create(
                                body=f"Tu RFI #{rfi_id} está listo. A continuación te envío el documento.",
                                from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                                to=clean_phone
                            )
                            print(f"Mensaje introductorio enviado con ID: {intro_message.sid}")
                        except Exception as e:
                            print(f"No se pudo enviar mensaje introductorio: {e}")
                            # Seguimos intentando enviar el PDF aunque falle el intro
                        
                        # Ahora enviar el PDF
                        pdf_message = client.messages.create(
                            body=f"Aquí está tu documento RFI #{rfi_id}:",
                            from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                            to=clean_phone,
                            media_url=[valid_url]
                        )
                        print(f"Mensaje con PDF adjunto enviado con ID: {pdf_message.sid}")
                        success = True
                        
                        # Al finalizar, cuando se marca como exitoso:
                        if success:
                            # Actualizar la sesión para marcar que el PDF fue enviado
                            session = db.get_session(clean_num)
                            if session:
                                # Marcar PDF como enviado Y desactivar send_pdf
                                session['pdf_sent'] = True
                                session['send_pdf'] = False
                                db.save_session(clean_num, session)
                            
                            # Enviar mensaje final
                            try:
                                client.messages.create(
                                    body="Tu RFI ha sido procesado exitosamente. Si necesitas crear otro RFI, envía 'nuevo'.",
                                    from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}", 
                                    to=clean_phone
                                )
                            except Exception as final_msg_error:
                                print(f"No se pudo enviar mensaje final, pero PDF enviado correctamente: {final_msg_error}")
                        
                        return True
                    else:
                        print(f"La URL del PDF devolvió un código de estado no válido: {status}")
                except Exception as url_check_error:
                    print(f"Error al verificar URL: {url_check_error}")
            except Exception as url_send_error:
                print(f"Error al enviar URL del PDF: {url_send_error}")
                
        # Si llegamos aquí, la URL de S3 falló, intentar con archivo local
        if not success and local_file_exists:
            print(f"Intentando con archivo local: {pdf_path}")
            try:
                # Usar algún servicio alternativo para subir y compartir el archivo
                # Opción 1: Generar nueva URL presignada con boto3 directamente
                if not valid_url or status != 200:
                    try:
                        s3_client = boto3.client('s3')
                        bucket_name = "anyscale-production-data-cld-2s5xxprx3uhiearmm2mqapkg85"
                        key = f"rfi-bot/users/{clean_num}/pdfs/RFI_{rfi_id}.pdf"
                        
                        # Subir el archivo desde la ruta local
                        print(f"Intentando subir archivo local a S3: {pdf_path}")
                        try:
                            with open(pdf_path, 'rb') as file_data:
                                s3_client.upload_fileobj(
                                    file_data, 
                                    bucket_name,
                                    key,
                                    ExtraArgs={
                                        'ContentType': 'application/pdf',
                                        'ContentDisposition': f'attachment; filename="RFI-{rfi_id}.pdf"'
                                    }
                                )
                            print("Archivo subido correctamente a S3")
                            
                            # Generar URL presignada para el archivo recién subido
                            new_url = s3_client.generate_presigned_url(
                                'get_object',
                                Params={
                                    'Bucket': bucket_name,
                                    'Key': key,
                                    'ResponseContentType': 'application/pdf',
                                    'ResponseContentDisposition': f'attachment; filename="RFI-{rfi_id}.pdf"'
                                },
                                ExpiresIn=604800  # 7 días en segundos
                            )
                            
                            print(f"Nueva URL presignada generada: {new_url}")
                            
                            # Enviar mensaje con la nueva URL
                            intro_message = client.messages.create(
                                body=f"Tu RFI #{rfi_id} está listo. A continuación te envío el documento.",
                                from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                                to=clean_phone
                            )
                            print(f"Mensaje introductorio enviado con ID: {intro_message.sid}")
                            
                            pdf_message = client.messages.create(
                                body=f"Aquí está tu documento RFI #{rfi_id}:",
                                from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}", 
                                to=clean_phone,
                                media_url=[new_url]
                            )
                            print(f"Mensaje con PDF adjunto enviado con ID: {pdf_message.sid}")
                            success = True
                            
                            # Actualizar la sesión para marcar que el PDF fue enviado
                            session = db.get_session(clean_num)
                            if session:
                                session['pdf_sent'] = True
                                db.save_session(clean_num, session)
                            
                            # Enviar mensaje final
                            client.messages.create(
                                body="Tu RFI ha sido procesado exitosamente. Si necesitas crear otro RFI, envía 'nuevo'.",
                                from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}", 
                                to=clean_phone
                            )
                            return True
                        except Exception as s3_upload_error:
                            print(f"Error al subir archivo a S3: {s3_upload_error}")
                    except Exception as s3_error:
                        print(f"Error al interactuar con S3: {s3_error}")
                        
                # Si todo lo anterior falló, intentar con servicios alternativos
                alternate_services = [
                    # Servicio original (con mejor manejo de errores)
                    {'name': 'transfer.sh', 'url': 'https://transfer.sh/'},
                    # Servicios alternativos
                    {'name': 'file.io', 'url': 'https://file.io/'},
                    {'name': 'tmp.ninja', 'url': 'https://tmp.ninja/'}
                ]
                
                for service in alternate_services:
                    try:
                        print(f"Intentando subir a {service['name']}...")
                        with open(pdf_path, 'rb') as file:
                            files = {'file': file}
                            response = requests.post(service['url'], files=files, timeout=30)
                            
                            if response.status_code == 200:
                                # La respuesta varía según el servicio
                                if service['name'] == 'transfer.sh':
                                    public_url = response.text.strip()
                                elif service['name'] == 'file.io':
                                    public_url = response.json().get('link')
                                elif service['name'] == 'tmp.ninja':
                                    public_url = response.json().get('url')
                                else:
                                    public_url = None
                                
                                if public_url:
                                    print(f"Archivo subido exitosamente a {service['name']}: {public_url}")
                                    
                                    # Enviar mensaje con URL pública
                                    try:
                                        intro_message = client.messages.create(
                                            body=f"Tu RFI #{rfi_id} está listo. A continuación te envío el documento.",
                                            from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                                            to=clean_phone
                                        )
                                        print(f"Mensaje introductorio enviado con ID: {intro_message.sid}")
                                    except Exception as intro_error:
                                        print(f"No se pudo enviar mensaje introductorio: {intro_error}")
                                    
                                    pdf_message = client.messages.create(
                                        body=f"Aquí está tu documento RFI #{rfi_id}:",
                                        from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                                        to=clean_phone,
                                        media_url=[public_url]
                                    )
                                    print(f"Mensaje con PDF adjunto enviado con ID: {pdf_message.sid}")
                                    success = True
                                    
                                    # Marcar PDF como enviado
                                    session = db.get_session(clean_num)
                                    if session:
                                        session['pdf_sent'] = True
                                        db.save_session(clean_num, session)
                                        
                                    # Intentar enviar mensaje final (no crítico)
                                    try:
                                        client.messages.create(
                                            body="Tu RFI ha sido procesado exitosamente. Si necesitas crear otro RFI, envía 'nuevo'.",
                                            from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}", 
                                            to=clean_phone
                                        )
                                    except:
                                        pass
                                    
                                    break  # Salir del bucle si tuvimos éxito
                    except Exception as service_error:
                        print(f"Error al usar {service['name']}: {service_error}")
            except Exception as local_file_error:
                print(f"Error al procesar archivo local: {local_file_error}")
        
        # Si llegamos aquí y no hemos tenido éxito, enviar un mensaje de error
        if not success:
            try:
                error_message = client.messages.create(
                    body=f"Lo sentimos, hubo un problema al generar el PDF para tu RFI #{rfi_id}. "
                         f"Por favor, intenta nuevamente o contacta a soporte.",
                    from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                    to=clean_phone
                )
                print(f"Mensaje de error enviado con ID: {error_message.sid}")
            except Exception as error_msg_error:
                print(f"No se pudo enviar mensaje de error: {error_msg_error}")
        
        return success
    except Exception as e:
        print(f"Error general al enviar PDF:\n{e}\n{traceback.format_exc()}")
        
        # Intentar enviar mensaje de error al usuario
        try:
            client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f"Lo sentimos, hubo un problema técnico al procesar tu RFI #{rfi_id}. "
                     f"Nuestro equipo ha sido notificado.",
                from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}", 
                to=clean_phone
            )
        except:
            pass
            
        return False


def upload_to_public_service(file_path):
    """
    Sube un archivo a un servicio público que genera URLs accesibles para Twilio
    """
    try:
        with open(file_path, 'rb') as file:
            # Intentar subir a transfer.sh
            files = {'file': file}
            response = requests.post('https://transfer.sh/', files=files, timeout=30)
            
            if response.status_code == 200:
                # transfer.sh retorna la URL como texto plano
                return response.text.strip()
                
        # Si llegamos aquí, la subida falló
        return None
    except Exception as e:
        print(f"Error al subir archivo a servicio público: {e}")
        return None