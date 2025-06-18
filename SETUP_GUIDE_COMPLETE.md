# 🚀 RFI Bot - Guía Completa de Configuración

## 📁 Archivos para Limpiar el Repositorio

### 🗑️ Archivos de Depuración (ELIMINAR ANTES DE PUBLICAR)

```bash
# Archivos de testing y debug
test/debug_*.py
test/test_*.py (excepto test_basic_functionality.py)
simple_test.py
reset_all.py
test_s3.py

# Datos temporales y de testing
temp/
data/rfis_backup.json
data/rfis_clean.json
data/sessions.json

# Archivos de caché Python
__pycache__/
app/__pycache__/
app/services/__pycache__/
test/__pycache__/

# Archivos de configuración local (NUNCA PUBLICAR)
.env

# Archivos de IDE
.vscode/
.idea/
*.log
*.bak
```

### ✅ Estructura Final del Repositorio

```
RFI-bot/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── command_handler.py
│   │   ├── menu_manager.py
│   │   ├── prompt_generator.py
│   │   ├── rfi_generator.py
│   │   ├── s3_service.py
│   │   ├── session_manager.py
│   │   ├── step_processor.py
│   │   ├── storage.py
│   │   └── whatsapp_api.py
│   └── utils/
│       └── config.py
├── static/
│   └── images/
├── test/
│   ├── __init__.py
│   └── test_basic_functionality.py
├── .gitignore
├── .env.example
├── app.py
├── config.py
├── requirements.txt
├── environment.yml
├── README.md
├── USER_GUIDE.md
├── SETUP_GUIDE.md
└── cleanup_repository.bat
```

## 🔧 Instalación Paso a Paso

### 1. Preparación del Entorno

#### Verificar Python
```bash
python --version
# Debe ser Python 3.9+ (recomendado 3.12)
```

#### Clonar el Repositorio
```bash
git clone <tu-repositorio>
cd RFI-bot
```

### 2. Configuración del Entorno Virtual

#### Opción A: Con Conda (Recomendado)
```bash
# Crear entorno desde archivo
conda env create -f environment.yml
conda activate rfi-bot
```

#### Opción B: Con venv
```bash
# Crear entorno virtual
python -m venv rfi-env
# Windows
rfi-env\Scripts\activate
# Linux/Mac
source rfi-env/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configuración de Variables de Entorno

#### Crear archivo .env
```bash
cp .env.example .env
```

#### Configurar variables (editar .env)
```env
# Twilio - WhatsApp
TWILIO_ACCOUNT_SID=tu_account_sid_de_twilio
TWILIO_AUTH_TOKEN=tu_auth_token_de_twilio
TWILIO_PHONE_NUMBER=whatsapp:+14155238886

# Google Gemini AI
GOOGLE_API_KEY=tu_api_key_de_google_gemini

# AWS S3 (opcional)
AWS_ACCESS_KEY=tu_access_key
AWS_SECRET_KEY=tu_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=tu-bucket-rfi-pdfs

# Configuración de la aplicación
DEBUG=False
SECRET_KEY=una_clave_secreta_muy_segura
```

### 4. Configuración de Servicios Externos

#### Twilio - WhatsApp Business
1. Crear cuenta en [Twilio](https://www.twilio.com/)
2. Acceder a WhatsApp Sandbox
3. Configurar número de teléfono
4. Obtener credenciales (SID y Auth Token)

#### Google Gemini AI
1. Acceder a [Google AI Studio](https://aistudio.google.com/)
2. Crear proyecto
3. Generar API Key
4. Configurar en .env

#### AWS S3 (Opcional pero Recomendado)
1. Crear cuenta AWS
2. Crear bucket S3
3. Configurar IAM user con permisos S3
4. Obtener credenciales de acceso

### 5. Preparación de Directorios
```bash
# Crear directorios necesarios
mkdir -p data temp static/images

# Verificar permisos de escritura
# Windows
echo test > data\test.txt && del data\test.txt
# Linux/Mac
touch data/test.txt && rm data/test.txt
```

### 6. Ejecutar la Aplicación

#### Desarrollo Local
```bash
python app.py
```

#### Con Gunicorn (Producción)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 7. Configuración de Webhook (Desarrollo)

#### Instalar ngrok
1. Descargar de [ngrok.com](https://ngrok.com/)
2. Crear cuenta gratuita
3. Configurar authtoken

#### Exponer aplicación local
```bash
ngrok http 5000
```

#### Configurar en Twilio
1. Copiar URL de ngrok (https://xxxxx.ngrok.io)
2. En Twilio Console → WhatsApp Sandbox
3. Webhook URL: `https://xxxxx.ngrok.io/webhook`
4. HTTP Method: POST

### 8. Verificación de Instalación

#### Ejecutar tests básicos
```bash
cd test
python test_basic_functionality.py
```

#### Verificar endpoint
```bash
curl http://localhost:5000/
# Debe retornar: "RFI Bot is running"
```

## 🚀 Despliegue en Producción

