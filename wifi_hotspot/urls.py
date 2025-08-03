# wifi_hotspot/wifi_hotspot/urls.py

from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # The main login page for the hotspot
    path('', views.hotspot_login_page, name='hotspot_login_page'),
    # API endpoint to handle the token activation form submission
    path('activate/', views.activate_wifi, name='activate_wifi'),
]