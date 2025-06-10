import re
import requests
import uuid
import traceback
import boto3
import os
import time
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from app.utils.config import get_config
from app.services.storage import DatabaseManager
from app.services.s3_service import save_image_from_url
from app.services.rfi_generator import improve_description, generate_subject
from app.services.menu_manager import (
    show_main_menu, 
    handle_menu_selection, 
    show_rfi_history, 
    handle_rfi_selection,
    handle_navigation_command
)
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
    
    twilio_limit_reached = False
    
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
        # Manejar comandos específicos después de enviar PDF
        if message and message.lower() in ['menu', 'menú']:
            # Regresar al menú principal
            session['step'] = 0
            session['menu_state'] = 'main_menu'
            session['pdf_sent'] = False  # Reset para permitir navegación
            msg.body("✅ Tu RFI anterior fue procesado exitosamente.\n\n" + show_main_menu())
            db.save_session(clean_sender, session)
            return str(resp), session
        elif message and message.lower() in ['nuevo', 'reiniciar', 'reset']:
            # Crear nuevo RFI
            try:
                # Eliminar sesión anterior
                db.delete_session(clean_sender)
                print(f"Sesión anterior eliminada para {clean_sender}")
            except Exception as e:
                print(f"Error al eliminar sesión anterior: {e}")
            
            # Crear nueva sesión para nuevo RFI
            user_rfi_count = db.get_user_rfi_count(clean_sender)
            session = {
                'step': 1,
                'data': {'images': []},
                'rfi_id': user_rfi_count + 1,
                'send_pdf': False,
                'pdf_sent': False,
                'twilio_limit_reached': False,
                'creation_time': time.time()
            }
            db.save_session(clean_sender, session)
            msg.body("Proceso reiniciado. Vamos a crear un nuevo RFI.")
            send_step_prompt(session, msg)
            return str(resp), session
        elif message and message.lower() in ['historial', '1']:
            # Mostrar historial de RFIs
            session['step'] = 0
            session['menu_state'] = 'viewing_history'
            session['pdf_sent'] = False
            msg.body(show_rfi_history(clean_sender))
            db.save_session(clean_sender, session)
            return str(resp), session
        else:
            # Para cualquier otro mensaje, mostrar opciones disponibles
            msg.body("✅ *RFI Procesado Exitosamente*\n\nTu RFI anterior fue completado.\n\n🔄 Escribe 'menu' para ver opciones\n📋 Escribe 'historial' para ver tus RFIs\n📝 Escribe 'nuevo' para crear otro RFI")
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
        user_rfi_count = db.get_user_rfi_count(clean_sender)
        new_rfi_id = user_rfi_count
        
        session = {
            'step': 1,
            'data': {
                'images': []  
            },
            'rfi_id': new_rfi_id + 1,
            'send_pdf': False,
            'pdf_sent': False,
            'twilio_limit_reached': twilio_limit_reached,
            'creation_time': time.time()
        }
        
        # Guardar la nueva sesión inmediatamente
        db.save_session(clean_sender, session)
        msg.body("Proceso reiniciado. Vamos a crear un nuevo RFI.")
        send_step_prompt(session, msg)
        return str(resp), session

    if not session:
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

        # Guardar la nueva sesión inmediatamente
        db.save_session(clean_sender, session)
        msg.body(show_main_menu())  # ← CAMBIAR: Mostrar menú en lugar de mensaje directo
        return str(resp), session

    # NUEVO: Manejar navegación si estamos en menú
    if session.get('step') == 0:  # En sistema de menú
        # Verificar comandos de navegación
        action, nav_message = handle_navigation_command(message)
        
        if action == "show_menu":
            session['menu_state'] = 'main_menu'
            msg.body(nav_message)
        elif action == "show_history":
            session['menu_state'] = 'viewing_history'
            msg.body(show_rfi_history(clean_sender))
        elif action == "create_new":
            # Cambiar a modo creación de RFI
            session['step'] = 1
            user_rfi_count = db.get_user_rfi_count(clean_sender)
            session['rfi_id'] = user_rfi_count + 1
            session['data']['images'] = []
            msg.body("¡Bienvenido al asistente de RFI! Vamos a ayudarte a crear un RFI según tus necesidades.")
            send_step_prompt(session, msg)
        else:
            # Manejar selección según estado del menú
            if session.get('menu_state') == 'main_menu':
                response, new_state = handle_menu_selection(clean_sender, message)
                session['menu_state'] = new_state
                msg.body(response)
                
                if new_state == "creating_rfi":
                    session['step'] = 1
                    user_rfi_count = db.get_user_rfi_count(clean_sender)
                    session['rfi_id'] = user_rfi_count + 1
                    session['data']['images'] = []
                    send_step_prompt(session, msg)
            
            elif session.get('menu_state') == 'viewing_history':
                response, selected_rfi = handle_rfi_selection(clean_sender, message)
                
                if selected_rfi:
                    # Mostrar información del RFI y preparar envío
                    msg.body(f"📄 *RFI #{selected_rfi.get('rfi_id')} Seleccionado*\n\n" +
                            f"*Asunto:* {selected_rfi.get('data', {}).get('asunto', 'N/A')}\n" +
                            "📤 Enviando documento...")
                    
                    # Enviar PDF del RFI seleccionado en respuesta separada
                    send_historical_pdf(clean_sender, selected_rfi, msg)
                else:
                    msg.body(response)
        
        db.save_session(clean_sender, session)
        return str(resp), session
    
    # Procesar el mensaje según el paso actual
    handle_step(session, message, msg, media_urls, clean_sender)
      
    db.save_session(clean_sender, session)
        
    # Devolver la respuesta y la sesión actualizada
    return str(resp), session


