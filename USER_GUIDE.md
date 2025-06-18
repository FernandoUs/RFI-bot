# 🏗️ RFI Bot - Sistema de WhatsApp para Solicitudes de Información

## 📋 Descripción General

El RFI Bot es un sistema automatizado de WhatsApp que permite a los usuarios crear, gestionar y consultar RFIs (Request for Information) de manera conversacional. El sistema genera documentos PDF automáticamente y los almacena en la nube para fácil acceso.

## ✨ Características Principales

### 🤖 Conversación Inteligente
- **Interfaz WhatsApp**: Interacción natural a través de mensajes
- **Flujo guiado**: El bot guía al usuario paso a paso para completar un RFI
- **Navegación intuitiva**: Opciones numeradas y comandos de texto
- **Manejo de errores**: Mensajes claros cuando algo sale mal

### 📄 Generación de PDF
- **Creación automática**: Genera PDFs profesionales con la información recopilada
- **Almacenamiento en memoria**: Proceso optimizado sin archivos temporales locales
- **Envío automático**: Entrega el PDF directamente por WhatsApp
- **Respaldo en la nube**: Todos los PDFs se almacenan en AWS S3

### 📚 Gestión de Historial
- **Consulta de RFIs anteriores**: Ver todos los RFIs creados
- **Reenvío de documentos**: Solicitar nuevamente cualquier PDF anterior
- **Búsqueda por número**: Acceso directo a RFIs específicos

### 🔄 Navegación Post-PDF
- **Opciones claras**: Después de cada PDF, el usuario ve opciones numeradas
- **Múltiples formas de navegar**: Números (1, 2) o comandos de texto ('historial', 'nuevo')
- **Estado persistente**: El sistema recuerda el contexto de cada usuario

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.8+**: Lenguaje principal
- **Flask**: Framework web para la API REST
- **Twilio**: Integración con WhatsApp Business API
- **ReportLab**: Generación de documentos PDF
- **Boto3**: Cliente de AWS para S3

### Base de Datos
- **SQLite**: Almacenamiento local de sesiones y datos de RFI
- **JSON**: Formato de intercambio de datos
- **AWS S3**: Almacenamiento de archivos PDF en la nube

### Infraestructura
- **AWS S3**: Almacenamiento de documentos
- **Twilio Sandbox**: Servicio de WhatsApp (desarrollo)
- **ngrok**: Túnel para desarrollo local (opcional)

### Dependencias Principales
```
flask==2.3.3
twilio==8.10.0
reportlab==4.0.4
boto3==1.28.57
python-dotenv==1.0.0
```

## 📱 Guía de Usuario

### 🚀 Iniciando una Conversación

1. **Primer contacto**: Envía cualquier mensaje al bot de WhatsApp
2. **Menú principal**: El bot mostrará las opciones disponibles
3. **Selección**: Elige entre ver historial (1) o crear nuevo RFI (2)

### 🆕 Creando un Nuevo RFI

#### Paso 1: Información Personal
```
👤 Información Personal
Por favor, ingresa tu nombre completo:
```
- Ingresa tu nombre completo
- Mínimo 3 caracteres

#### Paso 2: Cargo Profesional
```
👔 Cargo Profesional
Por favor, ingresa tu cargo:
```
- Describe tu posición o rol
- Mínimo 3 caracteres

#### Paso 3: Información del Sitio
```
🏗️ Información del Sitio
¿En qué sitio o proyecto trabajas?
```
- Nombre del proyecto o ubicación
- Mínimo 3 caracteres

#### Paso 4: Objetivo del RFI
```
🎯 Objetivo del RFI
¿Cuál es el objetivo principal de este RFI?
```
- Describe el propósito de la solicitud
- Mínimo 10 caracteres

#### Paso 5: Tipo de Información
```
📋 Tipo de Información
¿Qué tipo de información necesitas?
```
- Especifica qué tipo de datos requieres
- Mínimo 5 caracteres

