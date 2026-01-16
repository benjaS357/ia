# 🤖 Asistente Virtual de SAP Business One

## ✅ Configuración Completada

Tu asistente virtual está configurado y listo para usar con:
- **Gemini 2.0 Flash** (Vertex AI - servicio de PAGO)
- **SAP Business One Service Layer** 
- **Function Calling** para consultas automáticas

---

## 🚀 Cómo Usar

### 1. Iniciar el servidor
```bash
python manage.py runserver 9999
```

### 2. Abrir el navegador
Visita: http://127.0.0.1:9999/

### 3. Interactuar con el asistente

El asistente es un **arquitecto experto en SAP Service Layer**. Puedes pedirle:

#### Ejemplos de consultas:

**Artículos:**
- "Dame 5 artículos de la base de datos"
- "Muéstrame los artículos activos"
- "Lista los primeros 10 productos"

**Socios de Negocio:**
- "Dame los clientes activos"
- "Muéstrame 5 proveedores"
- "Lista socios de negocio"

**Documentos:**
- "Muéstrame los pedidos abiertos"
- "Dame las últimas 5 facturas"
- "Lista las órdenes de compra"

**Información General:**
- "¿Qué endpoints tienes disponibles?"
- "Muéstrame información de almacenes"
- "¿Cuáles son las listas de precios?"

---

## 🛠️ Cómo Funciona

### 1. **Interpretación Inteligente**
El asistente interpreta tu solicitud en lenguaje natural y determina:
- Qué entidad consultar (Items, BusinessPartners, etc.)
- Qué filtros aplicar
- Cuántos registros mostrar

### 2. **Construcción de Consulta**
Construye automáticamente la consulta OData para el Service Layer:
```
GET /Items?$top=5&$filter=Valid eq 'Y'
```

### 3. **Ejecución y Respuesta**
- Se conecta a SAP Service Layer
- Ejecuta la consulta
- Presenta los resultados de forma clara

---

## 📊 Endpoints Disponibles

| Entidad | Descripción | Ejemplo |
|---------|-------------|---------|
| Items | Artículos/Productos | "Dame 10 artículos" |
| BusinessPartners | Clientes y Proveedores | "Muéstrame clientes activos" |
| Orders | Pedidos de Venta | "Lista pedidos abiertos" |
| Invoices | Facturas de Venta | "Dame las últimas facturas" |
| PurchaseOrders | Órdenes de Compra | "Muéstrame órdenes de compra" |
| ItemGroups | Grupos de Artículos | "Lista grupos de artículos" |
| Warehouses | Almacenes | "Muéstrame los almacenes" |
| PriceLists | Listas de Precios | "Dame las listas de precios" |

---

## ⚙️ Configuración SAP

### Archivo: `sap_config.json`
```json
{
  "service_layer": {
    "base_url": "https://172.200.230.62:50000/b1s/v2",
    "username": "manager@DAMASCO_PRODUCTIVA",
    "password": "*Mb2021*"
  }
}
```

### Endpoints de ejemplo:
- Items: `/Items`
- BusinessPartners: `/BusinessPartners`
- Orders: `/Orders`
- Invoices: `/Invoices`

---

## 🔍 Filtros OData

El asistente puede construir filtros automáticamente:

| Filtro | Sintaxis OData | Ejemplo |
|--------|----------------|---------|
| Igualdad | `eq` | `CardType eq 'C'` (clientes) |
| Mayor que | `gt` | `DocTotal gt 1000` |
| Menor que | `lt` | `DocTotal lt 500` |
| Y lógico | `and` | `Valid eq 'Y' and CardType eq 'C'` |
| O lógico | `or` | `CardType eq 'C' or CardType eq 'S'` |

---

## 🎯 Características Avanzadas

### Function Calling
El asistente tiene acceso a funciones especializadas:

1. **query_sap_service_layer**
   - Ejecuta consultas en el Service Layer
   - Parámetros: entity, filters, select, top

2. **get_sap_metadata**
   - Obtiene información de todos los endpoints
   - Lista campos disponibles

### System Instruction
El asistente está configurado como un arquitecto SAP que:
- Conoce todos los endpoints disponibles
- Comprende sintaxis OData
- Explica qué consulta va a ejecutar
- Presenta resultados en formato claro

---

## 🔐 Seguridad

- ✅ Conexión HTTPS al Service Layer
- ✅ Autenticación con credenciales de manager
- ✅ SSL verification deshabilitado (ambiente interno)
- ✅ Sesión automática (login/logout)

---

## 🐛 Troubleshooting

### Error 206: Invalid credentials
- Verifica usuario y contraseña en `sap_config.json`
- Formato: `usuario@COMPANYDB`

### Error 404: Endpoint not found
- Verifica que el endpoint existe en SAP
- Usa `get_sap_metadata` para ver disponibles

### Error 400: Property invalid
- Algunos campos pueden tener nombres diferentes
- No especifiques `$select` para obtener todos los campos

### El asistente no responde
- Verifica que el servidor esté corriendo
- Revisa la consola para errores
- Verifica que Vertex AI esté configurado

---

## 📝 Ejemplos Completos

### Ejemplo 1: Consultar Artículos
```
Usuario: "Dame 5 artículos de la base de datos"

Asistente: 
Voy a consultar 5 artículos del maestro de Items.

[Ejecuta: query_sap_service_layer(entity="Items", top=5)]

Resultados:
1. B000003 - BOLSA DE MERCADO
2. C00000 - Sin descripción
3. C000001 - CINTAS EPSON
...
```

### Ejemplo 2: Filtrar Clientes
```
Usuario: "Muéstrame los clientes activos"

Asistente:
Voy a consultar los socios de negocio de tipo cliente que estén activos.

[Ejecuta: query_sap_service_layer(
    entity="BusinessPartners",
    filters="CardType eq 'C' and Valid eq 'Y'",
    top=10
)]

Resultados:
[Lista de clientes...]
```

---

## 🎓 Tips de Uso

1. **Sé específico**: "Dame 5 artículos" es mejor que "artículos"
2. **Usa lenguaje natural**: El asistente entiende español
3. **Pide explicaciones**: "¿Qué endpoints tienes?"
4. **Filtra resultados**: "artículos con stock mayor a cero"
5. **Explora capacidades**: Pregunta qué puede hacer

---

## 📊 Arquitectura

```
Usuario
  ↓
Django Chat Interface
  ↓
Gemini 2.0 Flash (Vertex AI)
  ↓
Function Calling
  ↓
SAP Service Layer Client
  ↓
SAP Business One
```

---

## ✅ ¡Listo para usar!

Tu asistente virtual de SAP Business One está completamente configurado y funcionando.

**Inicia el servidor y comienza a consultar tu base de datos SAP con lenguaje natural! 🚀**
