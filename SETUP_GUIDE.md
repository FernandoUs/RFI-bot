# 🚀 Guía de Configuración y Despliegue - RFI Bot

## 📁 Archivos a Eliminar para Repositorio

### 🗑️ Archivos de Testing y Debug (ELIMINAR)

```bash
# Archivos de testing desarrollados durante el debugging
test/debug_menu_issue.py
test/debug_navigation_flow.py
test/debug_option_2.py
test/debug_pdf_sent.py
test/debug_session_state.py
test/test_direct_option_2.py
test/test_final_verification.py
test/test_full_history_flow.py
test/test_historial_bucle_fix.py
test/test_main_menu_fix.py
test/test_memory_pdf_implementation.py
test/test_pdf_complete_flow.py
test/test_pdf_fix.py
test/test_pdf_whatsapp_diagnosis.py
test/test_post_pdf_experience.py
test/test_quick_history.py
test/test_realistic_menu.py
test/test_realistic_post_pdf.py
test/test_rfi_complete_flow_fixed.py
test/test_rfi_complete_flow.py
test/test_rfi_flow.py
test/test_rfi_history_functionality.py
test/test_rfi_selection_debug.py
test/test_rfi.py
test/test_s3_structure_verification.py
test/test_twilio_limit_handling.py
test/test_user_exact_scenario.py
test/test_user_scenario_fix.py
test/test_whatsapp_number_diagnosis.py
test/test_whatsapp_simulation.py

# Archivos de datos de testing
test/data/

# Archivos auxiliares de debugging
simple_test.py
reset_all.py
test_s3.py
```

### 🗑️ Archivos de Configuración y Temporales (ELIMINAR)

```bash
# Archivos de caché de Python
__pycache__/
app/__pycache__/
app/services/__pycache__/
test/__pycache__/

# Archivos temporales
temp/
data/rfis_backup.json
data/rfis_clean.json
data/sessions.json

# Archivos de entorno (contienen claves sensibles)
.env

# Archivos de configuración de IDE
.vscode/
.idea/

# Archivos de log
*.log

# Archivos de backup
*.bak
*.backup
```

### ✅ Archivos a MANTENER en el Repositorio

```bash
# Estructura principal
app/
├── __init__.py
├── routes.py
└── services/
    ├── __init__.py
    ├── command_handler.py
    ├── menu_manager.py
    ├── prompt_generator.py
    ├── rfi_generator.py
    ├── s3_service.py
    ├── session_manager.py
    ├── step_processor.py
    ├── storage.py
    └── whatsapp_api.py

# Configuración
config.py
app.py
requirements.txt
environment.yml

# Documentación
README.md
USER_GUIDE.md
MODULARIZATION_DOCS.md
MEMORY_PDF_IMPLEMENTATION.md
TWILIO_LIMIT_SOLUTION.md

# Archivos de ejemplo
.env.example         # (crear este archivo)
data/.gitkeep       # (mantener estructura de carpetas)
static/.gitkeep
temp/.gitkeep

# Archivos de testing esenciales (opcional)
test/__init__.py
test/test_basic_functionality.py  # (crear un test básico)
```

## 📋 Comando de Limpieza

```bash
# Navegar al directorio del proyecto
cd "c:\Users\Fernando\Documents\UTEC\RFI bot\RFI-bot"

# Eliminar archivos de testing
rmdir /s /q test

# Eliminar archivos temporales
rmdir /s /q temp
rmdir /s /q __pycache__
rmdir /s /q app\__pycache__
rmdir /s /q app\services\__pycache__

# Eliminar archivos específicos
del simple_test.py
del reset_all.py
del test_s3.py
del data\rfis_backup.json
del data\rfis_clean.json
del data\sessions.json

# Crear estructura limpia
mkdir test
mkdir temp
mkdir data
echo. > data\.gitkeep
echo. > temp\.gitkeep
echo. > static\.gitkeep
```

## 🔧 Configuración Paso a Paso

### 1. 📦 Requisitos del Sistema

```bash
# Verificar versión de Python
python --version  # Debe ser 3.8 o superior

# Verificar pip
pip --version
```

### 2. 📁 Clonar y Configurar el Proyecto

```bash
# Clonar el repositorio
git clone <URL_DEL_REPOSITORIO> rfi-bot
cd rfi-bot

# Crear entorno virtual
python -m venv rfi-env

# Activar entorno virtual
# En Windows:
rfi-env\Scripts\activate
# En macOS/Linux:
source rfi-env/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. 🔑 Configuración de Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Configuración de Twilio
TWILIO_ACCOUNT_SID=tu_account_sid_aqui
TWILIO_AUTH_TOKEN=tu_auth_token_aqui
TWILIO_PHONE_NUMBER=+14155238886

# Configuración de AWS S3
AWS_ACCESS_KEY_ID=tu_access_key_aqui
AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui
AWS_REGION=us-west-1
AWS_S3_BUCKET=tu-bucket-s3-aqui

# Configuración de Flask
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5000
```

### 4. 🏗️ Configurar Servicios Externos

#### 📱 Configuración de Twilio