#### Paso 6: Descripción Detallada
```
📝 Descripción Detallada
Proporciona una descripción completa del RFI:
```
- Descripción completa del requerimiento
- Mínimo 20 caracteres

#### Paso 7: Fecha Límite
```
📅 Fecha Límite
¿Cuál es la fecha límite para la respuesta? (DD/MM/AAAA)
```
- Formato: DD/MM/AAAA
- Debe ser fecha futura

#### Paso 8: Prioridad
```
⚡ Prioridad
Selecciona la prioridad:
1️⃣ Alta
2️⃣ Media  
3️⃣ Baja
```
- Elige un número (1, 2, o 3)

#### Paso 9: Información de Contacto
```
📞 Información de Contacto
Proporciona tu email o teléfono de contacto:
```
- Email válido o número de teléfono
- Mínimo 5 caracteres

#### Paso 10: Imagen (Opcional)
```
📷 Imagen de Referencia (Opcional)
Envía una imagen relacionada o escribe 'omitir':
```
- Sube una imagen (JPG, PNG, etc.)
- O escribe 'omitir' para continuar sin imagen

### 📄 Generación del PDF

Después de completar todos los pasos:

1. **Procesamiento**: El bot genera automáticamente el PDF
2. **Envío**: Recibes el documento por WhatsApp
3. **Opciones post-PDF**:
   ```
   ✅ RFI #001 Completado
   
   Tu solicitud de información ha sido generada exitosamente.
   
   ¿Qué quieres hacer ahora?
   
   1️⃣ Ver historial de RFIs
   2️⃣ Crear un nuevo RFI
   
   🔹 También puedes escribir:
   • 'menu' para ver opciones
   • 'historial' para ver tus RFIs
   • 'nuevo' para crear otro RFI
   ```

### 📚 Consultando el Historial

1. **Acceso**: Envía '1' o 'historial'
2. **Lista**: Ve todos tus RFIs anteriores numerados
3. **Selección**: Envía el número del RFI que quieres consultar
4. **Reenvío**: El bot te envía nuevamente el PDF

Ejemplo de historial:
```
📋 Mis RFIs anteriores

1️⃣ Problema de filtraciones en sótano
   📅 18/06/2025 11:08
   📊 Completado

2️⃣ Inspección de estructuras metálicas
   📅 18/06/2025 14:22
   📊 Completado

Para ver un RFI, envía el número correspondiente.
🔄 Envía 'menu' para volver al menú principal
```

### 🔄 Comandos de Navegación

En cualquier momento puedes usar:

- **'menu'**: Volver al menú principal
- **'historial'**: Ver tus RFIs anteriores
- **'nuevo'**: Crear un nuevo RFI
- **'volver'**: Regresar al paso anterior (durante creación)
- **'omitir'**: Saltar pasos opcionales
- **'reiniciar'**: Empezar desde el principio

### ⚠️ Manejo de Errores

#### Límite Diario de Twilio
Si aparece este mensaje:
```
⚠️ Límite diario de WhatsApp alcanzado

El servicio ha alcanzado el límite de mensajes diarios.
Tu RFI fue procesado correctamente pero no se pudo enviar automáticamente.

💡 Opciones disponibles:
• Escribe 'enlace' para obtener el link de descarga
• Escribe 'menu' para ir al menú principal
```

**Solución**: Escribe 'enlace' para obtener el link directo de descarga del PDF.

#### Errores de Validación
- **Texto muy corto**: Asegúrate de cumplir con los caracteres mínimos
- **Fecha inválida**: Usa el formato DD/MM/AAAA con fecha futura
- **Email inválido**: Verifica que el email tenga formato correcto

## 🔧 Configuración Técnica

### Variables de Entorno Necesarias

