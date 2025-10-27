"""
OBSOLETE YouTube Legacy Tests
These tests have been moved to OLD folder because YouTube functionality 
has been replaced by direct RTSP→HLS streaming.
"""
import json
from unittest.mock import Mock, patch
from django.test import TestCase, Client


class YouTubeLegacyTest(TestCase):
    """Test legacy YouTube functionality (OBSOLETE - moved to direct streaming)"""
    
    def setUp(self):
        """Skip all YouTube tests - functionality replaced by direct streaming"""
        self.skipTest("YouTube functionality obsolete - replaced by direct streaming")
    
    @patch('core.services.weather_service.requests.get')
    def test_youtube_live_check_active(self, mock_get):
        """Test YouTube live check when stream is active"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [{
                'liveStreamingDetails': {
                    'actualStartTime': '2025-10-26T10:00:00Z'
                    # No actualEndTime means still live
                }
            }]
        }
        mock_get.return_value = mock_response
        
        # Act
        response = self.client.get('/check-youtube-live/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['live'])
    
    @patch('core.services.weather_service.requests.get')
    def test_youtube_live_check_inactive(self, mock_get):
        """Test YouTube live check when stream is inactive"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [{
                'liveStreamingDetails': {
                    'actualStartTime': '2025-10-26T10:00:00Z',
                    'actualEndTime': '2025-10-26T11:00:00Z'
                }
            }]
        }
        mock_get.return_value = mock_response
        
        # Act
        response = self.client.get('/check-youtube-live/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['live'])
    
    @patch('core.services.weather_service.requests.get')
    def test_youtube_live_check_error(self, mock_get):
        """Test YouTube live check error handling"""
        # Arrange
        mock_get.side_effect = Exception('YouTube API Error')
        
        # Act
        response = self.client.get('/check-youtube-live/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['live'])
        self.assertIn('error', data)


class YouTubeIntegrationTest(TestCase):
    """Legacy YouTube integration tests (OBSOLETE)"""
    
    def setUp(self):
        """Skip all YouTube integration tests"""
        self.skipTest("YouTube integration obsolete - replaced by direct streaming")
    
    def test_legacy_youtube_endpoints_still_work(self):
        """Test that legacy YouTube endpoints still function"""
        response = self.client.get('/check-youtube-live/')
        self.assertEqual(response.status_code, 200)
        
        # Should return valid JSON even if YouTube is deprecated
        data = json.loads(response.content)
        self.assertIn('live', data)
        self.assertIsInstance(data['live'], bool)
    
    def test_legacy_stream_url_endpoint(self):
        """Test legacy stream URL endpoint"""
        response = self.client.get('/get-stream-url/')
        # Should respond (even if with error due to YouTube dependency)
        self.assertIn(response.status_code, [200, 403, 500])