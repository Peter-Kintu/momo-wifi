# wifi_hotspot/core/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import WifiSession, Plan, Company, Payment
from .savanna_api import create_savanna_user, disable_savanna_user
from .payment_services import handle_airtel_payment_callback # Import the payment callback handler
import logging
from django.http import JsonResponse
from django.db import transaction
import json
from .serializers import PlanSerializer # Import the serializer

logger = logging.getLogger(__name__)

def hotspot_login_page(request, company_id):
    """
    Renders the main hotspot login page, creating a default company if one doesn't exist.
    """
    # Use get_or_create to automatically create a company if it doesn't exist.
    # This prevents the 404 error on a fresh database.
    company, created = Company.objects.get_or_create(id=company_id, defaults={'name': 'My Hotspot'})
    
    # Fetch all available plans for this company
    plans = Plan.objects.filter(company=company)

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
            return JsonResponse({'message': 'Token is required.'}, status=400)
        
        try:
            # Find the session by token and company
            session = WifiSession.objects.get(token=token, company__id=company_id)
            
            # Check if the token has expired
            if session.end_time < timezone.now():
                return JsonResponse({'message': 'This token has expired.'}, status=400)
                
            if session.is_active:
                # If the session is already active, just return a success message
                return JsonResponse({'message': 'Session is already active.', 'expires_at': session.end_time.isoformat()}, status=200)

            # Activate the session. The model's save method will trigger the API call.
            session.is_active = True
            session.save()

            return JsonResponse({'message': 'WiFi session activated successfully!', 'expires_at': session.end_time.isoformat()}, status=200)

        except WifiSession.DoesNotExist:
            return JsonResponse({'message': 'Invalid token or company ID.'}, status=404)
        except Exception as e:
            logger.error(f"Error in activate_wifi: {e}")
            return JsonResponse({'message': 'An unexpected error occurred.'}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)


@csrf_exempt
def initiate_payment_view(request, company_id):
    """
    Handles the payment initiation and creates a pending WifiSession.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            plan_id = data.get('plan_id')

            if not phone_number or not plan_id:
                return JsonResponse({'message': 'Missing phone number or plan_id.'}, status=400)
            
            # Look up the plan
            plan = Plan.objects.get(id=plan_id)
            
            # In a real payment gateway integration, you'd make an API call here.
            # For this example, we'll assume the payment is successful.
            logger.info(f"Simulating payment for phone: {phone_number}, plan: {plan.name}")

            # Use a transaction to ensure both DB and router operations succeed or fail together.
            with transaction.atomic():
                # 1. Create a new WifiSession in a pending state
                session = WifiSession.objects.create(
                    phone_number=phone_number,
                    plan=plan,
                    is_active=False,
                    # The post_save signal will handle the API call to create the user
                )
            
            return JsonResponse({'message': 'Payment successful. You will receive an SMS with your token shortly.'})

        except Plan.DoesNotExist:
            return JsonResponse({'message': 'Invalid plan selected.'}, status=404)
        except Exception as e:
            logger.error(f"Error in initiate_payment_view: {e}")
            return JsonResponse({'message': f'An unexpected error occurred: {e}'}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)


@csrf_exempt
def payment_callback_view(request, company_id):
    """
    Handles the callback from the payment gateway. This is where the session is activated.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            transaction_id = data.get('transaction_id')
            
            if not transaction_id:
                return JsonResponse({'message': 'Missing transaction_id.'}, status=400)

            success, message = handle_airtel_payment_callback(company_id, transaction_id)

            if success:
                return JsonResponse({'message': message}, status=200)
            else:
                return JsonResponse({'message': message}, status=400)

        except Exception as e:
            logger.error(f"Error in payment_callback_view: {e}")
            return JsonResponse({'message': 'An unexpected error occurred.'}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)


def plan_list(request, company_id):
    """
    API endpoint to list all available plans for a specific company.
    """
    if request.method == 'GET':
        company = get_object_or_404(Company, id=company_id)
        plans = Plan.objects.filter(company=company)
        serializer = PlanSerializer(plans, many=True)
        return JsonResponse(serializer.data, safe=False)
    
    return JsonResponse({'message': 'Invalid request method.'}, status=405)


def admin_dashboard(request, company_id):
    """
    Renders the admin dashboard, showing active sessions.
    """
    company = get_object_or_404(Company, id=company_id)
    active_sessions = WifiSession.objects.filter(company=company, is_active=True)
    
    # Calculate time remaining for each session
    for session in active_sessions:
        if session.end_time:
            time_left = session.end_time - timezone.now()
            if time_left.total_seconds() > 0:
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                session.time_remaining = f"{hours}h {minutes}m {seconds}s"
            else:
                session.time_remaining = "Expired"
        else:
            session.time_remaining = "N/A"
            
    return render(request, 'core/admin_dashboard.html', {'company': company, 'active_sessions': active_sessions})


def manual_deactivate_session(request, company_id, session_id):
    """
    Deactivates a WiFi session manually from the admin dashboard.
    """
    if request.method == 'GET':
        company = get_object_or_404(Company, id=company_id)
        session = get_object_or_404(WifiSession, id=session_id, company=company, is_active=True)

        try:
            # Deactivate the session. The model's deactivate method will trigger the API call.
            session.deactivate()
            
            return redirect('admin_dashboard', company_id=company.id)
        except Exception as e:
            logger.error(f"Error manually deactivating session {session_id}: {e}")
            return redirect('admin_dashboard', company_id=company.id)
            
    return redirect('admin_dashboard', company_id=company_id)
