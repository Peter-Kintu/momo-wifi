# wifi_hotspot/wifi_hotspot/urls.py

from django.contrib import admin
from django.urls import path, include, re_path
from django.shortcuts import redirect
from django.conf.urls.static import static
from django.conf import settings
from core import views
from django.http import HttpRequest, HttpResponse

def root_redirect_view(request: HttpRequest) -> HttpResponse:
    """
    Redirects the root URL to a placeholder company page to demonstrate the multi-tenancy structure.
    Replace '00000000-0000-0000-0000-000000000000' with a real company's UUID.
    """
    # Use a dummy UUID for now. In a real-world scenario, you would
    # resolve the company_id dynamically.
    dummy_company_id = '00000000-0000-0000-0000-000000000000'
    return redirect('hotspot_login_page', company_id=dummy_company_id)

urlpatterns = [
    # The new root URL redirect
    path('', root_redirect_view),
    path('admin/', admin.site.urls),
    # The main login page for the hotspot
    path('<uuid:company_id>/', views.hotspot_login_page, name='hotspot_login_page'),
    # API endpoint to handle the token activation form submission
    path('<uuid:company_id>/login/', views.activate_wifi, name='activate_wifi'),
    # The new URL for activating a wifi session
    path('<uuid:company_id>/activate/', views.activate_wifi, name='activate_wifi'),
    # The new URL for initiating payment
    path('<uuid:company_id>/initiate-payment/', views.initiate_payment_view, name='initiate_payment'),
]
