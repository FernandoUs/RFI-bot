# RFI-bot

## Descripción del Proyecto

RFI-bot es un asistente automatizado para la generación de Solicitudes de Información (RFI - Request For Information) en proyectos de construcción. El bot utiliza WhatsApp como interfaz principal, permitiendo a los usuarios:

- Enviar consultas sobre incompatibilidades en planos o especificaciones técnicas
- Adjuntar imágenes del problema
- Recibir automáticamente un documento PDF con el formato RFI completo

El sistema utiliza inteligencia artificial para mejorar las descripciones proporcionadas por el usuario y genera documentación formal que puede ser compartida con los equipos de ingeniería y construcción.

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.9 o 3.12** (recomendado 3.12 para completa compatibilidad con Google Gemini)
- Git (para clonar el repositorio)
- Cuenta en Twilio para la integración con WhatsApp
- Credenciales de AWS para almacenamiento de archivos (opcional, pero recomendado)
- API keys para servicios de IA:
  - Google Gemini API key (requiere Python 3.12 para funcionamiento óptimo)
  - AnyScale API key (como alternativa a Gemini)

## Guía de Instalación Paso a Paso

### 1. Verificar Versión de Python

Antes de empezar, verifica que tienes instalada la versión correcta de Python:

```bash
# Comprobar versión de Python
python --version
```

