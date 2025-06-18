import logging
import threading
import uuid
import traceback
import time
from flask import request, Response
from app.services.whatsapp_api import process_incoming_message, send_pdf_to_whatsapp
from app.services.rfi_generator import generate_rfi_pdf
from app.services.storage import DatabaseManager


# Configuración básica de logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def configure_routes(app):
    # Ruta base para prueba
    @app.route("/", methods=["GET"])
    def home():
        return "RFI Bot is running"

    # Webhook para Twilio/WhatsApp
    @app.route("/webhook", methods=["POST"])
    def whatsapp_webhook():
        try:
            incoming_msg = request.values.get('Body', '').strip()
            sender = request.values.get('From', '').strip()

            if not sender:
                logger.warning("No se detectó remitente.")
                return Response("No se detectó remitente.", status=400)

            if not incoming_msg and int(request.values.get('NumMedia', 0)) == 0:
                logger.warning("Mensaje vacío sin imágenes.")
                return Response("Mensaje vacío o sin contenido válido.", status=400)

            # Procesar imágenes si existen
            num_media = int(request.values.get('NumMedia', 0))
            media_urls = []

            for i in range(num_media):
                media_url = request.values.get(f'MediaUrl{i}')
                media_type = request.values.get(f'MediaContentType{i}')
                if media_type and media_type.startswith('image/'):
                    media_urls.append(media_url)

            # Procesar mensaje entrante
            response_text, session_data = process_incoming_message(
                sender, incoming_msg, media_urls=media_urls
            )

            # Verificar si debemos generar un PDF y asegurarnos de iniciar el hilo
            if session_data and session_data.get('send_pdf') and not session_data.get('pdf_sent'):
                print(f"DEBUG: Detectado send_pdf=True para RFI #{session_data.get('rfi_id')}")
                
                def process_pdf_async():
                    try:
                        # Crear copia de los datos necesarios para evitar problemas de concurrencia
                        rfi_data = session_data.get('data', {}).copy()
                        rfi_id = session_data.get('rfi_id', str(uuid.uuid4())[:8])
                        
                        logger.info(f"Iniciando generación de PDF para RFI #{rfi_id} en hilo separado")
                        # Crear la estructura completa que espera generate_rfi_pdf
                        session_data_for_pdf = {
                            'data': rfi_data,
                            'rfi_id': rfi_id,
                            'phone_number': sender
                        }
                        pdf_tuple = generate_rfi_pdf(session_data_for_pdf, rfi_id, phone_number=sender)
                        db = DatabaseManager()
                        clean_sender = sender.replace('whatsapp:', '')
                        
                        # AGREGAR: Guardar el RFI en la base de datos ANTES del envío
                        try:
                            rfi_data_to_save = {
                                'data': rfi_data,
                                'rfi_id': rfi_id,
                                'pdf_path': pdf_tuple[0] if pdf_tuple and len(pdf_tuple) > 0 and pdf_tuple[0] else "MEMORIA",
                                'pdf_url': pdf_tuple[1] if pdf_tuple and len(pdf_tuple) > 1 else None,
                                'creation_time': time.time()
                            }
                            db.save_rfi(rfi_data_to_save, clean_sender)
                            logger.info(f"RFI #{rfi_id} guardado en la base de datos desde routes.py")
                        except Exception as save_error:
                            logger.error(f"Error al guardar RFI #{rfi_id}: {save_error}")

                        # Verificar que la sesión actual tenga el mismo RFI ID antes de enviar
                        current_session = db.get_session(clean_sender)
                        
                        if current_session and current_session.get('rfi_id') == rfi_id:
                            success = send_pdf_to_whatsapp(sender, pdf_tuple, rfi_id)
                            
                            if success:
                                # Actualizar la sesión para marcar que el PDF fue enviado
                                # Y TAMBIÉN desactivar send_pdf para evitar reenvíos
                                current_session['pdf_sent'] = True
                                current_session['send_pdf'] = False
                                db.save_session(clean_sender, current_session)
                                logger.info(f"Proceso de PDF para RFI #{rfi_id} completado. Éxito: {success}")
                        else:
                            # Si la sesión ha cambiado o ha sido reiniciada, no enviar el PDF
                            logger.info(f"No se envía el PDF para RFI #{rfi_id} porque la sesión ha cambiado")
                            
                    except Exception as e:
                        logger.error(f"Error en proceso asíncrono de PDF: {e}")
                        logger.error(traceback.format_exc())
            
                # AQUÍ ESTÁ EL PROBLEMA: Necesitamos iniciar el hilo
                print(f"DEBUG: Iniciando hilo para generar PDF de RFI #{session_data.get('rfi_id')}")
                thread = threading.Thread(target=process_pdf_async)
                thread.daemon = True
                thread.start()
        
            # Devolver respuesta inmediatamente sin esperar la generación del PDF
            if isinstance(response_text, str):
                return Response(response_text, mimetype="text/xml")
            else:
                return Response(str(response_text), mimetype="text/xml")

        except Exception as e:
            logger.exception(f"[ERROR webhook]: {e}")
            return Response("Ocurrió un error procesando tu mensaje. Intenta de nuevo.", status=500)