"""
TDD Test Suite for Camera Streaming Views
Comprehensive test coverage for streaming API endpoints and views
"""
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import Http404

from streaming.views import CameraStreamView, CameraSegmentView
from streaming.services import camera_service, payment_service


class CameraStreamViewTest(TestCase):
    """Test Camera Stream View (HLS Playlist)"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.temp_dir = tempfile.mkdtemp()
        cache.clear()
        
        # Mock stream output directory
        self.original_stream_dir = camera_service.stream_output_dir
        camera_service.stream_output_dir = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        cache.clear()
        camera_service.stream_output_dir = self.original_stream_dir
    
    def test_stream_access_without_payment(self):
        """Test stream access denied without payment"""
        # Act
        response = self.client.get('/streaming/camera/stream.m3u8')
        
        # Assert
        self.assertEqual(response.status_code, 403)
        self.assertIn('Acesso negado', response.content.decode())
        self.assertIn('Pagamento necessário', response.content.decode())
    
    def test_stream_access_with_payment_no_playlist(self):
        """Test stream access with payment but no playlist available"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        # Act
        response = self.client.get('/streaming/camera/stream.m3u8')
        
        # Assert
        self.assertEqual(response.status_code, 503)
        self.assertIn('temporariamente indisponível', response.content.decode())
    
    def test_stream_access_success(self):
        """Test successful stream access with payment and playlist"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        # Create mock playlist
        playlist_path = Path(self.temp_dir) / 'stream.m3u8'
        playlist_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:3
#EXTINF:3.0,
segment_001.ts
#EXTINF:3.0,
segment_002.ts
"""
        playlist_path.write_text(playlist_content)
        
        # Act
        response = self.client.get('/streaming/camera/stream.m3u8')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.apple.mpegurl')
        self.assertEqual(response['Cache-Control'], 'no-cache, no-store, must-revalidate')
        self.assertEqual(response['Access-Control-Allow-Origin'], '*')
        self.assertIn('#EXTM3U', response.content.decode())
    
    def test_stream_playlist_file_not_found(self):
        """Test playlist file not found error"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        # Mock status to indicate playlist available (but file doesn't exist)
        with patch('streaming.services.camera_service.get_status') as mock_status:
            mock_status.return_value = {'playlist_available': True}
            
            # Act
            response = self.client.get('/streaming/camera/stream.m3u8')
            
            # Assert
            self.assertEqual(response.status_code, 404)
    
    def test_stream_internal_error(self):
        """Test internal error during playlist serving"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        # Create playlist but simulate file read error
        playlist_path = Path(self.temp_dir) / 'stream.m3u8'
        playlist_path.write_text('test')
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with patch('streaming.services.camera_service.get_status') as mock_status:
                mock_status.return_value = {'playlist_available': True}
                
                # Act
                response = self.client.get('/streaming/camera/stream.m3u8')
                
                # Assert
                self.assertEqual(response.status_code, 500)
                self.assertIn('Erro interno', response.content.decode())


