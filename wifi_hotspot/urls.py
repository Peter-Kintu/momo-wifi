"""
URL configuration for wifi_hotspot project.
"""
from django.contrib import admin
from django.urls import path

# The view functions are now correctly imported.
from core.views import hotspot_login_page, initiate_payment, airtel_callback

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', hotspot_login_page, name='hotspot_login_page'),
    path('api/initiate-payment/', initiate_payment, name='initiate_payment'),
    # The URL path for the payment callback is also updated for consistency.
    path('api/airtel/callback/', airtel_callback, name='airtel_callback'),
]
