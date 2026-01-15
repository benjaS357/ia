# 💬 Chat con Gemini AI - Proyecto Django

Sistema de chat integrado con Google Gemini AI, desarrollado con Django.

## 🚀 Características

- ✅ Chat en tiempo real con Gemini AI
- ✅ Historial de conversaciones guardado en base de datos
- ✅ Interfaz moderna y responsive
- ✅ Panel de administración Django
- ✅ API REST para integración

## 📋 Requisitos

- Python 3.8+
- Django 5.0+
- Cuenta de Google con acceso a Gemini API

## 🔧 Instalación

### 1. Clona el repositorio

```bash
git clone <tu-repositorio>
cd ia
```

### 2. Crea y activa un entorno virtual

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Instala las dependencias

```bash
pip install -r requirements.txt
```

### 4. Configura las credenciales

#### **Opción A: Usando API Key (RECOMENDADO - Más fácil)**

1. Obtén tu API Key en: https://aistudio.google.com/app/apikey
2. Configura la variable de entorno:

```powershell
# Windows PowerShell:
$env:GEMINI_API_KEY="tu_api_key_aqui"

# Linux/Mac:
export GEMINI_API_KEY="tu_api_key_aqui"
```

#### **Opción B: Usando Service Account (Avanzado)**

1. Copia `credentials.example.json` a `credentials.json`
2. Reemplaza con tus credenciales reales de Google Cloud
3. Habilita Vertex AI API en tu proyecto de Google Cloud

### 5. Realiza las migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crea un superusuario (opcional)

```bash
python manage.py createsuperuser
```

### 7. Inicia el servidor

```bash
python manage.py runserver 9999
```

O usa el script de inicio:
```bash
# Windows:
.\iniciar_chat.bat
```

## 🌐 Acceso

- **Chat**: http://127.0.0.1:9999/
- **Admin**: http://127.0.0.1:9999/admin/

## 📁 Estructura del Proyecto

```
ia/
├── Damasco/           # Configuración principal de Django
│   ├── settings.py    # Configuración del proyecto
│   └── urls.py        # URLs principales
├── main/              # App principal del chat
│   ├── models.py      # Modelo ChatMessage
│   ├── views.py       # Vistas y lógica de Gemini
│   ├── admin.py       # Configuración del admin
│   └── urls.py        # URLs de la app
├── templates/         # Templates HTML
│   └── chat.html      # Interfaz del chat
├── static/            # Archivos estáticos (CSS, JS, imágenes)
├── credentials.example.json  # Ejemplo de credenciales
├── requirements.txt   # Dependencias Python
└── manage.py          # Script de gestión de Django
```

## 🔑 Variables de Entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `GEMINI_API_KEY` | API Key de Google Gemini | Sí (si no usas service account) |

## 📝 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Interfaz del chat |
| POST | `/send/` | Enviar mensaje a Gemini |
| POST | `/clear/` | Limpiar historial del chat |

## 🛡️ Seguridad

**IMPORTANTE:** Antes de subir a GitHub:

1. ✅ Nunca subas archivos con credenciales reales
2. ✅ Usa `.gitignore` para excluir archivos sensibles
3. ✅ Las credenciales deben estar en `credentials.json` (ignorado por git)
4. ✅ Usa variables de entorno para datos sensibles

Archivos que NUNCA deben subirse:
- `credentials.json`
- `sap-b1-ai-integration-*.json`
- `.env`
- `db.sqlite3` (base de datos local)

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit tus cambios (`git commit -m 'Agrega nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 🆘 Soporte

Si tienes problemas:

1. Revisa que tu API Key esté correctamente configurada
2. Verifica que las dependencias estén instaladas: `pip install -r requirements.txt`
3. Asegúrate de haber ejecutado las migraciones: `python manage.py migrate`

## 🙏 Agradecimientos

- Google Gemini AI por la API
- Django Framework
- Comunidad de código abierto

---

Desarrollado con ❤️ usando Django y Gemini AI
