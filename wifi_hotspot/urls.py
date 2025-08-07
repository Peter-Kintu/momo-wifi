# wifi_hotspot/wifi_hotspot/urls.py

from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.conf.urls.static import static
from django.conf import settings
from core import views
import uuid

def root_redirect_view(request):
    """
    Redirects the root URL to a placeholder company page to demonstrate the multi-tenancy structure.
    """
    dummy_company_id = '00000000-0000-0000-0000-000000000000'
    return redirect('hotspot_login_page', company_id=dummy_company_id)

urlpatterns = [
    # The new root URL redirect
    path('', root_redirect_view),
    path('admin/', admin.site.urls),
    
    # Hotspot pages and APIs
    path('<uuid:company_id>/', views.hotspot_login_page, name='hotspot_login_page'),
    path('<uuid:company_id>/api/plans/', views.plan_list, name='plan_list'),
    path('<uuid:company_id>/api/initiate_payment/', views.initiate_payment_view, name='initiate_payment'),
    path('<uuid:company_id>/payment_callback/', views.payment_callback_view, name='payment_callback'),
    path('<uuid:company_id>/activate/', views.activate_wifi, name='activate_wifi'),

    # Admin dashboard
    path('<uuid:company_id>/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('<uuid:company_id>/admin/deactivate/<uuid:session_id>/', views.manual_deactivate_session, name='manual_deactivate_session'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
