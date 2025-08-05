# wifi_hotspot/core/views.py

from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import WifiSession, Plan, Company
from .mikrotik_api import enable_mikrotik_user
import logging

logger = logging.getLogger(__name__)

def hotspot_landing_page(request, company_id):
    """
    Renders the main hotspot landing page where users can select a plan.
    """
    company = get_object_or_404(Company, id=company_id)
    plans = Plan.objects.all()
    return render(request, 'core/hotspot_landing_page.html', {
        'company': company,
        'plans': plans
    })

def hotspot_login_page(request, company_id):
    """
    Renders the login page where users can input their token.
    """
    company = get_object_or_404(Company, id=company_id)
    return render(request, 'core/hotspot_login.html', {
        'company': company
    })

@csrf_exempt
def activate_wifi(request, company_id):
    """
    Handles the POST request to activate a WiFi session with a token.
    """
    if request.method == 'POST':
        token = request.POST.get('token')

        if not token:
            return render(request, 'core/invalid_token.html', {'error': 'Token cannot be empty.'})

        session = WifiSession.objects.filter(token=token).first()

        if session:
            # Check if the session is not already active
            if session.is_active:
                return render(request, 'core/invalid_token.html', {'error': 'Token has already been used.'})

            # Check if the session has expired
            if session.end_time and session.end_time < timezone.now():
                return render(request, 'core/invalid_token.html', {'error': 'Expired token.'})

            try:
                mikrotik_success, mikrotik_message = enable_mikrotik_user(username=session.token)

                if mikrotik_success:
                    session.is_active = True
                    session.save()
                    return render(request, 'core/wifi_active.html', {'session': session})
                else:
                    return render(request, 'core/invalid_token.html', {'error': mikrotik_message})

            except Exception as e:
                logger.error(f"Error activating MikroTik user for token {token}: {e}")
                return render(request, 'core/invalid_token.html', {'error': 'An internal error occurred during activation.'})
        else:
            return render(request, 'core/invalid_token.html', {'error': 'Invalid token.'})

    return render(request, 'core/hotspot_login.html')