class CameraSegmentViewTest(TestCase):
    """Test Camera Segment View (HLS Segments)"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.temp_dir = tempfile.mkdtemp()
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        cache.clear()
    
    def test_segment_access_without_payment(self):
        """Test segment access denied without payment"""
        # Act
        response = self.client.get('/streaming/camera/segment_001.ts')
        
        # Assert
        self.assertEqual(response.status_code, 404)
    
    def test_segment_access_invalid_name(self):
        """Test segment access with invalid name"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        # Act - Test path traversal attempt
        response = self.client.get('/streaming/camera/../../../etc/passwd')
        
        # Assert
        self.assertEqual(response.status_code, 404)
    
    def test_segment_access_non_ts_file(self):
        """Test segment access with non-ts file"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        # Act
        response = self.client.get('/streaming/camera/segment_001.mp4')
        
        # Assert
        self.assertEqual(response.status_code, 404)
    
    def test_segment_not_found(self):
        """Test segment file not found"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        # Act
        response = self.client.get('/streaming/camera/nonexistent.ts')
        
        # Assert
        self.assertEqual(response.status_code, 404)
    
    def test_segment_access_success(self):
        """Test successful segment access"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        # Create mock segment file
        segment_path = Path(self.temp_dir) / 'segment_001.ts'
        segment_content = b'\x00\x01\x02\x03'  # Mock video data
        segment_path.write_bytes(segment_content)
        
        with patch('pathlib.Path') as mock_path:
            mock_segment = Mock()
            mock_segment.exists.return_value = True
            mock_segment.stat.return_value.st_size = len(segment_content)
            mock_path.return_value = mock_segment
            
            with patch('builtins.open', mock_open_binary(segment_content)):
                # Act
                response = self.client.get('/streaming/camera/segment_001.ts')
                
                # Assert
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Content-Type'], 'video/mp2t')
                self.assertEqual(response['Cache-Control'], 'public, max-age=3600')
                self.assertEqual(response['Access-Control-Allow-Origin'], '*')


def mock_open_binary(content):
    """Helper function to mock binary file opening"""
    from unittest.mock import mock_open
    return mock_open(read_data=content)


class CameraStatusAPITest(TestCase):
    """Test Camera Status API"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        cache.clear()
    
    def test_status_api_no_payment(self):
        """Test status API without payment"""
        # Act
        response = self.client.get('/streaming/api/status/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertFalse(data['access_granted'])
        self.assertEqual(data['payment_status'], 'pending')
        self.assertIsNone(data['stream_url'])
        self.assertIn('Pagamento necessário', data['message'])
    
    def test_status_api_with_payment_camera_offline(self):
        """Test status API with payment but camera offline"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        with patch('streaming.services.camera_service.get_status') as mock_status:
            mock_status.return_value = {
                'camera_status': 'offline',
                'streaming_status': 'stopped',
                'is_streaming': False,
                'process_active': False,
                'playlist_available': False
            }
            
            # Act
            response = self.client.get('/streaming/api/status/')
            
            # Assert
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            
            self.assertFalse(data['access_granted'])
            self.assertEqual(data['payment_status'], 'approved')
            self.assertFalse(data['camera_available'])
            self.assertIsNone(data['stream_url'])
    
    def test_status_api_full_access(self):
        """Test status API with full access granted"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        with patch('streaming.services.camera_service.get_status') as mock_status:
            mock_status.return_value = {
                'camera_status': 'online',
                'streaming_status': 'active',
                'is_streaming': True,
                'process_active': True,
                'playlist_available': True
            }
            
            # Act
            response = self.client.get('/streaming/api/status/')
            
            # Assert
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            
            self.assertTrue(data['access_granted'])
            self.assertEqual(data['payment_status'], 'approved')
            self.assertTrue(data['camera_available'])
            self.assertEqual(data['stream_url'], '/streaming/camera/stream.m3u8')
            self.assertIn('Acesso liberado', data['message'])


class StreamingControlAPITest(TestCase):
    """Test Streaming Control APIs"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='user',
            password='testpass'
        )
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        cache.clear()
    
    def test_start_streaming_unauthorized(self):
        """Test start streaming without authorization"""
        # Act
        response = self.client.post('/streaming/api/start/')
        
        # Assert
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Unauthorized')
    
    def test_start_streaming_with_payment(self):
        """Test start streaming with valid payment"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        with patch('streaming.services.camera_service.start_streaming') as mock_start:
            mock_start.return_value = True
            
            with patch('streaming.services.camera_service.get_status') as mock_status:
                mock_status.return_value = {'is_streaming': True}
                
                # Act
                response = self.client.post('/streaming/api/start/')
                
                # Assert
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.content)
                self.assertTrue(data['success'])
    
    def test_start_streaming_admin_user(self):
        """Test start streaming as admin user"""
        # Arrange
        self.client.force_login(self.admin_user)
        
        with patch('streaming.services.camera_service.start_streaming') as mock_start:
            mock_start.return_value = True
            
            with patch('streaming.services.camera_service.get_status') as mock_status:
                mock_status.return_value = {'is_streaming': True}
                
                # Act
                response = self.client.post('/streaming/api/start/')
                
                # Assert
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.content)
                self.assertTrue(data['success'])
    
    def test_start_streaming_already_active(self):
        """Test start streaming when already active"""
        # Arrange
        self.client.force_login(self.admin_user)
        
        with patch('streaming.services.camera_service.is_streaming', True):
            with patch('streaming.services.camera_service.get_status') as mock_status:
                mock_status.return_value = {'is_streaming': True}
                
                # Act
                response = self.client.post('/streaming/api/start/')
                
                # Assert
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.content)
                self.assertTrue(data['success'])
                self.assertIn('already active', data['message'])
    
    def test_start_streaming_failure(self):
        """Test start streaming failure"""
        # Arrange
        self.client.force_login(self.admin_user)
        
        with patch('streaming.services.camera_service.start_streaming') as mock_start:
            mock_start.return_value = False
            
            # Act
            response = self.client.post('/streaming/api/start/')
            
            # Assert
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertFalse(data['success'])
    
    def test_stop_streaming_unauthorized(self):
        """Test stop streaming without admin privileges"""
        # Act
        response = self.client.post('/streaming/api/stop/')
        
        # Assert
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Unauthorized')
    
    def test_stop_streaming_regular_user(self):
        """Test stop streaming as regular user"""
        # Arrange
        self.client.force_login(self.regular_user)
        
        # Act
        response = self.client.post('/streaming/api/stop/')
        
        # Assert
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_stop_streaming_admin_success(self):
        """Test successful stop streaming as admin"""
        # Arrange
        self.client.force_login(self.admin_user)
        
        with patch('streaming.services.camera_service.stop_streaming') as mock_stop:
            mock_stop.return_value = True
            
            with patch('streaming.services.camera_service.get_status') as mock_status:
                mock_status.return_value = {'is_streaming': False}
                
                # Act
                response = self.client.post('/streaming/api/stop/')
                
                # Assert
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.content)
                self.assertTrue(data['success'])


