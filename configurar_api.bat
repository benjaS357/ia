@echo off
echo ========================================
echo   CONFIGURAR API KEY DE GEMINI
echo ========================================
echo.
echo Este script te ayudara a configurar tu API Key de Gemini.
echo.
echo Pasos:
echo 1. Ve a: https://aistudio.google.com/app/apikey
echo 2. Crea o copia tu API Key
echo 3. Pegala cuando se te solicite
echo.
echo ========================================
echo.
set /p API_KEY="Ingresa tu API Key de Gemini: "

if "%API_KEY%"=="" (
    echo.
    echo Error: No ingresaste ninguna API Key
    pause
    exit /b 1
)

echo.
echo Guardando API Key en archivo .env...

(
echo # Configuracion de Gemini API
echo # Obtén tu API Key en: https://aistudio.google.com/app/apikey
echo GEMINI_API_KEY=%API_KEY%
echo.
echo # Configuracion de Django ^(para produccion^)
echo # SECRET_KEY=tu_secret_key_aqui
echo # DEBUG=False
) > .env

echo.
echo ========================================
echo   CONFIGURACION EXITOSA
echo ========================================
echo.
echo Tu API Key ha sido guardada en el archivo .env
echo.
echo Ahora puedes:
echo 1. Iniciar el servidor con: python manage.py runserver 9999
echo 2. O usar el script: iniciar_chat.bat
echo.
echo ========================================
pause
