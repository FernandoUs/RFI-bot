from app.services.storage import DatabaseManager
from datetime import datetime

db = DatabaseManager()

def format_date(date_string):
    """Formatea la fecha para mostrar al usuario"""
    try:
        date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date_obj.strftime('%d/%m/%Y %H:%M')
    except:
        return 'Fecha no disponible'

def show_main_menu():
    """
    Retorna el mensaje del menú principal
    
    Returns:
        str: Mensaje con opciones del menú principal
    """
    return """🏗️ *Sistema de RFIs*

Por favor, selecciona una opción:

1️⃣ Ver mis RFIs anteriores
2️⃣ Crear nuevo RFI

Envía el número de la opción que deseas."""

def handle_menu_selection(phone_number, option):
    """Maneja la selección del menú principal"""
    if option == "1":
        return show_rfi_history(phone_number), "viewing_history"
    elif option == "2":
        return "Perfecto! Vamos a crear un nuevo RFI.", "creating_rfi"
    else:
        return "❌ Opción inválida. Por favor, envía 1 o 2.", "main_menu"

def show_rfi_history(phone_number):
    """Muestra la lista de RFIs anteriores del usuario"""
    try:
        # Validar número de teléfono
        if not phone_number:
            return "❌ Error: Número de teléfono no válido."
        
        user_rfis = db.get_user_rfis(phone_number)
        
        if not user_rfis or len(user_rfis) == 0:
            return """📋 *Mis RFIs anteriores*

No tienes RFIs anteriores.

🔄 Envía 'menu' para volver al menú principal
➕ Envía 'nuevo' para crear tu primer RFI"""

        message = "📋 *Mis RFIs anteriores*\n\n"
        
        # AGREGAR: Ordenar RFIs por ID de forma consistente (más reciente primero)
        rfis_sorted = sorted(user_rfis, key=lambda x: x.get('rfi_id', 0), reverse=False)  # Orden ascendente
        # Limitar a máximo 10 RFIs para evitar mensajes muy largos
        rfis_to_show = rfis_sorted[:10]
        
        for i, rfi in enumerate(rfis_to_show, 1):
            # Mejor extracción de datos con valores por defecto
            rfi_data = rfi.get('data', {})
            asunto = rfi_data.get('asunto', 'Sin asunto')
            
            # Truncar asunto si es muy largo
            if len(asunto) > 50:
                asunto = asunto[:47] + "..."
            
            fecha = format_date(rfi.get('created_at', ''))
            
            # Agregar estado si existe
            estado = rfi_data.get('estado', 'Completado')
            
            message += f"{i}️⃣ *{asunto}*\n"
            message += f"   📅 {fecha}\n"
            message += f"   📊 {estado}\n\n"
        
        if len(user_rfis) > 10:
            message += f"... y {len(user_rfis) - 10} RFIs más\n\n"
        
        message += """Para ver un RFI, envía el número correspondiente.

🔄 Envía 'menu' para volver al menú principal"""
        
        return message
        
    except Exception as e:
        print(f"Error al mostrar historial: {e}")
        return "❌ Error al cargar el historial. Envía 'menu' para continuar."

def handle_rfi_selection(phone_number, selection):
    """
    Maneja la selección de un RFI específico del historial
    
    Args:
        phone_number: Número del usuario
        selection: Selección del usuario (número como string)
        
    Returns:
        tuple: (mensaje_respuesta, rfi_seleccionado o None)
    """
    try:
        # Validar que la selección sea un número
        if not selection.isdigit():
            return "❌ *Selección inválida*\n\nPor favor, ingresa el número del RFI que deseas ver.", None
        
        selection_num = int(selection)
        
        # Obtener lista de RFIs del usuario
        db = DatabaseManager()
        user_rfis = db.get_user_rfis(phone_number.replace('whatsapp:', ''))
        # IMPORTANTE: Usar exactamente el mismo ordenamiento
        rfis_sorted = sorted(user_rfis, key=lambda x: x.get('rfi_id', 0), reverse=False)  # Orden ascendente
        rfis_to_show = rfis_sorted[:10]  # Mismo límite que show_rfi_history
        rfis = rfis_to_show  # Para mantener compatibilidad con el resto del código
        
        if not rfis or len(rfis) == 0:
            return "❌ *No tienes RFIs*\n\nNo se encontraron RFIs en tu historial.", None
        
        # PROBLEMA AQUÍ: Verificar indexación correcta
        # La selección del usuario es 1-based, pero la lista es 0-based
        if selection_num < 1 or selection_num > len(rfis):
            return f"❌ *Número inválido*\n\nPor favor, selecciona un número entre 1 y {len(rfis)}.", None
        
        # CORREGIR: Convertir de 1-based a 0-based CORRECTAMENTE
        selected_rfi = rfis[selection_num - 1]  # ← AQUÍ puede estar el problema
        
        # AGREGAR DEBUG: Verificar que se selecciona el RFI correcto
        print(f"DEBUG: Usuario seleccionó {selection_num}, RFI seleccionado: #{selected_rfi.get('rfi_id')}")
        print(f"DEBUG: Lista de RFIs disponibles: {[rfi.get('rfi_id') for rfi in rfis]}")
        
        return f"Seleccionaste RFI #{selected_rfi.get('rfi_id')}", selected_rfi
        
    except Exception as e:
        print(f"Error al procesar selección de RFI: {e}")
        return "❌ Error al procesar tu selección. Intenta de nuevo.", None

def handle_navigation_command(command):
    """Maneja comandos de navegación especiales"""
    command = command.lower().strip()
    
    if command in ['menu', 'inicio', 'principal']:
        return "show_menu", show_main_menu()
    elif command in ['historial', 'lista', 'rfis']:
        return "show_history", None
    elif command in ['nuevo', 'crear']:
        return "create_new", "Perfecto! Vamos a crear un nuevo RFI."
    else:
        return "unknown", None

