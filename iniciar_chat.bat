@echo off
echo ========================================
echo   CHAT CON GEMINI - CONFIGURACION
echo ========================================
echo.
echo Por favor, ingresa tu API Key de Gemini:
echo (Obtenla en: https://aistudio.google.com/app/apikey)
echo.
set /p GEMINI_API_KEY="API Key: "
echo.
echo Configurando...
set GEMINI_API_KEY=%GEMINI_API_KEY%
echo.
echo ✅ API Key configurada!
echo 🚀 Iniciando servidor en puerto 9999...
echo 🌐 Abre: http://127.0.0.1:9999/
echo.
python manage.py runserver 9999
pause
