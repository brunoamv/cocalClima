"""
Test Suite for Frontend-API Integration
Validates that frontend JavaScript correctly consumes API responses
"""
import json
from django.test import TestCase, Client
from django.core.cache import cache
from unittest.mock import patch


class FrontendAPIIntegrationTest(TestCase):
    """Test frontend JavaScript integration with API responses"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        cache.clear()
    
    def tearDown(self):
        """Clean up after tests"""
        cache.clear()
    
    def test_api_returns_correct_field_names(self):
        """Test that API returns the correct field names expected by frontend"""
        # Set up approved payment
        cache.set('payment_status_test', 'approved', timeout=600)
        
        response = self.client.get('/streaming/api/status/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Critical: These fields MUST match what frontend JavaScript expects
        self.assertIn('has_access', data, "Frontend expects 'has_access' field")
        self.assertIn('stream_url', data, "Frontend expects 'stream_url' field")
        self.assertIn('camera_available', data, "Frontend expects 'camera_available' field")
        self.assertIn('streaming_active', data, "Frontend expects 'streaming_active' field")
        
        # Deprecated fields should NOT be present
        self.assertNotIn('access_granted', data, "Deprecated field 'access_granted' should not exist")
    
    def test_frontend_stream_access_conditions(self):
        """Test conditions under which frontend should show stream vs error"""
        
        # Test Case 1: Valid payment with streaming active
        cache.set('payment_status_approved', 'approved', timeout=600)
        
        response = self.client.get('/streaming/api/status/')
        data = response.json()
        
        # Frontend checks: data.has_access && data.stream_url
        frontend_should_show_stream = data.get('has_access', False) and data.get('stream_url', False)
        
        if data.get('has_access') and data.get('streaming_active'):
            self.assertTrue(frontend_should_show_stream, 
                          f"Frontend should show stream when API returns: {data}")
        
        # Test Case 2: No payment
        cache.clear()
        
        response = self.client.get('/streaming/api/status/')
        data = response.json()
        
        frontend_should_show_stream = data.get('has_access', False) and data.get('stream_url', False)
        
        if not data.get('has_access'):
            self.assertFalse(frontend_should_show_stream,
                           f"Frontend should NOT show stream when no access: {data}")
    
    def test_payment_success_page_javascript_logic(self):
        """Test the specific logic used in payment_success.html"""
        
        # Test valid scenario
        cache.set('payment_status_test', 'approved', timeout=600)
        
        response = self.client.get('/streaming/api/status/')
        data = response.json()
        
        # This is the exact condition from payment_success.html line 299
        # if (data.has_access && data.stream_url) {
        condition_result = data.get('has_access', False) and bool(data.get('stream_url'))
        
        if data.get('streaming_active', False):
            self.assertTrue(condition_result, 
                          f"JavaScript condition should pass with valid payment: {data}")
            self.assertIsNotNone(data.get('stream_url'),
                                "stream_url should be provided when streaming is active")
    
    def test_climber_access_page_javascript_logic(self):
        """Test the specific logic used in climber/access.html"""
        
        # Test valid scenario  
        cache.set('payment_status_climber', 'approved', timeout=600)
        
        response = self.client.get('/streaming/api/status/')
        data = response.json()
        
        # This is the exact condition from climber/access.html
        # if (data.has_access && data.stream_url) {
        condition_result = data.get('has_access', False) and bool(data.get('stream_url'))
        
        if data.get('streaming_active', False):
            self.assertTrue(condition_result,
                          f"Climber page JavaScript condition should pass: {data}")
    
    def test_api_consistent_response_structure(self):
        """Test that API response structure is consistent across different states"""
        
        # Test different payment states
        payment_states = ['approved', 'pending', None]
        
        for state in payment_states:
            with self.subTest(payment_state=state):
                cache.clear()
                if state:
                    cache.set('payment_status_test', state, timeout=600)
                
                response = self.client.get('/streaming/api/status/')
                self.assertEqual(response.status_code, 200)
                
                data = response.json()
                
                # All responses should have these core fields
                required_fields = ['has_access', 'camera_available', 'streaming_active', 'message']
                for field in required_fields:
                    self.assertIn(field, data, f"Field '{field}' missing for payment state: {state}")
                
                # Boolean fields should actually be booleans
                boolean_fields = ['has_access', 'camera_available', 'streaming_active']
                for field in boolean_fields:
                    self.assertIsInstance(data[field], bool, 
                                        f"Field '{field}' should be boolean, got {type(data[field])}")
    
    def test_stream_temporarily_unavailable_message_consistency(self):
        """Test that 'Stream Temporariamente Indisponível' message logic is consistent"""
        
        # Mock streaming as inactive
        with patch('streaming.services.CameraStreamingService.get_status') as mock_status:
            mock_status.return_value = {
                'is_streaming': False,
                'camera_available': False,
                'ffmpeg_process': None
            }
            
            response = self.client.get('/streaming/api/status/')
            data = response.json()
            
            # When streaming is not available, frontend should show error
            frontend_condition = data.get('has_access', False) and bool(data.get('stream_url'))
            
            if not data.get('streaming_active', False):
                self.assertFalse(frontend_condition,
                               "Frontend should show 'temporariamente indisponível' when streaming inactive")


class FrontendErrorMessageTest(TestCase):
    """Test specific error messages and their triggers"""
    
    def test_error_message_triggers(self):
        """Test conditions that should trigger specific error messages"""
        
        test_cases = [
            {
                'name': 'No payment',
                'setup': lambda: cache.clear(),
                'expected_has_access': False,
                'expected_message_contains': 'pagamento'
            },
            {
                'name': 'Payment pending', 
                'setup': lambda: cache.set('payment_status_test', 'pending', timeout=600),
                'expected_has_access': False,
                'expected_message_contains': 'pagamento'
            },
            {
                'name': 'Payment approved',
                'setup': lambda: cache.set('payment_status_test', 'approved', timeout=600),
                'expected_has_access': True,
                'expected_message_contains': 'liberado'
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case['name']):
                case['setup']()
                
                response = self.client.get('/streaming/api/status/')
                data = response.json()
                
                self.assertEqual(data['has_access'], case['expected_has_access'])
                self.assertIn(case['expected_message_contains'], data['message'].lower())


def run_frontend_integration_tests():
    """Helper function to run frontend integration tests"""
    import unittest
    
    suite = unittest.TestLoader().loadTestsFromTestCase(FrontendAPIIntegrationTest)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(FrontendErrorMessageTest))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    run_frontend_integration_tests()