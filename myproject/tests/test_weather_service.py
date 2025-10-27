"""
Tests for WeatherService extracted from core/views.py
Following Test-Driven Development practices.
"""

from unittest.mock import patch, Mock
from django.test import TestCase

from core.services.weather_service import WeatherService


class WeatherServiceTest(TestCase):
    
    def setUp(self):
        self.weather_service = WeatherService()
    
    @patch('requests.get')
    def test_get_current_weather_success(self, mock_get):
        """Test successful weather data retrieval"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "temperature": 25,
                "humidity": 60,
                "condition": "sunny"
            }
        }
        mock_get.return_value = mock_response
        
        # Act
        result = self.weather_service.get_current_weather()
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn('data', result)
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_current_weather_api_error(self, mock_get):
        """Test weather data retrieval with API error"""
        # Arrange
        mock_get.side_effect = Exception("API Error")
        
        # Act
        result = self.weather_service.get_current_weather()
        
        # Assert
        self.assertIsNone(result)
    
    def test_get_api_url(self):
        """Test weather API URL construction"""
        # Act
        url = self.weather_service._get_api_url()
        
        # Assert
        self.assertIn('apiadvisor.climatempo.com.br', url)
        self.assertIn(self.weather_service.city_id, url)
        self.assertIn(self.weather_service.api_token, url)
    
    def test_is_available(self):
        """Test weather service availability check"""
        # Act
        result = self.weather_service.is_available()
        
        # Assert
        self.assertTrue(result)  # Should be True with default config