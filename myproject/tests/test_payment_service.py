"""
Tests for PaymentService extracted from core/views.py
Following Test-Driven Development practices.
"""

import json
from unittest.mock import Mock, patch
from django.test import TestCase
from django.core.cache import cache
from django.conf import settings

from core.services.payment_service import PaymentService


class PaymentServiceTest(TestCase):
    
    def setUp(self):
        cache.clear()
        self.payment_service = PaymentService()
    
    def tearDown(self):
        cache.clear()
    
    @patch('mercadopago.SDK')
    def test_create_preference_success(self, mock_sdk):
        """Test successful payment preference creation"""
        # Arrange
        mock_sdk_instance = Mock()
        mock_sdk.return_value = mock_sdk_instance
        mock_preference = Mock()
        mock_sdk_instance.preference.return_value = mock_preference
        mock_preference.create.return_value = {
            'response': {'init_point': 'https://test.mercadopago.com/checkout'}
        }
        
        # Act
        result = self.payment_service.create_preference(
            title="Teste acesso 3 minutos",
            price=3.00
        )
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn('init_point', result)
        self.assertEqual(result['init_point'], 'https://test.mercadopago.com/checkout')
        mock_preference.create.assert_called_once()
    
    @patch('mercadopago.SDK')
    def test_create_preference_failure(self, mock_sdk):
        """Test payment preference creation failure"""
        # Arrange
        mock_sdk_instance = Mock()
        mock_sdk.return_value = mock_sdk_instance
        mock_preference = Mock()
        mock_sdk_instance.preference.return_value = mock_preference
        mock_preference.create.return_value = {
            'error': 'Invalid credentials'
        }
        
        # Act
        result = self.payment_service.create_preference(
            title="Teste acesso 3 minutos", 
            price=3.00
        )
        
        # Assert
        self.assertIsNone(result)
    
    def test_validate_webhook_success(self):
        """Test webhook validation for payment created"""
        # Arrange
        webhook_data = {
            "action": "payment.created",
            "data": {"id": "12345"}
        }
        
        # Act
        result = self.payment_service.validate_webhook(webhook_data)
        
        # Assert
        self.assertTrue(result)
        status = cache.get("payment_status")
        self.assertEqual(status, "approved")
    
    def test_validate_webhook_invalid_action(self):
        """Test webhook validation for invalid action"""
        # Arrange
        webhook_data = {
            "action": "payment.updated", 
            "data": {"id": "12345"}
        }
        
        # Act
        result = self.payment_service.validate_webhook(webhook_data)
        
        # Assert
        self.assertFalse(result)
        status = cache.get("payment_status", "pending")
        self.assertEqual(status, "pending")
    
    def test_set_payment_status(self):
        """Test setting payment status in cache"""
        # Act
        self.payment_service.set_payment_status("approved", timeout=300)
        
        # Assert
        status = cache.get("payment_status")
        self.assertEqual(status, "approved")
    
    def test_get_payment_status_default(self):
        """Test getting payment status with default value"""
        # Act
        status = self.payment_service.get_payment_status()
        
        # Assert
        self.assertEqual(status, "pending")
    
    def test_get_payment_status_cached(self):
        """Test getting payment status from cache"""
        # Arrange
        cache.set("payment_status", "approved", timeout=600)
        
        # Act
        status = self.payment_service.get_payment_status()
        
        # Assert
        self.assertEqual(status, "approved")
    
    def test_get_preference_data_structure(self):
        """Test preference data structure matches MercadoPago requirements"""
        # Act
        preference_data = self.payment_service._get_preference_data(
            title="Teste acesso",
            price=3.00
        )
        
        # Assert
        self.assertIn('items', preference_data)
        self.assertIn('payer', preference_data)
        self.assertIn('back_urls', preference_data)
        self.assertIn('auto_return', preference_data)
        
        # Check items structure
        items = preference_data['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['title'], "Teste acesso")
        self.assertEqual(items[0]['unit_price'], 3.00)
        self.assertEqual(items[0]['quantity'], 1)
        self.assertEqual(items[0]['currency_id'], "BRL")
        
        # Check back URLs
        back_urls = preference_data['back_urls']
        self.assertIn('success', back_urls)
        self.assertIn('failure', back_urls)