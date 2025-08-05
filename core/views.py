# wifi_hotspot/core/views.py

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import WifiSession, Plan, Company
from .mikrotik_api import enable_mikrotik_user, create_mikrotik_user
import logging
from django.http import JsonResponse
from django.db import transaction

logger = logging.getLogger(__name__)

def hotspot_login_page(request, company_id):
    """
    Renders the main hotspot login page where users can input their token.
    """
    # Fetch all available plans and company info
    plans = Plan.objects.all()
    company, created = Company.objects.get_or_create(id=1, defaults={'name': 'My Hotspot'})
    return render(request, 'core/hotspot_login.html', {'plans': plans, 'company': company})

@csrf_exempt
def activate_wifi(request):
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

    return render(request, 'core/invalid_token.html', {'error': 'Invalid request method.'})


@csrf_exempt
def initiate_payment_view(request):
    """
    Handles the payment initiation and subsequent MikroTik user creation.
    This view is a placeholder for a real payment gateway integration.
    """
    if request.method == 'POST':
        try:
            # This is a simplified example. In a real-world scenario, you would
            # parse the JSON body and validate the data.
            plan_id = request.POST.get('plan_id')
            phone_number = request.POST.get('phone_number')

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
                session.save()  # This will trigger the post_save signal which creates the MikroTik user

            return JsonResponse({'message': 'Payment successful. You will receive an SMS with your token shortly.'})

        except Plan.DoesNotExist:
            return JsonResponse({'message': 'Invalid plan selected.'}, status=404)
        except Exception as e:
            logger.error(f"Error in initiate_payment_view: {e}")
            return JsonResponse({'message': f'An unexpected error occurred: {e}'}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)