1. **Crear cuenta en Twilio**: [twilio.com](https://twilio.com)
2. **Obtener credenciales**:
   - Account SID
   - Auth Token
   - Phone Number del Sandbox de WhatsApp
3. **Configurar Sandbox de WhatsApp**:
   - Ir a Console > Develop > Messaging > Try it out > Send a WhatsApp message
   - Seguir instrucciones para unir tu número al sandbox
4. **Configurar Webhook**:
   - URL: `https://tu-dominio.com/webhook`
   - Para desarrollo local usar ngrok

#### ☁️ Configuración de AWS S3

1. **Crear cuenta en AWS**: [aws.amazon.com](https://aws.amazon.com)
2. **Crear bucket S3**:
   ```bash
   aws s3 mb s3://tu-bucket-rfi-bot --region us-west-1
   ```
3. **Configurar políticas de acceso**:
   - Crear usuario IAM con permisos S3
   - Obtener Access Key ID y Secret Access Key
4. **Configurar CORS** (si es necesario):
   ```json
   [
     {
       "AllowedHeaders": ["*"],
       "AllowedMethods": ["GET", "PUT", "POST"],
       "AllowedOrigins": ["*"],
       "ExposeHeaders": []
     }
   ]
   ```

### 5. 🚀 Ejecutar la Aplicación

```bash
# Activar entorno virtual (si no está activo)
rfi-env\Scripts\activate

# Ejecutar la aplicación
python app.py

# La aplicación estará disponible en:
# http://localhost:5000
```

### 6. 🌐 Configuración para Producción

#### Usando ngrok (Desarrollo/Testing)

```bash
# Instalar ngrok
# Descargar desde: https://ngrok.com/download

# Ejecutar ngrok
ngrok http 5000

# Copiar la URL HTTPS generada y usarla en Twilio Webhook
```

#### Usando Servidor de Producción

```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar con gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Para HTTPS (recomendado)
gunicorn -w 4 -b 0.0.0.0:5000 --certfile=cert.pem --keyfile=key.pem app:app
```

### 7. 🧪 Verificar Instalación

```bash
# Probar endpoints básicos
curl http://localhost:5000/health
# Respuesta esperada: {"status": "OK"}

# Probar webhook (con datos de prueba)
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+1234567890&Body=test"
```

## 🔄 Soporte para Múltiples Chats

### ❓ ¿El Sistema Actual Soporta Múltiples Chats?

**SÍ**, el sistema **SOPORTA múltiples usuarios simultáneamente**:

✅ **Características actuales**:
- Cada usuario tiene su propia sesión independiente
- Las conversaciones no se interfieren entre sí
- Base de datos SQLite maneja múltiples sesiones
- Almacenamiento S3 organizado por usuario

✅ **Identificación por número de teléfono**:
```python
# Cada usuario se identifica por su número de WhatsApp
clean_sender = sender.replace('whatsapp:', '')
session = SessionManager.get_user_session(clean_sender)
```

### 🚀 Mejoras Recomendadas para Escalabilidad

#### 1. 📊 Base de Datos Escalable

**Cambio de SQLite a PostgreSQL/MySQL**:

```python
# Configuración mejorada en config.py
DATABASE_CONFIG = {
    'engine': 'postgresql',  # o 'mysql'
    'host': 'localhost',
    'port': 5432,
    'database': 'rfi_bot',
    'username': 'rfi_user',
    'password': 'secure_password'
}
```

#### 2. 🔄 Sistema de Colas

**Para alto volumen de mensajes**:

```python
# Usar Redis + Celery para procesamiento asíncrono
from celery import Celery

app = Celery('rfi_bot')
app.config_from_object('celeryconfig')

@app.task
def process_message_async(sender, message, media_urls):
    return process_incoming_message(sender, message, media_urls)
```

#### 3. 📈 Monitoreo y Métricas

```python
# Agregar métricas de uso
import time
from datetime import datetime

def log_user_activity(user_id, action, duration=None):
    with open('user_activity.log', 'a') as f:
        f.write(f"{datetime.now()},{user_id},{action},{duration}\n")
```

#### 4. 🛡️ Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/webhook', methods=['POST'])
@limiter.limit("10 per minute")
def webhook():
    # ... código existente
```

#### 5. 📱 Dashboard de Administración

```python
# Nuevo archivo: admin_dashboard.py
from flask import Blueprint, render_template, jsonify

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/stats')
def get_stats():
    return jsonify({
        'total_users': DatabaseManager().get_user_count(),
        'total_rfis': DatabaseManager().get_rfi_count(),
        'active_sessions': SessionManager.get_active_session_count()
    })
```

### 🏗️ Arquitectura Escalada Recomendada

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   Load          │    │   Flask App     │
│   Business API  │───▶│   Balancer      │───▶│   (Multiple     │
│   (Twilio)      │    │   (nginx)       │    │   Instances)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐             │
                       │   Redis Queue   │◀────────────┘
                       │   (Celery)      │
                       └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Worker        │    │   AWS S3        │
│   Database      │◀───│   Processes     │───▶│   Storage       │
│                 │    │   (Background)  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 📊 Límites Actuales y Recomendaciones

#### Límites Actuales (SQLite + Flask simple):
- **Usuarios simultáneos**: ~50-100
- **Mensajes por segundo**: ~10-20
- **Almacenamiento**: Limitado por disco local

#### Con Mejoras Recomendadas:
- **Usuarios simultáneos**: 1000+
- **Mensajes por segundo**: 100+
- **Almacenamiento**: Ilimitado (AWS S3)
- **Alta disponibilidad**: Sí
- **Escalabilidad horizontal**: Sí

## 🚨 Consideraciones de Seguridad

1. **Variables de entorno**: Nunca commitear claves en el repositorio
2. **HTTPS**: Usar siempre HTTPS en producción
3. **Validación**: Validar todas las entradas de usuario
4. **Rate limiting**: Implementar límites de velocidad
5. **Logs seguros**: No loggear información sensible

## 📞 Soporte Técnico

Para implementación y configuración:
1. Revisar logs en `app.log`
2. Verificar configuración de variables de entorno
3. Comprobar conectividad con Twilio y AWS
4. Revisar documentación de APIs externas

---

*Esta guía cubre la configuración completa del sistema RFI Bot para producción. Para dudas específicas, consultar la documentación técnica individual de cada servicio.*
