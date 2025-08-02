import os
import requests
import json
import uuid
from django.conf import settings
from django.utils import timezone
from .models import Payment, WifiSession, Plan
from .mtnmomo_api import get_access_token, request_to_pay, get_payment_status

# This is a placeholder for your MikroTik integration.
def create_mikrotik_user(phone_number, plan: Plan):
    """
    This function will be implemented to connect to the MikroTik router
    and create a new user account for the paid session.
    """
    # Placeholder for the actual MikroTik API call
    token = str(uuid.uuid4())[:8].upper()
    end_time = timezone.now() + timezone.timedelta(minutes=plan.duration_minutes)

    # Save the session to your database
    WifiSession.objects.create(
        phone_number=phone_number,
        plan=plan,
        token=token,
        end_time=end_time
    )

    print(f"MikroTik user would be created with token: {token}")
    return token

def initiate_momo_payment(phone_number, amount, transaction_id):
    """
    Initiates a payment request using the MTN MoMo API.
    """
    try:
        # Get an access token for the API call
        access_token = get_access_token()
        if not access_token:
            return False, "Failed to get access token for payment."
            
        # Use the custom request_to_pay function
        success, message = request_to_pay(access_token, phone_number, str(amount), transaction_id)
        
        if success:
            return True, "Payment request sent successfully."
        else:
            return False, message

    except Exception as e:
        print(f"Error in initiate_momo_payment: {e}")
        return False, "An unexpected error occurred while initiating payment."

def check_momo_payment_status(transaction_id):
    """
    Checks the status of a payment.
    """
    try:
        access_token = get_access_token()
        if not access_token:
            return False, "Failed to get access token to check payment status."
            
        # Use the custom get_payment_status function
        success, status = get_payment_status(access_token, transaction_id)
        
        if success:
            return True, status
        else:
            return False, status
            
    except Exception as e:
        print(f"Error in check_momo_payment_status: {e}")
        return False, "An unexpected error occurred while checking payment status."
