from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import google.generativeai as genai
import json
import os
from .models import ChatMessage

# Configurar Gemini con API Key
def configure_gemini():
    """Configura Gemini usando API Key"""
    try:
        # Obtener API Key de variable de entorno o settings
        api_key = os.environ.get('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
        
        if not api_key:
            print("⚠️ GEMINI_API_KEY no encontrada. Por favor configúrala.")
            return None
        
        genai.configure(api_key=api_key)
        
        # Intentar con diferentes modelos disponibles
        model_names = ['gemini-1.5-pro', 'gemini-1.5-flash-latest', 'gemini-1.0-pro']
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                print(f"✅ Usando modelo: {model_name}")
                return model
            except Exception as e:
                print(f"⚠️ Modelo {model_name} no disponible: {e}")
                continue
        
        return None
    except Exception as e:
        print(f"Error configurando Gemini: {e}")
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
            
            # Configurar y llamar a Gemini
            model = configure_gemini()
            if not model:
                return JsonResponse({
                    'error': '⚠️ API Key de Gemini no configurada. Por favor:\n1. Ve a https://aistudio.google.com/app/apikey\n2. Crea una API Key\n3. Ejecuta: $env:GEMINI_API_KEY="tu_api_key"\n4. Reinicia el servidor'
                }, status=500)
            
            # Crear chat con historial
            chat = model.start_chat(history=[])
            
            # Enviar mensaje
            response = chat.send_message(user_message)
            
            assistant_message = response.text
            
            # Guardar respuesta del asistente
            ChatMessage.objects.create(
                role='assistant',
                message=assistant_message
            )
            
            return JsonResponse({
                'success': True,
                'response': assistant_message
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
    """Endpoint para limpiar el historial del chat"""
    if request.method == 'POST':
        try:
            ChatMessage.objects.all().delete()
            return JsonResponse({
                'success': True,
                'message': 'Historial eliminado'
            })
        except Exception as e:
            return JsonResponse({
                'error': f'Error al limpiar historial: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'error': 'Método no permitido'
    }, status=405)
