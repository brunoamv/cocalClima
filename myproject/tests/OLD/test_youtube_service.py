"""
Tests for YouTubeService extracted from core/views.py
Following Test-Driven Development practices.
"""

from unittest.mock import patch, Mock
from django.test import TestCase
from django.conf import settings

from core.services.youtube_service import YouTubeService


class YouTubeServiceTest(TestCase):
    
    def setUp(self):
        self.youtube_service = YouTubeService()
    
    @patch('requests.get')
    def test_check_live_status_active(self, mock_get):
        """Test YouTube live status check when stream is active"""
        # Arrange - Mock API key configuration
        self.youtube_service.api_key = 'test_api_key'
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [{
                "liveStreamingDetails": {
                    "actualStartTime": "2025-10-26T10:00:00Z",
                    # No actualEndTime means still live
                }
            }]
        }
        mock_get.return_value = mock_response
        
        # Act
        result = self.youtube_service.check_live_status()
        
        # Assert
        self.assertTrue(result['live'])
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_check_live_status_inactive(self, mock_get):
        """Test YouTube live status check when stream is inactive"""
        # Arrange - Mock API key configuration
        self.youtube_service.api_key = 'test_api_key'
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [{
                "liveStreamingDetails": {
                    "actualStartTime": "2025-10-26T10:00:00Z",
                    "actualEndTime": "2025-10-26T11:00:00Z"  # Stream ended
                }
            }]
        }
        mock_get.return_value = mock_response
        
        # Act
        result = self.youtube_service.check_live_status()
        
        # Assert
        self.assertFalse(result['live'])
    
    @patch('requests.get')
    def test_check_live_status_no_items(self, mock_get):
        """Test YouTube live status check when no items returned"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response
        
        # Act
        result = self.youtube_service.check_live_status()
        
        # Assert
        self.assertFalse(result['live'])
    
    @patch('requests.get')
    def test_check_live_status_api_error(self, mock_get):
        """Test YouTube live status check with API error"""
        # Arrange
        mock_get.side_effect = Exception("API Error")
        
        # Act
        result = self.youtube_service.check_live_status()
        
        # Assert
        self.assertFalse(result['live'])
        self.assertIn('error', result)
    
    def test_get_embed_url(self):
        """Test YouTube embed URL generation"""
        # Act
        url = self.youtube_service.get_embed_url()
        
        # Assert
        self.assertIn('youtube.com/embed/', url)
        self.assertIn('autoplay=1', url)
        self.assertIn('mute=1', url)
        self.assertIn(self.youtube_service.video_id, url)
    
    def test_get_embed_url_custom_params(self):
        """Test YouTube embed URL with custom parameters"""
        # Act
        url = self.youtube_service.get_embed_url(autoplay=False, mute=False)
        
        # Assert
        self.assertIn('youtube.com/embed/', url)
        self.assertIn('autoplay=0', url)
        self.assertIn('mute=0', url)