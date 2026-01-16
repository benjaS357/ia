"""
Script de prueba para verificar la conexión con SAP Service Layer
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Damasco.settings')
import django
django.setup()

from main.sap_service_layer import SAPServiceLayer, query_sap_service_layer, get_sap_metadata

def test_connection():
    """Probar conexión básica a SAP"""
    print("=" * 60)
    print("PRUEBA DE CONEXIÓN A SAP SERVICE LAYER")
    print("=" * 60)
    
    try:
        sap = SAPServiceLayer()
        print(f"\n📋 Configuración:")
        print(f"   URL: {sap.base_url}")
        print(f"   Usuario: {sap.username}")
        print(f"   Endpoints disponibles: {len(sap.endpoints_metadata)}")
        
        # Intentar login
        print(f"\n🔐 Intentando login...")
        if sap.login():
            print(f"   ✅ Session ID: {sap.session_id[:20]}...")
            
            # Probar consulta simple
            print(f"\n📊 Consultando 5 artículos...")
            result = sap.query("/Items", top=5)
            
            if result.get('success'):
                print(f"   ✅ Consulta exitosa!")
                print(f"   Registros encontrados: {result.get('count')}")
                
                if result.get('data'):
                    print(f"\n   Primeros registros:")
                    for idx, item in enumerate(result['data'][:3], 1):
                        print(f"   {idx}. {item.get('ItemCode')} - {item.get('ItemName')}")
                        # Mostrar algunos campos disponibles
                        print(f"       Campos disponibles: {', '.join(list(item.keys())[:8])}...")
            else:
                print(f"   ❌ Error en consulta: {result.get('error')}")
            
            # Logout
            sap.logout()
        else:
            print(f"   ❌ Login falló")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_metadata():
    """Probar función de metadata"""
    print("\n" + "=" * 60)
    print("METADATA DE ENDPOINTS")
    print("=" * 60)
    metadata = get_sap_metadata()
    print(metadata)

if __name__ == "__main__":
    test_connection()
    test_metadata()
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")
    print("=" * 60)