class HealthCheckAPITest(TestCase):
    """Test Health Check API"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        cache.clear()
    
    def test_health_check_healthy(self):
        """Test health check when system is healthy"""
        # Arrange
        with patch('streaming.services.camera_service.get_status') as mock_status:
            mock_status.return_value = {
                'camera_status': 'online',
                'is_streaming': True,
                'process_active': True
            }
            
            # Act
            response = self.client.get('/streaming/api/health/')
            
            # Assert
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['healthy'])
            self.assertIn('services', data)
    
    def test_health_check_unhealthy(self):
        """Test health check when system is unhealthy"""
        # Arrange
        with patch('streaming.services.camera_service.get_status') as mock_status:
            mock_status.return_value = {
                'camera_status': 'error',
                'is_streaming': True,
                'process_active': False  # Process should be active but isn't
            }
            
            # Act
            response = self.client.get('/streaming/api/health/')
            
            # Assert
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.content)
            self.assertFalse(data['healthy'])


class LegacyCompatibilityTest(TestCase):
    """Test Legacy URL Compatibility"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        cache.clear()
    
    def tearDown(self):
        """Clean up test environment"""
        cache.clear()
    
    def test_legacy_stream_url(self):
        """Test legacy stream URL redirects properly"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        # Act
        response = self.client.get('/streaming/camera/stream/')
        
        # Assert
        # Should behave the same as new URL (but might return 503 due to no playlist)
        self.assertIn(response.status_code, [403, 503])
    
    def test_legacy_segment_url(self):
        """Test legacy segment URL redirects properly"""
        # Arrange
        cache.set('payment_status', 'approved', timeout=600)
        
        # Act
        response = self.client.get('/streaming/camera/segment/segment_001.ts')
        
        # Assert
        self.assertEqual(response.status_code, 404)  # File doesn't exist


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['tests.test_streaming_views'])
    
    if failures:
        exit(1)