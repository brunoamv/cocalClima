import mercadopago
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.shortcuts import render, redirect

#MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-5215197145934497-010910-a8f4c879eb5cfbe282fc5b72ef91ddf3-234559853"

MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-6572778228467438-012815-7995636b4be0f51ec60422f0069b396a-2210813103"



def home(request):
    return render(request, "index.html")


def create_payment(request):
    sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)

    preference_data = {
        "items": [{
            "title": "YouTube Live Access",
            "quantity": 1,
            "currency_id": "BRL",
            "unit_price": 3.00
        }],
        "payer": {
            # "id": "CompradorTestBruno",  # Use your test user "Identificação da conta"
            "email": "bruno.amv@gmail.com",  # Mercado Pago auto-assigns an email
        },
        "back_urls": {
           # "success": "http://127.0.0.1:8000/payment-success/", ##DEV
            "success": "http://177.47.221.44:8000/payment-success/", ## PROD
           # "failure": "http://13.58.251.9:8000/",
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
    
    # Print full response for debugging
    print("Mercado Pago API Response:", preference_response)

    # Check if init_point exists
    if "response" in preference_response and "init_point" in preference_response["response"]:
        return JsonResponse({"init_point": preference_response["response"]["init_point"]})
    else:
        return JsonResponse({"error": "Failed to create Mercado Pago payment", "details": preference_response}, status=400)


def payment_success(request):
    # Store that the user has successfully paid
    cache.set("payment_status", "approved", timeout=600)
    return render(request, "payment_success.html")



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


# def get_weather(request):
#     import requests
    
#     API_TOKEN = "8309ca82f5db93cbec74e34a65312592"
#     CITY_ID = "cocalzinho-de-goias"
#     url = f"https://apiadvisor.climatempo.com.br/api/v1/weather/locale/{CITY_ID}/current?token={API_TOKEN}"
    
#     response = requests.get(url)
#     data = response.json()
#     return JsonResponse(data)
