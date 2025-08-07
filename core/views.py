# wifi_hotspot/core/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction
import json
import logging

from .models import WifiSession, Plan, Company, Payment
from .savanna_api import create_savanna_user, disable_savanna_user
from .payment_services import initiate_airtel_payment, handle_airtel_payment_callback

logger = logging.getLogger(__name__)

def get_user_ip(request):
    """
    Retrieves the user's real IP address, handling proxies and load balancers.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def hotspot_login_page(request, company_id):
    """
    Renders the main hotspot login page for a specific company.
    """
    company = get_object_or_404(Company, id=company_id)
    plans = Plan.objects.filter(company=company) 

    return render(request, 'core/hotspot_login.html', {
        'company': company,
        'plans': plans
    })

@csrf_exempt
def payment_callback_view(request, company_id):
    """
    Simulates the callback from a mobile money provider (e.g., Airtel Money).
    This view handles the post-payment session activation.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            plan_id = data.get('plan_id')
            
            company = get_object_or_404(Company, id=company_id)
            plan = get_object_or_404(Plan, id=plan_id, company=company)
            
            # Create a pending session
            session = WifiSession.objects.create(
                phone_number=phone_number,
                company=company,
                plan=plan,
                is_active=False
            )
            
            # Initiate payment (this function will handle the actual API call)
            success, transaction_id = initiate_airtel_payment(session)

            if success:
                # For this simulated environment, we'll immediately handle the callback
                callback_success, message = handle_airtel_payment_callback(company, transaction_id)
                if callback_success:
                    return JsonResponse({
                        'message': 'Payment successful. You will receive an SMS with your token shortly.',
                        'token': session.token
                    })
                else:
                    return JsonResponse({'message': message}, status=500)
            else:
                return JsonResponse({'message': message}, status=500)

        except (Plan.DoesNotExist, Company.DoesNotExist) as e:
            return JsonResponse({'message': 'Invalid plan or company.'}, status=404)
        except Exception as e:
            logger.error(f"Error in payment_callback_view: {e}")
            return JsonResponse({'message': f'An unexpected error occurred: {e}'}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)


@csrf_exempt
def activate_token(request, company_id):
    """
    Activates a WiFi session using a valid token and the user's IP address.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get("token")
            ip_address = get_user_ip(request)

            if not token:
                return JsonResponse({'message': 'Token is required.'}, status=400)
            
            session = get_object_or_404(WifiSession, token=token, company__id=company_id)

            if session.is_active:
                return JsonResponse({"message": "Your session is already active.", "expires_at": session.end_time})

            if session.end_time and session.end_time < timezone.now():
                 return JsonResponse({"message": "This token has expired and cannot be activated."}, status=400)
            
            session.activate(ip_address)

            return JsonResponse({
                "message": "Session activated.", 
                "expires_at": session.end_time
            })
            
        except WifiSession.DoesNotExist:
            return JsonResponse({'message': 'Invalid token.'}, status=404)
        except Exception as e:
            return JsonResponse({'message': f'An error occurred: {e}'}, status=500)
            
    return JsonResponse({'message': 'Invalid request method.'}, status=405)


def admin_dashboard(request, company_id):
    """
    Renders a simple dashboard showing all active WiFi sessions for a specific company.
    """
    company = get_object_or_404(Company, id=company_id)
    active_sessions = WifiSession.objects.filter(is_active=True, company=company).order_by('-start_time')
    
    now = timezone.now()
    for session in active_sessions:
        if session.end_time:
            remaining = session.end_time - now
            total_seconds = int(remaining.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            session.time_remaining = f"{hours}h {minutes}m {seconds}s"
        else:
            session.time_remaining = "N/A"
            
    return render(request, 'core/admin_dashboard.html', {
        'active_sessions': active_sessions,
        'company': company
    })
    
def manual_deactivate_session(request, company_id, session_id):
    """
    A view to manually deactivate a specific session for a company.
    """
    company = get_object_or_404(Company, id=company_id)
    session = get_object_or_404(WifiSession, id=session_id, company=company)
    session.deactivate()
    return redirect('admin_dashboard', company_id=company_id)
