"""
Procesador de pasos del flujo RFI
"""
import traceback
from app.services.input_validator import InputValidator
from app.services.rfi_generator import improve_description, generate_subject
from app.services.s3_service import save_image_from_url

# Especialidades disponibles
ESPECIALIDADES = ["Estructuras", "Arquitectura", "Sanitarias", "Eléctricas"]

class StepProcessor:
    """Procesa cada paso del flujo de creación de RFI"""
    
    @staticmethod
    def process_step_1(session, message, msg_response):
        """Procesa el paso 1: Nombre del usuario"""
        try:
            is_valid, error_msg = InputValidator.validate_name(message)
            if is_valid:
                session['data']['nombre_usuario'] = message.strip()
                session['step'] = 1.1
                return True
            else:
                msg_response.body(error_msg)
                return False
        except Exception as e:
            print(f"Error en step 1: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar el nombre. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_1_1(session, message, msg_response):
        """Procesa el paso 1.1: Cargo del usuario"""
        try:
            is_valid, error_msg = InputValidator.validate_job_title(message)
            if is_valid:
                session['data']['cargo_usuario'] = message.strip()
                session['step'] = 1.2
                return True
            else:
                msg_response.body(error_msg)
                return False
        except Exception as e:
            print(f"Error en step 1.1: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar el cargo. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_1_2(session, message, msg_response):
        """Procesa el paso 1.2: Fecha límite de respuesta"""
        try:
            is_valid, error_msg = InputValidator.validate_date(message)
            if is_valid:
                session['data']['fecha_respuesta'] = message.strip()
                session['step'] = 1.3
                return True
            else:
                msg_response.body(error_msg)
                return False
        except Exception as e:
            print(f"Error en step 1.2: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar la fecha. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_1_3(session, message, msg_response):
        """Procesa el paso 1.3: Número de documentos de referencia"""
        try:
            is_valid, num_docs, error_msg = InputValidator.validate_document_count(message)
            if is_valid:
                session['data']['num_documentos_referencia'] = num_docs
                if num_docs == 0:
                    session['step'] = 2
                else:
                    session['step'] = 1.4
                    msg_response.body(f"Por favor, ingresa los {num_docs} documentos de referencia separados por coma. Por ejemplo: 'Plano E-01, Memo 132, Especificación técnica'\n\n⬅️ Escribe 'volver' para regresar")
                return True
            else:
                msg_response.body(error_msg)
                return False
        except Exception as e:
            print(f"Error en step 1.3: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar el número de documentos. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_1_4(session, message, msg_response):
        """Procesa el paso 1.4: Lista de documentos de referencia"""
        try:
            is_valid, docs, error_msg = InputValidator.validate_documents_list(message)
            if is_valid:
                max_docs = session['data'].get('num_documentos_referencia', 3)
                docs = docs[:max_docs]
                session['data']['documentos_referencia'] = docs
                session['step'] = 2
                return True
            else:
                msg_response.body(error_msg)
                return False
        except Exception as e:
            print(f"Error en step 1.4: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar los documentos. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_2(session, message, msg_response):
        """Procesa el paso 2: Selección de especialidad"""
        try:
            is_valid, selection, error_msg = InputValidator.validate_specialty_selection(message)
            if is_valid:
                if selection == 5:
                    session['step'] = 2.1
                    msg_response.body("✏️ *Especialidad Personalizada*\n\nPor favor, especifica tu especialidad:")
                else:
                    session['data']['especialidad'] = ESPECIALIDADES[selection - 1]
                    session['step'] = 3
                return True
            else:
                msg_response.body(error_msg)
                return False
        except Exception as e:
            print(f"Error en step 2: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar la especialidad. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_2_1(session, message, msg_response):
        """Procesa el paso 2.1: Especialidad personalizada"""
        try:
            is_valid, error_msg = InputValidator.validate_custom_specialty(message)
            if is_valid:
                session['data']['especialidad'] = message.strip()
                session['step'] = 3
                return True
            else:
                msg_response.body(error_msg)
                return False
        except Exception as e:
            print(f"Error en step 2.1: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar la especialidad personalizada. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_3(session, message, msg_response):
        """Procesa el paso 3: Incompatibilidad con otra especialidad"""
        try:
            is_valid, selection, error_msg = InputValidator.validate_yes_no_selection(message)
            if is_valid:
                session['data']['incompatibilidad'] = selection
                if selection:
                    session['step'] = 4
                else:
                    session['step'] = 5
                return True
            else:
                msg_response.body(error_msg)
                return False
        except Exception as e:
            print(f"Error en step 3: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar la incompatibilidad. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_4(session, message, msg_response):
        """Procesa el paso 4: Especialidad con incompatibilidad"""
        try:
            is_valid, selection, error_msg = InputValidator.validate_specialty_selection(message)
            if is_valid:
                if selection == 5:
                    session['step'] = 4.1
                    msg_response.body("✏️ *Especialidad de Incompatibilidad*\n\nEspecifica con qué especialidad encuentra la incompatibilidad:")
                else:
                    session['data']['incompatibilidad_con'] = ESPECIALIDADES[selection - 1]
                    session['step'] = 5
                return True
            else:
                msg_response.body(error_msg)
                return False
        except Exception as e:
            print(f"Error en step 4: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar la especialidad de incompatibilidad. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_4_1(session, message, msg_response):
        """Procesa el paso 4.1: Especialidad de incompatibilidad personalizada"""
        try:
            is_valid, error_msg = InputValidator.validate_custom_specialty(message)
            if is_valid:
                session['data']['incompatibilidad_con'] = message.strip()
                session['step'] = 5
                return True
            else:
                msg_response.body(error_msg)
                return False
        except Exception as e:
            print(f"Error en step 4.1: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar la especialidad de incompatibilidad. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_5(session, message, msg_response):
        """Procesa el paso 5: Número de piso"""
        try:
            is_valid, error_msg = InputValidator.validate_floor_number(message)
            if is_valid:
                session['data']['piso'] = message
                session['step'] = 6
                return True
            else:
                msg_response.body(error_msg)
                return False
        except Exception as e:
            print(f"Error en step 5: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar el piso. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_6(session, message, msg_response):
        """Procesa el paso 6: Sector/ubicación"""
        try:
            is_valid, error_msg = InputValidator.validate_sector(message)
            if is_valid:
                session['data']['sector'] = message
                session['step'] = 7
                return True
            else:
                msg_response.body(error_msg)
                return False
        except Exception as e:
            print(f"Error en step 6: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar el sector. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_7(session, message, msg_response):
        """Procesa el paso 7: Descripción del problema"""
        try:
            is_valid, error_msg = InputValidator.validate_description(message)
            if not is_valid:
                msg_response.body(error_msg)
                return False
            
            session['data']['descripcion_original'] = message
            
            try:
                # Mejorar descripción
                mejorada = improve_description(message)
                session['data']['descripcion_mejorada'] = mejorada
                
                # Generar asunto
                try:
                    asunto = generate_subject(mejorada)
                    session['data']['asunto'] = asunto
                except Exception as subject_error:
                    print(f"Error al generar asunto: {subject_error}")
                    traceback.print_exc()
                    session['data']['asunto'] = "SOLICITUD DE INFORMACIÓN"
                
                msg_response.body(f"🤖 *Descripción Mejorada*\n\n{mejorada}\n\n✅ ¿Está bien?\n\n1️⃣ Sí, continuar\n2️⃣ No, modificar")
                
            except Exception as e:
                print(f"Error al mejorar descripción: {e}")
                traceback.print_exc()
                session['data']['descripcion_mejorada'] = message
                session['data']['asunto'] = "SOLICITUD DE INFORMACIÓN"
                msg_response.body("Ocurrió un error. Usaremos tu descripción original.\n¿Está bien?\n1. Sí\n2. No, modificar")
                
            session['step'] = 8
            return True
            
        except Exception as e:
            print(f"Error en step 7: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar la descripción. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_8(session, message, msg_response):
        """Procesa el paso 8: Confirmación de descripción mejorada"""
        try:
            if message == "1":
                session['step'] = 8.5
                msg_response.body("📷 *Imagen Opcional*\n\n¿Deseas enviar una imagen del problema?\n\n1️⃣ Sí, enviar imagen\n2️⃣ No, continuar sin imagen\n\n⬅️ Escribe 'volver' para regresar")
                return True
            elif message == "2":
                session['step'] = 8.1
                return True
            else:
                # Mostrar información completa
                desc_original = session['data'].get('descripcion_original', '')
                desc_mejorada = session['data'].get('descripcion_mejorada', '')
                asunto = session['data'].get('asunto', 'Sin asunto')
                
                if not desc_mejorada:
                    desc_mejorada = desc_original
                
                msg_response.body(f"✅ *Descripción Mejorada*\n\n📌 *Asunto:* {asunto}\n\n📝 *Descripción Original:*\n{desc_original}\n\n✨ *Descripción Mejorada:*\n{desc_mejorada}\n\n¿La descripción mejorada te parece correcta?\n\n1️⃣ Sí, continuar con esta descripción\n2️⃣ No, quiero editarla\n\n⬅️ Escribe 'volver' para regresar")
                return False
        except Exception as e:
            print(f"Error en step 8: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar la confirmación. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_8_1(session, message, msg_response):
        """Procesa el paso 8.1: Editar descripción manualmente"""
        try:
            # El usuario ha proporcionado una descripción editada
            edited_description = message.strip()
            
            # Validar que la descripción no esté vacía
            if len(edited_description) < 10:
                msg_response.body("❌ La descripción debe tener al menos 10 caracteres.\n\nPor favor, proporciona una descripción más detallada:")
                return False
            
            # Guardar la descripción editada
            session['data']['descripcion_mejorada'] = edited_description
            session['step'] = 8.2
            
            return True
            
        except Exception as e:
            print(f"Error en step 8.1: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar la descripción editada. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_8_2(session, message, msg_response):
        """Procesa el paso 8.2: Confirmar edición de descripción"""
        try:
            if message == "1":
                # Continuar con la descripción editada
                session['step'] = 8.5
                return True
            elif message == "2":
                # Volver a editar
                session['step'] = 8.1
                return True
            else:
                # Opción inválida - mostrar el prompt de confirmación nuevamente
                desc_editada = session['data'].get('descripcion_mejorada', '')
                msg_response.body(f"🔍 *Confirmar Edición*\n\n📝 *Tu versión editada:*\n{desc_editada}\n\n¿Estás conforme con esta descripción?\n\n1️⃣ Sí, continuar con esta descripción\n2️⃣ No, seguir editando\n\n⬅️ Escribe 'volver' para regresar")
                return False
                
        except Exception as e:
            print(f"Error en step 8.2: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar la confirmación. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_8_5(session, message, msg_response):
        """Procesa el paso 8.5: Decidir si enviar imagen"""
        try:
            if message == "1":
                session['step'] = 8.6
                msg_response.body("📷 *Enviar Imagen*\n\nEnvía la imagen del problema ahora.\n\n⏭️ O escribe 'saltar' para continuar sin imagen")
                return True
            elif message == "2":
                session['step'] = 9
                session['send_pdf'] = True
                session['pdf_sent'] = False
                msg_response.body("✅ *RFI Completado*\n\nGenerando documento sin imágenes...")
                return True
            else:
                msg_response.body("Selecciona una opción válida:\n1. Sí, enviar imagen\n2. No, continuar sin imagen\n\n⬅️ Escribe 'volver' para regresar")
                return False
        except Exception as e:
            print(f"Error en step 8.5: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar la selección. Por favor, intenta nuevamente.")
            return False
    
    @staticmethod
    def process_step_8_6(session, message, msg_response, media_urls, sender):
        """Procesa el paso 8.6: Recibir imagen"""
        try:
            if media_urls and len(media_urls) > 0 and media_urls[0]:
                print(f"Procesando {len(media_urls)} imágenes recibidas")
                
                # Inicializar lista de imágenes si no existe
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
                        traceback.print_exc()
                
                # Finalizar proceso
                if s3_image_urls:
                    session['data']['images'].extend(s3_image_urls)
                    session['step'] = 9
                    session['send_pdf'] = True
                    session['pdf_sent'] = False
                    msg_response.body("✅ *RFI Completado*\n\nImagen recibida correctamente. Generando archivo RFI...")
                else:
                    session['step'] = 9
                    session['send_pdf'] = True
                    session['pdf_sent'] = False
                    msg_response.body("✅ *RFI Completado*\n\nGenerando RFI sin imágenes...")
                
                return True
                
            elif message and message.lower() == "saltar":
                session['step'] = 9
                session['send_pdf'] = True
                session['pdf_sent'] = False
                msg_response.body("✅ *RFI Completado*\n\nGenerando RFI sin imágenes...")
                return True
            else:
                print("No se detectaron imágenes en el mensaje")
                msg_response.body("No se detectó ninguna imagen. Por favor, envía una imagen o escribe 'saltar' para continuar sin imágenes.\n\n⚠️ No puedes volver atrás desde este punto")
                return False
                
        except Exception as e:
            print(f"Error en step 8.6: {e}")
            traceback.print_exc()
            msg_response.body("❌ Error al procesar la imagen. Por favor, intenta nuevamente.")
            return False    
    @staticmethod
    def _needs_auto_prompt(original_step, current_step):
        """
        Determina si un paso necesita envío automático de prompt
        
        Args:
            original_step: El paso que se estaba procesando
            current_step: El paso actual después del procesamiento
            
        Returns:
            bool: True si necesita prompt automático
        """
        # Pasos que siempre necesitan prompt automático
        always_need_prompt = [1, 1.1, 1.2, 1.4, 2.1, 3, 4.1, 5, 6, 8.1, 8.2]
        
        if original_step in always_need_prompt:
            return True
        
        # Casos especiales: pasos que condicionalmente necesitan prompt
        # Paso 1.3: necesita prompt solo si num_docs == 0 (va directo al paso 2)
        if original_step == 1.3 and current_step == 2:
            return True
        
        # Paso 2: necesita prompt solo si selection != 5 (va directo al paso 3) 
        if original_step == 2 and current_step == 3:
            return True
        
        # Paso 4: necesita prompt solo si selection != 5 (va directo al paso 5)
        if original_step == 4 and current_step == 5:
            return True
            
        # Paso 8: necesita prompt cuando va al paso 8.1 (editar descripción)
        if original_step == 8 and abs(current_step - 8.1) < 0.01:
            return True
        
        return False
