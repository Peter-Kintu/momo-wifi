# wifi_hotspot/core/views.py

from django.shortcuts import  redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import WifiSession, Plan, Company, Payment
from .mikrotik_api import enable_mikrotik_user, create_mikrotik_user, disable_mikrotik_user
from .payment_services import get_savanna_access_token
import logging
from django.http import JsonResponse
from django.db import transaction
import json
import uuid

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
def payment_callback_view(request, company_id):
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

            company = get_object_or_404(Company, id=company_id)
            plan = get_object_or_404(Plan, id=plan_id, company=company)
            
            # Here we'd integrate with the Savanna API.
            # For now, we'll simulate a successful payment and create a pending session.
            logger.info(f"Simulating payment for phone: {phone_number}, plan: {plan.name} at company: {company.name}")
            
            # The transaction will ensure the session and payment are saved atomically.
            with transaction.atomic():
                session = WifiSession.objects.create(
                    company=company,
                    phone_number=phone_number,
                    plan=plan,
                    is_active=False
                )
                
                # The post_save signal in models.py will handle MikroTik user creation
                # and token generation. We'll simply save the session here.
                session.save()

                Payment.objects.create(
                    session=session,
                    amount=plan.price,
                    transaction_id=str(uuid.uuid4()), # Placeholder transaction ID
                    status='SUCCESS'
                )

            return JsonResponse({'message': 'Payment successful. You will receive an SMS with your token shortly.', 'token': session.token})
        
        except Exception as e:
            logger.error(f"Error in payment_callback_view for company {company_id}: {e}")
            return JsonResponse({'message': f'An unexpected error occurred: {e}'}, status=500)
    
    return JsonResponse({'message': 'Invalid request method.'}, status=405)


@csrf_exempt
def activate_token(request, company_id):
    """
    Handles the POST request to activate a WiFi session with a token.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token')

            if not token:
                return JsonResponse({'message': 'Token is required.'}, status=400)
            
            company = get_object_or_404(Company, id=company_id)
            session = get_object_or_404(WifiSession, token=token, company=company, is_active=False)

            # Enable the MikroTik user
            success, message = enable_mikrotik_user(company, username=session.token)

            if success:
                session.is_active = True
                session.start_time = timezone.now()
                session.end_time = session.start_time + timezone.timedelta(minutes=session.plan.duration_minutes)
                session.save()

                return JsonResponse({'message': 'WiFi session activated successfully.', 'expires_at': session.end_time})
            else:
                return JsonResponse({'message': f'Failed to activate session: {message}'}, status=500)

        except WifiSession.DoesNotExist:
            return JsonResponse({'message': 'Invalid or expired token.'}, status=404)
        except Exception as e:
            logger.error(f"Error in activate_token for company {company_id}: {e}")
            return JsonResponse({'message': f'An unexpected error occurred: {e}'}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)


def admin_dashboard(request, company_id):
    """
    Renders a simple admin dashboard with a list of active sessions for a company.
    """
    company = get_object_or_404(Company, id=company_id)
    active_sessions = WifiSession.objects.filter(company=company, is_active=True).order_by('-start_time')
    
    # Example of how to add a calculated property for time remaining
    for session in active_sessions:
        if session.end_time:
            time_remaining = session.end_time - timezone.now()
            seconds = int(time_remaining.total_seconds())
            if seconds > 0:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                session.time_remaining = f"{hours}h {minutes}m"
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
            # Disable the MikroTik user
            success, message = disable_mikrotik_user(company, username=session.token)
            
            if success:
                session.is_active = False
                session.save()
                return redirect('admin_dashboard', company_id=company.id)
            else:
                # Handle cases where MikroTik user can't be disabled
                # For now, we'll just log and redirect.
                logger.error(f"Failed to disable MikroTik user for session {session_id}: {message}")
                return redirect('admin_dashboard', company_id=company.id)
        except Exception as e:
            logger.error(f"Error manually deactivating session {session_id}: {e}")
            return redirect('admin_dashboard', company_id=company.id)
            
    return redirect('admin_dashboard', company_id=company.id)

