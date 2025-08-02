"""
URL configuration for wifi_hotspot project.
"""
from django.contrib import admin
from django.urls import path

# The view functions are now correctly imported.
from core.views import hotspot_login_page, initiate_payment, payment_callback

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', hotspot_login_page, name='hotspot_login_page'),
    # The URL path is updated to match the front-end request.
    path('api/initiate-payment/', initiate_payment, name='initiate_payment'),
    # The URL path for the payment callback is also updated for consistency.
    path('api/payment-callback/', payment_callback, name='payment_callback'),
]
