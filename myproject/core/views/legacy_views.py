"""
Legacy views for backward compatibility.

These views should be gradually migrated to the streaming app.
Marked for deprecation and eventual removal.
"""

import os
import mimetypes
from django.http import HttpResponse, StreamingHttpResponse, Http404, JsonResponse
from django.core.cache import cache

from core.services.payment_service import PaymentService


def camera_stream(request):
    """
    Serve camera HLS stream only for paid users.
    
    DEPRECATED: This should be moved to streaming app.
    """
    # Check payment status (using PaymentService)
    payment_service = PaymentService()
    payment_status = payment_service.get_payment_status()
    
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
    """
    Serve HLS segments (protected by payment).
    
    DEPRECATED: This should be moved to streaming app.
    """
    # Check payment status (using PaymentService)
    payment_service = PaymentService()
    payment_status = payment_service.get_payment_status()
    
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
    """
    API to check camera availability and payment status.
    
    DEPRECATED: This should be moved to streaming app.
    """
    payment_service = PaymentService()
    payment_status = payment_service.get_payment_status()
    camera_available = os.path.exists("/app/camera_stream/stream.m3u8")
    
    return JsonResponse({
        "camera_available": camera_available,
        "payment_status": payment_status,
        "access_granted": payment_status == "approved" and camera_available,
        "message": _get_access_message(payment_status, camera_available),
        "stream_url": "/camera/stream.m3u8" if payment_status == "approved" and camera_available else None
    })


def _get_access_message(payment_status, camera_available):
    """
    Get user-friendly access message.
    
    DEPRECATED: This should be moved to streaming app.
    """
    if payment_status != "approved":
        return "💳 Pagamento necessário para acessar câmera ao vivo"
    elif not camera_available:
        return "📷 Câmera temporariamente indisponível"
    else:
        return "✅ Acesso liberado - transmissão ao vivo disponível"