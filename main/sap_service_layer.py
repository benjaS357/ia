"""
Módulo para interactuar con SAP Business One Service Layer
"""
import requests
import json
import os
from typing import Dict, List, Optional, Any
import urllib3

# Deshabilitar warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Session ID global para el caché
CURRENT_SESSION_ID = None

def get_session_id():
    """Obtener o crear session ID para el caché"""
    global CURRENT_SESSION_ID
    if not CURRENT_SESSION_ID:
        import uuid
        CURRENT_SESSION_ID = str(uuid.uuid4())[:8]
    return CURRENT_SESSION_ID

def reset_session():
    """Resetear session (útil al limpiar historial)"""
    global CURRENT_SESSION_ID
    CURRENT_SESSION_ID = None

class SAPServiceLayer:
    """Cliente para SAP Business One Service Layer"""
    
    def __init__(self, config_path: str = 'sap_config.json'):
        """Inicializa el cliente con la configuración"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.base_url = config['service_layer']['base_url']
        self.username = config['service_layer']['username']
        self.password = config['service_layer']['password']
        self.verify_ssl = config['service_layer'].get('verify_ssl', False)
        self.endpoints_metadata = config['endpoints']
        self.session_id = None
        
        # Crear sesión con adaptador de reintentos
        from requests.adapters import HTTPAdapter
        from requests.packages.urllib3.util.retry import Retry
        
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def login(self) -> bool:
        """Autenticarse en Service Layer"""
        try:
            url = f"{self.base_url}/Login"
            
            # Extraer CompanyDB del username (después del @)
            if '@' in self.username:
                username_part = self.username.split('@')[0]
                company_db = self.username.split('@')[1]
            else:
                username_part = self.username
                company_db = ""
            
            payload = {
                "CompanyDB": company_db,
                "UserName": username_part,
                "Password": self.password
            }
            
            response = self.session.post(
                url,
                json=payload,
                verify=self.verify_ssl,
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get('SessionId')
                print(f"✅ Login exitoso en SAP Service Layer")
                print(f"   CompanyDB: {company_db}")
                print(f"   Usuario: {username_part}")
                return True
            else:
                print(f"❌ Error en login: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en login: {e}")
            return False
    
    def logout(self):
        """Cerrar sesión en Service Layer"""
        try:
            if self.session_id:
                url = f"{self.base_url}/Logout"
                self.session.post(url, verify=self.verify_ssl, timeout=30)
                print("✅ Logout exitoso")
        except Exception as e:
            print(f"⚠️ Error en logout: {e}")
    
    def query(self, endpoint: str, filters: Optional[str] = None, 
              select: Optional[str] = None, top: int = None) -> Dict[str, Any]:
        """
        Ejecutar una consulta en Service Layer con paginación automática
        
        Args:
            endpoint: Endpoint a consultar (ej: '/Items', '/BusinessPartners')
            filters: Filtros OData (ej: "OnHand gt 0")
            select: Campos a seleccionar (ej: "ItemCode,ItemName")
            top: Cantidad de registros a retornar (None = TODOS los registros)
        
        Returns:
            Dict con los resultados de la consulta
        """
        try:
            # Autenticarse si no hay sesión
            if not self.session_id:
                if not self.login():
                    return {"error": "No se pudo autenticar en SAP Service Layer"}
            
            all_data = []
            skip = 0
            
            # Si hay top definido, usar ese límite
            if top:
                params = {'$top': top}
                if select:
                    params['$select'] = select
                if filters:
                    params['$filter'] = filters
                
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    verify=self.verify_ssl,
                    timeout=180
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "data": data.get('value', []),
                        "count": len(data.get('value', [])),
                        "endpoint": endpoint,
                        "filters": filters
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Error {response.status_code}: {response.text}",
                        "endpoint": endpoint
                    }
            
            # Si no hay top, paginar para obtener TODOS los registros
            print(f"   📄 Paginando para obtener TODOS los registros...")
            max_pages = 500  # Máximo 10000 registros (SAP devuelve ~20 por página)
            page = 0
            page_size = 500  # Intentar 500, SAP puede limitar a menos
            
            while page < max_pages:
                params = {
                    '$top': page_size,
                    '$skip': skip
                }
                if select:
                    params['$select'] = select
                if filters:
                    params['$filter'] = filters
                
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    verify=self.verify_ssl,
                    timeout=180
                )
                
                if response.status_code == 200:
                    data = response.json()
                    page_data = data.get('value', [])
                    
                    if not page_data:
                        break  # No hay más datos
                    
                    all_data.extend(page_data)
                    print(f"   📄 Página {page + 1}: {len(page_data)} registros (Total: {len(all_data)})")
                    
                    # Verificar si hay más páginas
                    # SAP indica esto con odata.nextLink o si devuelve menos registros que el page_size solicitado
                    has_next = 'odata.nextLink' in data or '@odata.nextLink' in data
                    
                    if len(page_data) < page_size and not has_next:
                        break  # Última página
                    
                    skip += len(page_data)  # Usar la cantidad real devuelta
                    page += 1
                else:
                    return {
                        "success": False,
                        "error": f"Error {response.status_code}: {response.text}",
                        "endpoint": endpoint
                    }
            
            print(f"   ✅ Total registros obtenidos: {len(all_data)}")
            return {
                "success": True,
                "data": all_data,
                "count": len(all_data),
                "endpoint": endpoint,
                "filters": filters,
                "paginated": True
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Excepción: {str(e)}",
                "endpoint": endpoint
            }
    
    def get_endpoint_info(self, entity_name: str) -> Optional[Dict]:
        """Obtener información de un endpoint por nombre de entidad"""
        return self.endpoints_metadata.get(entity_name)
    
    def list_available_endpoints(self) -> List[str]:
        """Listar todos los endpoints disponibles"""
        return list(self.endpoints_metadata.keys())
    
    def get_metadata_summary(self) -> str:
        """Obtener un resumen de todos los endpoints disponibles"""
        summary = "=== SAP Business One Service Layer - Endpoints Disponibles ===\n\n"
        
        for name, info in self.endpoints_metadata.items():
            summary += f"• {name}\n"
            summary += f"  Endpoint: {info['endpoint']}\n"
            summary += f"  Descripción: {info['description']}\n"
            summary += f"  Campos: {', '.join(info['common_fields'][:5])}...\n\n"
        
        return summary


def query_sap_service_layer(entity: str, filters: str = "", select: str = "", top: int = None) -> str:
    """
    Función para que Gemini consulte SAP Service Layer
    Guarda resultados en caché para investigación acumulativa
    
    Args:
        entity: Nombre de la entidad (Items, BusinessPartners, Orders, etc.)
        filters: Filtros OData (opcional)
        select: Campos a seleccionar (opcional)
        top: Cantidad de registros (None = TODOS los registros con paginación)
    
    Returns:
        JSON string con los resultados
    """
    try:
        sap = SAPServiceLayer()
        
        # Obtener información del endpoint
        endpoint_info = sap.get_endpoint_info(entity)
        if not endpoint_info:
            return json.dumps({
                "error": f"Entidad '{entity}' no encontrada",
                "available_entities": sap.list_available_endpoints()
            }, ensure_ascii=False, indent=2)
        
        # Ejecutar consulta
        endpoint = endpoint_info['endpoint']
        result = sap.query(
            endpoint=endpoint,
            filters=filters if filters else None,
            select=select if select else None,
            top=top
        )
        
        # Guardar en caché si la consulta fue exitosa
        if result.get('success'):
            try:
                # Importar aquí para evitar circular import
                import sys
                import django
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Damasco.settings')
                if 'django' not in sys.modules or not django.apps.apps.ready:
                    django.setup()
                
                from main.models import QueryCache
                
                session_id = get_session_id()
                query_desc = f"{entity}"
                if filters:
                    query_desc += f" con filtros: {filters[:50]}"
                if select:
                    query_desc += f" (campos: {select[:30]})"
                
                QueryCache.objects.create(
                    session_id=session_id,
                    query_type=entity,
                    query_description=query_desc,
                    query_params={
                        "entity": entity,
                        "filters": filters,
                        "select": select,
                        "top": top
                    },
                    result_data=result,
                    result_summary=f"Consulta a {entity}: {result.get('count', 0)} registros"
                )
                print(f"💾 Guardado en caché: {query_desc}")
                
            except Exception as cache_error:
                print(f"⚠️ Error guardando en caché: {cache_error}")
        
        # Cerrar sesión
        sap.logout()
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Error ejecutando consulta: {str(e)}"
        }, ensure_ascii=False, indent=2)


def get_sap_metadata() -> str:
    """
    Obtener metadata de los endpoints disponibles en SAP Service Layer
    
    Returns:
        String con la información de todos los endpoints
    """
    try:
        sap = SAPServiceLayer()
        return sap.get_metadata_summary()
    except Exception as e:
        return f"Error obteniendo metadata: {str(e)}"


def get_cached_queries(summary_only: bool = False) -> str:
    """
    Obtener todas las consultas cacheadas de la sesión actual
    Permite a Gemini revisar investigaciones previas y hacer resúmenes
    
    Args:
        summary_only: Si True, solo retorna resúmenes. Si False, retorna datos completos
    
    Returns:
        JSON con las consultas cacheadas
    """
    try:
        import sys
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Damasco.settings')
        if 'django' not in sys.modules or not django.apps.apps.ready:
            django.setup()
        
        from main.models import QueryCache
        
        session_id = get_session_id()
        cached_queries = QueryCache.objects.filter(session_id=session_id).order_by('timestamp')
        
        if not cached_queries.exists():
            return json.dumps({
                "message": "No hay consultas previas en esta sesión",
                "count": 0
            }, ensure_ascii=False, indent=2)
        
        result = {
            "session_id": session_id,
            "total_queries": cached_queries.count(),
            "queries": []
        }
        
        for query in cached_queries:
            query_info = {
                "id": query.id,
                "type": query.query_type,
                "description": query.query_description,
                "timestamp": query.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "params": query.query_params,
                "summary": query.result_summary
            }
            
            if not summary_only and query.result_data:
                query_info["data"] = query.result_data
            
            result["queries"].append(query_info)
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Error obteniendo caché: {str(e)}"
        }, ensure_ascii=False, indent=2)


def get_top_selling_products(date_from: str, date_to: str, top: int = 5) -> str:
    """
    Obtener los productos más vendidos en un rango de fechas.
    Esta función hace la paginación, descarga TODAS las facturas, 
    RESTA las notas de crédito y calcula ventas netas.
    
    Args:
        date_from: Fecha inicio en formato YYYY-MM-DD (ej: '2026-01-01')
        date_to: Fecha fin en formato YYYY-MM-DD (ej: '2026-01-05')
        top: Cantidad de productos a retornar (default: 5)
    
    Returns:
        JSON string con los productos más vendidos (ventas netas) y sus cantidades totales
    """
    from collections import defaultdict
    
    try:
        print(f"🔍 Calculando top {top} productos vendidos (VENTAS NETAS) del {date_from} al {date_to}...")
        
        sap = SAPServiceLayer()
        if not sap.login():
            return json.dumps({"error": "No se pudo conectar a SAP"}, ensure_ascii=False)
        
        filters = f"DocDate ge '{date_from}' and DocDate le '{date_to}'"
        
        # 1. Obtener TODAS las facturas con sus líneas
        print("   📄 Consultando facturas...")
        invoices_result = sap.query(
            endpoint='/Invoices',
            filters=filters,
            select='DocumentLines',
            top=None  # Sin límite - obtener TODAS
        )
        
        if not invoices_result.get('success'):
            sap.logout()
            return json.dumps({
                "error": f"Error consultando facturas: {invoices_result.get('error')}"
            }, ensure_ascii=False)
        
        invoices = invoices_result.get('data', [])
        total_invoices = len(invoices)
        print(f"   ✅ {total_invoices} facturas encontradas")
        
        # 2. Obtener TODAS las notas de crédito
        print("   📄 Consultando notas de crédito...")
        credit_notes_result = sap.query(
            endpoint='/CreditNotes',
            filters=filters,
            select='DocumentLines',
            top=None  # Sin límite - obtener TODAS
        )
        
        sap.logout()
        
        credit_notes = []
        total_credit_notes = 0
        if credit_notes_result.get('success'):
            credit_notes = credit_notes_result.get('data', [])
            total_credit_notes = len(credit_notes)
            print(f"   ✅ {total_credit_notes} notas de crédito encontradas")
        else:
            print(f"   ⚠️ No se pudieron obtener notas de crédito: {credit_notes_result.get('error')}")
        
        # 3. Sumar cantidades por producto (facturas positivas, notas crédito negativas)
        product_sales = defaultdict(lambda: {"quantity": 0, "description": "", "total_amount": 0})
        
        # Sumar facturas (solo productos >= $3)
        for invoice in invoices:
            lines = invoice.get('DocumentLines', [])
            for line in lines:
                item_code = line.get('ItemCode', '')
                if item_code:
                    price = float(line.get('Price', 0))
                    
                    # 🚨 REGLA: Ignorar productos con precio menor a $3
                    if price < 3:
                        continue
                    
                    quantity = float(line.get('Quantity', 0))
                    line_total = float(line.get('LineTotal', 0))
                    description = line.get('ItemDescription', '')
                    
                    product_sales[item_code]["quantity"] += quantity
                    product_sales[item_code]["total_amount"] += line_total
                    if description:
                        product_sales[item_code]["description"] = description
        
        # Restar notas de crédito (solo productos >= $3)
        for credit_note in credit_notes:
            lines = credit_note.get('DocumentLines', [])
            for line in lines:
                item_code = line.get('ItemCode', '')
                if item_code:
                    price = float(line.get('Price', 0))
                    
                    # 🚨 REGLA: Ignorar productos con precio menor a $3
                    if price < 3:
                        continue
                    
                    quantity = float(line.get('Quantity', 0))
                    line_total = float(line.get('LineTotal', 0))
                    description = line.get('ItemDescription', '')
                    
                    product_sales[item_code]["quantity"] -= quantity  # RESTAR
                    product_sales[item_code]["total_amount"] -= line_total  # RESTAR
                    if description and not product_sales[item_code]["description"]:
                        product_sales[item_code]["description"] = description
        
        # Ordenar por cantidad descendente
        sorted_products = sorted(
            product_sales.items(),
            key=lambda x: x[1]["quantity"],
            reverse=True
        )[:top]
        
        # Formatear resultado
        products_result = []
        for item_code, data in sorted_products:
            products_result.append({
                "ItemCode": item_code,
                "ItemDescription": data["description"],
                "NetQuantitySold": round(data["quantity"], 2),
                "NetSalesAmount": round(data["total_amount"], 2)
            })
        
        print(f"   ✅ Análisis completado: {len(product_sales)} productos únicos encontrados")
        
        return json.dumps({
            "success": True,
            "date_range": f"{date_from} al {date_to}",
            "total_invoices_analyzed": total_invoices,
            "total_credit_notes_analyzed": total_credit_notes,
            "net_sales_calculation": "Facturas - Notas de Crédito",
            "unique_products": len(product_sales),
            "top_products": products_result
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Error calculando productos más vendidos: {str(e)}"
        }, ensure_ascii=False)


def get_top_customers(date_from: str, date_to: str, top: int = 5) -> str:
    """
    Obtener los clientes que más compraron en un rango de fechas.
    Calcula ventas netas (Facturas - Notas de Crédito) por cliente.
    Solo considera productos con precio >= $3.
    
    Args:
        date_from: Fecha inicio en formato YYYY-MM-DD (ej: '2026-01-01')
        date_to: Fecha fin en formato YYYY-MM-DD (ej: '2026-01-31')
        top: Cantidad de clientes a retornar (default: 5)
    
    Returns:
        JSON string con los clientes top y sus compras netas
    """
    from collections import defaultdict
    
    try:
        print(f"🔍 Calculando top {top} clientes (VENTAS NETAS) del {date_from} al {date_to}...")
        
        sap = SAPServiceLayer()
        if not sap.login():
            return json.dumps({"error": "No se pudo conectar a SAP"}, ensure_ascii=False)
        
        filters = f"DocDate ge '{date_from}' and DocDate le '{date_to}'"
        
        # 1. Obtener TODAS las facturas (solo campos necesarios)
        print("   📄 Consultando facturas...")
        invoices_result = sap.query(
            endpoint='/Invoices',
            filters=filters,
            select='CardCode,CardName,DocumentLines',
            top=None  # Sin límite - obtener TODAS
        )
        
        if not invoices_result.get('success'):
            sap.logout()
            return json.dumps({
                "error": f"Error consultando facturas: {invoices_result.get('error')}"
            }, ensure_ascii=False)
        
        invoices = invoices_result.get('data', [])
        total_invoices = len(invoices)
        print(f"   ✅ {total_invoices} facturas encontradas")
        
        # 2. Obtener TODAS las notas de crédito
        print("   📄 Consultando notas de crédito...")
        credit_notes_result = sap.query(
            endpoint='/CreditNotes',
            filters=filters,
            select='CardCode,CardName,DocumentLines',
            top=None  # Sin límite - obtener TODAS
        )
        
        sap.logout()
        
        credit_notes = []
        total_credit_notes = 0
        if credit_notes_result.get('success'):
            credit_notes = credit_notes_result.get('data', [])
            total_credit_notes = len(credit_notes)
            print(f"   ✅ {total_credit_notes} notas de crédito encontradas")
        else:
            print(f"   ⚠️ No se pudieron obtener notas de crédito: {credit_notes_result.get('error')}")
        
        # 3. Calcular ventas netas por cliente (solo productos >= $3)
        customer_sales = defaultdict(lambda: {"name": "", "total_amount": 0, "invoice_count": 0})
        
        # Sumar facturas (solo productos >= $3)
        for invoice in invoices:
            card_code = invoice.get('CardCode', '')
            card_name = invoice.get('CardName', '')
            if card_code:
                lines = invoice.get('DocumentLines', [])
                invoice_total = 0
                
                for line in lines:
                    price = float(line.get('Price', 0))
                    
                    # 🚨 REGLA: Ignorar productos con precio menor a $3
                    if price < 3:
                        continue
                    
                    line_total = float(line.get('LineTotal', 0))
                    invoice_total += line_total
                
                # Solo contar si hubo productos válidos
                if invoice_total > 0:
                    customer_sales[card_code]["name"] = card_name
                    customer_sales[card_code]["total_amount"] += invoice_total
                    customer_sales[card_code]["invoice_count"] += 1
        
        # Restar notas de crédito (solo productos >= $3)
        for credit_note in credit_notes:
            card_code = credit_note.get('CardCode', '')
            card_name = credit_note.get('CardName', '')
            if card_code:
                lines = credit_note.get('DocumentLines', [])
                credit_note_total = 0
                
                for line in lines:
                    price = float(line.get('Price', 0))
                    
                    # 🚨 REGLA: Ignorar productos con precio menor a $3
                    if price < 3:
                        continue
                    
                    line_total = float(line.get('LineTotal', 0))
                    credit_note_total += line_total
                
                # Solo restar si hubo productos válidos
                if credit_note_total > 0:
                    if not customer_sales[card_code]["name"]:
                        customer_sales[card_code]["name"] = card_name
                    customer_sales[card_code]["total_amount"] -= credit_note_total  # RESTAR
        
        # Ordenar por monto total descendente
        sorted_customers = sorted(
            customer_sales.items(),
            key=lambda x: x[1]["total_amount"],
            reverse=True
        )[:top]
        
        # Formatear resultado
        customers_result = []
        for card_code, data in sorted_customers:
            customers_result.append({
                "CardCode": card_code,
                "CardName": data["name"],
                "NetSalesAmount": round(data["total_amount"], 2),
                "InvoiceCount": data["invoice_count"]
            })
        
        print(f"   ✅ Análisis completado: {len(customer_sales)} clientes únicos encontrados")
        
        return json.dumps({
            "success": True,
            "date_range": f"{date_from} al {date_to}",
            "total_invoices_analyzed": total_invoices,
            "total_credit_notes_analyzed": total_credit_notes,
            "net_sales_calculation": "Facturas - Notas de Crédito (solo productos >= $3)",
            "unique_customers": len(customer_sales),
            "top_customers": customers_result
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Error calculando top clientes: {str(e)}"
        }, ensure_ascii=False)


def get_sales_person_performance(sales_person_code: str, date_from: str, date_to: str) -> str:
    """
    Analizar el desempeño de un vendedor en un rango de fechas.
    Calcula ventas netas, productos vendidos, clientes atendidos, y métricas clave.
    Solo considera productos con precio >= $3.
    
    Args:
        sales_person_code: Código del vendedor (ej: '1522', '-1' para sin vendedor)
        date_from: Fecha inicio en formato YYYY-MM-DD (ej: '2026-01-01')
        date_to: Fecha fin en formato YYYY-MM-DD (ej: '2026-01-31')
    
    Returns:
        JSON string con el análisis completo del vendedor
    """
    from collections import defaultdict
    
    try:
        print(f"🔍 Analizando desempeño del vendedor {sales_person_code} del {date_from} al {date_to}...")
        
        sap = SAPServiceLayer()
        if not sap.login():
            return json.dumps({"error": "No se pudo conectar a SAP"}, ensure_ascii=False)
        
        filters = f"DocDate ge '{date_from}' and DocDate le '{date_to}' and SalesPersonCode eq {sales_person_code}"
        
        # 1. Obtener facturas del vendedor
        print("   📄 Consultando facturas del vendedor...")
        invoices_result = sap.query(
            endpoint='/Invoices',
            filters=filters,
            select='DocEntry,DocNum,CardCode,CardName,DocDate,DocTotal,DocumentLines',
            top=None
        )
        
        if not invoices_result.get('success'):
            sap.logout()
            return json.dumps({
                "error": f"Error consultando facturas: {invoices_result.get('error')}"
            }, ensure_ascii=False)
        
        invoices = invoices_result.get('data', [])
        total_invoices = len(invoices)
        print(f"   ✅ {total_invoices} facturas encontradas")
        
        # 2. Obtener notas de crédito del vendedor
        print("   📄 Consultando notas de crédito del vendedor...")
        credit_notes_result = sap.query(
            endpoint='/CreditNotes',
            filters=filters,
            select='DocEntry,DocNum,CardCode,CardName,DocDate,DocTotal,DocumentLines',
            top=None
        )
        
        sap.logout()
        
        credit_notes = []
        total_credit_notes = 0
        if credit_notes_result.get('success'):
            credit_notes = credit_notes_result.get('data', [])
            total_credit_notes = len(credit_notes)
            print(f"   ✅ {total_credit_notes} notas de crédito encontradas")
        
        # 3. Calcular métricas
        product_sales = defaultdict(lambda: {"quantity": 0, "description": "", "amount": 0})
        customer_sales = defaultdict(lambda: {"name": "", "amount": 0, "invoice_count": 0})
        total_sales_amount = 0
        total_returns_amount = 0
        
        # Procesar facturas (solo productos >= $3)
        for invoice in invoices:
            card_code = invoice.get('CardCode', '')
            card_name = invoice.get('CardName', '')
            lines = invoice.get('DocumentLines', [])
            
            invoice_total = 0
            for line in lines:
                price = float(line.get('Price', 0))
                
                # 🚨 REGLA: Ignorar productos con precio menor a $3
                if price < 3:
                    continue
                
                item_code = line.get('ItemCode', '')
                quantity = float(line.get('Quantity', 0))
                line_total = float(line.get('LineTotal', 0))
                description = line.get('ItemDescription', '')
                
                if item_code:
                    product_sales[item_code]["quantity"] += quantity
                    product_sales[item_code]["amount"] += line_total
                    if description:
                        product_sales[item_code]["description"] = description
                
                invoice_total += line_total
            
            # Acumular por cliente
            if invoice_total > 0 and card_code:
                customer_sales[card_code]["name"] = card_name
                customer_sales[card_code]["amount"] += invoice_total
                customer_sales[card_code]["invoice_count"] += 1
                total_sales_amount += invoice_total
        
        # Procesar notas de crédito (solo productos >= $3)
        for credit_note in credit_notes:
            card_code = credit_note.get('CardCode', '')
            card_name = credit_note.get('CardName', '')
            lines = credit_note.get('DocumentLines', [])
            
            credit_note_total = 0
            for line in lines:
                price = float(line.get('Price', 0))
                
                # 🚨 REGLA: Ignorar productos con precio menor a $3
                if price < 3:
                    continue
                
                item_code = line.get('ItemCode', '')
                quantity = float(line.get('Quantity', 0))
                line_total = float(line.get('LineTotal', 0))
                description = line.get('ItemDescription', '')
                
                if item_code:
                    product_sales[item_code]["quantity"] -= quantity
                    product_sales[item_code]["amount"] -= line_total
                    if description and not product_sales[item_code]["description"]:
                        product_sales[item_code]["description"] = description
                
                credit_note_total += line_total
            
            # Restar del cliente
            if credit_note_total > 0 and card_code:
                if not customer_sales[card_code]["name"]:
                    customer_sales[card_code]["name"] = card_name
                customer_sales[card_code]["amount"] -= credit_note_total
                total_returns_amount += credit_note_total
        
        # Top 5 productos del vendedor
        sorted_products = sorted(
            product_sales.items(),
            key=lambda x: x[1]["amount"],
            reverse=True
        )[:5]
        
        top_products = []
        for item_code, data in sorted_products:
            top_products.append({
                "ItemCode": item_code,
                "ItemDescription": data["description"],
                "NetQuantitySold": round(data["quantity"], 2),
                "NetSalesAmount": round(data["amount"], 2)
            })
        
        # Top 5 clientes del vendedor
        sorted_customers = sorted(
            customer_sales.items(),
            key=lambda x: x[1]["amount"],
            reverse=True
        )[:5]
        
        top_customers = []
        for card_code, data in sorted_customers:
            top_customers.append({
                "CardCode": card_code,
                "CardName": data["name"],
                "NetSalesAmount": round(data["amount"], 2),
                "InvoiceCount": data["invoice_count"]
            })
        
        # Calcular métricas de desempeño
        net_sales = total_sales_amount - total_returns_amount
        return_rate = (total_returns_amount / total_sales_amount * 100) if total_sales_amount > 0 else 0
        avg_invoice = net_sales / total_invoices if total_invoices > 0 else 0
        
        print(f"   ✅ Análisis completado")
        
        return json.dumps({
            "success": True,
            "sales_person_code": sales_person_code,
            "date_range": f"{date_from} al {date_to}",
            "summary": {
                "total_invoices": total_invoices,
                "total_credit_notes": total_credit_notes,
                "gross_sales": round(total_sales_amount, 2),
                "returns": round(total_returns_amount, 2),
                "net_sales": round(net_sales, 2),
                "return_rate_percent": round(return_rate, 2),
                "average_invoice_amount": round(avg_invoice, 2),
                "unique_customers": len(customer_sales),
                "unique_products_sold": len(product_sales)
            },
            "top_products": top_products,
            "top_customers": top_customers,
            "improvement_opportunities": {
                "high_return_rate": return_rate > 10,
                "low_customer_diversity": len(customer_sales) < 10,
                "low_product_diversity": len(product_sales) < 20,
                "suggestions": []
            }
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Error analizando vendedor: {str(e)}"
        }, ensure_ascii=False)