def handle_step(session, message, msg_response, media_urls=None, sender=None):
    step = session.get('step', 1)
    
    # ✅ VERIFICAR comando "volver" ANTES de procesar el paso
    if message and message.lower() in ['volver', 'atras', 'atrás', 'back']:
        # Solo permitir volver en pasos específicos (no en procesamiento final)
        if step in [1, 1.1, 1.2, 1.3, 1.4, 2, 2.1, 3, 4, 4.1, 5, 6, 7, 8]:
            if handle_back_command(session, msg_response):
                return  # Salir de la función después de manejar "volver"
        else:
            msg_response.body("❌ No puedes volver en este punto del proceso.")
            return
    
    if step == 1:
        # Validar que el nombre tenga al menos 3 caracteres
        if len(message.strip()) >= 3:
            session['data']['nombre_usuario'] = message.strip()
            session['step'] = 1.1
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("❌ *Nombre muy corto*\n\nPor favor, ingresa tu nombre completo (mínimo 3 caracteres).\n\n⬅️ Escribe 'volver' para regresar")
            return
            
    elif step == 1.1:
        # Validar que el cargo tenga al menos 3 caracteres
        if len(message.strip()) >= 3:
            session['data']['cargo_usuario'] = message.strip()
            session['step'] = 1.2
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("❌ *Cargo muy corto*\n\nPor favor, ingresa tu cargo (mínimo 3 caracteres).\n\n⬅️ Escribe 'volver' para regresar")
            return
            
    elif step == 1.2:
        # Validar formato de fecha DD/MM/AA o DD/MM/AAAA
        if re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})$', message.strip()):
            session['data']['fecha_respuesta'] = message.strip()
            session['step'] = 1.3
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("❌ *Formato incorrecto*\n\nPor favor, ingresa la fecha en formato DD/MM/AA o DD/MM/AAAA.\n\n💡 Ejemplo: 15/12/24\n⬅️ Escribe 'volver' para regresar")
            return
    
    elif step == 1.3:
        try:
            num_docs = int(message.strip())
            if 0 <= num_docs <= 3:
                session['data']['num_documentos_referencia'] = num_docs
                if num_docs == 0:
                    session['step'] = 2
                    send_step_prompt(session, msg_response)
                else:
                    session['step'] = 1.4
                    msg_response.body(f"Por favor, ingresa los {num_docs} documentos de referencia separados por coma. Por ejemplo: 'Plano E-01, Memo 132, Especificación técnica'\n\n⬅️ Escribe 'volver' para regresar")
                return
            else:
                msg_response.body("❌ *Número inválido*\n\nPor favor, ingresa un número entre 0 y 3.\n\n⬅️ Escribe 'volver' para regresar")
                return
        except ValueError:
            msg_response.body("❌ *Número inválido*\n\nPor favor, ingresa un número válido entre 0 y 3.\n\n⬅️ Escribe 'volver' para regresar")
            return
    
    elif step == 1.4:
        if len(message.strip()) > 0:
            docs = [doc.strip() for doc in message.split(',') if doc.strip()]
            max_docs = session['data'].get('num_documentos_referencia', 3)
            docs = docs[:max_docs]
            session['data']['documentos_referencia'] = docs
            session['step'] = 2
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("Por favor, ingresa al menos un documento de referencia.\n\n⬅️ Escribe 'volver' para regresar")
            return
            
    elif step == 2:
        if message in map(str, range(1, 5)):
            session['data']['especialidad'] = ESPECIALIDADES[int(message) - 1]
            session['step'] = 3
            send_step_prompt(session, msg_response)
            return
        elif message == "5":
            session['step'] = 2.1  
            msg_response.body("✏️ *Especialidad Personalizada*\n\nPor favor, especifica tu especialidad:")
            return
        else:
            msg_response.body("❌ *Opción inválida*\n\nSelecciona una opción válida (1-5)\n\n⬅️ Escribe 'volver' para regresar")
            return

    # ✅ NUEVO PASO 2.1: Capturar especialidad personalizada
    elif step == 2.1:
        if len(message.strip()) >= 3:  # Validar mínimo 3 caracteres
            session['data']['especialidad'] = message.strip()
            session['step'] = 3
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("❌ *Especialidad muy corta*\n\nPor favor, ingresa una especialidad válida (mínimo 3 caracteres):\n\n⬅️ Escribe 'volver' para regresar")
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
            msg_response.body("❌ *Opción inválida*\n\nSelecciona una opción válida:\n\n1️⃣ Sí\n2️⃣ No\n\n⬅️ Escribe 'volver' para regresar")
            return

    elif step == 4:
        if message in map(str, range(1, 5)):
            seleccionada = ESPECIALIDADES[int(message)-1]
            session['data']['incompatibilidad_con'] = seleccionada
            session['step'] = 5
            send_step_prompt(session, msg_response)
            return
        elif message == "5":
            session['step'] = 4.1 
            msg_response.body("✏️ *Especialidad de Incompatibilidad*\n\nEspecifica con qué especialidad encuentra la incompatibilidad:")
            return
        else:
            msg_response.body("❌ *Opción inválida*\n\nSelecciona una opción válida (1-5)\n\n⬅️ Escribe 'volver' para regresar")
            return

    elif step == 4.1:
        if len(message.strip()) >= 3:  # Validar mínimo 3 caracteres
            session['data']['incompatibilidad_con'] = message.strip()
            session['step'] = 5
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("❌ *Especialidad muy corta*\n\nPor favor, ingresa una especialidad válida (mínimo 3 caracteres):\n\n⬅️ Escribe 'volver' para regresar")
            return


    elif step == 5:
        if re.match(r'^\d+$', message):
            session['data']['piso'] = message
            session['step'] = 6
            send_step_prompt(session, msg_response)
            return
        else:
            msg_response.body("Por favor, ingresa un número válido para el piso.\n\n⬅️ Escribe 'volver' para regresar")
            return


    elif step == 6:
        session['data']['sector'] = message
        session['step'] = 7
        send_step_prompt(session, msg_response)
        return

    elif step == 7:
        if len(message.strip()) < 10:
            msg_response.body("❌ *Descripción muy corta*\n\nDescribe el problema con más detalle (mínimo 10 caracteres).\n\n⬅️ Escribe 'volver' para regresar")
            return
        session['data']['descripcion_original'] = message
        try:
            mejorada = improve_description(message)
            session['data']['descripcion_mejorada'] = mejorada
            
            # NUEVO: Generar automáticamente el asunto basado en la descripción
            try:
                asunto = generate_subject(mejorada)
                session['data']['asunto'] = asunto
            except Exception as subject_error:
                print(f"Error al generar asunto: {subject_error}")
                session['data']['asunto'] = "SOLICITUD DE INFORMACIÓN"
            
            msg_response.body(f"🤖 *Descripción Mejorada*\n\n{mejorada}\n\n✅ ¿Está bien?\n\n1️⃣ Sí, continuar\n2️⃣ No, modificar")
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
            msg_response.body("📸 *Imágenes Opcionales*\n\n¿Deseas adjuntar una imagen del problema?\n\n1️⃣ Sí, adjuntar imagen\n2️⃣ No, continuar sin imagen")
        elif message == "2":
            # CORREGIR: Marcar como completado cuando elige "No modificar"
            session['step'] = 9
            session['send_pdf'] = True
            session['pdf_sent'] = False
            msg_response.body("✅ *RFI Completado*\n\nGenerando documento sin modificaciones...")
        else:
            msg_response.body("Selecciona una opción válida:\n1. Sí\n2. No, modificar\n\n⬅️ Escribe 'volver' para regresar")
        return

    elif step == 8.5:
        if message == "1":
            session['step'] = 8.6
            msg_response.body("📷 *Enviar Imagen*\n\nEnvía la imagen del problema ahora.\n\n⏭️ O escribe 'saltar' para continuar sin imagen")
        elif message == "2":
            # CORREGIR: Marcar como completado cuando elige "No"
            session['step'] = 9
            session['send_pdf'] = True
            session['pdf_sent'] = False
            msg_response.body("✅ *RFI Completado*\n\nGenerando documento sin imágenes...")
        else:
            msg_response.body("Selecciona una opción válida:\n1. Sí\n2. No\n\n⬅️ Escribe 'volver' para regresar")
        return

    # AGREGAR después del step 8.5:
    elif step == 8.6:
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
                    s3_url = save_image_from_url(media_url, sender)   
                    if s3_url:
                        s3_image_urls.append(s3_url)
                        print(f"Imagen {i+1} guardada correctamente: {s3_url}")
                    else:
                        print(f"No se pudo guardar la imagen {i+1} de {media_url}")
                except Exception as img_error:
                    print(f"Error al guardar imagen {i+1}: {img_error}")
            
            if s3_image_urls:
                session['data']['images'].extend(s3_image_urls)
                # Marcar como completado y activar PDF
                session['step'] = 9
                session['send_pdf'] = True
                session['pdf_sent'] = False
                msg_response.body("✅ *RFI Completado*\n\nImagen recibida correctamente. Generando archivo RFI...")
            else:
                # Marcar como completado incluso sin imágenes exitosas
                session['step'] = 9
                session['send_pdf'] = True
                session['pdf_sent'] = False
                msg_response.body("✅ *RFI Completado*\n\nGenerando RFI sin imágenes...")
            
            return
            
        elif message and message.lower() == "saltar":
            # Marcar como completado al saltar imágenes
            session['step'] = 9
            session['send_pdf'] = True
            session['pdf_sent'] = False
            msg_response.body("✅ *RFI Completado*\n\nGenerando RFI sin imágenes...")
            return
        else:
            print("No se detectaron imágenes en el mensaje")
            msg_response.body("No se detectó ninguna imagen. Por favor, envía una imagen o escribe 'saltar' para continuar sin imágenes.\n\n⚠️ No puedes volver atrás desde este punto")
            return

    if session['step'] != 9 and not session.get('send_pdf', False):
        if not getattr(msg_response, 'body', None):  # Verificar si ya tiene un cuerpo de mensaje
            send_step_prompt(session, msg_response)
        return


