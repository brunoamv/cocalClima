"""
Payment-related views using PaymentService.

Extracted from core/views.py following Single Responsibility Principle.
Handles payment callbacks and user-facing payment flows.
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from core.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


def create_payment(request):
    """Create MercadoPago payment preference."""
    payment_service = PaymentService()
    
    init_point = payment_service.create_preference(
        title="Único acesso de 3 minutos a transmissão ao vivo",
        price=3.00
    )
    
    if init_point:
        return JsonResponse({"init_point": init_point})
    else:
        return JsonResponse({
            "error": "Failed to create MercadoPago payment"
        }, status=400)


def payment_success(request):
    """Handle successful payment callback."""
    payment_service = PaymentService()
    payment_service.set_payment_status("approved")
    return render(request, "payment_success.html")


def test_payment_success(request):
    """
    Test endpoint to simulate approved payment.
    Allows testing success page without going through MercadoPago.
    """
    payment_service = PaymentService()
    payment_service.set_payment_status("approved")
    return render(request, "payment_success.html")


def test_payment_direct(request):
    """
    Direct access to test page with valid payment state.
    For camera/streaming development testing.
    
    IMPORTANT: This endpoint simulates approved payment for testing.
    """
    # Set correct payment status for testing
    payment_service = PaymentService()
    payment_service.set_payment_status("approved", timeout=600)
    
    # Log for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"TEST PAYMENT DIRECT accessed from {request.META.get('REMOTE_ADDR')} - This should NOT affect production flow")
    
    context = {
        'test_mode': True,
        'message': 'MODO TESTE - Pagamento simulado (NÃO afeta fluxo normal)',
        'warning': 'Este é um endpoint de teste. Use apenas para desenvolvimento.'
    }
    return render(request, "payment_success.html", context)


def payment_failure(request):
    """Handle payment failure callback."""
    payment_service = PaymentService()
    payment_service.set_payment_status("failure")
    
    # Log parameters for debugging ECH certificate issues
    logger.info(f"Payment failure callback - Query params: {request.GET}")
    logger.info(f"Payment failure callback - Headers: {dict(request.headers)}")
    
    return render(request, "payment_failure.html")


def payment_failure_safe(request):
    """
    Alternative payment failure route to handle ECH certificate issues.
    This route has additional SSL/TLS safety measures.
    """
    payment_service = PaymentService()
    payment_service.set_payment_status("failure")
    
    # Log parameters for debugging
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
    """Handle MercadoPago webhook notifications."""
    try:
        data = json.loads(request.body)
        payment_service = PaymentService()
        
        if payment_service.validate_webhook(data):
            logger.info(f"Payment webhook processed successfully: {data}")
        
        return JsonResponse({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error processing payment webhook: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=400)