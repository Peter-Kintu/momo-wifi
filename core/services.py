import os
import requests
import json
import uuid
from django.conf import settings
from django.utils import timezone
from .models import Payment, WifiSession, Plan
from mtnmomo.collection import Collection

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
        collections = Collection({
            'COLLECTIONS_API_KEY': settings.MOMO_COLLECTIONS_API_KEY,
            'MOMO_API_USER_ID': settings.MOMO_API_USER_ID,
            'MOMO_API_KEY': settings.MOMO_API_KEY,
            'TARGET_ENVIRONMENT': settings.MOMO_TARGET_ENVIRONMENT,
        })
    except Exception as e:
        print(f"Error initializing MoMo collections: {e}")
        return False, "Failed to initialize payment gateway. Please check your API credentials."

    try:
        print(f"Attempting MoMo payment for phone: {phone_number}, amount: {amount}, transaction_id: {transaction_id}")
        
        # Corrected parameter name from 'msisdn' to 'mobile'
        response = collections.requestToPay(
            mobile=phone_number,
            amount=str(amount),
            external_id=transaction_id,
            payer_message="Payment for Wi-Fi hotspot",
            payee_note="Wi-Fi Hotspot Service"
        )
        
        # --- ENHANCED LOGGING ---
        print("--- MoMo API Response Start ---")
        print(f"Status Code: {response.get('status_code')}")
        print(f"Response Body: {response.get('json_response')}")
        print("--- MoMo API Response End ---")

        if response.get('status_code') == 202:
            return True, "Payment request sent successfully."
        else:
            error_message = response.get('json_response', {}).get('message', 'Payment initiation failed.')
            return False, error_message
    except Exception as e:
        print(f"Exception during MoMo payment initiation: {e}")
        return False, "An error occurred while initiating the payment."

# New function to check the status of a payment request
def check_payment_status(transaction_id):
    """
    Checks the status of a payment request using the MTN MoMo API.
    """
    try:
        collections = Collection({
            'COLLECTIONS_API_KEY': settings.MOMO_COLLECTIONS_API_KEY,
            'MOMO_API_USER_ID': settings.MOMO_API_USER_ID,
            'MOMO_API_KEY': settings.MOMO_API_KEY,
            'TARGET_ENVIRONMENT': settings.MOMO_TARGET_ENVIRONMENT,
        })
        response = collections.requestToPayStatus(transaction_id)
        return response.get('json_response', {})
    except Exception as e:
        print(f"Error checking payment status: {e}")
        return {"status": "failed", "message": "Failed to check payment status."}