def send_step_prompt(session, msg_response):
    """
    Envía el mensaje correspondiente al paso actual con mejor diseño
    """
    step = session.get('step', 1)
    
    # NUEVOS PASOS
    if step == 1:
        msg_response.body("👤 *Información Personal*\n\nPor favor, ingresa tu nombre completo:")
    
    elif step == 1.1:
        nombre = session['data'].get('nombre_usuario')
        msg_response.body(f"👔 *Cargo Profesional*\n\nGracias {nombre}. Por favor, ingresa tu cargo:\n\n⬅️ Escribe 'volver' para regresar")
    
    elif step == 1.2:
        msg_response.body("📅 *Fecha Límite de Respuesta*\n\n¿Para cuándo necesitas la respuesta del RFI?\n\n📝 Formato: DD/MM/AA o DD/MM/AAAA\n⬅️ Escribe 'volver' para regresar")
    
    elif step == 1.3:
        msg_response.body("📄 *Documentos de Referencia*\n\n¿Cuántos documentos de referencia deseas incluir?\n\n🔢 Ingresa un número del 0 al 3\n⬅️ Escribe 'volver' para regresar")
    
    elif step == 1.4:
        num_docs = session['data'].get('num_documentos_referencia', 0)
        msg_response.body(f"📋 *Lista de Documentos*\n\nPor favor, ingresa los {num_docs} documentos separados por coma.\n\n💡 Ejemplo: 'Plano E-01, Memo 132, Especificación técnica'\n⬅️ Escribe 'volver' para regresar")
    
    elif step == 2:
        msg_response.body("🔧 *Especialidad*\n\n¿Cuál es tu especialidad?\n\n1️⃣ Estructuras\n2️⃣ Arquitectura\n3️⃣ Sanitarias\n4️⃣ Eléctricas\n5️⃣ Otra (especificar)\n\n⬅️ Escribe 'volver' para regresar")
    
    elif step == 2.1:
        msg_response.body("✏️ *Especialidad Personalizada*\n\nPor favor, especifica tu especialidad:\n\n⬅️ Escribe 'volver' para regresar")

    elif step == 3:
        especialidad = session['data'].get('especialidad', 'tu especialidad')
        msg_response.body(f"🔄 *Incompatibilidades*\n\n¿Presenta incompatibilidad con otra especialidad?\n\n1️⃣ Sí\n2️⃣ No\n\n⬅️ Escribe 'volver' para regresar")
    
    elif step == 4:
        options = []
        for i, esp in enumerate(ESPECIALIDADES, 1):
            options.append(f"{i}️⃣ {esp}")
        options.append("5️⃣ Otra (especificar)")
        options.append("\n⬅️ Escribe 'volver' para regresar")
        
        msg_response.body(f"⚠️ *Incompatibilidad Detectada*\n\n¿Con qué especialidad encuentra la incompatibilidad?\n\n{chr(10).join(options)}")
    
    # ✅ NUEVO CASO 4.1
    elif step == 4.1:
        msg_response.body("✏️ *Especialidad de Incompatibilidad*\n\nEspecifica con qué especialidad encuentra la incompatibilidad:\n\n⬅️ Escribe 'volver' para regresar")
    
    elif step == 5:
        msg_response.body("🏢 *Ubicación - Nivel*\n\n¿En qué piso se encontró el problema?\n\n🔢 Ingresa un número\n\n⬅️ Escribe 'volver' para regresar")
    
    elif step == 6:
        msg_response.body("📍 *Ubicación - Sector*\n\nSegún el plano, describe la ubicación específica del problema:\n\n⬅️ Escribe 'volver' para regresar")
    
    elif step == 7:
        # MEJORADO: Incluir información de especialidades
        especialidad_principal = session['data'].get('especialidad', '')
        incompatibilidad = session['data'].get('incompatibilidad', False)
        especialidad_conflicto = session['data'].get('incompatibilidad_con', '')
        
        contexto_especialidades = ""
        if incompatibilidad and especialidad_conflicto:
            contexto_especialidades = f"\n\n🔧 *Contexto:* Problema de {especialidad_principal} con incompatibilidad en {especialidad_conflicto}"
        elif especialidad_principal:
            contexto_especialidades = f"\n\n🔧 *Contexto:* Problema de especialidad {especialidad_principal}"
        
        msg_response.body(f"📝 *Descripción del Problema*{contexto_especialidades}\n\nDescribe el problema con el mayor detalle posible:\n\n✅ Mínimo 10 caracteres\n⬅️ Escribe 'volver' para regresar")
    
    elif step == 8:
        msg_response.body("🤖 *Confirmar Descripción*\n\n1️⃣ Sí, continuar\n2️⃣ No, modificar\n\n⬅️ Escribe 'volver' para regresar")
    
    elif step == 8.5:
        msg_response.body("📸 *Imágenes Opcionales*\n\n¿Deseas adjuntar una imagen del problema?\n\n1️⃣ Sí, adjuntar imagen\n2️⃣ No, continuar sin imagen\n\n⚠️ Después de este paso no podrás volver atrás")
    
    # PASOS SIN OPCIÓN DE VOLVER (8.6 y 9)
    elif step == 8.6:
        msg_response.body("📷 *Enviar Imagen*\n\nEnvía la imagen del problema ahora.\n\n⏭️ O escribe 'saltar' para continuar sin imagen\n\n⚠️ No puedes volver atrás desde este punto")
    
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
    
    # AGREGAR: Verificar si ya se envió este RFI específico
    session = db.get_session(clean_num)
    if session and session.get('pdf_sent') and str(session.get('rfi_id')) == str(rfi_id):
        print(f"PDF para RFI #{rfi_id} ya fue enviado anteriormente. Saltando envío.")
        return True
    
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
                    session['send_pdf'] = False
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
                                # AGREGAR: Marcar como enviado y cambiar al estado de menú
                                session['pdf_sent'] = True
                                session['step'] = 0  # Cambiar a estado de menú
                                session['menu_state'] = 'main_menu'  # Preparar para menú
                                session['data']['images'] = []
                                rfi_data_to_save = {
                                    'data': session.get('data', {}),
                                    'rfi_id': session.get('rfi_id'),
                                    'pdf_path': pdf_path if local_file_exists else None,
                                    'pdf_url': valid_url,
                                    'creation_time': session.get('creation_time', time.time())
                                }
                                
                                # Guardar el RFI en la base de datos
                                try:
                                    db.save_rfi(rfi_data_to_save, clean_num)
                                    print(f"RFI #{session.get('rfi_id')} guardado exitosamente para {clean_num}")
                                except Exception as save_error:
                                    print(f"Error al guardar RFI: {save_error}")
                                
                                # Guardar sesión actualizada
                                db.save_session(clean_num, session)
                            
                            # Enviar mensaje final
                            try:
                                client.messages.create(
                                    body="✅ *RFI Procesado Exitosamente*\n\nTu RFI ha sido generado y enviado correctamente.\n\n🔄 Escribe 'menu' para ver opciones\n📋 Escribe 'historial' para ver tus RFIs\n📝 Escribe 'nuevo' para crear otro RFI",
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
                        bucket_name = config.AWS_S3_BUCKET
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
                                session['step'] = 0  # AGREGAR: Cambiar a estado de menú
                                session['menu_state'] = 'main_menu'  # AGREGAR: Preparar para menú
                                db.save_session(clean_num, session)  
                            
                            # Enviar mensaje final
                            client.messages.create(
                                body="✅ *RFI Procesado Exitosamente*\n\nTu RFI ha sido generado y enviado correctamente.\n\n🔄 Para crear otro RFI, envía 'nuevo'\n📋 Para ver tus RFIs, envía 'menu'",
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
                                            body="✅ *RFI Procesado Exitosamente*\n\nTu RFI ha sido generado y enviado correctamente.\n\n🔄 Para crear otro RFI, envía 'nuevo'\n📋 Para ver tus RFIs, envía 'menu'",
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


def send_historical_pdf(phone_number, rfi_data, msg):
    """
    Envía un PDF histórico del RFI seleccionado
    """
    try:
        pdf_url = rfi_data.get('pdf_url')
        pdf_path = rfi_data.get('pdf_path')
        rfi_id = rfi_data.get('rfi_id')
        
        if pdf_url or pdf_path:
            success = send_historical_pdf_direct(phone_number, (pdf_path, pdf_url), rfi_id)
            if success:
                # NO duplicar mensaje aquí - ya se maneja en la función direct
                print(f"✅ PDF histórico #{rfi_id} enviado exitosamente")
            else:
                msg.body(f"❌ *Error al Enviar RFI #{rfi_id}*\n\nNo se pudo enviar el PDF. Por favor, intenta de nuevo más tarde.")
        else:
            msg.body(f"❌ *PDF No Disponible*\n\nNo se encontró el archivo PDF para RFI #{rfi_id}.")
    except Exception as e:
        print(f"Error al enviar PDF histórico: {e}")
        msg.body("❌ Error al procesar el PDF histórico.")

def send_historical_pdf_direct(phone_number, pdf_tuple, rfi_id):
    """
    Envía un PDF histórico sin verificar duplicados (para reenvíos)
    """
    config = get_config()
    clean_num = phone_number.replace('whatsapp:', '')
    
    # Desempaquetar la tupla y asegurarse que tenemos datos válidos
    if not pdf_tuple or len(pdf_tuple) != 2:
        print(f"Error: pdf_tuple inválido: {pdf_tuple}")
        return False
        
    pdf_path, pdf_url_data = pdf_tuple
    
    # Limpiar el número de teléfono para prevenir errores
    clean_phone = phone_number.replace(' ', '').replace('\u200e', '')
    if "whatsapp:" not in clean_phone:
        clean_phone = f"whatsapp:{clean_phone}"
    
    try:
        # Inicializar cliente de Twilio
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        
        # Verificar límite diario
        session = db.get_session(clean_num)
        if session and session.get('twilio_limit_reached'):
            print("Límite diario de Twilio alcanzado")
            return False
        
        # VARIABLE para controlar si se envió exitosamente
        pdf_sent_successfully = False
        
        # MÉTODO 1: Intentar con URL existente primero
        if pdf_url_data:
            valid_url = None
            
            # Manejar diferentes formatos de URL
            if isinstance(pdf_url_data, dict):
                if "direct_url" in pdf_url_data and pdf_url_data["direct_url"]:
                    valid_url = pdf_url_data["direct_url"]
                elif "presigned_url" in pdf_url_data and pdf_url_data["presigned_url"]:
                    valid_url = pdf_url_data["presigned_url"]
            elif isinstance(pdf_url_data, str) and not pdf_url_data.startswith("ERROR:"):
                valid_url = pdf_url_data
            
            if valid_url:
                try:
                    print(f"Intentando envío con URL existente: {valid_url[:50]}...")
                    # Verificar URL
                    test_response = requests.head(valid_url, timeout=10)
                    if test_response.status_code == 200:
                        # Enviar PDF directamente
                        pdf_message = client.messages.create(
                            body=f"📄 *RFI #{rfi_id} - Reenvío*\n\nAquí está tu documento solicitado:",
                            from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                            to=clean_phone,
                            media_url=[valid_url]
                        )
                        print(f"PDF histórico enviado con URL existente, ID: {pdf_message.sid}")
                        pdf_sent_successfully = True
                    else:
                        print(f"URL existente no funciona: Status {test_response.status_code}")
                except Exception as url_error:
                    print(f"Error con URL existente: {url_error}")
        
        # MÉTODO 2: Si falló la URL, intentar con archivo local
        if not pdf_sent_successfully and pdf_path and os.path.exists(pdf_path):
            print(f"Intentando reenvío con archivo local: {pdf_path}")
            
            try:
                s3_client = boto3.client('s3')
                bucket_name = config.AWS_S3_BUCKET
                key = f"rfi-bot/users/{clean_num}/pdfs/RFI_{rfi_id}_resend.pdf"
                
                # Subir archivo
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
                
                # Generar URL presignada
                new_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': bucket_name,
                        'Key': key,
                        'ResponseContentType': 'application/pdf',
                        'ResponseContentDisposition': f'attachment; filename="RFI-{rfi_id}.pdf"'
                    },
                    ExpiresIn=604800  # 7 días
                )
                
                # Enviar PDF
                pdf_message = client.messages.create(
                    body=f"📄 *RFI #{rfi_id} - Reenvío*\n\nAquí está tu documento solicitado:",
                    from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                    to=clean_phone,
                    media_url=[new_url]
                )
                print(f"PDF histórico reenviado con nueva URL, ID: {pdf_message.sid}")
                pdf_sent_successfully = True
                
            except Exception as s3_error:
                print(f"Error al subir a S3 para reenvío: {s3_error}")
        
        # ENVIAR MENSAJE DE CONFIRMACIÓN para TODOS los casos exitosos
        if pdf_sent_successfully:
            try:
                confirmation_message = client.messages.create(
                    body="✅ *Documento Enviado*\n\nTu RFI ha sido reenviado exitosamente.\n\n🔄 Escribe 'menu' para ver opciones\n📋 Escribe 'historial' para ver otros RFIs\n📝 Escribe 'nuevo' para crear otro RFI",
                    from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                    to=clean_phone
                )
                print(f"Mensaje de confirmación enviado con ID: {confirmation_message.sid}")
            except Exception as conf_error:
                print(f"Error al enviar mensaje de confirmación: {conf_error}")
            
            return True
        else:
            try:
                error_message = client.messages.create(
                    body=f"❌ *Error al Enviar RFI #{rfi_id}*\n\nNo se pudo enviar el PDF. Por favor, intenta de nuevo más tarde.",
                    from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                    to=clean_phone
                )
                print(f"Mensaje de error enviado con ID: {error_message.sid}")
            except Exception as error_msg_error:
                print(f"Error al enviar mensaje de error: {error_msg_error}")
            
            return False
        
    except Exception as e:
        print(f"Error general al enviar PDF histórico: {e}")
        # Intentar notificar al usuario del error
        try:
            client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f"❌ *Error Técnico*\n\nHubo un problema al procesar tu solicitud para RFI #{rfi_id}. Por favor, intenta de nuevo.",
                from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                to=clean_phone
            )
        except:
            pass
        return False


