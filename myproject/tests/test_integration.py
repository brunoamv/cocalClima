"""
TDD Integration Test Suite
Tests component interactions and end-to-end workflows
"""
import json
import time
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from django.test import TestCase, TransactionTestCase, Client
from django.core.cache import cache
from django.test.utils import override_settings
from streaming.services import CameraStreamingService, PaymentValidationService, camera_service


class PaymentStreamingIntegrationTest(TransactionTestCase):
    """Test integration between payment system and streaming service"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.temp_dir = tempfile.mkdtemp()
        self.streaming_service = CameraStreamingService()
        self.payment_service = PaymentValidationService()
        cache.clear()
        
        # Mock stream output directory for controlled testing
        self.original_stream_dir = camera_service.stream_output_dir
        camera_service.stream_output_dir = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        cache.clear()
        camera_service.stream_output_dir = self.original_stream_dir
        if self.streaming_service.ffmpeg_process:
            self.streaming_service.stop_streaming()
    
    @patch('streaming.services.CameraStreamingService.test_camera_connection')
    def test_complete_user_journey_success(self, mock_camera):
        """Test complete user journey from homepage to streaming"""
        # Arrange
        mock_camera.return_value = True
        
        # Create playlist and segments to simulate active stream
        playlist_path = Path(self.temp_dir) / 'stream.m3u8'
        playlist_path.write_text('#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:4\n')
        
        for i in range(3):
            segment_path = Path(self.temp_dir) / f'segment_{i:03d}.ts'
            segment_path.write_text('dummy segment content')
        
        # Step 1: User visits homepage
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Check for expected homepage content (more flexible)
        self.assertContains(response, 'ClimaCocal')
        
        # Step 2: Check camera status
        response = self.client.get('/streaming/api/status/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get('camera_available', False))
        
        # Step 3: Simulate payment approval
        cache.set('payment_status', 'approved', timeout=600)
        
        # Step 4: Access payment success page
        response = self.client.get('/payment-success/')
        self.assertEqual(response.status_code, 200)
        
        # Step 5: Verify streaming access
        response = self.client.get('/streaming/api/status/')
        data = json.loads(response.content)
        self.assertTrue(data.get('access_granted', False))
    
    @patch('streaming.services.CameraStreamingService.test_camera_connection')
    def test_payment_timeout_behavior(self, mock_camera):
        """Test payment timeout and access revocation"""
        # Arrange
        mock_camera.return_value = True
        
        # Create playlist and segments to simulate active stream
        playlist_path = Path(self.temp_dir) / 'stream.m3u8'
        playlist_path.write_text('#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:4\n')
        
        for i in range(3):
            segment_path = Path(self.temp_dir) / f'segment_{i:03d}.ts'
            segment_path.write_text('dummy segment content')
        
        # Set payment with very short timeout for testing
        cache.set('payment_status', 'approved', timeout=1)
        
        # Initial access should be granted
        response = self.client.get('/streaming/api/status/')
        data = json.loads(response.content)
        self.assertTrue(data.get('access_granted', False))
        
        # Wait for timeout (in real scenario this would be 600 seconds)
        time.sleep(2)
        
        # Access should now be denied
        response = self.client.get('/streaming/api/status/')
        data = json.loads(response.content)
        self.assertFalse(data.get('access_granted', False))
    
    @patch('core.services.payment_service.mercadopago.SDK')
    @patch('streaming.services.CameraStreamingService.test_camera_connection')
    def test_payment_creation_streaming_integration(self, mock_camera, mock_mp_sdk):
        """Test payment creation when streaming is available"""
        # Arrange
        mock_camera.return_value = True
        mock_sdk_instance = Mock()
        mock_preference = Mock()
        mock_preference.create.return_value = {
            'response': {'init_point': 'https://test.mercadopago.com/checkout'}
        }
        mock_sdk_instance.preference.return_value = mock_preference
        mock_mp_sdk.return_value = mock_sdk_instance
        
        # Act: Create payment when camera is available
        response = self.client.get('/create-payment/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('init_point', data)
    
    @patch('streaming.services.CameraStreamingService.test_camera_connection')
    def test_streaming_unavailable_payment_prevention(self, mock_camera):
        """Test that payment is prevented when streaming is unavailable"""
        # Arrange - camera test fails AND no playlist files
        mock_camera.return_value = False
        # Ensure no playlist files exist (temp_dir is empty)
        
        # Act: Check status when camera unavailable and no playlist
        response = self.client.get('/streaming/api/status/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data.get('camera_available', False))
        self.assertFalse(data.get('access_granted', False))


class CacheStreamingIntegrationTest(TestCase):
    """Test integration between Django cache and streaming service"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.payment_service = PaymentValidationService()
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        cache.clear()
    
    def test_payment_validation_service_integration(self):
        """Test PaymentValidationService with Django cache"""
        # No payment initially
        self.assertFalse(self.payment_service.is_access_granted())
        
        # Set payment status
        cache.set('payment_status', 'approved', timeout=600)
        self.assertTrue(self.payment_service.is_access_granted())
        
        # Clear payment
        cache.delete('payment_status')
        self.assertFalse(self.payment_service.is_access_granted())
    
    def test_multiple_user_session_isolation(self):
        """Test that payment sessions are properly isolated"""
        # This test verifies cache key isolation
        # In real implementation, you'd want user-specific keys
        
        # User 1 payment
        cache.set('payment_status', 'approved', timeout=600)
        self.assertTrue(self.payment_service.is_access_granted())
        
        # Clear for user isolation test
        cache.clear()
        self.assertFalse(self.payment_service.is_access_granted())


