import os
import mercadopago
import requests
import mimetypes
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.conf import settings

# Get API keys from settings (which now use environment variables)
MERCADO_PAGO_ACCESS_TOKEN = settings.MERCADO_PAGO_ACCESS_TOKEN
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
YOUTUBE_VIDEO_ID = "zsGnr5FT-Qw"

def home(request):
    return render(request, "index.html")


def check_youtube_live(request):
    try:
        url = f"https://www.googleapis.com/youtube/v3/videos?id={YOUTUBE_VIDEO_ID}&part=liveStreamingDetails&key={YOUTUBE_API_KEY}"
        response = requests.get(url).json()
        
        # Verifica se a chave "items" existe e não está vazia
        if "items" in response and response["items"]:
            live_details = response["items"][0].get("liveStreamingDetails", {})

            actual_start_time = live_details.get("actualStartTime")  # Quando a live começou
            actual_end_time = live_details.get("actualEndTime")  # Quando a live terminou (se existir)

            # Se "actualStartTime" existe e "actualEndTime" NÃO existe, a live ainda está ao vivo
            if actual_start_time and not actual_end_time:
                return JsonResponse({"live": True})

        return JsonResponse({"live": False})  # Retorna False se a live terminou ou nunca começou
    
    except Exception as e:
        print(f"Erro ao verificar YouTube Live: {e}")  # Debug no terminal
        return JsonResponse({"live": False, "error": str(e)})

def get_stream_url(request):
    try:
        if check_youtube_live(request).content.decode('utf-8').find('"live": true') != -1:
            return JsonResponse({"url": f"https://www.youtube.com/embed/{YOUTUBE_VIDEO_ID}?autoplay=1&mute=1"})
        else:
            return JsonResponse({"error": "Live não está disponível."}, status=403)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def create_payment(request):
    sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)

    preference_data = {
        "items": [{
            "title": "Único acesso de 3 minutos a transmissão ao vivo",
            "quantity": 1,
            "currency_id": "BRL",
            "unit_price": 3.00
        }],
        "payer": {
            # "id": "CompradorTestBruno",  # Use your test user "Identificação da conta"
            "email": "bruno.amv@gmail.com",  # Mercado Pago auto-assigns an email
        },
        "back_urls": {
           "success": "https://climacocal.com.br/payment-success/",  # Produção
           "failure": "https://climacocal.com.br/payment-failure-safe/",  # Produção com fallback
          #  "success": "http://127.0.0.1:8000/payment-success/", ##DEV
          #  "failure": "http://127.0.0.1:8000/payment-failure/", ## DEV
        },
        "auto_return": "approved"
    }


   #CONTA BRUNO.AMV
   # identificação da conta: CompradorTestBruno
   # USER: TESTUSER329221664
   # SENHA: ql6N6FLTsd
   # email:test_user_329221664@testuser.com


    # Send request to Mercado Pago
    preference_response = sdk.preference().create(preference_data)
    
    # # Print full response for debugging
    # print("Mercado Pago API Response:", preference_response)

    # Check if init_point exists
    if "response" in preference_response and "init_point" in preference_response["response"]:
        return JsonResponse({"init_point": preference_response["response"]["init_point"]})
    else:
        return JsonResponse({"error": "Failed to create Mercado Pago payment", "details": preference_response}, status=400)


def payment_success(request):
    # Store that the user has successfully paid
    cache.set("payment_status", "approved", timeout=600)
    return render(request, "payment_success.html")

def test_payment_success(request):
    """
    Endpoint de teste para simular pagamento aprovado
    Permite testar a página de sucesso sem passar pelo MercadoPago
    """
    # Simula estado de pagamento aprovado no cache
    cache.set("payment_status", "approved", timeout=600)
    return render(request, "payment_success.html")

def test_payment_direct(request):
    """
    Acesso direto à página de teste com estado de pagamento válido
    Para testes de desenvolvimento da câmera/streaming
    """
    # Define estado de pagamento aprovado
    cache.set("payment_status", "approved", timeout=600)
    
    # Retorna página com indicador de modo teste
    context = {
        'test_mode': True,
        'message': 'MODO TESTE - Pagamento simulado'
    }
    return render(request, "payment_success.html", context)

def payment_failure(request):
    # Store that the user has failure paid
    cache.set("payment_status", "failure", timeout=600)
    
    # Log parameters for debugging ECH certificate issues
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Payment failure callback - Query params: {request.GET}")
    logger.info(f"Payment failure callback - Headers: {dict(request.headers)}")
    
    return render(request, "payment_failure.html")

