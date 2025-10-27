"""
Payment service for MercadoPago integration.

Extracted from core/views.py following Single Responsibility Principle.
Handles payment preference creation, webhook validation, and status management.
"""

import logging
import mercadopago
from django.conf import settings
from django.core.cache import cache
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for handling MercadoPago payment operations."""
    
    def __init__(self):
        """Initialize PaymentService with MercadoPago SDK."""
        self.sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
    
    def create_preference(self, title: str, price: float) -> Optional[str]:
        """
        Create MercadoPago payment preference.
        
        Args:
            title: Payment item title
            price: Payment amount in BRL
            
        Returns:
            Payment init_point URL if successful, None otherwise
        """
        try:
            preference_data = self._get_preference_data(title, price)
            preference_response = self.sdk.preference().create(preference_data)
            
            if ("response" in preference_response and 
                "init_point" in preference_response["response"]):
                return preference_response["response"]["init_point"]
            else:
                logger.error(f"MercadoPago preference creation failed: {preference_response}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating MercadoPago preference: {e}")
            return None
    
    def validate_webhook(self, data: Dict[str, Any]) -> bool:
        """
        Validate MercadoPago webhook data and update payment status.
        
        Args:
            data: Webhook payload data
            
        Returns:
            True if payment created webhook, False otherwise
        """
        try:
            if data.get("action") == "payment.created":
                self.set_payment_status("approved")
                logger.info(f"Payment webhook validated: {data.get('data', {}).get('id')}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error validating webhook: {e}")
            return False
    
    def set_payment_status(self, status: str, timeout: int = 180) -> None:
        """
        Set payment status in cache.
        
        Args:
            status: Payment status (approved, failure, pending)
            timeout: Cache timeout in seconds (default: 180 = 3 minutes)
        """
        cache.set("payment_status", status, timeout=timeout)
        logger.info(f"Payment status set to: {status}")
    
    def get_payment_status(self) -> str:
        """
        Get current payment status from cache.
        
        Returns:
            Current payment status (default: 'pending')
        """
        return cache.get("payment_status", "pending")
    
    def _get_preference_data(self, title: str, price: float) -> Dict[str, Any]:
        """
        Build MercadoPago preference data structure.
        
        Args:
            title: Payment item title
            price: Payment amount
            
        Returns:
            Preference data dictionary
        """
        return {
            "items": [{
                "title": title,
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": price
            }],
            "payer": {
                "email": getattr(settings, 'MERCADO_PAGO_PAYER_EMAIL', 'bruno.amv@gmail.com')
            },
            "back_urls": {
                "success": getattr(settings, 'MERCADO_PAGO_SUCCESS_URL', 
                                 'https://climacocal.com.br/payment-success/'),
                "failure": getattr(settings, 'MERCADO_PAGO_FAILURE_URL',
                                 'https://climacocal.com.br/payment-failure-safe/')
            },
            "auto_return": "approved"
        }