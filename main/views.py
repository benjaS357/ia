from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from google import genai
from google.genai.types import Tool, FunctionDeclaration, GenerateContentConfig
import json
import os
from .models import ChatMessage, QueryCache
from .sap_service_layer import query_sap_service_layer, get_sap_metadata, get_cached_queries, get_top_selling_products, get_top_customers, get_sales_person_performance, reset_session

# Cliente global de Vertex AI
vertex_client = None

# Definir las herramientas (Functions) para SAP Service Layer
sap_tools = [
    Tool(
        function_declarations=[
            FunctionDeclaration(
                name="query_sap_service_layer",
                description="""Consulta datos de SAP Business One Service Layer. 
                
                Entidades disponibles:
                - Items: Maestro de artículos/productos
                - BusinessPartners: Clientes y proveedores
                - Orders: Pedidos de venta
                - Invoices: Facturas de venta
                - PurchaseOrders: Órdenes de compra
                - InventoryGenEntries: Entradas de mercancías
                - InventoryGenExits: Salidas de mercancías
                - ItemGroups: Grupos de artículos
                - Warehouses: Almacenes
                - PriceLists: Listas de precios
                
                Ejemplos de filtros OData:
                - Items activos: "Valid eq 'Y'"
                - Items con stock: "OnHand gt 0"
                - Clientes: "CardType eq 'C'"
                - Documentos abiertos: "DocumentStatus eq 'O'"
                """,
                parameters={
                    "type": "object",
                    "properties": {
                        "entity": {
                            "type": "string",
                            "description": "Nombre de la entidad SAP (Items, BusinessPartners, Orders, etc.)"
                        },
                        "filters": {
                            "type": "string",
                            "description": "Filtros OData (opcional). Ejemplo: 'OnHand gt 0'"
                        },
                        "select": {
                            "type": "string",
                            "description": "Campos a seleccionar separados por coma (opcional). Ejemplo: 'ItemCode,ItemName,OnHand'"
                        },
                        "top": {
                            "type": "integer",
                            "description": "Cantidad de registros. OMITE este parámetro para obtener TODOS los registros (usa paginación automática). Solo úsalo si necesitas limitar resultados."
                        }
                    },
                    "required": ["entity"]
                }
            ),
            FunctionDeclaration(
                name="get_sap_metadata",
                description="Obtiene información sobre todos los endpoints disponibles en SAP Service Layer, sus campos y filtros comunes",
                parameters={
                    "type": "object",
                    "properties": {}
                }
            ),
            FunctionDeclaration(
                name="get_top_selling_products",
                description="""Obtiene los productos más vendidos en un rango de fechas con VENTAS NETAS.
                
                ⚠️ USA ESTA FUNCIÓN cuando el usuario pregunte por:
                - "productos más vendidos"
                - "top X productos"
                - "ranking de ventas por producto"
                - "qué productos se vendieron más"
                
                🚨 IMPORTANTE: Esta función automáticamente:
                1. Descarga TODAS las facturas (Invoices) del período
                2. Descarga TODAS las notas de crédito (CreditNotes) del período
                3. Calcula: Ventas Netas = Facturas - Notas de Crédito
                4. EXCLUYE productos con precio < $3 dólares
                5. Suma las cantidades de cada producto (netas)
                6. Ordena de mayor a menor
                7. Retorna el top solicitado
                
                Es mucho más eficiente y precisa que query_sap_service_layer para este análisis.
                SIEMPRE incluye el impacto de devoluciones y EXCLUYE productos baratos.
                """,
                parameters={
                    "type": "object",
                    "properties": {
                        "date_from": {
                            "type": "string",
                            "description": "Fecha inicio en formato YYYY-MM-DD (ej: '2026-01-01')"
                        },
                        "date_to": {
                            "type": "string",
                            "description": "Fecha fin en formato YYYY-MM-DD (ej: '2026-01-05')"
                        },
                        "top": {
                            "type": "integer",
                            "description": "Cantidad de productos a retornar (default: 5)"
                        }
                    },
                    "required": ["date_from", "date_to"]
                }
            ),
            FunctionDeclaration(
                name="get_top_customers",
                description="""Obtiene los clientes que más compraron en un rango de fechas con VENTAS NETAS.
                
                ⚠️ USA ESTA FUNCIÓN cuando el usuario pregunte por:
                - "clientes que más compraron"
                - "top X clientes"
                - "mejores clientes"
                - "ranking de clientes por ventas"
                
                🚨 IMPORTANTE: Esta función automáticamente:
                1. Descarga TODAS las facturas (Invoices) del período
                2. Descarga TODAS las notas de crédito (CreditNotes) del período
                3. Calcula: Ventas Netas = Facturas - Notas de Crédito
                4. EXCLUYE productos con precio < $3 dólares
                5. Agrupa por cliente (CardCode)
                6. Suma montos netos por cliente
                7. Ordena de mayor a menor
                8. Retorna el top solicitado
                
                Es MUCHO más eficiente que query_sap_service_layer para análisis de clientes.
                """,
                parameters={
                    "type": "object",
                    "properties": {
                        "date_from": {
                            "type": "string",
                            "description": "Fecha inicio en formato YYYY-MM-DD (ej: '2026-01-01')"
                        },
                        "date_to": {
                            "type": "string",
                            "description": "Fecha fin en formato YYYY-MM-DD (ej: '2026-01-31')"
                        },
                        "top": {
                            "type": "integer",
                            "description": "Cantidad de clientes a retornar (default: 5)"
                        }
                    },
                    "required": ["date_from", "date_to"]
                }
            ),
            FunctionDeclaration(
                name="get_sales_person_performance",
                description="""Analiza el desempeño de un vendedor en un rango de fechas.
                
                ⚠️ USA ESTA FUNCIÓN cuando el usuario pregunte por:
                - "ventas de [nombre vendedor]"
                - "analizar vendedor [código]"
                - "desempeño de [nombre]"
                - "evaluar ventas de [vendedor]"
                - "oportunidades de mejora [vendedor]"
                
                🚨 IMPORTANTE: Esta función automáticamente:
                1. Filtra facturas por SalesPersonCode
                2. Calcula ventas netas (Facturas - Notas de Crédito)
                3. EXCLUYE productos con precio < $3 dólares
                4. Identifica top productos del vendedor
                5. Identifica top clientes del vendedor
                6. Calcula métricas: tasa de devolución, ticket promedio, etc.
                7. Sugiere oportunidades de mejora
                
                Cuando el usuario menciona un código + nombre (ej: "1522 JEAN MORENO"),
                el código es el SalesPersonCode.
                """,
                parameters={
                    "type": "object",
                    "properties": {
                        "sales_person_code": {
                            "type": "string",
                            "description": "Código del vendedor (ej: '1522', '-1' para sin vendedor)"
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Fecha inicio en formato YYYY-MM-DD (ej: '2026-01-01')"
                        },
                        "date_to": {
                            "type": "string",
                            "description": "Fecha fin en formato YYYY-MM-DD (ej: '2026-01-31')"
                        }
                    },
                    "required": ["sales_person_code", "date_from", "date_to"]
                }
            ),
            FunctionDeclaration(
                name="get_cached_queries",
                description="""Obtiene todas las consultas SAP que has ejecutado en esta sesión.
                
                Útil para:
                - Revisar investigaciones previas
                - Hacer resúmenes consolidados de múltiples consultas
                - Evitar consultas duplicadas
                - Analizar patrones en los datos consultados
                
                Puedes investigar libremente haciendo múltiples consultas y luego usar esta función para generar un resumen completo.
                """,
                parameters={
                    "type": "object",
                    "properties": {
                        "summary_only": {
                            "type": "boolean",
                            "description": "Si True, solo retorna descripciones de consultas. Si False, incluye datos completos."
                        }
                    }
                }
            )
        ]
    )
]

