# wifi_hotspot/wifi_hotspot/urls.py

from django.contrib import admin
from django.urls import path, include, re_path
from django.shortcuts import redirect
from django.conf.urls.static import static
from django.conf import settings
from core import views
import uuid # Import the uuid module

def root_redirect_view(request):
    """
    Redirects the root URL to a placeholder company page to demonstrate the multi-tenancy structure.
    """
    # Ensure the dummy_company_id is a valid UUID string
    dummy_company_id = '00000000-0000-0000-0000-000000000000'
    return redirect('hotspot_login_page', company_id=dummy_company_id)

urlpatterns = [
    # The new root URL redirect
    path('', root_redirect_view),
    path('admin/', admin.site.urls),
    # The main login page for the hotspot
    path('<uuid:company_id>/', views.hotspot_login_page, name='hotspot_login_page'),
    # The new URL for activating a wifi session. This replaces both the old login and activate paths.
    path('<uuid:company_id>/activate/', views.activate_wifi, name='activate_wifi'),
    # The new URL for initiating payment
    path('<uuid:company_id>/initiate_payment/', views.initiate_payment_view, name='initiate_payment'),
    # The new URL for the payment callback
    path('<uuid:company_id>/payment_callback/', views.payment_callback_view, name='payment_callback'),
    # The new URL for the admin dashboard
    path('<uuid:company_id>/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # The new URL for manual deactivation
    path('<uuid:company_id>/deactivate/<uuid:session_id>/', views.manual_deactivate_session, name='manual_deactivate_session'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
