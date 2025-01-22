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
from django.urls import path
from core.views import create_payment, payment_webhook, check_payment_status, home, payment_success   #, get_weather

urlpatterns = [
    path("", home, name="home"),
    path("create-payment/", create_payment, name="create_payment"),
    path("payment-success/", payment_success, name="payment_success"),
    path("webhook/", payment_webhook, name="webhook"),
    path("check-payment/", check_payment_status, name="check_payment"),
    # path("weather/", get_weather, name="get_weather"),
]


# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', views.home, name='home'),  # Root URL for homepage
#     path('create-payment/', views.create_payment, name='create_payment'),
# ]