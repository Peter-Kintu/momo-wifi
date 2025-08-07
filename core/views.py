# wifi_hotspot/core/views.py

from django.shortcuts import  redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import WifiSession, Plan, Company, Payment
# The MikroTik API is no longer used directly in the views. The WifiSession model's
# methods now handle the router API calls, making this import unnecessary.
from .payment_services import get_airtel_access_token, initiate_airtel_payment, handle_airtel_payment_callback
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
def activate_wifi(request, company_id):
    """
    Handles the POST request to activate a WiFi session with a token.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token')
            company = get_object_or_404(Company, id=company_id)

            if not token:
                return JsonResponse({'message': 'Token is required.'}, status=400)

            # Check for an active session with the provided token and company
            session = get_object_or_404(WifiSession, token=token, company=company, is_active=False)

            # Get the client's IP address from the request
            ip_address = request.META.get('REMOTE_ADDR')

            # Activate the session using the model's method, which handles the Savanna API call.
            success, message = session.activate(ip_address)

            if success:
                return JsonResponse({
                    'message': 'WiFi activated successfully!',
                    'expires_at': session.end_time.isoformat()
                })
            else:
                return JsonResponse({'message': message}, status=500)

        except WifiSession.DoesNotExist:
            return JsonResponse({'message': 'Invalid or expired token.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON.'}, status=400)
        except Exception as e:
            logger.error(f"Error activating token: {e}")
            return JsonResponse({'message': f'An unexpected error occurred: {e}'}, status=500)

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
            company = get_object_or_404(Company, id=company_id)

            if not phone_number or not plan_id:
                return JsonResponse({'message': 'Phone number and plan are required.'}, status=400)

            # Look up the plan
            plan = get_object_or_404(Plan, id=plan_id, company=company)
            
            # Initiate payment via the payment_services module
            success, message = initiate_airtel_payment(plan, phone_number, company)

            if success:
                return JsonResponse({'message': message})
            else:
                return JsonResponse({'message': message}, status=500)

        except Plan.DoesNotExist:
            return JsonResponse({'message': 'Invalid plan selected.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON.'}, status=400)
        except Exception as e:
            logger.error(f"Error in initiate_payment_view: {e}")
            return JsonResponse({'message': f'An unexpected error occurred: {e}'}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def payment_callback_view(request, company_id):
    """
    Handles the callback from the payment gateway to finalize a payment.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            company = get_object_or_404(Company, id=company_id)

            # Corrected function call to match the name in payment_services.py
            success, message = handle_airtel_payment_callback(data, company)

            if success:
                return JsonResponse({'status': 'success', 'message': message})
            else:
                return JsonResponse({'status': 'failed', 'message': message}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'failed', 'message': 'Invalid JSON in callback.'}, status=400)
        except Exception as e:
            logger.error(f"Error in payment_callback_view: {e}")
            return JsonResponse({'status': 'failed', 'message': f'An unexpected error occurred: {e}'}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)

def admin_dashboard(request, company_id):
    """
    Renders a simple admin dashboard showing active WiFi sessions.
    """
    company = get_object_or_404(Company, id=company_id)
    # Fetch all active sessions for the specific company
    active_sessions = WifiSession.objects.filter(
        company=company,
        is_active=True,
        end_time__gt=timezone.now()
    ).order_by('-start_time')

    # Calculate time remaining for each session
    for session in active_sessions:
        time_left = session.end_time - timezone.now()
        total_seconds = int(time_left.total_seconds())
        
        if total_seconds > 0:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            session.time_remaining = f"{hours}h {minutes}m {seconds}s"
        else:
            session.time_remaining = "Expired"

    return render(request, 'core/admin_dashboard.html', {'company': company, 'active_sessions': active_sessions})

def manual_deactivate_session(request, company_id, session_id):
    """
    Deactivates a WiFi session manually from the admin dashboard.
    """
    if request.method == 'GET':
        company = get_object_or_404(Company, id=company_id)
        session = get_object_or_404(WifiSession, id=session_id, company=company, is_active=True)

        try:
            # Deactivate the session using the model's method, which handles the Savanna API call.
            success, message = session.deactivate()
            
            if success:
                return redirect('admin_dashboard', company_id=company.id)
            else:
                logger.error(f"Failed to deactivate session {session_id}: {message}")
                return redirect('admin_dashboard', company_id=company.id)
        except Exception as e:
            logger.error(f"Error manually deactivating session {session_id}: {e}")
            return redirect('admin_dashboard', company_id=company.id)
