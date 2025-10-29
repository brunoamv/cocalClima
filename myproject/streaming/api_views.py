"""
Enhanced API views for streaming service with climber support.

This module provides API endpoints that properly integrate with both
payment-based access and climber authentication.
"""

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache

from .services import camera_service, payment_service

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@never_cache
def streaming_status(request):
    """
    Enhanced streaming status API that recognizes both payment and climber access.
    
    Returns JSON with access status, user type, and streaming availability.
    """
    
    # Check payment status first
    payment_status = payment_service.check_payment_status()
    has_payment_access = payment_service.is_access_granted()
    
    # Check climber access from session
    climber_id = request.session.get('climber_id')
    climber_name = request.session.get('climber_name')
    climber_access_until = request.session.get('climber_access_until')
    has_climber_access = bool(climber_id)
    
    # Determine overall access and user type
    has_access = has_payment_access or has_climber_access
    user_type = None
    
    if has_climber_access:
        user_type = 'climber'
    elif has_payment_access:
        user_type = 'payment'
    
    # Get camera status
    camera_service.test_camera_connection()
    camera_status = camera_service.get_status()
    
    # Check if streaming is available
    camera_available = camera_status['camera_status'] == 'online'
    playlist_working = camera_status['playlist_available'] and camera_status['process_active']
    
    if playlist_working:
        camera_available = True
        camera_status['camera_status'] = 'online'
    
    # Build response
    response_data = {
        'has_access': has_access,
        'user_type': user_type,
        'payment_status': payment_status,
        'camera_available': camera_available,
        'streaming_active': camera_status['is_streaming'],
        'playlist_available': camera_status['playlist_available'],
        'stream_url': '/streaming/camera/stream.m3u8' if has_access and camera_available else None
    }
    
    # Add climber-specific information if applicable
    if has_climber_access:
        response_data.update({
            'climber_name': climber_name,
            'access_until': climber_access_until,
            'message': f'Acesso liberado para {climber_name} até {climber_access_until}'
        })
    elif has_payment_access:
        response_data['message'] = 'Acesso liberado por pagamento'
    else:
        response_data['message'] = 'Acesso negado. Faça o pagamento ou login como escalador.'
    
    # Add technical details for debugging
    response_data['technical'] = {
        'is_streaming': camera_status['is_streaming'],
        'process_active': camera_status['process_active'],
        'camera_status': camera_status['camera_status'],
        'streaming_status': camera_status['streaming_status']
    }
    
    logger.info(
        f"Streaming status check: user_type={user_type}, "
        f"has_access={has_access}, camera={camera_available}"
    )
    
    return JsonResponse(response_data)