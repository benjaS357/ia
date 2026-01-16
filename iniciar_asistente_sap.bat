@echo off
chcp 65001 > nul
cls
echo ========================================
echo 🤖 ASISTENTE VIRTUAL SAP BUSINESS ONE
echo ========================================
echo.
echo ✅ Configuración:
echo    - Gemini 2.0 Flash (Vertex AI)
echo    - SAP Service Layer
echo    - Function Calling activado
echo.
echo 🔵 Iniciando servidor...
echo.

python manage.py runserver 9999

pause
