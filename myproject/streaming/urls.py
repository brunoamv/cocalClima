"""
URL Configuration for Direct Camera Streaming
"""
from django.urls import path
from . import views
from . import api_views

app_name = 'streaming'

urlpatterns = [
    # HLS Streaming endpoints
    path('camera/stream.m3u8', views.CameraStreamView.as_view(), name='camera_stream'),
    path('camera/<str:segment_name>', views.CameraSegmentView.as_view(), name='camera_segment'),
    
    # API endpoints
    path('api/status/', api_views.streaming_status, name='camera_status'),  # Enhanced with climber support
    path('api/start/', views.start_streaming_api, name='start_streaming'),
    path('api/stop/', views.stop_streaming_api, name='stop_streaming'),
    path('api/health/', views.health_check, name='health_check'),
    
    # Legacy compatibility URLs
    path('camera/stream/', views.legacy_camera_stream, name='legacy_stream'),
    path('camera/segment/<str:segment_name>', views.legacy_camera_segment, name='legacy_segment'),
]