# Documentación de la Modularización del Bot RFI

## Estructura Modular

El código del bot de WhatsApp ha sido completamente refactorizado para ser más modular, mantenible y fácil de debuggear. A continuación se describe la nueva estructura:

## Módulos Creados

### 1. `session_manager.py`
**Responsabilidad**: Gestión completa de sesiones de usuario

**Funciones principales**:
- `get_user_session(clean_sender)`: Obtiene la sesión de un usuario
- `create_new_session(clean_sender, twilio_limit_reached)`: Crea una nueva sesión de menú
- `create_rfi_session(clean_sender, twilio_limit_reached)`: Crea una sesión para crear RFI
- `reset_session(clean_sender)`: Reinicia completamente la sesión de un usuario
- `save_session(clean_sender, session)`: Guarda la sesión del usuario
- `update_session_for_menu(session)`: Actualiza sesión para mostrar menú
- `update_session_for_history(session)`: Actualiza sesión para mostrar historial

**Beneficios**:
- Centraliza toda la lógica de manejo de sesiones
- Reduce duplicación de código
- Facilita el mantenimiento de estados de sesión

### 2. `command_handler.py`
**Responsabilidad**: Manejo de comandos específicos del usuario

**Funciones principales**:
- `handle_post_pdf_commands(session, message, clean_sender)`: Comandos después de enviar PDF
- `handle_reset_command(session, clean_sender)`: Comando de reinicio
- `handle_menu_navigation(session, message, clean_sender)`: Navegación en menús

**Beneficios**:
- Separa la lógica de comandos del flujo principal
- Facilita agregar nuevos comandos
- Mejora la legibilidad del código

### 3. `input_validator.py`
**Responsabilidad**: Validación de todas las entradas del usuario

**Funciones principales**:
- `validate_name(message)`: Valida nombres (mínimo 3 caracteres)
- `validate_job_title(message)`: Valida cargos profesionales
- `validate_date(message)`: Valida formato de fechas DD/MM/AA
- `validate_document_count(message)`: Valida número de documentos (0-3)
- `validate_documents_list(message)`: Valida lista de documentos
- `validate_specialty_selection(message)`: Valida selección de especialidad
- `validate_custom_specialty(message)`: Valida especialidad personalizada
- `validate_yes_no_selection(message)`: Valida selecciones Sí/No
- `validate_floor_number(message)`: Valida números de piso
- `validate_sector(message)`: Valida descripción de sector
- `validate_description(message)`: Valida descripción del problema

**Beneficios**:
- Centraliza todas las validaciones
- Estandariza mensajes de error
- Facilita mantener consistencia en validaciones

### 4. `step_processor.py`
**Responsabilidad**: Procesamiento de cada paso del flujo RFI

**Funciones principales**:
- `process_step_1()` a `process_step_8_6()`: Procesadores específicos para cada paso
- Cada función maneja un paso específico del flujo de creación de RFI

**Beneficios**:
- Separa la lógica de cada paso
- Facilita modificar pasos individuales
- Mejora la testabilidad del código

### 5. `prompt_generator.py`
**Responsabilidad**: Generación de todos los mensajes/prompts del bot

**Funciones principales**:
- `get_step_prompt(session, step)`: Obtiene el prompt para cualquier paso
- Funciones privadas para generar prompts específicos de cada paso

**Beneficios**:
- Centraliza todos los mensajes del bot
- Facilita cambios en el tono o formato de mensajes
- Permite reutilizar prompts en diferentes contextos

### 6. `back_navigation.py`
**Responsabilidad**: Manejo de la navegación hacia atrás en el flujo

**Funciones principales**:
- `can_go_back(step)`: Verifica si se puede ir hacia atrás
- `get_previous_step(session, current_step)`: Calcula el paso anterior
- `handle_back_command(session, msg_response)`: Maneja el comando "volver"
- `is_back_command(message)`: Identifica comandos de navegación hacia atrás

**Beneficios**:
- Simplifica la lógica de navegación hacia atrás
- Maneja casos especiales de flujo condicional
- Facilita agregar/modificar pasos sin romper la navegación

## Archivo Principal Refactorizado

### `whatsapp_api.py` (Refactorizado)
**Responsabilidad**: Coordinación general y manejo de errores de alto nivel

**Funciones restantes**:
- `process_incoming_message()`: Función principal que coordina todo el flujo
- `handle_step()`: Coordinador de procesamiento de pasos usando los módulos
- `send_step_prompt()`: Wrapper simplificado para envío de prompts
- `send_historical_pdf()`: Placeholder para envío de PDFs históricos

**Cambios principales**:
- Eliminación de código duplicado (80% menos líneas)
- Uso de los nuevos módulos especializados
- Manejo de errores más granular y específico
- Lógica de flujo más clara y legible

## Beneficios de la Modularización

### 1. **Mantenibilidad**
- Cada módulo tiene una responsabilidad específica
- Cambios en validaciones no afectan la lógica de pasos
- Fácil localizar y modificar funcionalidades específicas

### 2. **Testabilidad**
- Cada módulo puede ser probado independientemente
- Funciones más pequeñas y enfocadas
- Mocking más sencillo para pruebas unitarias

### 3. **Legibilidad**
- Código más organizado y comprensible
- Separación clara de responsabilidades
- Documentación integrada en cada módulo

### 4. **Escalabilidad**
- Fácil agregar nuevos pasos al flujo
- Sencillo implementar nuevas validaciones
- Extensible para nuevas funcionalidades

### 5. **Debugging**
- Errores más específicos y localizados
- Logs mejorados con contexto de módulo
- Rastreo de errores más eficiente

## Cómo Usar la Nueva Estructura

### Para agregar un nuevo paso:
1. Crear el procesador en `step_processor.py`
2. Agregar el prompt en `prompt_generator.py`
3. Implementar validaciones en `input_validator.py`
4. Actualizar la navegación en `back_navigation.py`

### Para modificar validaciones:
1. Editar la función correspondiente en `input_validator.py`
2. Los cambios se reflejan automáticamente en todos los usos

### Para cambiar mensajes:
1. Modificar los prompts en `prompt_generator.py`
2. Mantiene consistencia en todo el bot

### Para debuggear:
1. Los logs incluyen el módulo específico donde ocurre el error
2. Cada módulo maneja sus propios errores con contexto
3. Fácil identificar qué componente está fallando

## Estructura de Archivos

```
app/services/
├── whatsapp_api.py          # Coordinador principal (refactorizado)
├── session_manager.py       # Gestión de sesiones
├── command_handler.py       # Manejo de comandos
├── input_validator.py       # Validaciones de entrada
├── step_processor.py        # Procesamiento de pasos
├── prompt_generator.py      # Generación de mensajes
├── back_navigation.py       # Navegación hacia atrás
└── [otros archivos existentes...]
```

Esta modularización convierte el código monolítico original en un sistema modular, mantenible y extensible, facilitando significativamente el desarrollo futuro y la resolución de problemas.