def handle_back_command(session, msg_response):
    """
    Maneja el comando 'volver' para regresar al paso anterior
    """
    current_step = session.get('step', 1)
    
    step_back_mapping = {
        1.1: 1,     
        1.2: 1.1,  
        1.3: 1.2, 
        1.4: 1.3,   
        2: 1.4,     
        2.1: 2,     
        3: 2,       
        4: 3,       
        4.1: 4,    
        5: 3,       
        6: 5,
        7: 6,       
        8: 7        
    }
    
    if current_step not in step_back_mapping:
        msg_response.body("❌ No puedes volver en este punto del proceso.")
        return False
    
    previous_step = step_back_mapping[current_step]
    
    if current_step == 2:
        num_docs = session['data'].get('num_documentos_referencia', 0)
        if num_docs == 0:
            previous_step = 1.3  
        else:
            previous_step = 1.4  
    
    elif current_step == 3:
        especialidad_actual = session['data'].get('especialidad', '')
        if especialidad_actual not in ESPECIALIDADES:
            previous_step = 2.1 
        else:
            previous_step = 2    
    
    elif current_step == 5:
        if session['data'].get('incompatibilidad', False):
            incomp_esp = session['data'].get('incompatibilidad_con', '')
            if incomp_esp not in ESPECIALIDADES:
                previous_step = 4.1  
            else:
                previous_step = 4    
        else:
            previous_step = 3        
    
    session['step'] = previous_step
    
    cleanup_data_for_step(session, previous_step)
    
    msg_response.body("⬅️ *Regresando al paso anterior...*")
    send_step_prompt(session, msg_response)
    
    return True

