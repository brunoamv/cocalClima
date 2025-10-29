"""
Direct Camera Streaming Views
Enhanced views for camera streaming with payment validation
"""
import os
import time
import mimetypes
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.views import View
from pathlib import Path
import logging

from .services import camera_service, payment_service

logger = logging.getLogger(__name__)


class CameraStreamView(View):
    """Serve camera HLS stream with payment validation"""
    
    @method_decorator(never_cache)
    def get(self, request):
        """Serve HLS playlist for paid users"""
        
        # Check payment status
        if not payment_service.is_access_granted():
            logger.warning(f"Unauthorized camera access attempt from {request.META.get('REMOTE_ADDR')}")
            return HttpResponse(
                "❌ Acesso negado. Pagamento necessário para visualizar câmera ao vivo.",
                status=403,
                content_type="text/plain"
            )
        
        # Check if streaming is active
        status = camera_service.get_status()
        if not status['playlist_available']:
            return HttpResponse(
                "📷 Câmera temporariamente indisponível. Aguarde alguns segundos e tente novamente.",
                status=503,
                content_type="text/plain"
            )
        
        try:
            playlist_path = Path('/app/camera_stream/stream.m3u8')
            
            with open(playlist_path, 'r') as f:
                content = f.read()
            
            response = HttpResponse(content, content_type='application/vnd.apple.mpegurl')
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Headers'] = 'Range'
            
            logger.info(f"Served HLS playlist to authenticated user from {request.META.get('REMOTE_ADDR')}")
            return response
            
        except FileNotFoundError:
            logger.error("HLS playlist file not found")
            return HttpResponse("📷 Playlist não disponível", status=404)
        except Exception as e:
            logger.error(f"Error serving HLS playlist: {e}")
            return HttpResponse(f"❌ Erro interno: {str(e)}", status=500)


class CameraSegmentView(View):
    """Serve HLS segments with payment validation"""
    
    @method_decorator(never_cache)
    def get(self, request, segment_name):
        """Serve HLS video segments for paid users"""
        
        # Check payment status
        if not payment_service.is_access_granted():
            logger.warning(f"Unauthorized segment access attempt: {segment_name} from {request.META.get('REMOTE_ADDR')}")
            raise Http404("Acesso negado")
        
        # Validate segment name to prevent path traversal
        if not segment_name.endswith('.ts') or '/' in segment_name or '..' in segment_name:
            logger.warning(f"Invalid segment name: {segment_name}")
            raise Http404("Segmento inválido")
        
        segment_path = Path(f'/app/camera_stream/{segment_name}')
        
        if not segment_path.exists():
            logger.debug(f"Segment not found: {segment_name}")
            raise Http404("Segmento não encontrado")
        
        try:
            def file_iterator(file_path, chunk_size=8192):
                """Generator for streaming file content"""
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
            
            mime_type, _ = mimetypes.guess_type(str(segment_path))
            response = StreamingHttpResponse(
                file_iterator(segment_path),
                content_type=mime_type or 'video/mp2t'
            )
            
            response['Cache-Control'] = 'public, max-age=3600'  # Cache segments for 1 hour
            response['Access-Control-Allow-Origin'] = '*'
            response['Content-Length'] = segment_path.stat().st_size
            
            logger.debug(f"Served segment: {segment_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error serving segment {segment_name}: {e}")
            raise Http404(f"Erro ao acessar segmento: {str(e)}")


