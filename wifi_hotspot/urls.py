# wifi_hotspot/wifi_hotspot/urls.py

from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    # Admin site URL
    path('admin/', admin.site.urls),

    # The main hotspot landing page, which is now multi-tenant aware.
    # The URL will look like example.com/12345678-1234-5678-1234-567812345678/
    path('<uuid:company_id>/', views.hotspot_landing_page, name='hotspot_landing_page'),

    # The login page for users who already have a token
    path('<uuid:company_id>/login/', views.hotspot_login_page, name='hotspot_login_page'),

    # API endpoint to handle the token activation form submission
    path('<uuid:company_id>/activate/', views.activate_wifi, name='activate_wifi'),

    # API endpoint to initiate a payment
    path('<uuid:company_id>/initiate-payment/', views.initiate_payment_view, name='initiate_payment_view'),

    # Webhook endpoint to receive payment confirmation callbacks
    path('<uuid:company_id>/airtel-callback/', views.airtel_payment_callback, name='airtel_payment_callback'),
]