# Configurar Vertex AI con Service Account
def configure_gemini():
    """Configura Gemini usando Vertex AI (servicio de PAGO)"""
    global vertex_client
    
    try:
        # Configurar credenciales
        credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'sap-b1-ai-integration')
        location = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        if not os.path.exists(credentials_path):
            print(f"⚠️ No se encontró el archivo de credenciales: {credentials_path}")
            return None
        
        # Configurar variable de entorno para las credenciales
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        print(f"🔵 Configurando Vertex AI...")
        print(f"   Proyecto: {project_id}")
        print(f"   Ubicación: {location}")
        print(f"   Credenciales: {credentials_path}")
        
        # Crear cliente de Vertex AI
        vertex_client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        
        print(f"✅ Vertex AI configurado correctamente con herramientas SAP")
        return vertex_client
        
    except Exception as e:
        print(f"❌ Error configurando Vertex AI: {e}")
        import traceback
        traceback.print_exc()
        return None

def chat_view(request):
    """Vista principal del chat"""
    # Obtener historial de mensajes
    messages = ChatMessage.objects.all().order_by('timestamp')
    return render(request, 'chat.html', {
        'messages': messages
    })

@csrf_exempt
def send_message(request):
    """API endpoint para enviar mensajes a Gemini"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            if not user_message:
                return JsonResponse({
                    'error': 'El mensaje no puede estar vacío'
                }, status=400)
            
            # Guardar mensaje del usuario
            ChatMessage.objects.create(
                role='user',
                message=user_message
            )
            
            # Obtener historial de conversación (últimos 10 mensajes)
            history_messages = ChatMessage.objects.all().order_by('-timestamp')[:10]
            history_messages = list(reversed(history_messages))
            
            # Construir historial para Gemini
            conversation_history = []
            for msg in history_messages[:-1]:  # Todos menos el último (que acabamos de agregar)
                if msg.role == 'user':
                    conversation_history.append({
                        "role": "user",
                        "parts": [{"text": msg.message}]
                    })
                elif msg.role == 'assistant':
                    conversation_history.append({
                        "role": "model",
                        "parts": [{"text": msg.message}]
                    })
            
            # Configurar y llamar a Vertex AI (Gemini de PAGO)
            client = configure_gemini()
            if not client:
                return JsonResponse({
                    'error': '⚠️ Vertex AI no está configurado correctamente.\n\n' +
                             'Verifica:\n' +
                             '1. Archivo credentials.json existe\n' +
                             '2. Vertex AI API está habilitada\n' +
                             '3. Service Account tiene permisos'
                }, status=500)
            
            # Enviar mensaje a Gemini en Vertex AI con herramientas SAP
            try:
                # Probar modelos disponibles
                model_names = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
                
                response = None
                model_used = None
                
                for model_name in model_names:
                    try:
                        # System instruction para el agente SAP
                        system_instruction = """Eres un arquitecto experto en SAP Business One Service Layer con acceso DIRECTO a la base de datos.

