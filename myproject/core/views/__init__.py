"""
Core views for ClimaCocal application.

Modular view structure extracted from monolithic views.py
following Django best practices and Single Responsibility Principle.
"""

# Import views for easier access
from .home_views import home
from .payment_views import (
    create_payment, payment_success, test_payment_success, 
    test_payment_direct, payment_failure, payment_failure_safe, 
    payment_webhook
)
from .api_views import youtube_live_check, weather, check_payment_status, get_stream_url
from .legacy_views import *
from .climber_views import (
    climber_register, verify_email, climber_status, climber_access,
    climber_logout, climber_admin_stats, resend_verification
)