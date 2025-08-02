"""
URL configuration for wifi_hotspot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include

# Assuming you have a core/urls.py for the 'core' app, this is best practice.
# If you don't, you can keep all the paths in this file as shown below.

from core.views import hotspot_login_page, initiate_payment, payment_callback

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', hotspot_login_page, name='hotspot_login_page'),
    path('initiate-payment/', initiate_payment, name='initiate_payment'),
    path('payment-callback/', payment_callback, name='payment_callback'),
]