def payment_failure_safe(request):
    """
    Alternative payment failure route to handle ECH certificate issues
    This route has additional SSL/TLS safety measures
    """
    # Store that the user has failure paid
    cache.set("payment_status", "failure", timeout=600)
    
    # Log parameters for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Payment failure SAFE callback - Query params: {request.GET}")
    logger.info(f"Payment failure SAFE callback - User Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
    
    # Create a more robust response with explicit headers
    response = render(request, "payment_failure.html")
    
    # Add headers to help with SSL/TLS issues
    response['X-Content-Type-Options'] = 'nosniff'
    response['X-Frame-Options'] = 'DENY'
    response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response


@csrf_exempt
def payment_webhook(request):
    import json
    from django.core.cache import cache

    data = json.loads(request.body)
    if data.get("action") == "payment.created":
        cache.set("payment_status", "approved", timeout=600)

    return JsonResponse({"status": "ok"})


def check_payment_status(request):
    status = cache.get("payment_status", "pending")
    return JsonResponse({"status": status})


def get_weather(request):
    import requests
    
    API_TOKEN = "546659d2c8b489261f185e4e10b21d3c"
    CITY_ID = "3137"
    url = f"https://apiadvisor.climatempo.com.br/api/v1/weather/locale/{CITY_ID}/current?token={API_TOKEN}"
    
    response = requests.get(url)
    data = response.json()
    return JsonResponse(data)


# ========== DIRECT CAMERA STREAMING (New Solution) ==========

def camera_stream(request):
    """Serve camera HLS stream only for paid users"""
    
    # Check payment status (using existing MercadoPago cache)
    payment_status = cache.get("payment_status", "pending")
    
    if payment_status != "approved":
        return HttpResponse(
            "❌ Acesso negado. Pagamento necessário para visualizar câmera ao vivo.",
            status=403,
            content_type="text/plain"
        )
    
    # Serve HLS playlist
    playlist_path = "/app/camera_stream/stream.m3u8"
    
    if not os.path.exists(playlist_path):
        return HttpResponse("📷 Câmera temporariamente indisponível", status=503)
    
    try:
        with open(playlist_path, 'r') as f:
            content = f.read()
        
        response = HttpResponse(content, content_type='application/vnd.apple.mpegurl')
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        response['Access-Control-Allow-Origin'] = '*'
        
        return response
        
    except Exception as e:
        return HttpResponse(f"❌ Erro acessando câmera: {str(e)}", status=500)


def camera_segment(request, segment_name):
    """Serve HLS segments (protected by payment)"""
    
    # Check payment status (using existing MercadoPago cache)
    payment_status = cache.get("payment_status", "pending")
    
    if payment_status != "approved":
        raise Http404("Acesso negado")
    
    segment_path = f"/app/camera_stream/{segment_name}"
    
    if not os.path.exists(segment_path):
        raise Http404("Segmento não encontrado")
    
    try:
        def file_iterator(file_path, chunk_size=8192):
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        
        mime_type, _ = mimetypes.guess_type(segment_path)
        response = StreamingHttpResponse(
            file_iterator(segment_path),
            content_type=mime_type or 'video/mp2t'
        )
        
        response['Cache-Control'] = 'no-cache'
        response['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        raise Http404(f"Erro: {str(e)}")


def camera_status_api(request):
    """API to check camera availability and payment status"""
    payment_status = cache.get("payment_status", "pending")
    camera_available = os.path.exists("/app/camera_stream/stream.m3u8")
    
    return JsonResponse({
        "camera_available": camera_available,
        "payment_status": payment_status,
        "access_granted": payment_status == "approved" and camera_available,
        "message": get_access_message(payment_status, camera_available),
        "stream_url": "/camera/stream.m3u8" if payment_status == "approved" and camera_available else None
    })


def get_access_message(payment_status, camera_available):
    """Get user-friendly access message"""
    if payment_status != "approved":
        return "💳 Pagamento necessário para acessar câmera ao vivo"
    elif not camera_available:
        return "📷 Câmera temporariamente indisponível"
    else:
        return "✅ Acesso liberado - transmissão ao vivo disponível"


# Modified existing function to support both YouTube and direct streaming
def get_stream_url(request):
    """Get stream URL - now supports direct camera streaming"""
    try:
        # Check payment status first
        payment_status = cache.get("payment_status", "pending")
        
        if payment_status != "approved":
            return JsonResponse({"error": "Pagamento necessário para acessar transmissão."}, status=403)
        
        # Check if direct camera streaming is available
        if os.path.exists("/app/camera_stream/stream.m3u8"):
            return JsonResponse({
                "url": "/camera/stream.m3u8",
                "type": "hls",
                "message": "Transmissão direta da câmera"
            })
        
        # Fallback to YouTube if available
        if check_youtube_live(request).content.decode('utf-8').find('"live": true') != -1:
            return JsonResponse({
                "url": f"https://www.youtube.com/embed/{YOUTUBE_VIDEO_ID}?autoplay=1&mute=1",
                "type": "youtube",
                "message": "Transmissão via YouTube"
            })
        else:
            return JsonResponse({"error": "Nenhuma transmissão disponível no momento."}, status=503)
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)