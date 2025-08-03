import os
import requests
import json
import uuid
from django.conf import settings
from django.utils import timezone
from .models import Payment, WifiSession, Plan
from .mtnmomo_api import get_access_token, request_to_pay, get_payment_status


# The create_mikrotik_user function has been moved to views.py to resolve import issues.

def initiate_momo_payment(phone_number, amount, transaction_id):
    """
    Initiates a payment request using the MTN MoMo API.
    
    Note: The `phone_number` argument is currently not used, as the
    `request_to_pay` function is hardcoded to use a sandbox test MSISDN.
    """
    try:
        # Get an access token for the API call
        access_token = get_access_token()
        if not access_token:
            # The error is already logged in get_access_token, return a simple message.
            return False, "Failed to get access token for payment."
            
        # Use the custom request_to_pay function, passing positional arguments
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
