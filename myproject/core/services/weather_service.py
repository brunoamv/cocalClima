"""
Weather service for ClimaTempoAPI integration.

Extracted from core/views.py following Single Responsibility Principle.
Handles weather API calls and data retrieval.
"""

import logging
import requests
from django.conf import settings
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for handling weather data operations."""
    
    def __init__(self):
        """Initialize WeatherService with API configuration."""
        self.api_token = getattr(settings, 'WEATHER_API_TOKEN', 
                                '546659d2c8b489261f185e4e10b21d3c')
        self.city_id = getattr(settings, 'WEATHER_CITY_ID', '3137')
    
    def get_current_weather(self) -> Optional[Dict[str, Any]]:
        """
        Get current weather data from ClimaTempoAPI.
        
        Returns:
            Weather data dictionary if successful, None otherwise
        """
        try:
            url = self._get_api_url()
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Weather data retrieved for city {self.city_id}")
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving weather data: {e}")
            return None
    
    def _get_api_url(self) -> str:
        """
        Build ClimaTempoAPI URL.
        
        Returns:
            Complete API URL with token and city ID
        """
        return (f"https://apiadvisor.climatempo.com.br/api/v1/weather/"
                f"locale/{self.city_id}/current?token={self.api_token}")
    
    def is_available(self) -> bool:
        """
        Check if weather service is properly configured.
        
        Returns:
            True if API token and city ID are configured
        """
        return bool(self.api_token and self.city_id)