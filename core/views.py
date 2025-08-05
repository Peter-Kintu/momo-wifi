# wifi_hotspot/core/views.py

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.http import JsonResponse
import json
from .models import WifiSession, Plan
from .mikrotik_api import enable_mikrotik_user
import logging

logger = logging.getLogger(__name__)

# NOTE: The 'company' object is assumed to be retrieved or passed
# from another part of your application, for example, based on
# the company_id in the URL. For this example, we'll use a placeholder.
class Company:
    def __init__(self, name):
        self.name = name
    
def hotspot_landing_page(request, company_id):
    """
    Renders the hotspot landing page, displaying available plans.
    """
    # In a real-world scenario, you would fetch the company from the database.
    # company = Company.objects.get(id=company_id)
    company = Company("My Awesome Wifi")
    
    plans = Plan.objects.all()
    
    return render(request, 'core/hotspot_landing_page.html', {
        'company': company,
        'plans': plans
    })

def hotspot_login_page(request):
    """
    Renders the main hotspot login page where users can input their token.
    """
    return render(request, 'core/hotspot_login.html')

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

    return render(request, 'core/hotspot_login.html')

@csrf_exempt
def initiate_payment_view(request, company_id):
    """
    Handles the POST request from the hotspot landing page to initiate a payment.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            plan_id = data.get('plan_id')
            phone_number = data.get('phone_number')

            if not plan_id or not phone_number:
                return JsonResponse({'message': 'Missing plan or phone number.'}, status=400)

            plan = Plan.objects.get(id=plan_id)
            
            # Here, you would integrate with a payment gateway.
            # For this example, we'll assume a successful payment and proceed directly.
            # In a real-world scenario, the payment gateway would trigger a callback to your server
            # upon successful payment, which would then create the session.
            
            # Check if a session already exists for this number to prevent duplicates
            session, created = WifiSession.objects.get_or_create(
                phone_number=phone_number,
                plan=plan
            )
            
            # If the session was newly created, its save() method will handle
            # the token generation, MikroTik user creation, and SMS sending.
            # If it already existed, we can assume the process is already underway.
            if created:
                session.save()
                return JsonResponse({'message': 'Payment initiated. You will receive an SMS with your token shortly.'})
            else:
                return JsonResponse({'message': 'A session for this phone number is already pending or active.'}, status=409)

        except Plan.DoesNotExist:
            return JsonResponse({'message': 'Invalid plan selected.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            logger.error(f"Error in initiate_payment_view: {e}")
            return JsonResponse({'message': 'An internal error occurred.'}, status=500)
    
    return JsonResponse({'message': 'Invalid request method.'}, status=405)


@csrf_exempt
def airtel_payment_callback(request, company_id):
    """
    Handles the callback from the Airtel payment gateway.
    """
    if request.method == 'POST':
        try:
            # Parse the incoming JSON payload from Airtel.
            # The exact structure will depend on Airtel's API documentation.
            # For now, we'll use a placeholder.
            data = json.loads(request.body)
            logger.info(f"Airtel payment callback received: {data}")
            
            # Here, you would extract the transaction ID, phone number, and status
            # from the `data` payload.
            transaction_id = data.get('transactionId')
            phone_number = data.get('sourceNumber')
            status = data.get('status') # e.g., 'SUCCESS', 'FAILED'
            
            if status == 'SUCCESS':
                # Find the pending WifiSession for this phone number and mark it as paid/active.
                # In a real app, you would also match the transaction ID to a record
                # in your database to prevent duplicate activations.
                session = WifiSession.objects.filter(phone_number=phone_number, is_active=False).first()

                if session:
                    # Activate the MikroTik user. The save() method of WifiSession will handle it.
                    # Note: Our current model.save() logic creates the user,
                    # so this step would likely be more complex in a real payment callback
                    # where you would need to enable an already created user.
                    # For now, we will simply assume the session exists and a user
                    # has been created.
                    session.is_active = True
                    session.save()
                    return JsonResponse({'message': 'Payment successful and session activated.'}, status=200)
                else:
                    return JsonResponse({'message': 'No pending session found for this number.'}, status=404)
            else:
                # Handle failed or other statuses
                return JsonResponse({'message': f'Payment failed with status: {status}.'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            logger.error(f"Error processing Airtel callback: {e}")
            return JsonResponse({'message': 'An internal error occurred.'}, status=500)
    
    return JsonResponse({'message': 'Invalid request method.'}, status=405)
