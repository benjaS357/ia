# 🔵 Configurar Vertex AI (Servicio de Pago de Google Cloud)

Tu proyecto: **sap-b1-ai-integration**

---

## 📝 Pasos para Obtener las Credenciales:

### **1. Ve a Google Cloud Console**
Abre: https://console.cloud.google.com/

### **2. Selecciona tu proyecto**
Asegúrate de estar en el proyecto: **sap-b1-ai-integration**

### **3. Habilita la API de Vertex AI**
- Ve a: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
- Haz clic en **"Enable"** (Habilitar)

### **4. Crea una Service Account**

**a) Ve a Service Accounts:**
   - https://console.cloud.google.com/iam-admin/serviceaccounts

**b) Crea una nueva:**
   - Clic en **"Create Service Account"**
   - Nombre: `gemini-api-service`
   - Descripción: `Service account para usar Gemini API`
   - Clic en **"Create and Continue"**

**c) Asigna permisos:**
   - Busca y selecciona el rol: **"Vertex AI User"**
   - Clic en **"Continue"**
   - Clic en **"Done"**

### **5. Descarga las Credenciales JSON**

**a) En la lista de Service Accounts:**
   - Encuentra `gemini-api-service@sap-b1-ai-integration.iam.gserviceaccount.com`
   - Haz clic en los tres puntos (⋮) → **"Manage keys"**

**b) Crea una nueva clave:**
   - Clic en **"Add Key"** → **"Create new key"**
   - Selecciona tipo: **JSON**
   - Clic en **"Create"**
   - Se descargará un archivo JSON

**c) Guarda el archivo:**
   - Renombra el archivo a: `credentials.json`
   - Muévelo a la carpeta del proyecto: `C:\Users\bvelazco\damasco\ia\`

---

## ✅ Una vez que tengas el archivo credentials.json:

1. El archivo debe estar en: `C:\Users\bvelazco\damasco\ia\credentials.json`
2. Reinicia el servidor: `python manage.py runserver 9999`
3. El sistema detectará automáticamente las credenciales y usará Vertex AI

---

## 🔗 Enlaces Rápidos:

- **Service Accounts**: https://console.cloud.google.com/iam-admin/serviceaccounts?project=sap-b1-ai-integration
- **Vertex AI API**: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=sap-b1-ai-integration
- **Vertex AI Console**: https://console.cloud.google.com/vertex-ai?project=sap-b1-ai-integration

---

## 💡 Nota Importante:

El token `AQ.Ab8...` que tienes es un **token OAuth2 temporal** para uso en consola web.
Para usar Gemini en tu aplicación Django necesitas un **archivo JSON de credenciales de Service Account**.
