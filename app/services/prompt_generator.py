"""
Generador de prompts para cada paso del flujo RFI
"""
import traceback

# Especialidades disponibles
ESPECIALIDADES = ["Estructuras", "Arquitectura", "Sanitarias", "Eléctricas"]

class PromptGenerator:
    """Genera los prompts/mensajes para cada paso del flujo"""
    
    @staticmethod
    def get_step_prompt(session, step=None):
        """
        Obtiene el prompt correspondiente al paso actual
        
        Args:
            session (dict): Sesión actual
            step (int, optional): Paso específico (usa session['step'] si no se proporciona)
            
        Returns:
            str: Mensaje del prompt
        """
        try:
            # Asegurar que session sea un dict
            if not isinstance(session, dict):
                session = {}
            
            print(f"Obteniendo prompt para el paso: {step} (sesión: {session.get('step', 'no disponible')})")
            if step is None:
                step = session.get('step', 1)
            
            prompts = {
                1: "👤 *Información Personal*\n\nPor favor, ingresa tu nombre completo:",
                
                1.1: PromptGenerator._get_job_title_prompt(session),
                
                1.2: "📅 *Fecha Límite de Respuesta*\n\n¿Para cuándo necesitas la respuesta del RFI?\n\n📝 Formato: DD/MM/AA o DD/MM/AAAA\n⬅️ Escribe 'volver' para regresar",
                
                1.3: "📄 *Documentos de Referencia*\n\n¿Cuántos documentos de referencia deseas incluir?\n\n🔢 Ingresa un número del 0 al 3\n⬅️ Escribe 'volver' para regresar",
                
                1.4: PromptGenerator._get_documents_list_prompt(session),
                
                2: "🔧 *Especialidad*\n\n¿Cuál es tu especialidad?\n\n1️⃣ Estructuras\n2️⃣ Arquitectura\n3️⃣ Sanitarias\n4️⃣ Eléctricas\n5️⃣ Otra (especificar)\n\n⬅️ Escribe 'volver' para regresar",
                
                2.1: "✏️ *Especialidad Personalizada*\n\nPor favor, especifica tu especialidad:\n\n⬅️ Escribe 'volver' para regresar",
                
                3: "🔄 *Incompatibilidades*\n\n¿Presenta incompatibilidad con otra especialidad?\n\n1️⃣ Sí\n2️⃣ No\n\n⬅️ Escribe 'volver' para regresar",
                
                4: PromptGenerator._get_incompatibility_specialty_prompt(),
                
                4.1: "✏️ *Especialidad de Incompatibilidad*\n\nEspecifica con qué especialidad encuentra la incompatibilidad:\n\n⬅️ Escribe 'volver' para regresar",
                
                5: "🏢 *Ubicación - Nivel*\n\n¿En qué piso se encontró el problema?\n\n🔢 Ingresa un número\n\n⬅️ Escribe 'volver' para regresar",
                
                6: "📍 *Ubicación - Sector*\n\nSegún el plano, describe la ubicación específica del problema:\n\n⬅️ Escribe 'volver' para regresar",
                
                7: PromptGenerator._get_description_prompt(session),
                  8: PromptGenerator._get_description_review_prompt(session),
                
                8.1: PromptGenerator._get_edit_description_prompt(session),
                
                8.2: PromptGenerator._get_confirm_edit_prompt(session),
                
                8.5: "📷 *Imagen Opcional*\n\n¿Deseas enviar una imagen del problema?\n\n1️⃣ Sí, enviar imagen\n2️⃣ No, continuar sin imagen\n\n⬅️ Escribe 'volver' para regresar"
            }
            
            return prompts.get(step, "❌ Paso no reconocido. Escribe 'menu' para regresar al inicio.")
            
        except Exception as e:
            print(f"Error en get_step_prompt: {e}")
            traceback.print_exc()
            return "❌ Error al generar el mensaje. Por favor, intenta nuevamente."
    
    @staticmethod
    def _get_job_title_prompt(session):
        """Genera el prompt para el cargo profesional"""
        try:
            nombre = session['data'].get('nombre_usuario', '')
            return f"👔 *Cargo Profesional*\n\nGracias {nombre}. Por favor, ingresa tu cargo:\n\n⬅️ Escribe 'volver' para regresar"
        except Exception as e:
            print(f"Error en prompt step 1.1: {e}")
            return "👔 *Cargo Profesional*\n\nPor favor, ingresa tu cargo:\n\n⬅️ Escribe 'volver' para regresar"
    
    @staticmethod
    def _get_documents_list_prompt(session):
        """Genera el prompt para la lista de documentos"""
        try:
            num_docs = session['data'].get('num_documentos_referencia', 0)
            return f"📋 *Lista de Documentos*\n\nPor favor, ingresa los {num_docs} documentos separados por coma.\n\n💡 Ejemplo: 'Plano E-01, Memo 132, Especificación técnica'\n⬅️ Escribe 'volver' para regresar"
        except Exception as e:
            print(f"Error en prompt step 1.4: {e}")
            return "📋 *Lista de Documentos*\n\nPor favor, ingresa los documentos separados por coma.\n\n⬅️ Escribe 'volver' para regresar"
    
    @staticmethod
    def _get_incompatibility_specialty_prompt():
        """Genera el prompt para seleccionar especialidad de incompatibilidad"""
        try:
            options = []
            for i, esp in enumerate(ESPECIALIDADES, 1):
                options.append(f"{i}️⃣ {esp}")
            options.append("5️⃣ Otra (especificar)")
            options.append("\n⬅️ Escribe 'volver' para regresar")
            
            return f"⚠️ *Incompatibilidad Detectada*\n\n¿Con qué especialidad encuentra la incompatibilidad?\n\n{chr(10).join(options)}"
        except Exception as e:
            print(f"Error en prompt step 4: {e}")
            return "⚠️ *Incompatibilidad Detectada*\n\nSelecciona la especialidad con la que hay incompatibilidad.\n\n⬅️ Escribe 'volver' para regresar"
    
    @staticmethod
    def _get_description_prompt(session):
        """Genera el prompt para la descripción del problema"""
        try:
            especialidad_principal = session['data'].get('especialidad', '')
            incompatibilidad = session['data'].get('incompatibilidad', False)
            especialidad_conflicto = session['data'].get('incompatibilidad_con', '')
            
            contexto_especialidades = ""
            if incompatibilidad and especialidad_conflicto:
                contexto_especialidades = f"\n\n🔧 *Contexto:* Problema de {especialidad_principal} con incompatibilidad en {especialidad_conflicto}"
            elif especialidad_principal:
                contexto_especialidades = f"\n\n🔧 *Contexto:* Problema de especialidad {especialidad_principal}"
            
            return f"📝 *Descripción del Problema*{contexto_especialidades}\n\nDescribe el problema con el mayor detalle posible:\n\n✅ Mínimo 10 caracteres\n⬅️ Escribe 'volver' para regresar"
        except Exception as e:
            print(f"Error en prompt step 7: {e}")
            return "📝 *Descripción del Problema*\n\nDescribe el problema con el mayor detalle posible:\n\n✅ Mínimo 10 caracteres\n⬅️ Escribe 'volver' para regresar"
    
    @staticmethod
    def _get_description_review_prompt(session):
        """Genera el prompt para revisar la descripción mejorada"""
        try:
            desc_original = session['data'].get('descripcion_original', '')
            desc_mejorada = session['data'].get('descripcion_mejorada', '')
            asunto = session['data'].get('asunto', 'Sin asunto')
            
            if not desc_mejorada:
                desc_mejorada = desc_original
            
            return f"✅ *Descripción Mejorada*\n\n📌 *Asunto:* {asunto}\n\n📝 *Descripción Original:*\n{desc_original}\n\n✨ *Descripción Mejorada:*\n{desc_mejorada}\n\n¿La descripción mejorada te parece correcta?\n\n1️⃣ Sí, continuar con esta descripción\n2️⃣ No, quiero editarla\n\n⬅️ Escribe 'volver' para regresar"
        except Exception as e:
            print(f"Error en prompt step 8: {e}")
            return "✅ *Descripción Mejorada*\n\n¿La descripción te parece correcta?\n\n1️⃣ Sí, continuar\n2️⃣ No, editarla\n\n⬅️ Escribe 'volver' para regresar"
    
    @staticmethod
    def _get_edit_description_prompt(session):
        """Genera el prompt para editar la descripción"""
        try:
            desc_mejorada = session['data'].get('descripcion_mejorada', session['data'].get('descripcion_original', ''))
            return f"✏️ *Editar Descripción*\n\nA continuación te mostramos la descripción actual.\n\n*COPIA, PEGA Y MODIFICA* el siguiente texto:\n\n```{desc_mejorada}```\n\nEdita el texto como desees y envíalo completo."
        except Exception as e:
            print(f"Error en prompt step 8.1: {e}")
            return "✏️ *Editar Descripción*\n\nPor favor, proporciona la nueva descripción:"
    
    @staticmethod
    def _get_confirm_edit_prompt(session):
        """Genera el prompt para confirmar la edición"""
        try:
            desc_editada = session['data'].get('descripcion_mejorada', '')
            return f"🔍 *Confirmar Edición*\n\n📝 *Tu versión editada:*\n{desc_editada}\n\n¿Estás conforme con esta descripción?\n\n1️⃣ Sí, continuar con esta descripción\n2️⃣ No, seguir editando"
        except Exception as e:
            print(f"Error en prompt step 8.2: {e}")
            return "🔍 *Confirmar Edición*\n\n¿Estás conforme con la descripción?\n\n1️⃣ Sí, continuar\n2️⃣ No, seguir editando"
