"""
URL configuration for wifi_hotspot project.
"""
from django.contrib import admin
from django.urls import path

# Import the new view
from core.views import hotspot_login_page, verify_payment

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', hotspot_login_page, name='hotspot_login_page'),
    # New URL path for Flutterwave payment verification
    path('api/verify-payment/', verify_payment, name='verify_payment'),
]