@require_http_methods(["GET"])
@never_cache
def camera_status_api(request):
    """API endpoint for camera and payment status"""
    
    payment_status = payment_service.check_payment_status()
    
    # Force camera test to get fresh status
    camera_service.test_camera_connection()
    camera_status = camera_service.get_status()
    
    # Use FFmpeg HLS streaming instead of YouTube
    camera_available = camera_status['camera_status'] == 'online'
    
    # BYPASS: If playlist is available, camera is working regardless of cache status
    playlist_working = camera_status['playlist_available'] and camera_status.get('external_stream_detected', False)
    if playlist_working:
        camera_available = True
        camera_status['camera_status'] = 'online'
    
    # Use consistent streaming status from service
    streaming_active = camera_status['is_streaming']
    actual_streaming_status = camera_status['streaming_status']
    
    # CRITICAL: Do not grant access if camera is offline
    if not camera_available:
        logger.warning(f"Camera offline - denying payment flow")
        access_granted = False
        stream_url = None
        has_access = False
    else:
        # Check both payment and climber access
        has_access = payment_service.is_access_granted(request)
        access_granted = has_access and camera_available
        stream_url = "/streaming/camera/stream.m3u8" if access_granted else None
    
    # Determine user type for cleaner response
    user_type = "climber" if (request and hasattr(request, 'climber_access') and request.climber_access) else "payment"
    
    response_data = {
        "has_access": has_access,
        "user_type": user_type,
        "payment_status": payment_status,
        "camera_available": camera_available,
        "streaming_active": streaming_active,
        "playlist_available": camera_status['playlist_available'],
        "stream_url": stream_url,
        "message": payment_service.get_access_message(payment_status, camera_available),
        "technical": {
            "is_streaming": streaming_active,
            "process_active": camera_status['process_active'],
            "camera_status": camera_status['camera_status'],
            "streaming_status": actual_streaming_status
        }
    }
    
    logger.info(f"Camera status API called: payment={payment_status}, camera={camera_available}")
    return JsonResponse(response_data)


@require_http_methods(["POST"])
@csrf_exempt
def start_streaming_api(request):
    """API endpoint to start camera streaming"""
    
    # Check if user has admin privileges or valid payment
    if not (request.user.is_staff or payment_service.is_access_granted()):
        return JsonResponse({
            "success": False,
            "error": "Unauthorized",
            "message": "Admin privileges or valid payment required"
        }, status=403)
    
    if camera_service.is_streaming:
        return JsonResponse({
            "success": True,
            "message": "Streaming already active",
            "status": camera_service.get_status()
        })
    
    success = camera_service.start_streaming()
    
    if success:
        logger.info(f"Streaming started by user: {request.user.username if request.user.is_authenticated else 'anonymous'}")
        return JsonResponse({
            "success": True,
            "message": "Streaming started successfully",
            "status": camera_service.get_status()
        })
    else:
        logger.error("Failed to start streaming")
        return JsonResponse({
            "success": False,
            "error": "Failed to start streaming",
            "message": "Could not initialize camera stream"
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def stop_streaming_api(request):
    """API endpoint to stop camera streaming"""
    
    # Check if user has admin privileges
    if not request.user.is_staff:
        return JsonResponse({
            "success": False,
            "error": "Unauthorized",
            "message": "Admin privileges required"
        }, status=403)
    
    if not camera_service.is_streaming:
        return JsonResponse({
            "success": True,
            "message": "Streaming already stopped",
            "status": camera_service.get_status()
        })
    
    success = camera_service.stop_streaming()
    
    if success:
        logger.info(f"Streaming stopped by admin user: {request.user.username}")
        return JsonResponse({
            "success": True,
            "message": "Streaming stopped successfully",
            "status": camera_service.get_status()
        })
    else:
        logger.error("Failed to stop streaming")
        return JsonResponse({
            "success": False,
            "error": "Failed to stop streaming",
            "message": "Could not stop camera stream"
        }, status=500)


@require_http_methods(["GET"])
@never_cache
def health_check(request):
    """Health check endpoint for monitoring"""
    
    camera_status = camera_service.get_status()
    
    # Determine overall health
    healthy = (
        camera_status['camera_status'] in ['online', 'unknown'] and
        (not camera_status['is_streaming'] or camera_status['process_active'])
    )
    
    response_data = {
        "healthy": healthy,
        "timestamp": str(time.time()),
        "services": {
            "camera": camera_status,
            "payment": {
                "service_available": True,  # Payment service is always available
                "cache_available": True     # Django cache is always available
            }
        }
    }
    
    status_code = 200 if healthy else 503
    return JsonResponse(response_data, status=status_code)


# Legacy compatibility - redirect old URLs to new streaming endpoints
def legacy_camera_stream(request):
    """Legacy compatibility for old camera stream URLs"""
    return CameraStreamView.as_view()(request)


def legacy_camera_segment(request, segment_name):
    """Legacy compatibility for old camera segment URLs"""
    return CameraSegmentView.as_view()(request, segment_name)