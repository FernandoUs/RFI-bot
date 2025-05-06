import re
import requests
from twilio.rest import Client
from app.utils.config import get_config

def download_media_from_whatsapp(media_url):
    """
    Descarga un archivo multimedia desde WhatsApp Business API
    """
    config = get_config()
    try:
        # Obtener el token de WhatsApp/Twilio
        account_sid = config.TWILIO_ACCOUNT_SID
        auth_token = config.TWILIO_AUTH_TOKEN
        
        if not auth_token or not account_sid:
            print("ERROR: No se ha configurado el token o SID de Twilio")
            return None
        
        print(f"Descargando imagen desde: {media_url}")
        
        # PRIMERA ESTRATEGIA: Usar credenciales de configuración directamente sin parsear la URL
        # Probar primero con las credenciales configuradas tal cual
        try:
            print(f"Intentando descarga directa con credenciales de configuración")
            response = requests.get(
                media_url,
                auth=(account_sid, auth_token)
            )
            
            if response.status_code == 200:
                print(f"Descarga directa exitosa con credenciales de configuración: {len(response.content)} bytes")
                return response.content
        except Exception as direct_error:
            print(f"Error en descarga directa inicial: {direct_error}")
        
        # SEGUNDA ESTRATEGIA: Parsear URL y usar SDK
        # Verificar si la URL sigue el formato esperado y extraer IDs
        match = re.search(r'Accounts/([^/]+)/Messages/([^/]+)/Media/([^/]+)', media_url)
        
        if match:
            url_account_sid = match.group(1)
            message_sid = match.group(2)
            media_sid = match.group(3)
            
            print(f"URL analizada: Account SID={url_account_sid}, Message SID={message_sid}, Media SID={media_sid}")
            
            # IMPORTANTE: Probar con el SID original primero, luego con el de la URL
            account_sids_to_try = [account_sid]
            
            # Añadir el SID de la URL si es diferente y parece válido
            if url_account_sid.startswith('AC') and url_account_sid != account_sid:
                print(f"También probaremos con el SID de la URL: {url_account_sid}")
                account_sids_to_try.append(url_account_sid)
            
            # Probar con cada SID
            for sid_to_try in account_sids_to_try:
                try:
                    print(f"Intentando con SID: {sid_to_try}")
                    client = Client(sid_to_try, auth_token)
                    media = client.messages(message_sid).media(media_sid).fetch()
                    
                    # Construir la URL de contenido correctamente
                    content_url = f"https://api.twilio.com{media.uri}"
                    
                    # Descargar con autenticación básica
                    response = requests.get(
                        content_url,
                        auth=(sid_to_try, auth_token)
                    )
                    
                    if response.status_code == 200:
                        print(f"Imagen descargada correctamente con SID {sid_to_try}: {len(response.content)} bytes")
                        return response.content
                    else:
                        print(f"Error con SID {sid_to_try}: {response.status_code}, {response.text}")
                except Exception as e:
                    print(f"Error al usar SDK de Twilio con SID {sid_to_try}: {e}")
        
        # TERCERA ESTRATEGIA: Intentar añadir /Content a la URL
        content_url = media_url
        if not content_url.endswith('/Content'):
            content_url = f"{media_url}/Content"
        
        print(f"Intentando descarga con URL de contenido: {content_url}")
        
        # Probar con ambos SIDs para la URL de contenido
        for sid_to_try in ([account_sid] + ([url_account_sid] if match and url_account_sid.startswith('AC') and url_account_sid != account_sid else [])):
            try:
                response = requests.get(
                    content_url,
                    auth=(sid_to_try, auth_token)
                )
                
                if response.status_code == 200:
                    print(f"Descarga exitosa con URL de contenido y SID {sid_to_try}: {len(response.content)} bytes")
                    return response.content
            except Exception as content_error:
                print(f"Error con URL de contenido y SID {sid_to_try}: {content_error}")
        
        # FALLBACK: Si todo falla, crear imagen de marcador
        print("Todas las estrategias de descarga fallaron. Creando imagen de marcador.")
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (800, 600), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            
            # Intentar usar una fuente si está disponible
            try:
                # Para Windows
                font = ImageFont.truetype("arial.ttf", 24)
                font_small = ImageFont.truetype("arial.ttf", 18)
            except:
                font = None
                font_small = None
            
            if font:
                d.text((50, 50), "Imagen adjuntada por el usuario", font=font, fill=(0, 0, 0))
                d.text((50, 100), "No se pudo mostrar en el PDF", font=font, fill=(255, 0, 0))
                d.text((50, 150), "Ver imagen original en WhatsApp", font=font_small, fill=(0, 0, 255))
            else:
                d.text((50, 50), "Imagen adjuntada por el usuario", fill=(0, 0, 0))
                d.text((50, 100), "No se pudo mostrar en el PDF", fill=(255, 0, 0))
                d.text((50, 150), "Ver imagen original en WhatsApp", fill=(0, 0, 255))
            
            # Guardar en memoria
            import io
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            return img_bytes.read()
        except Exception as img_error:
            print(f"Error al crear imagen de marcador: {img_error}")
            return None
    
    except Exception as e:
        print(f"Error general al descargar multimedia: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Último intento de crear marcador incluso después de error general
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (800, 600), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            d.text((50, 50), "Imagen no disponible", fill=(0, 0, 0))
            d.text((50, 100), "Error al procesar desde WhatsApp", fill=(255, 0, 0))
            
            import io
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            
            return img_bytes.read()
        except:
            return None