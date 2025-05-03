import logging
from flask import request, Response
from app.services.whatsapp_api import process_incoming_message, send_pdf_to_whatsapp
from app.services.rfi_generator import generate_rfi_pdf
from twilio.twiml.messaging_response import MessagingResponse

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

            if session_data.get('send_pdf'):
                rfi_data = session_data.get('data')
                rfi_id = session_data.get('rfi_id', str(uuid.uuid4())[:8])
                try:

                    pdf_tuple = generate_rfi_pdf(rfi_data, rfi_id)
                    success = send_pdf_to_whatsapp(sender, pdf_tuple, rfi_id)
                    
                    # Si send_pdf_to_whatsapp no eliminó la sesión (por algún error)
                    # y teníamos marcado para eliminar después del PDF
                    if session_data.get('delete_after_pdf', False):
                        from app.services.storage import DatabaseManager
                        db = DatabaseManager()
                        db.delete_session(sender)
                        
                except Exception as e:
                    logger.exception(f"Error al procesar el RFI: {e}")
                    try:
                        resp = MessagingResponse()
                        resp.message("Hubo un problema al generar tu RFI. Por favor intenta nuevamente.")
                        return str(resp)
                    except:
                        return Response("Hubo un problema al procesar tu solicitud.", status=500)
            if isinstance(response_text, str):
                return Response(response_text, mimetype="text/xml")
            else:
                return Response(str(response_text), mimetype="text/xml")

        except Exception as e:
            logger.exception(f"[ERROR webhook]: {e}")
            return Response("Ocurrió un error procesando tu mensaje. Intenta de nuevo.", status=500)
