# 🏗️ RFI Bot - Sistema de WhatsApp para Solicitudes de Información

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![Twilio](https://img.shields.io/badge/twilio-8.10.0-red.svg)](https://www.twilio.com/)
[![AWS S3](https://img.shields.io/badge/aws-s3-orange.svg)](https://aws.amazon.com/s3/)

> Sistema automatizado de WhatsApp para crear, gestionar y consultar RFIs (Request for Information) con generación automática de PDFs y almacenamiento en la nube.

## 🌟 Características Principales

- **🤖 Conversación Inteligente**: Interfaz natural a través de WhatsApp
- **📄 Generación Automática de PDFs**: Documentos profesionales generados al instante
- **☁️ Almacenamiento en la Nube**: Todos los PDFs almacenados en AWS S3
- **📚 Historial Completo**: Consulta y reenvío de RFIs anteriores
- **🔄 Navegación Intuitiva**: Opciones numeradas y comandos de texto
- **👥 Soporte Multi-usuario**: Sesiones independientes por usuario
- **⚡ Tiempo Real**: Respuestas inmediatas y procesamiento rápido

## 🚀 Inicio Rápido

### 1. 📁 Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/rfi-bot.git
cd rfi-bot
```

### 2. 🐍 Configurar Entorno Python

```bash
# Crear entorno virtual
python -m venv rfi-env

# Activar entorno virtual
# Windows:
rfi-env\Scripts\activate
# macOS/Linux:
source rfi-env/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. 🔧 Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
# - Credenciales de Twilio
# - Credenciales de AWS S3
# - Configuración de Flask
```

### 4. ▶️ Ejecutar la Aplicación

```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

## 📋 Requisitos

### Sistema
- Python 3.8 o superior
- Conexión a internet estable

### Servicios Externos
- **Cuenta Twilio**: Para WhatsApp Business API
- **Cuenta AWS**: Para almacenamiento S3
- **ngrok** (opcional): Para desarrollo local

## 🔧 Configuración Detallada

### 📱 Configurar Twilio WhatsApp

1. Crear cuenta en [Twilio](https://twilio.com)
2. Obtener credenciales del Console
3. Configurar Sandbox de WhatsApp
4. Configurar Webhook URL

### ☁️ Configurar AWS S3

1. Crear cuenta en [AWS](https://aws.amazon.com)
2. Crear bucket S3
3. Configurar políticas de acceso
4. Obtener Access Keys

Ver la [Guía de Configuración Completa](SETUP_GUIDE.md) para instrucciones detalladas.

## 📖 Documentación

- **[Guía de Usuario](USER_GUIDE.md)**: Manual completo para usuarios finales
- **[Guía de Configuración](SETUP_GUIDE.md)**: Instrucciones de instalación y despliegue
- **[Documentación de Modularización](MODULARIZATION_DOCS.md)**: Arquitectura del sistema
- **[Implementación de PDF en Memoria](MEMORY_PDF_IMPLEMENTATION.md)**: Detalles técnicos

## 🏗️ Arquitectura

```
WhatsApp ──► Twilio ──► Flask App ──► SQLite DB
                           │
                           ▼
                      AWS S3 Storage
```

### 📂 Estructura del Proyecto

```
rfi-bot/
├── app/
│   ├── routes.py              # API endpoints
│   └── services/
│       ├── whatsapp_api.py    # Integración WhatsApp
│       ├── session_manager.py # Gestión de sesiones
│       ├── command_handler.py # Manejo de comandos
│       ├── rfi_generator.py   # Generación de PDFs
│       └── s3_service.py      # Servicio AWS S3
├── config.py                  # Configuración principal
├── app.py                     # Punto de entrada
└── requirements.txt           # Dependencias
```

## 💬 Uso del Bot

### Comandos Principales

- **Crear RFI**: Envía `2` o `nuevo`
- **Ver Historial**: Envía `1` o `historial`
- **Menú Principal**: Envía `menu`
- **Volver**: Envía `volver` durante la creación

### Flujo de Creación de RFI

1. **Información Personal** → Nombre completo
2. **Cargo Profesional** → Tu posición
3. **Información del Sitio** → Proyecto/ubicación
4. **Objetivo del RFI** → Propósito de la solicitud
5. **Tipo de Información** → Qué necesitas
6. **Descripción Detallada** → Explicación completa
7. **Fecha Límite** → Cuándo necesitas respuesta
8. **Prioridad** → Alta, Media o Baja
9. **Contacto** → Email o teléfono
10. **Imagen** → Adjuntar foto (opcional)

## 🧪 Testing

```bash
# Ejecutar tests básicos
python -m pytest test/ -v

# Verificar instalación
curl http://localhost:5000/health
```

## 🚀 Despliegue en Producción

### Con Docker

```bash
# Construir imagen
docker build -t rfi-bot .

# Ejecutar contenedor
docker run -p 5000:5000 --env-file .env rfi-bot
```

### Con Gunicorn

```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar en producción
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📊 Escalabilidad

### Límites Actuales
- **Usuarios simultáneos**: ~100
- **Mensajes por segundo**: ~20
- **Almacenamiento**: Ilimitado (S3)

### Para Mayor Escala
- Migrar a PostgreSQL/MySQL
- Implementar Redis + Celery
- Usar múltiples instancias con Load Balancer
- Configurar monitoreo y métricas

## 🔒 Seguridad

- Variables de entorno para credenciales
- Validación de todas las entradas
- URLs firmadas para acceso a S3
- Rate limiting implementado
- HTTPS requerido en producción

## 🤝 Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 📞 Soporte

Para soporte técnico o reportar bugs:

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/rfi-bot/issues)
- **Email**: soporte@tu-dominio.com
- **Documentación**: Ver archivos `.md` en este repositorio

## 🎯 Roadmap

- [ ] Dashboard web para administradores
- [ ] Soporte multiidioma
- [ ] Integración con otros sistemas de construcción
- [ ] App móvil complementaria
- [ ] Análisis de datos y reportes

---

**Desarrollado con ❤️ para optimizar procesos de construcción e ingeniería**