### Opciones de Hosting

#### 1. Heroku
```bash
# Crear Procfile
echo "web: gunicorn app:app" > Procfile

# Desplegar
git add .
git commit -m "Deploy RFI Bot"
git push heroku main
```

#### 2. AWS EC2
- Crear instancia EC2
- Instalar Python y dependencias
- Configurar nginx como proxy reverso
- Usar systemd para gestión de procesos

#### 3. DigitalOcean Droplet
- Similar a EC2
- Usar espacios de DigitalOcean en lugar de S3

### Configuración de Producción

#### Variables de entorno
```bash
export DEBUG=False
export FLASK_ENV=production
```

#### Base de datos
- Migrar de JSON a PostgreSQL o MySQL
- Configurar conexión con SSL
- Implementar backup automático

## 🔄 Mantenimiento y Monitoreo

### Logs
```bash
# Configurar logging en producción
tail -f /var/log/rfi-bot/app.log
```

### Backup
```bash
# Backup de datos (script automatizado)
./backup_data.sh
```

### Actualizaciones
```bash
git pull origin main
pip install -r requirements.txt
systemctl restart rfi-bot
```

## 👥 Soporte para Múltiples Usuarios

### ✅ ¿Soporta Chats Múltiples? SÍ

El sistema **SÍ soporta múltiples usuarios simultáneos**:

#### Cómo Funciona
- **Sesiones por número**: Cada usuario de WhatsApp tiene su propia sesión
- **Aislamiento de datos**: Los datos de cada usuario están completamente separados
- **Concurrencia**: Múltiples usuarios pueden usar el bot al mismo tiempo
- **Persistencia**: Cada usuario mantiene su estado independiente

#### Arquitectura de Sesiones
```python
# Ejemplo de estructura de sesiones
{
  "+51987654321": {
    "step": 3,
    "data": {...},
    "rfi_id": "ABC123"
  },
  "+51912345678": {
    "step": 1,
    "data": {...},
    "rfi_id": "XYZ789"
  }
}
```

### 🚀 Mejoras para Mayor Escalabilidad

#### 1. Base de Datos Dedicada
```bash
# Migrar de JSON a PostgreSQL
# Beneficios:
- Mejor rendimiento con muchos usuarios
- Transacciones ACID
- Consultas complejas
- Backup profesional
```

#### 2. Cache con Redis
```bash
# Implementar Redis para sesiones activas
# Beneficios:
- Acceso ultra-rápido
- Expiración automática
- Gestión de memoria optimizada
```

#### 3. Cola de Tareas (Celery)
```bash
# Para procesamiento asíncrono
# Beneficios:
- Generación de PDF no bloquea chat
- Mejor experiencia de usuario
- Escalabilidad horizontal
```

#### 4. Load Balancer
```bash
# Para alta disponibilidad
# Beneficios:
- Distribución de carga
- Failover automático
- Soporte a miles de usuarios
```

#### 5. Monitoreo Avanzado
```bash
# Implementar métricas
# Métricas clave:
- Usuarios activos simultáneos
- Tiempo de respuesta
- Tasa de error
- Uso de recursos
```

### 📊 Límites Actuales

#### Límites de Twilio
- **Sandbox**: 1 número de WhatsApp Business
- **Producción**: Depende del plan contratado
- **Rate limiting**: ~1 mensaje/segundo por defecto

#### Límites de Recursos
- **Memoria**: Depende del servidor
- **Almacenamiento**: Limitado por AWS S3 o disco local
- **CPU**: Generación de PDF es CPU-intensiva

### 🎯 Recomendaciones por Escala

#### Hasta 50 usuarios simultáneos
- Configuración actual es suficiente
- Usar SQLite como base de datos
- Servidor básico (2GB RAM)

#### 50-500 usuarios simultáneos
- Migrar a PostgreSQL
- Implementar Redis para cache
- Servidor medio (4-8GB RAM)
- Usar Celery para tareas pesadas

#### 500+ usuarios simultáneos
- Arquitectura de microservicios
- Load balancer
- Múltiples instancias del bot
- Base de datos replicada
- CDN para PDFs

### 🔧 Script de Limpieza de Repositorio

Se incluye `cleanup_repository.bat` que elimina automáticamente archivos no necesarios:

```bash
# Ejecutar antes de publicar
./cleanup_repository.bat
```

## 📋 Lista de Verificación Final

### Antes del Despliegue
- [ ] Variables de entorno configuradas
- [ ] Servicios externos funcionando
- [ ] Tests básicos pasando
- [ ] Archivos de debug eliminados
- [ ] .env no incluido en git
- [ ] Webhook configurado correctamente

### Después del Despliegue
- [ ] Endpoint respondiendo
- [ ] WhatsApp conectado
- [ ] Generación de PDF funcionando
- [ ] S3 guardando archivos
- [ ] Logs monitoreados

---

*Para soporte adicional o contribuciones, revisar la documentación técnica completa o contactar al equipo de desarrollo.*
