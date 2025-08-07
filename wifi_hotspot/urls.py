# wifi_hotspot/wifi_hotspot/urls.py

from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from core import views
import uuid

def root_redirect_view(request):
    """
    Redirects the root URL to a placeholder company page.
    This is useful for local testing or a default entry point.
    """
    dummy_company_id = '00000000-0000-0000-0000-000000000000'
    return redirect('hotspot_login_page', company_id=dummy_company_id)

urlpatterns = [
    # The new root URL redirect
    path('', root_redirect_view, name='root'),
    
    path('admin/', admin.site.urls),
    
    # URL for the main hotspot login page with a company_id
    path('<uuid:company_id>/', views.hotspot_login_page, name='hotspot_login_page'),
    
    # URL for the payment callback (simulated Airtel Money)
    path('<uuid:company_id>/payment/callback/', views.payment_callback_view, name='payment_callback_view'),
    
    # URL to activate a WiFi session with a token
    path('<uuid:company_id>/activate/', views.activate_token, name='activate_token'),
    
    # URL for the admin dashboard for a specific company
    path('<uuid:company_id>/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # URL to manually deactivate a session from the admin dashboard
    path('<uuid:company_id>/session/<uuid:session_id>/deactivate/', views.manual_deactivate_session, name='manual_deactivate_session'),
]