SIEMPRE debes usar las herramientas disponibles para responder consultas sobre datos de SAP. NUNCA digas que no puedes consultar datos.

Herramientas disponibles:
1. query_sap_service_layer(entity, filters, select, top) - Consulta datos de SAP
2. get_sap_metadata() - Lista todos los endpoints disponibles
3. get_cached_queries(summary_only) - Recupera consultas previas de esta sesión

🎯 ESTRATEGIA DE INVESTIGACIÓN ACUMULATIVA:

Cuando necesites analizar datos complejos o hacer análisis que requieren múltiples consultas:

1. **INVESTIGA LIBREMENTE**: Puedes hacer tantas consultas como necesites
2. **ACUMULA DATOS**: Cada consulta se guarda automáticamente en caché
3. **CONSOLIDA AL FINAL**: Usa get_cached_queries() para recuperar todo y hacer un resumen

Ejemplo de flujo:
- Usuario: "dame un análisis completo de ventas de enero"
- Tú: Hago query de Invoices de enero → Se guarda en caché
- Tú: Hago query de clientes frecuentes → Se guarda en caché  
- Tú: Hago query de productos vendidos → Se guarda en caché
- Tú: Llamo get_cached_queries() → Obtengo TODAS mis consultas
- Tú: Genero resumen consolidado con toda la información

Entidades principales y sus campos clave:
- Items: ItemCode, ItemName, ItemsGroupCode, QuantityOnStock, AvgPrice
- BusinessPartners: CardCode, CardName, CardType (C=Cliente, S=Proveedor), Balance, Phone1
- Orders: DocEntry, DocNum, CardCode, CardName, DocDate, DocTotal, DocumentStatus (O=Abierto, C=Cerrado), SalesPersonCode
- Invoices: DocEntry, DocNum, CardCode, CardName, DocDate, DocTotal, DocumentLines, SalesPersonCode (código del vendedor)
- CreditNotes: DocEntry, DocNum, CardCode, CardName, DocDate, DocTotal, DocumentLines, SalesPersonCode (notas de crédito - DEVOLUCIONES)
- PurchaseOrders: DocEntry, DocNum, CardCode, CardName, DocDate, DocTotal
- Warehouses: WarehouseCode, WarehouseName
- ItemGroups: Number, GroupName

