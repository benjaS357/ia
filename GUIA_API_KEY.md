# 🔑 Guía para Obtener la API Key Correcta de Gemini

## ⚠️ IMPORTANTE: Usa Google AI Studio, NO Vertex AI

El error que estás recibiendo indica que estás usando una API Key de **Vertex AI** en lugar de **Google AI Studio**.

---

## ✅ Pasos Correctos para Obtener la API Key:

### 1. **Ve a Google AI Studio**
   - Abre tu navegador y ve a: **https://aistudio.google.com/app/apikey**
   - Inicia sesión con tu cuenta de Google

### 2. **Crea una Nueva API Key**
   - Haz clic en el botón **"Create API Key"** o **"Crear API Key"**
   - Selecciona un proyecto de Google Cloud (o crea uno nuevo)
   - Espera a que se genere la API Key

### 3. **Verifica el Formato**
   - La API Key **DEBE** empezar con: `AIza`
   - Ejemplo: `AIzaSyDXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`
   - **NO debe empezar con**: `AQ.`, `ya29.`, u otros prefijos

### 4. **Copia la API Key Completa**
   - Haz clic en el botón de copiar
   - Guarda la API Key en un lugar seguro

### 5. **Configúrala en el Proyecto**
   - Ejecuta el script: `.\configurar_api.bat`
   - Pega la API Key cuando se te solicite
   - O edita manualmente el archivo `.env`:
     ```
     GEMINI_API_KEY=AIzaSy...tu_api_key_completa...
     ```

### 6. **Reinicia el Servidor**
   - Detén el servidor actual (Ctrl+C)
   - Inicia de nuevo: `python manage.py runserver 9999`

---

## ❌ Errores Comunes:

### **Error 1: API Key de Vertex AI**
```
Error: API keys are not supported by this API. Expected OAuth2...
```
**Solución**: Estás usando una API Key de Vertex AI. Necesitas una de Google AI Studio.

### **Error 2: API Key sin prefijo "AIza"**
```
GEMINI_API_KEY=AQ.Ab8RN6Kvpn...
```
**Solución**: Esta es una credencial de OAuth, no una API Key. Obtén una nueva de AI Studio.

### **Error 3: API Key no configurada**
```
Error: GEMINI_API_KEY no encontrada
```
**Solución**: Ejecuta `.\configurar_api.bat` y configura tu API Key.

---

## 🔗 Enlaces Importantes:

- **Google AI Studio (Crear API Key)**: https://aistudio.google.com/app/apikey
- **Documentación de Gemini**: https://ai.google.dev/gemini-api/docs
- **Modelos Disponibles**: https://ai.google.dev/gemini-api/docs/models

---

## 📝 Nota Importante:

**Google AI Studio** y **Vertex AI** son diferentes servicios:

| Google AI Studio | Vertex AI |
|-----------------|-----------|
| ✅ Usa API Keys simples | ❌ Usa OAuth2 |
| ✅ Más fácil de configurar | ❌ Más complejo |
| ✅ Gratis para desarrollo | 💰 Requiere facturación |
| ✅ API Key empieza con `AIza` | ❌ Tokens diferentes |

**Para este proyecto, usa Google AI Studio.**
