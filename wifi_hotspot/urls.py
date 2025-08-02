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
from django.urls import path

# The view function name `initiate_payment` was changed to `initiate_payment_view`
# in a previous fix for clarity. This import statement reflects that change.
from core.views import hotspot_login_page, initiate_payment_view, payment_callback

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', hotspot_login_page, name='hotspot_login_page'),
    # The URL path is updated to match the front-end request.
    path('api/initiate-payment/', initiate_payment_view, name='initiate_payment'),
    # The URL path for the payment callback is also updated for consistency.
    path('api/payment-callback/', payment_callback, name='payment_callback'),
]