🎯 RECONOCIMIENTO DE VENDEDORES:
Cuando el usuario menciona un código + nombre (ej: "1522 JEAN MORENO"):
- El número (1522) es el SalesPersonCode
- El nombre (JEAN MORENO) es el nombre del vendedor
- USA get_sales_person_performance() para analizar ese vendedor específico
- Ejemplos de preguntas sobre vendedores:
  * "evalúa las ventas de 1522 JEAN MORENO"
  * "desempeño del vendedor 1522 en enero"
  * "oportunidades de mejora para JEAN MORENO"

🚨 REGLA CRÍTICA DE VENTAS NETAS:
⚠️ SIEMPRE que analices ventas, facturas, productos vendidos o cualquier métrica de venta:
- Las VENTAS NETAS = Facturas (Invoices) - Notas de Crédito (CreditNotes)
- Las notas de crédito son DEVOLUCIONES que deben RESTARSE
- USA la función get_top_selling_products() que automáticamente calcula ventas netas
- Si consultas manualmente, SIEMPRE resta las notas de crédito del mismo período

🚨 REGLA CRÍTICA DE PRECIOS:
⚠️ PRODUCTOS CON PRECIO MENOR A $3 DÓLARES NO SE TOMAN EN CUENTA:
- Ignora completamente productos con precio unitario < $3
- Esto aplica a TODOS los análisis: ventas, inventario, estadísticas, etc.
- La función get_top_selling_products() automáticamente excluye estos productos
- Si consultas manualmente, SIEMPRE filtra: Price >= 3

🚨 REGLA CRÍTICA DE MONEDA:
⚠️ TODOS LOS MONTOS ESTÁN EN LA MONEDA DEL SISTEMA:
- La moneda siempre es la moneda configurada en SAP (USD - dólares)
- NO necesitas hacer conversiones de moneda
- Cuando reportes montos, puedes asumir que están en USD
- Campos como DocTotal, LineTotal, Balance, Price están en la moneda del sistema

Ejemplo:
- Usuario: "ventas de enero"
  ❌ MAL: Solo consultar Invoices
  ✅ BIEN: Invoices - CreditNotes del mismo período, solo Price >= 3
  
- Usuario: "productos más vendidos"
  ✅ MEJOR: Usar get_top_selling_products() (ya incluye el cálculo neto y excluye < $3)

MEJORES PRÁCTICAS para consultas:
1. Siempre usa el parámetro "select" para obtener SOLO los campos necesarios
2. Para consultas de ventas, usa "Invoices" (facturas cerradas)
3. Para análisis complejos, haz múltiples consultas y luego consolida con get_cached_queries()

⚠️ CRÍTICO para "productos más vendidos" o análisis de ventas:
- Para obtener LOS PRODUCTOS MÁS VENDIDOS necesitas TODAS las facturas del período
- ¡¡¡NO uses el parámetro "top" cuando el usuario pregunta por "más vendidos"!!!
- El parámetro top LIMITA las facturas, NO los productos
- Si usas top=5 solo verás 5 facturas, no todos los productos vendidos

Ejemplo CORRECTO para "5 productos más vendidos del 1/1/2026 al 5/1/2026":
1. Consultar SIN TOP: entity="Invoices", select="DocumentLines", filters="DocDate ge '2026-01-01' and DocDate le '2026-01-05'"
   ⚠️ NO incluir el parámetro top para obtener TODAS las facturas
2. Procesar TODAS las líneas de DocumentLines de TODAS las facturas
3. Agrupar por ItemCode, sumar Quantity de cada producto
4. Ordenar por cantidad total descendente
5. Mostrar los 5 productos con mayor cantidad

Ejemplo INCORRECTO (NO hacer esto):
- entity="Invoices", top=5 ❌ (esto solo trae 5 facturas, no 5 productos)

Filtros OData importantes:
- Fechas: "DocDate ge '2026-01-01' and DocDate le '2026-01-31'" (formato YYYY-MM-DD)
- Igualdad: "CardType eq 'C'"
- Contiene texto: "substringof('TEXTO', CardName)"
- Mayor/Menor: "DocTotal gt 1000"
- Y/O: "and", "or"

FORMATO DE RESPUESTA:
SIEMPRE usa formato de TABLA Markdown para resultados tabulares:

