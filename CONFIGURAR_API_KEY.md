# IMPORTANTE: Configuración de Gemini API Key

Para que el chat funcione, necesitas configurar tu API Key de Gemini.

## Paso 1: Obtener API Key
1. Ve a: https://makersuite.google.com/app/apikey
2. Inicia sesión con tu cuenta de Google
3. Haz clic en "Create API Key"
4. Copia la API Key generada

## Paso 2: Configurar la API Key

### Opción A - Variable de entorno temporal (PowerShell):
```powershell
$env:GEMINI_API_KEY="tu_api_key_aqui"
python manage.py runserver 9999
```

### Opción B - Variable de entorno permanente (Windows):
1. Busca "Variables de entorno" en Windows
2. Haz clic en "Variables de entorno..."
3. En "Variables del sistema" haz clic en "Nueva..."
4. Nombre: GEMINI_API_KEY
5. Valor: tu_api_key_aqui
6. Acepta y reinicia tu terminal

### Opción C - Archivo .env (Recomendado):
1. Crea un archivo `.env` en la raíz del proyecto
2. Agrega: `GEMINI_API_KEY=tu_api_key_aqui`
3. Instala python-dotenv: `pip install python-dotenv`

## Paso 3: Iniciar el servidor
```bash
python manage.py runserver 9999
```

Tu chat estará en: http://127.0.0.1:9999/
