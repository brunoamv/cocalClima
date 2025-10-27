"""myproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static

from django.urls import path, include

from core.views import create_payment, payment_webhook, check_payment_status, home, payment_success ,payment_failure, payment_failure_safe , weather , youtube_live_check , get_stream_url, camera_stream, camera_segment, camera_status_api, test_payment_success, test_payment_direct 
urlpatterns = [
    path("", home, name="home"),
    path("create-payment/", create_payment, name="create_payment"),
    path("payment-success/", payment_success, name="payment_success"),
    path("payment-failure/", payment_failure, name="payment_failure"),
    path("payment-failure-safe/", payment_failure_safe, name="payment_failure_safe"),
    
    # Test endpoints for development
    path("test-payment-success/", test_payment_success, name="test_payment_success"),
    path("test-payment-direct/", test_payment_direct, name="test_payment_direct"),
    path("webhook/", payment_webhook, name="webhook"),
    path("check-payment/", check_payment_status, name="check_payment"),
    path("weather/", weather, name="get_weather"),
    path("check-youtube-live/", youtube_live_check, name="check_youtube_live"),
    path("get-stream-url/", get_stream_url, name="get_stream_url"),
    
    # Enhanced Streaming URLs
    path("streaming/", include('streaming.urls')),
    
    # Legacy Camera Streaming URLs (for backward compatibility)
    path("camera/stream.m3u8", camera_stream, name="legacy_camera_stream"),
    path("camera/<str:segment_name>", camera_segment, name="legacy_camera_segment"),
    path("api/camera-status/", camera_status_api, name="legacy_camera_status"),

] 

# Static files serving (for development and production)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Production static files serving
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', views.home, name='home'),  # Root URL for homepage
#     path('create-payment/', views.create_payment, name='create_payment'),
# ]