| # | Factura | Cliente | Total | Fecha |
|---|---------|---------|-------|-------|
| 1 | 3474817 | EFRAIN CHABASQUEN | $141,314.33 | 14/01/2026 |

Para resúmenes de investigaciones, estructura así:
1. Intro breve de qué investigaste
2. Tabla(s) con datos clave
3. Conclusiones/insights

IMPORTANTE:
- USA SIEMPRE el parámetro "select" para optimizar consultas
- Para análisis complejos, NO dudes en hacer 5-10 consultas diferentes
- Al final usa get_cached_queries() para consolidar todo
- Convierte fechas DD/MM/YYYY a YYYY-MM-DD en filtros
- Formatea números con separador de miles: $1,234.56
- Muestra fechas en formato DD/MM/YYYY al usuario
"""
                        
                        # Configurar con herramientas
                        config = GenerateContentConfig(
                            tools=sap_tools,
                            system_instruction=system_instruction
                        )
                        
                        # Construir contenido con historial
                        contents = conversation_history + [{
                            "role": "user",
                            "parts": [{"text": user_message}]
                        }]
                        
                        # Primera llamada al modelo con historial
                        response = client.models.generate_content(
                            model=model_name,
                            contents=contents,
                            config=config
                        )
                        
                        model_used = model_name
                        print(f"✅ Usando modelo: {model_name} (con historial de {len(conversation_history)} mensajes)")
                        break
                        
                    except Exception as e:
                        print(f"⚠️ Modelo {model_name} no disponible: {e}")
                        continue
                
                if not response:
                    raise Exception("Ningún modelo disponible")
                
                # Procesar respuesta y manejar function calling
                max_iterations = 5
                iteration = 0
                assistant_message = None
                query_logs = []  # Lista para rastrear queries ejecutados
                
                while iteration < max_iterations:
                    iteration += 1
                    print(f"🔄 Iteración {iteration}")
                    
                    # Verificar si hay texto en la respuesta
                    try:
                        if hasattr(response, 'text') and response.text:
                            assistant_message = response.text
                            print(f"📝 Respuesta con texto: {assistant_message[:100]}...")
                            break
                    except:
                        pass
                    
                    # Verificar si hay function calls
                    function_calls = []
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'function_call') and part.function_call:
                                    function_calls.append(part.function_call)
                    
                    # Si no hay function calls, terminar
                    if not function_calls:
                        print("⚠️ No hay function calls ni texto")
                        assistant_message = "No pude generar una respuesta. Intenta reformular tu pregunta."
                        break
                    
                    # Ejecutar function calls
                    print(f"🔧 Ejecutando {len(function_calls)} función(es)...")
                    function_responses = []
                    
                    for fc in function_calls:
                        func_name = fc.name
                        func_args = dict(fc.args) if fc.args else {}
                        
                        print(f"   → {func_name}({func_args})")
                        
                        # Guardar query log si es una consulta SAP
                        if func_name == "query_sap_service_layer":
                            query_log = {
                                "entity": func_args.get("entity", ""),
                                "filters": func_args.get("filters", ""),
                                "select": func_args.get("select", ""),
                                "top": func_args.get("top", "Sin límite")
                            }
                            query_logs.append(query_log)
                            print(f"   📊 Log guardado: {query_log}")
                        elif func_name == "get_top_selling_products":
                            query_log = {
                                "entity": "TopSellingProducts",
                                "filters": f"{func_args.get('date_from', '')} al {func_args.get('date_to', '')}",
                                "select": f"Top {func_args.get('top', 5)} productos",
                                "top": "Análisis completo"
                            }
                            query_logs.append(query_log)
                            print(f"   📊 Log guardado: {query_log}")
                        elif func_name == "get_top_customers":
                            query_log = {
                                "entity": "TopCustomers",
                                "filters": f"{func_args.get('date_from', '')} al {func_args.get('date_to', '')}",
                                "select": f"Top {func_args.get('top', 5)} clientes",
                                "top": "Análisis completo"
                            }
                            query_logs.append(query_log)
                            print(f"   📊 Log guardado: {query_log}")
                        elif func_name == "get_sales_person_performance":
                            query_log = {
                                "entity": "SalesPersonPerformance",
                                "filters": f"Vendedor {func_args.get('sales_person_code', '')} - {func_args.get('date_from', '')} al {func_args.get('date_to', '')}",
                                "select": "Análisis completo de desempeño",
                                "top": "Ventas, clientes, productos, oportunidades"
                            }
                            query_logs.append(query_log)
                            print(f"   📊 Log guardado: {query_log}")
                        
                        # Ejecutar la función
                        if func_name == "query_sap_service_layer":
                            result = query_sap_service_layer(**func_args)
                        elif func_name == "get_sap_metadata":
                            result = get_sap_metadata()
                        elif func_name == "get_cached_queries":
                            result = get_cached_queries(**func_args)
                        elif func_name == "get_top_selling_products":
                            result = get_top_selling_products(**func_args)
                        elif func_name == "get_top_customers":
                            result = get_top_customers(**func_args)
                        elif func_name == "get_sales_person_performance":
                            result = get_sales_person_performance(**func_args)
                        else:
                            result = json.dumps({"error": f"Función {func_name} no encontrada"})
                        
                        print(f"   ✅ Resultado: {result[:200] if isinstance(result, str) else str(result)[:200]}...")
                        
                        function_responses.append({
                            "name": func_name,
                            "response": result
                        })
                    
                    # Construir nueva conversación con los resultados
                    # Gemini espera format específico para function responses
                    parts_request = []
                    for fc in function_calls:
                        parts_request.append({"function_call": fc})
                    
                    parts_response = []
                    for fr in function_responses:
                        parts_response.append({
                            "function_response": {
                                "name": fr["name"],
                                "response": {"result": fr["response"]}
                            }
                        })
                    
                    # Llamar nuevamente al modelo con los resultados
                    print(f"🔄 Enviando resultados al modelo...")
                    
                    # Construir conversación completa con historial + request + response
                    full_conversation = conversation_history + [
                        {"role": "user", "parts": [{"text": user_message}]},
                        {"role": "model", "parts": parts_request},
                        {"role": "user", "parts": parts_response}
                    ]
                    
                    response = client.models.generate_content(
                        model=model_used,
                        contents=full_conversation,
                        config=config
                    )
                
                # Si no hay mensaje después de las iteraciones
                if not assistant_message:
                    assistant_message = "No pude completar la solicitud. Por favor intenta de nuevo."
                
                # Verificar si la respuesta tiene contenido
                if not assistant_message:
                    return JsonResponse({
                        'error': 'Gemini no pudo generar una respuesta. Intenta de nuevo.'
                    }, status=500)
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Error de Vertex AI: {error_msg}")
                
                # Mensajes de error específicos
                if '404' in error_msg or 'not found' in error_msg.lower():
                    return JsonResponse({
                        'error': '⚠️ Modelo no encontrado.\n\n' +
                                 'Habilita Vertex AI API:\n' +
                                 'https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=sap-b1-ai-integration'
                    }, status=500)
                
                if '403' in error_msg or 'permission' in error_msg.lower():
                    return JsonResponse({
                        'error': '⚠️ Sin permisos.\n\n' +
                                 'Asegúrate que vertex-express@sap-b1-ai-integration\n' +
                                 'tenga el rol "Vertex AI User"'
                    }, status=500)
                
                return JsonResponse({
                    'error': f'Error en Vertex AI: {error_msg}'
                }, status=500)
            
            # Guardar respuesta del asistente
            ChatMessage.objects.create(
                role='assistant',
                message=assistant_message
            )
            
            print(f"📤 Enviando respuesta con {len(query_logs)} query log(s)")
            
            return JsonResponse({
                'success': True,
                'response': assistant_message,
                'query_logs': query_logs
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Formato JSON inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': f'Error al procesar el mensaje: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'error': 'Método no permitido'
    }, status=405)

@csrf_exempt
def clear_history(request):
    """Endpoint para limpiar el historial del chat y el caché de consultas"""
    if request.method == 'POST':
        try:
            # Limpiar mensajes
            ChatMessage.objects.all().delete()
            
            # Limpiar caché de consultas
            QueryCache.objects.all().delete()
            
            # Resetear session ID
            reset_session()
            
            print("🗑️ Historial y caché limpiados")
            
            return JsonResponse({
                'success': True,
                'message': 'Historial y caché eliminados'
            })
        except Exception as e:
            return JsonResponse({
                'error': f'Error al limpiar historial: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'error': 'Método no permitido'
    }, status=405)