```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=tu_account_sid
TWILIO_AUTH_TOKEN=tu_auth_token
TWILIO_PHONE_NUMBER=+14155238886

# AWS Configuration
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_REGION=us-west-1
AWS_S3_BUCKET=tu-bucket-name

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### Estructura del Proyecto

```
RFI-bot/
├── app/
│   ├── __init__.py
│   ├── routes.py              # Rutas principales de la API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── whatsapp_api.py    # Integración con Twilio/WhatsApp
│   │   ├── session_manager.py  # Gestión de sesiones de usuario
│   │   ├── command_handler.py  # Manejo de comandos y navegación
│   │   ├── menu_manager.py     # Gestión de menús y opciones
│   │   ├── step_processor.py   # Procesamiento de pasos del RFI
│   │   ├── rfi_generator.py    # Generación de PDFs
│   │   ├── s3_service.py       # Servicio de AWS S3
│   │   ├── storage.py          # Gestión de base de datos
│   │   └── prompt_generator.py # Generación de prompts
│   └── utils/
├── data/                      # Datos de la aplicación
├── static/                    # Archivos estáticos
├── temp/                     # Archivos temporales
├── config.py                 # Configuración principal
├── app.py                   # Punto de entrada de la aplicación
├── requirements.txt         # Dependencias de Python
└── README.md               # Este archivo
```

## 🎯 Características Avanzadas

### 📊 Persistencia de Datos
- **Sesiones de usuario**: Cada conversación se mantiene independiente
- **Historial completo**: Todos los RFIs se almacenan permanentemente
- **Recuperación automática**: Si hay una desconexión, el usuario puede continuar

### 🔒 Seguridad
- **Validación de entrada**: Todos los datos se validan antes de procesarse
- **Sanitización**: Los textos se limpian para evitar inyecciones
- **URLs firmadas**: Los enlaces de S3 tienen expiración automática

### 🌐 Escalabilidad
- **Base de datos**: SQLite para desarrollo, fácil migración a PostgreSQL/MySQL
- **Almacenamiento**: AWS S3 para escalabilidad ilimitada
- **API REST**: Arquitectura preparada para múltiples clientes

## 📈 Métricas y Monitoreo

El sistema registra automáticamente:
- Número de RFIs creados por usuario
- Tiempos de respuesta
- Errores y excepciones
- Uso de funcionalidades

## 🆘 Soporte y Troubleshooting

### Problemas Comunes

1. **"No puedo enviar imágenes"**
   - Verifica que el formato sea JPG, PNG, GIF o WEBP
   - El archivo no debe exceder 5MB
   - Usa 'omitir' si no tienes imagen

2. **"Mi mensaje no se procesa"**
   - Verifica que estés enviando el tipo de dato correcto
   - Revisa los caracteres mínimos requeridos
   - Usa 'volver' para regresar al paso anterior

3. **"No recibo el PDF"**
   - Puede ser límite diario de Twilio
   - Escribe 'enlace' para obtener link de descarga
   - Verifica tu conexión a internet

### Contacto de Soporte

Para problemas técnicos o dudas sobre el sistema, contacta al administrador del bot con:
- Número de teléfono
- Descripción del problema
- Pasos que causaron el error

---

## 📝 Notas de Versión

### Versión Actual: 2.0
- ✅ Generación de PDF en memoria
- ✅ Navegación mejorada post-PDF
- ✅ Manejo robusto de errores
- ✅ Soporte para múltiples formatos de imagen
- ✅ Interfaz de usuario optimizada
- ✅ Almacenamiento en la nube con AWS S3

### Próximas Funcionalidades
- 🔄 Soporte para múltiples idiomas
- 📊 Dashboard web para administradores
- 🔔 Notificaciones de seguimiento
- 👥 Soporte para equipos/grupos
- 📱 App móvil complementaria

---

*Este sistema fue diseñado para optimizar el proceso de creación y gestión de RFIs en proyectos de construcción e ingeniería, proporcionando una interfaz intuitiva y accesible a través de WhatsApp.*