Si no tienes Python 3.12 o 3.9, descárgalo desde [python.org](https://www.python.org/downloads/) e instálalo marcando la opción "Add Python to PATH" durante la instalación.

### 2. Obtener el Código Fuente

Si estás familiarizado con Git:

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/RFI-bot.git

# Entrar al directorio del proyecto
cd RFI-bot
```

Si no estás familiarizado con Git:
1. Descarga el código como archivo ZIP desde el repositorio
2. Descomprime el archivo en tu carpeta de preferencia
3. Abre una terminal o línea de comandos y navega hasta la carpeta extraída

### 3. Configuración del Entorno

#### Opción 1: Usando Conda
```bash
# Crear el entorno desde el archivo environment.yml
conda env create -f environment.yml

# Activar el entorno
conda activate rfi-bot
```

#### Opción 2: Usando Pip y venv
```bash
# Crear un entorno virtual con la versión correcta de Python
# Para Python 3.12 (recomendado para Google Gemini):
python3.12 -m venv venv
# O para Python 3.9:
# python3.9 -m venv venv

# Activar el entorno (Windows)
.\venv\Scripts\activate
# O en macOS/Linux
# source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar las dependencias
pip install -r requirements.txt
```

### 4. Configuración de Variables de Entorno

1. Crea un archivo llamado `.env` en la carpeta principal del proyecto
2. Añade las siguientes variables (reemplaza los valores con tus propias credenciales):

```
# Configuración general
DEBUG=False
SECRET_KEY=tu-clave-secreta-aquí

# Configuración de Twilio
TWILIO_ACCOUNT_SID=tu-sid-de-twilio
TWILIO_AUTH_TOKEN=tu-token-de-twilio
TWILIO_PHONE_NUMBER=+14155238886

# Configuración de AnyScale (IA)
ANY_SCALE_API_KEY=tu-api-key-de-anyscale
ANY_SCALE_API_BASE=https://api.endpoints.anyscale.com/v1

# Configuración de Google (IA)
GOOGLE_API_KEY=tu-api-key-de-google

# Configuración de AWS
AWS_ACCESS_KEY=tu-access-key-de-aws
AWS_SECRET_KEY=tu-secret-key-de-aws
AWS_REGION=us-east-1
S3_BUCKET_NAME=nombre-de-tu-bucket
```

### 5. Configuración de credenciales AWS (si es necesario)
```bash
aws configure
```
Introduce tu Access Key ID, Secret Access Key y la región preferida (ej. us-west-1).

### 6. Preparación de Carpetas del Sistema

El sistema necesita algunas carpetas para funcionar correctamente:

```bash
# Crear carpetas necesarias
mkdir -p data temp
```

### 7. Ejecutar la Aplicación

```bash
# Iniciar el servidor
python app.py
```

La aplicación estará disponible en http://localhost:5000

### 8. Configuración de Webhook de Twilio

Para recibir mensajes de WhatsApp, debes configurar Twilio:

1. Inicia sesión en tu cuenta de Twilio
2. Navega a la sección de WhatsApp Sandbox
3. Configura la URL del webhook como: `https://tu-dominio.com/webhook`
   (O usa ngrok para desarrollo local: `https://tu-subdominio-ngrok.io/webhook`)

### 8. Configuración de Webhook de Twilio con ngrok

Para que Twilio pueda comunicarse con tu aplicación, necesitas que tu servidor local sea accesible desde Internet. Para esto, ngrok es la herramienta ideal durante el desarrollo:

#### 8.1 Instalar ngrok

1. Descarga ngrok desde [ngrok.com](https://ngrok.com/download)
2. Extrae el archivo descargado y colócalo en una ubicación accesible
3. Registra una cuenta gratuita en ngrok.com para obtener tu authtoken

#### 8.2 Ejecutar ngrok

```bash
# Para usuarios de Windows, navega a la carpeta donde extrajiste ngrok, o agrégalo al PATH
# Ejecuta este comando para exponer tu puerto local 5000 a Internet
ngrok http 5000
```

Se abrirá una ventana de terminal con información sobre tu túnel. Busca la URL con formato `https://xxxx-xxxx-xxxx.ngrok.io`.

#### 8.3 Configurar el Webhook en Twilio

1. Inicia sesión en tu cuenta de Twilio
2. Navega a la sección de "Messaging" > "Try it Out" > "Send a WhatsApp Message"
3. En "Sandbox Settings", configura la URL del webhook como: 
   `https://xxxx-xxxx-xxxx.ngrok.io/webhook`
   (Reemplaza la URL con la proporcionada por ngrok)
4. Selecciona "HTTP POST" como método
5. Guarda la configuración

#### 8.4 Conexión a WhatsApp Sandbox de Twilio

Para unirte al sandbox de WhatsApp de Twilio:

1. Envía un mensaje de WhatsApp al número proporcionado por Twilio
2. Incluye el código exacto que Twilio te muestra en su panel
3. Una vez conectado, podrás intercambiar mensajes con tu bot

> **Importante**: Cada vez que reinicies ngrok, obtendrás una nueva URL, y tendrás que actualizar el webhook en Twilio.

## Notas para Desarrollo y Solución de Problemas

- **Versiones de Python:** Este proyecto funciona mejor con Python 3.12, especialmente para integraciones con Google Gemini. Python 3.9 también es compatible, pero algunas funcionalidades de IA pueden tener limitaciones.
- Si encuentras errores relacionados con las bibliotecas de IA, verifica que estás usando la versión correcta de Python para tu entorno virtual.
- Los archivos temporales se almacenan en la carpeta `temp/`
- Los datos de sesión y RFIs se guardan en `data/`
- Para probar el sistema sin Twilio, puedes usar la interfaz web accediendo a http://localhost:5000
- Si encuentras errores de importación, verifica que tu entorno virtual está activado
- **Uso de ngrok**: La URL de ngrok cambia cada vez que inicias el servicio (en la versión gratuita). Si cierras la terminal de ngrok, tendrás que actualizar la URL del webhook en Twilio.
- **Alternativas a ngrok**: Si prefieres no usar ngrok, puedes considerar alternativas como [localhost.run](https://localhost.run/), [localtunnel](https://localtunnel.github.io/www/) o desplegar tu aplicación en un servidor público.

## Más Información

Para obtener más información sobre cómo funciona el sistema o para contribuir al desarrollo, consulta la documentación adicional o abre un Issue en el repositorio.