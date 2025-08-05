# wifi_hotspot/core/views.py

from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import WifiSession, Plan, Company
from .mikrotik_api import enable_mikrotik_user
import logging
from django.http import JsonResponse
from django.db import transaction
import json

logger = logging.getLogger(__name__)

def hotspot_login_page(request, company_id):
    """
    Renders the main hotspot login page where users can input their token.
    The company is now retrieved based on the URL's company_id.
    """
    # Use get_object_or_404 as a shortcut to get the company or raise a 404 Http404 exception.
    company = get_object_or_404(Company, id=company_id)
    
    # Fetch all available plans for the company. In a multi-tenant setup, you might want to filter plans by company.
    # For now, we assume all plans are available to all companies.
    plans = Plan.objects.all()

    return render(request, 'core/hotspot_login.html', {'plans': plans, 'company': company})

@csrf_exempt
def activate_wifi(request, company_id):
    """
    Handles the POST request to activate a WiFi session with a token.
    This view now also receives the company_id from the URL.
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

@csrf_exempt
def initiate_payment_view(request, company_id):
    """
    Handles the payment initiation process for a selected plan.
    """
    if request.method == 'POST':
        try:
            # Get data from the JSON body
            data = json.loads(request.body)
            plan_id = data.get('plan_id')
            phone_number = data.get('phone_number')

            if not plan_id or not phone_number:
                return JsonResponse({'message': 'Missing plan or phone number.'}, status=400)

            # Look up the plan
            plan = Plan.objects.get(id=plan_id)
            
            # In a real payment gateway integration, you'd make an API call here.
            # For this example, we'll assume the payment is successful.
            logger.info(f"Simulating payment for phone: {phone_number}, plan: {plan.name}")

            # Use a transaction to ensure both DB and MikroTik operations succeed or fail together.
            with transaction.atomic():
                # 1. Create a new WifiSession in a pending state
                session = WifiSession.objects.create(
                    phone_number=phone_number,
                    plan=plan,
                    is_active=False,
                    # We will set the token and end_time later, or use the post_save signal
                )
                session.save() # This will trigger the post_save signal which creates the MikroTik user
            
            return JsonResponse({'message': 'Payment successful. You will receive an SMS with your token shortly.'})

        except Plan.DoesNotExist:
            return JsonResponse({'message': 'Invalid plan selected.'}, status=404)
        except Exception as e:
            logger.error(f"Error in initiate_payment_view: {e}")
            return JsonResponse({'message': f'An unexpected error occurred: {e}'}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)
