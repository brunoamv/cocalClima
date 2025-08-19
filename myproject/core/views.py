import mercadopago
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.shortcuts import render, redirect

#MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-5215197145934497-010910-a8f4c879eb5cfbe282fc5b72ef91ddf3-234559853" # ANTIGA

MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-6572778228467438-012815-7995636b4be0f51ec60422f0069b396a-2210813103" # ANTIGA TESTE 

#MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-6307889355339219-070811-052b29ec7cd8b6761b3fd53128543c5f-61367856"
############################Access Token PRD APP_USR-6307889355339219-070811-052b29ec7cd8b6761b3fd53128543c5f-61367856
########## PUBLIC KEY PRD APP_USR-516092f3-91d4-4fe7-849b-55534ef996d2


YOUTUBE_API_KEY = "AIzaSyAfNYAuhX5za5hQpZk3Dx5cesgGULWuVIE"
YOUTUBE_VIDEO_ID = "hVV7SMh-bO0"

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
           "failure": "https://climacocal.com.br/payment-failure/",  # Produção
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

def payment_failure(request):
    # Store that the user has failure paid
    cache.set("payment_status", "failure", timeout=600)
    return render(request, "payment_failure.html")


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