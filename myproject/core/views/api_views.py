"""
API endpoints using modular services.

Extracted from core/views.py following Single Responsibility Principle.
Provides RESTful API endpoints for payment, weather, and YouTube services.
"""

from django.http import JsonResponse

from core.services.payment_service import PaymentService
from core.services.youtube_service import YouTubeService
from core.services.weather_service import WeatherService


def payment_status(request):
    """Get current payment status API endpoint."""
    payment_service = PaymentService()
    status = payment_service.get_payment_status()
    return JsonResponse({"status": status})


def weather(request):
    """Get current weather data API endpoint."""
    weather_service = WeatherService()
    data = weather_service.get_current_weather()
    
    if data:
        return JsonResponse(data)
    else:
        return JsonResponse({
            "error": "Unable to retrieve weather data"
        }, status=503)


def youtube_live_check(request):
    """Check YouTube live stream status API endpoint."""
    youtube_service = YouTubeService()
    result = youtube_service.check_live_status()
    return JsonResponse(result)


def get_stream_url(request):
    """
    Get stream URL - supports both direct camera and YouTube streaming.
    
    This is a hybrid endpoint that checks multiple stream sources
    and returns the available one with payment validation.
    """
    import os
    
    # Check payment status first
    payment_service = PaymentService()
    payment_status = payment_service.get_payment_status()
    
    if payment_status != "approved":
        return JsonResponse({
            "error": "Pagamento necessário para acessar transmissão."
        }, status=403)
    
    try:
        # Check if direct camera streaming is available
        if os.path.exists("/app/camera_stream/stream.m3u8"):
            return JsonResponse({
                "url": "/camera/stream.m3u8",
                "type": "hls",
                "message": "Transmissão direta da câmera"
            })
        
        # Fallback to YouTube if available
        youtube_service = YouTubeService()
        youtube_status = youtube_service.check_live_status()
        
        if youtube_status.get('live'):
            return JsonResponse({
                "url": youtube_service.get_embed_url(),
                "type": "youtube", 
                "message": "Transmissão via YouTube"
            })
        else:
            return JsonResponse({
                "error": "Nenhuma transmissão disponível no momento."
            }, status=503)
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)