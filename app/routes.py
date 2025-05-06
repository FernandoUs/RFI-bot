import logging
from flask import request, Response
from app.services.whatsapp_api import process_incoming_message, send_pdf_to_whatsapp
from app.services.rfi_generator import generate_rfi_pdf
from twilio.twiml.messaging_response import MessagingResponse
import threading
import uuid

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

            # CAMBIO IMPORTANTE: Manejar la generación y envío del PDF en un hilo separado
            if session_data.get('send_pdf'):
                def process_pdf_async():
                    try:
                        rfi_data = session_data.get('data')
                        rfi_id = session_data.get('rfi_id', str(uuid.uuid4())[:8])
                        
                        logger.info(f"Iniciando generación de PDF para RFI #{rfi_id} en hilo separado")
                        pdf_tuple = generate_rfi_pdf(rfi_data, rfi_id, phone_number=sender)
                        success = send_pdf_to_whatsapp(sender, pdf_tuple, rfi_id)
                        
                        # Si send_pdf_to_whatsapp no eliminó la sesión (por algún error)
                        # y teníamos marcado para eliminar después del PDF
                        if session_data.get('delete_after_pdf', False):
                            from app.services.storage import DatabaseManager
                            db = DatabaseManager()
                            db.delete_session(sender)
                            
                        logger.info(f"Proceso de PDF para RFI #{rfi_id} completado. Éxito: {success}")
                    except Exception as e:
                        logger.exception(f"Error al procesar el RFI en hilo separado: {e}")
                        # Enviar mensaje de error
                        try:
                            from twilio.rest import Client
                            from app.utils.config import get_config
                            config = get_config()
                            client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
                            
                            client.messages.create(
                                body="Hubo un problema al generar tu RFI. Por favor intenta nuevamente.",
                                from_=f"whatsapp:{config.TWILIO_PHONE_NUMBER}",
                                to=sender
                            )
                        except Exception as e2:
                            logger.exception(f"Error al enviar mensaje de error: {e2}")
                
                # Iniciar un hilo para procesar el PDF en segundo plano
                pdf_thread = threading.Thread(target=process_pdf_async)
                pdf_thread.daemon = True  # El hilo terminará cuando el programa principal termine
                pdf_thread.start()
                
                # Añadir mensaje al usuario indicando que el proceso ha comenzado
                if isinstance(response_text, str):
                    # Si es una cadena XML, convertirla a objeto MessagingResponse
                    try:
                        from lxml import etree
                        root = etree.fromstring(response_text)
                        msg_text = root.xpath('//Message/Body/text()')
                        
                        resp = MessagingResponse()
                        msg = resp.message()
                        if msg_text and msg_text[0]:
                            msg.body(msg_text[0] + "\n\nEstamos generando tu RFI. Recibirás el PDF en breve.")
                        else:
                            msg.body("Estamos generando tu RFI. Recibirás el PDF en breve.")
                        
                        response_text = str(resp)
                    except:
                        # Si hay error al parsear, dejar como está
                        pass
                else:
                    # Es un objeto MessagingResponse
                    for msg in response_text.messages:
                        body = msg.body
                        msg.body = body + "\n\nEstamos generando tu RFI. Recibirás el PDF en breve."
            
            # Devolver respuesta inmediatamente sin esperar la generación del PDF
            if isinstance(response_text, str):
                return Response(response_text, mimetype="text/xml")
            else:
                return Response(str(response_text), mimetype="text/xml")

        except Exception as e:
            logger.exception(f"[ERROR webhook]: {e}")
            return Response("Ocurrió un error procesando tu mensaje. Intenta de nuevo.", status=500)