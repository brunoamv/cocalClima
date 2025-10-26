"""
YouTube service for live stream integration.

Extracted from core/views.py following Single Responsibility Principle.
Handles YouTube API calls and live stream status checking.
"""

import logging
import requests
from django.conf import settings
from typing import Dict, Any

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for handling YouTube live stream operations."""
    
    def __init__(self):
        """Initialize YouTubeService with API configuration."""
        self.api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
        self.video_id = getattr(settings, 'YOUTUBE_VIDEO_ID', 'zsGnr5FT-Qw')
    
    def check_live_status(self) -> Dict[str, Any]:
        """
        Check if YouTube live stream is currently active.
        
        Returns:
            Dictionary with live status and optional error message
        """
        try:
            if not self.api_key:
                logger.warning("YouTube API key not configured")
                return {"live": False, "error": "YouTube API key not configured"}
            
            url = (f"https://www.googleapis.com/youtube/v3/videos"
                   f"?id={self.video_id}&part=liveStreamingDetails&key={self.api_key}")
            
            response = requests.get(url)
            data = response.json()
            
            # Check if video exists and has live streaming details
            if "items" in data and data["items"]:
                live_details = data["items"][0].get("liveStreamingDetails", {})
                
                actual_start_time = live_details.get("actualStartTime")
                actual_end_time = live_details.get("actualEndTime")
                
                # Live if started but not ended
                is_live = actual_start_time and not actual_end_time
                return {"live": is_live}
            
            return {"live": False}
            
        except Exception as e:
            logger.error(f"Error checking YouTube live status: {e}")
            return {"live": False, "error": str(e)}
    
    def get_embed_url(self, autoplay: bool = True, mute: bool = True) -> str:
        """
        Generate YouTube embed URL for the configured video.
        
        Args:
            autoplay: Enable autoplay parameter
            mute: Enable mute parameter
            
        Returns:
            YouTube embed URL with parameters
        """
        autoplay_param = "1" if autoplay else "0"
        mute_param = "1" if mute else "0"
        
        return (f"https://www.youtube.com/embed/{self.video_id}"
                f"?autoplay={autoplay_param}&mute={mute_param}")
    
    def is_available(self) -> bool:
        """
        Check if YouTube service is properly configured.
        
        Returns:
            True if API key and video ID are configured
        """
        return bool(self.api_key and self.video_id)