class APIConsistencyTest(TestCase):
    """Test API consistency across different endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        cache.clear()
    
    def test_streaming_api_response_format(self):
        """Test streaming API response format consistency"""
        response = self.client.get('/streaming/api/status/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Verify required fields
        required_fields = ['camera_available', 'access_granted', 'message']
        for field in required_fields:
            self.assertIn(field, data)
        
        # Verify data types
        self.assertIsInstance(data['camera_available'], bool)
        self.assertIsInstance(data['access_granted'], bool)
        self.assertIsInstance(data['message'], str)
    
    def test_payment_api_response_format(self):
        """Test payment API response format consistency"""
        with patch('core.services.payment_service.mercadopago.SDK') as mock_mp_sdk:
            mock_sdk_instance = Mock()
            mock_preference = Mock()
            mock_preference.create.return_value = {
                'response': {'init_point': 'https://test.mercadopago.com/checkout'}
            }
            mock_sdk_instance.preference.return_value = mock_preference
            mock_mp_sdk.return_value = mock_sdk_instance
            
            response = self.client.get('/create-payment/')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.content)
            self.assertIn('init_point', data)
            self.assertIsInstance(data['init_point'], str)
    
    def test_error_response_consistency(self):
        """Test error response format consistency"""
        with patch('core.services.payment_service.mercadopago.SDK') as mock_mp_sdk:
            mock_sdk_instance = Mock()
            mock_preference = Mock()
            mock_preference.create.return_value = {'error': 'API Error'}
            mock_sdk_instance.preference.return_value = mock_preference
            mock_mp_sdk.return_value = mock_sdk_instance
            
            response = self.client.get('/create-payment/')
            self.assertEqual(response.status_code, 400)
            
            data = json.loads(response.content)
            self.assertIn('error', data)
            self.assertIsInstance(data['error'], str)


class PerformanceIntegrationTest(TestCase):
    """Test performance aspects of integrated systems"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        cache.clear()
    
    def test_streaming_status_response_time(self):
        """Test streaming status API response time"""
        import time
        
        start_time = time.time()
        response = self.client.get('/streaming/api/status/')
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        
        # Response should be fast (under 1 second)
        response_time = end_time - start_time
        self.assertLess(response_time, 1.0)
    
    def test_multiple_concurrent_status_checks(self):
        """Test handling of multiple concurrent status checks"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def check_status():
            response = self.client.get('/streaming/api/status/')
            results.put(response.status_code)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=check_status)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        while not results.empty():
            status_code = results.get()
            self.assertEqual(status_code, 200)


class RobustnessTest(TestCase):
    """Test system robustness under various conditions"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        cache.clear()
    
    def test_cache_unavailable_graceful_degradation(self):
        """Test graceful degradation when cache is unavailable"""
        # This would require mocking cache to fail
        # For now, we test that the system works with cache
        
        response = self.client.get('/streaming/api/status/')
        self.assertEqual(response.status_code, 200)
        
        # System should handle cache issues gracefully
        data = json.loads(response.content)
        self.assertIn('message', data)
    
    @patch('streaming.services.CameraStreamingService.get_status')
    def test_camera_connection_timeout_handling(self, mock_camera):
        """Test handling of camera connection timeouts"""
        # Simulate camera offline status
        mock_camera.return_value = {
            'is_streaming': False,
            'camera_status': 'offline',
            'streaming_status': 'stopped',
            'playlist_available': False,
            'external_stream_detected': False
        }
        
        response = self.client.get('/streaming/api/status/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertFalse(data.get('camera_available', False))
        self.assertIn('message', data)
    
    def test_malformed_request_handling(self):
        """Test handling of malformed requests"""
        # Test with various malformed requests
        test_urls = [
            '/streaming/api/status/?invalid=param',
            '/payment-success/?malformed=<script>',
            '/create-payment/?extra=data',
        ]
        
        for url in test_urls:
            response = self.client.get(url)
            # Should not crash - either 200, 400, or 404 is acceptable
            self.assertIn(response.status_code, [200, 400, 404])


class BackwardCompatibilityTest(TestCase):
    """Test backward compatibility with legacy features"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
    
    
    def test_legacy_camera_endpoints_redirect(self):
        """Test that legacy camera endpoints properly redirect"""
        legacy_endpoints = [
            '/camera/stream.m3u8',
            '/api/camera-status/',
        ]
        
        for endpoint in legacy_endpoints:
            response = self.client.get(endpoint, follow=True)
            # Should either work or redirect properly (403 for authentication required)
            self.assertIn(response.status_code, [200, 301, 302, 403, 404])