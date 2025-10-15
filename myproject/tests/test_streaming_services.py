"""
TDD Test Suite for Camera Streaming Services
Comprehensive test coverage for direct streaming functionality
"""
import os
import tempfile
import shutil
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from django.test import TestCase
from django.core.cache import cache
from django.conf import settings

from streaming.services import CameraStreamingService, PaymentValidationService


class CameraStreamingServiceTest(TestCase):
    """Test Direct Camera Streaming Service"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.service = CameraStreamingService()
        self.service.stream_output_dir = Path(self.temp_dir)
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        cache.clear()
        if self.service.ffmpeg_process:
            self.service.stop_streaming()
    
    def test_service_initialization(self):
        """Test service initializes with correct configuration"""
        self.assertIsNotNone(self.service.rtsp_url)
        self.assertIn('1280x720', self.service.stream_config['resolution'])
        self.assertEqual(self.service.stream_config['fps'], '20')
        self.assertFalse(self.service.is_streaming)
        self.assertIsNone(self.service.ffmpeg_process)
    
    @patch('subprocess.run')
    def test_camera_connection_success(self, mock_run):
        """Test successful camera connection"""
        # Arrange
        mock_run.return_value = Mock(stdout='video\n', returncode=0)
        
        # Act
        result = self.service.test_camera_connection()
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(cache.get('camera_status'), 'online')
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_camera_connection_failure(self, mock_run):
        """Test failed camera connection"""
        # Arrange
        mock_run.return_value = Mock(stdout='', returncode=1)
        
        # Act
        result = self.service.test_camera_connection()
        
        # Assert
        self.assertFalse(result)
        self.assertEqual(cache.get('camera_status'), 'offline')
    
    @patch('subprocess.run')
    def test_camera_connection_timeout(self, mock_run):
        """Test camera connection timeout"""
        # Arrange
        mock_run.side_effect = subprocess.TimeoutExpired('ffprobe', 10)
        
        # Act
        result = self.service.test_camera_connection()
        
        # Assert
        self.assertFalse(result)
        self.assertEqual(cache.get('camera_status'), 'error')
    
    def test_ffmpeg_command_generation(self):
        """Test FFmpeg command generation"""
        # Act
        cmd = self.service.get_ffmpeg_command()
        
        # Assert
        self.assertIn('ffmpeg', cmd)
        self.assertIn('-rtsp_transport', cmd)
        self.assertIn('tcp', cmd)
        self.assertIn('-c:v', cmd)
        self.assertIn('libx264', cmd)
        self.assertIn('-f', cmd)
        self.assertIn('hls', cmd)
        self.assertIn(self.service.rtsp_url, cmd)
    
    @patch('streaming.services.CameraStreamingService.test_camera_connection')
    @patch('subprocess.Popen')
    def test_start_streaming_success(self, mock_popen, mock_camera_test):
        """Test successful streaming start"""
        # Arrange
        mock_camera_test.return_value = True
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        # Act
        result = self.service.start_streaming()
        
        # Assert
        self.assertTrue(result)
        self.assertTrue(self.service.is_streaming)
        self.assertEqual(self.service.ffmpeg_process, mock_process)
        self.assertEqual(cache.get('streaming_status'), 'active')
    
    @patch('streaming.services.CameraStreamingService.test_camera_connection')
    def test_start_streaming_camera_unavailable(self, mock_camera_test):
        """Test streaming start when camera unavailable"""
        # Arrange
        mock_camera_test.return_value = False
        
        # Act
        result = self.service.start_streaming()
        
        # Assert
        self.assertFalse(result)
        self.assertFalse(self.service.is_streaming)
        self.assertIsNone(self.service.ffmpeg_process)
    
    def test_start_streaming_already_active(self):
        """Test starting streaming when already active"""
        # Arrange
        self.service.is_streaming = True
        
        # Act
        result = self.service.start_streaming()
        
        # Assert
        self.assertTrue(result)
    
    @patch('subprocess.Popen')
    def test_start_streaming_ffmpeg_failure(self, mock_popen):
        """Test streaming start when FFmpeg fails"""
        # Arrange
        mock_popen.side_effect = OSError("FFmpeg not found")
        
        with patch.object(self.service, 'test_camera_connection', return_value=True):
            # Act
            result = self.service.start_streaming()
            
            # Assert
            self.assertFalse(result)
            self.assertFalse(self.service.is_streaming)
    
    def test_stop_streaming_not_active(self):
        """Test stopping streaming when not active"""
        # Act
        result = self.service.stop_streaming()
        
        # Assert
        self.assertTrue(result)
    
    @patch('streaming.services.CameraStreamingService._cleanup_stream_files')
    def test_stop_streaming_success(self, mock_cleanup):
        """Test successful streaming stop"""
        # Arrange
        mock_process = Mock()
        mock_process.wait.return_value = None
        self.service.ffmpeg_process = mock_process
        self.service.is_streaming = True
        
        # Act
        result = self.service.stop_streaming()
        
        # Assert
        self.assertTrue(result)
        self.assertFalse(self.service.is_streaming)
        self.assertIsNone(self.service.ffmpeg_process)
        mock_process.terminate.assert_called_once()
        mock_cleanup.assert_called_once()
        self.assertEqual(cache.get('streaming_status'), 'stopped')
    
    @patch('streaming.services.CameraStreamingService._cleanup_stream_files')
    def test_stop_streaming_force_kill(self, mock_cleanup):
        """Test streaming stop with force kill"""
        # Arrange
        mock_process = Mock()
        mock_process.wait.side_effect = [subprocess.TimeoutExpired('ffmpeg', 5), None]
        self.service.ffmpeg_process = mock_process
        self.service.is_streaming = True
        
        # Act
        result = self.service.stop_streaming()
        
        # Assert
        self.assertTrue(result)
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()
    
    def test_cleanup_stream_files(self):
        """Test stream files cleanup"""
        # Arrange
        test_file = self.service.stream_output_dir / 'test_segment.ts'
        test_file.write_text('test content')
        
        # Act
        self.service._cleanup_stream_files()
        
        # Assert
        self.assertFalse(test_file.exists())
    
    def test_get_status_streaming_active(self):
        """Test status when streaming is active"""
        # Arrange
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process running
        self.service.ffmpeg_process = mock_process
        self.service.is_streaming = True
        cache.set('camera_status', 'online')
        cache.set('streaming_status', 'active')
        
        # Create playlist file
        playlist_path = self.service.stream_output_dir / 'stream.m3u8'
        playlist_path.write_text('#EXTM3U\n')
        
        # Act
        status = self.service.get_status()
        
        # Assert
        self.assertTrue(status['is_streaming'])
        self.assertEqual(status['camera_status'], 'online')
        self.assertEqual(status['streaming_status'], 'active')
        self.assertTrue(status['playlist_available'])
        self.assertTrue(status['process_active'])
    
    def test_get_status_streaming_inactive(self):
        """Test status when streaming is inactive"""
        # Act
        status = self.service.get_status()
        
        # Assert
        self.assertFalse(status['is_streaming'])
        self.assertEqual(status['camera_status'], 'unknown')
        self.assertEqual(status['streaming_status'], 'stopped')
        self.assertFalse(status['playlist_available'])
        self.assertFalse(status['process_active'])


class PaymentValidationServiceTest(TestCase):
    """Test Payment Validation Service"""
    
    def setUp(self):
        """Set up test environment"""
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        cache.clear()
    
    def test_check_payment_status_pending(self):
        """Test payment status check when pending"""
        # Act
        status = PaymentValidationService.check_payment_status()
        
        # Assert
        self.assertEqual(status, 'pending')
    
    def test_check_payment_status_approved(self):
        """Test payment status check when approved"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        # Act
        status = PaymentValidationService.check_payment_status()
        
        # Assert
        self.assertEqual(status, 'approved')
    
    def test_is_access_granted_true(self):
        """Test access granted when payment approved"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        # Act
        access = PaymentValidationService.is_access_granted()
        
        # Assert
        self.assertTrue(access)
    
    def test_is_access_granted_false(self):
        """Test access denied when payment pending"""
        # Act
        access = PaymentValidationService.is_access_granted()
        
        # Assert
        self.assertFalse(access)
    
    def test_get_access_message_payment_required(self):
        """Test access message when payment required"""
        # Act
        message = PaymentValidationService.get_access_message('pending', True)
        
        # Assert
        self.assertIn('Pagamento necessário', message)
        self.assertIn('💳', message)
    
    def test_get_access_message_camera_unavailable(self):
        """Test access message when camera unavailable"""
        # Act
        message = PaymentValidationService.get_access_message('approved', False)
        
        # Assert
        self.assertIn('Câmera temporariamente indisponível', message)
        self.assertIn('📷', message)
    
    def test_get_access_message_access_granted(self):
        """Test access message when access granted"""
        # Act
        message = PaymentValidationService.get_access_message('approved', True)
        
        # Assert
        self.assertIn('Acesso liberado', message)
        self.assertIn('✅', message)
    
    def test_set_payment_status(self):
        """Test setting payment status"""
        # Act
        PaymentValidationService.set_payment_status('approved', 300)
        
        # Assert
        self.assertEqual(cache.get('payment_status'), 'approved')
    
    def test_payment_status_expiration(self):
        """Test payment status expiration"""
        # Arrange
        PaymentValidationService.set_payment_status('approved', 1)
        
        # Act & Assert
        self.assertEqual(cache.get('payment_status'), 'approved')
        
        # Wait for expiration (in real test, use time manipulation)
        import time
        time.sleep(2)
        
        # Payment should have expired
        self.assertEqual(PaymentValidationService.check_payment_status(), 'pending')


class StreamingIntegrationTest(TestCase):
    """Integration tests for streaming system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.camera_service = CameraStreamingService()
        self.camera_service.stream_output_dir = Path(self.temp_dir)
        self.payment_service = PaymentValidationService()
        cache.clear()
    
    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        cache.clear()
        if self.camera_service.ffmpeg_process:
            self.camera_service.stop_streaming()
    
    def test_end_to_end_streaming_flow(self):
        """Test complete streaming flow from payment to stream access"""
        # Step 1: No payment - access denied
        self.assertFalse(self.payment_service.is_access_granted())
        
        # Step 2: Payment approved
        self.payment_service.set_payment_status('approved')
        self.assertTrue(self.payment_service.is_access_granted())
        
        # Step 3: Camera available (mock)
        with patch.object(self.camera_service, 'test_camera_connection', return_value=True), \
             patch('subprocess.Popen') as mock_popen:
            
            mock_process = Mock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process
            
            # Start streaming
            success = self.camera_service.start_streaming()
            self.assertTrue(success)
            
            # Create mock playlist
            playlist_path = self.camera_service.stream_output_dir / 'stream.m3u8'
            playlist_path.write_text('#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=2500000\nsegment_001.ts\n')
            
            # Verify streaming status
            status = self.camera_service.get_status()
            self.assertTrue(status['is_streaming'])
            self.assertTrue(status['playlist_available'])
            
            # Verify access granted
            access_message = self.payment_service.get_access_message('approved', True)
            self.assertIn('Acesso liberado', access_message)
    
    def test_payment_expiration_during_streaming(self):
        """Test behavior when payment expires during streaming"""
        # Arrange: Start with valid payment
        self.payment_service.set_payment_status('approved', 1)  # 1 second timeout
        
        # Act: Payment expires
        import time
        time.sleep(2)
        
        # Assert: Access should be denied
        self.assertFalse(self.payment_service.is_access_granted())
        self.assertEqual(self.payment_service.check_payment_status(), 'pending')
    
    def test_camera_failure_during_streaming(self):
        """Test behavior when camera fails during streaming"""
        # Arrange: Valid payment and streaming
        self.payment_service.set_payment_status('approved')
        
        with patch.object(self.camera_service, 'test_camera_connection', return_value=False):
            # Act: Camera becomes unavailable
            camera_available = self.camera_service.test_camera_connection()
            
            # Assert: Camera should be reported as offline
            self.assertFalse(camera_available)
            self.assertEqual(cache.get('camera_status'), 'offline')
    
    def test_concurrent_access_control(self):
        """Test concurrent access scenarios"""
        # Multiple users with payment
        for i in range(3):
            cache.set(f'payment_status_user_{i}', 'approved', timeout=600)
        
        # All should have access if camera is available
        for i in range(3):
            # Simulate different user sessions
            with patch('streaming.services.cache.get', return_value='approved'):
                access = self.payment_service.is_access_granted()
                self.assertTrue(access)


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['tests.test_streaming_services'])
    
    if failures:
        exit(1)