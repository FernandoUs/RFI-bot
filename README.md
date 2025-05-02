# RFI-bot

## Configuración del entorno

### Opción 1: Usando Conda
```bash
# Crear el entorno desde el archivo environment.yml
conda env create -f environment.yml

# Activar el entorno
conda activate rfi-bot
```

### Opción 2: Usando Pip
```bash
# Crear un entorno virtual
python -m venv venv

# Activar el entorno (Windows)
.\venv\Scripts\activate
# O en macOS/Linux
# source venv/bin/activate

# Instalar las dependencias
pip install -r requirements.txt
```

### Configuración de credenciales AWS (si es necesario)
```bash
aws configure
```
Introduce tu Access Key ID, Secret Access Key y la región preferida (ej. us-west-1).