def cleanup_data_for_step(session, step):
    """
    Limpia datos que podrían quedar obsoletos al volver a un paso anterior
    """
    data = session.get('data', {})
    
    if step <= 1:
        data.pop('nombre_usuario', None)
        data.pop('cargo_usuario', None)
        data.pop('fecha_respuesta', None)
        data.pop('num_documentos_referencia', None)
        data.pop('documentos_referencia', None)
        data.pop('especialidad', None)
        data.pop('incompatibilidad', None)
        data.pop('incompatibilidad_con', None)
        data.pop('piso', None)
        data.pop('sector', None)
        data.pop('descripcion_original', None)
        data.pop('descripcion_mejorada', None)
        data.pop('asunto', None)
    elif step <= 1.1:
        data.pop('cargo_usuario', None)
        data.pop('fecha_respuesta', None)
        data.pop('num_documentos_referencia', None)
        data.pop('documentos_referencia', None)
        data.pop('especialidad', None)
        data.pop('incompatibilidad', None)
        data.pop('incompatibilidad_con', None)
        data.pop('piso', None)
        data.pop('sector', None)
        data.pop('descripcion_original', None)
        data.pop('descripcion_mejorada', None)
        data.pop('asunto', None)
    elif step <= 1.2:
        data.pop('fecha_respuesta', None)
        data.pop('num_documentos_referencia', None)
        data.pop('documentos_referencia', None)
        data.pop('especialidad', None)
        data.pop('incompatibilidad', None)
        data.pop('incompatibilidad_con', None)
        data.pop('piso', None)
        data.pop('sector', None)
        data.pop('descripcion_original', None)
        data.pop('descripcion_mejorada', None)
        data.pop('asunto', None)
    elif step <= 1.3:
        data.pop('num_documentos_referencia', None)
        data.pop('documentos_referencia', None)
        data.pop('especialidad', None)
        data.pop('incompatibilidad', None)
        data.pop('incompatibilidad_con', None)
        data.pop('piso', None)
        data.pop('sector', None)
        data.pop('descripcion_original', None)
        data.pop('descripcion_mejorada', None)
        data.pop('asunto', None)
    elif step <= 1.4:
        data.pop('documentos_referencia', None)
        data.pop('especialidad', None)
        data.pop('incompatibilidad', None)
        data.pop('incompatibilidad_con', None)
        data.pop('piso', None)
        data.pop('sector', None)
        data.pop('descripcion_original', None)
        data.pop('descripcion_mejorada', None)
        data.pop('asunto', None)
    elif step <= 2:
        data.pop('especialidad', None)
        data.pop('incompatibilidad', None)
        data.pop('incompatibilidad_con', None)
        data.pop('piso', None)
        data.pop('sector', None)
        data.pop('descripcion_original', None)
        data.pop('descripcion_mejorada', None)
        data.pop('asunto', None)
    elif step <= 3:
        data.pop('incompatibilidad', None)
        data.pop('incompatibilidad_con', None)
        data.pop('piso', None)
        data.pop('sector', None)
        data.pop('descripcion_original', None)
        data.pop('descripcion_mejorada', None)
        data.pop('asunto', None)
    elif step <= 4:
        data.pop('incompatibilidad_con', None)
        data.pop('piso', None)
        data.pop('sector', None)
        data.pop('descripcion_original', None)
        data.pop('descripcion_mejorada', None)
        data.pop('asunto', None)
    elif step <= 5:
        data.pop('piso', None)
        data.pop('sector', None)
        data.pop('descripcion_original', None)
        data.pop('descripcion_mejorada', None)
        data.pop('asunto', None)
    elif step <= 6:
        data.pop('sector', None)
        data.pop('descripcion_original', None)
        data.pop('descripcion_mejorada', None)
        data.pop('asunto', None)
    elif step <= 7:
        data.pop('descripcion_original', None)
        data.pop('descripcion_mejorada', None)
        data.pop('asunto', None)

    session['data'] = data