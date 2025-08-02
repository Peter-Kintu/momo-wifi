# wifi_hotspot/services.py

import os
import requests
import json
import uuid
from django.conf import settings
from django.utils import timezone
from .models import Payment, WifiSession, Plan
from mtnmomo.collection import Collection

# --- MikroTik Integration Placeholder ---
def create_mikrotik_user(phone_number, plan: Plan):
    """
    This function connects to the MikroTik router and creates a new user.
    The implementation is a placeholder, as the actual MikroTik API call
    would require specific router details and API configuration.
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

    print(f"MikroTik user created with token: {token}")
    return token

# --- MoMo API Integration ---
def initiate_momo_payment(phone_number, amount, transaction_id):
    """
    Initiates a payment request using the MTN MoMo API.
    
    Args:
        phone_number (str): The phone number to be debited (e.g., '256771234567').
        amount (Decimal): The amount to request.
        transaction_id (str): A unique identifier for the transaction.
        
    Returns:
        tuple: A tuple containing (success_status, message).
    """
    try:
        # Initialize the MoMo API collection client
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
        
        # The mtnmomo library's requestToPay method expects 'mobile' as the phone number parameter
        response = collections.requestToPay(
            mobile=phone_number,
            amount=str(amount),
            external_id=transaction_id,
            payer_message="Payment for Wi-Fi hotspot",
            payee_note="Wi-Fi Hotspot Service"
        )
        
        # Enhanced logging for debugging
        print("--- MoMo API Response Start ---")
        print(f"Status Code: {response.get('status_code')}")
        print(f"Response Body: {response.get('json_response')}")
        print("--- MoMo API Response End ---")

        # Check if the request was successful (status code 202)
        if response.get('status_code') == 202:
            return True, "Payment request sent successfully."
        else:
            # If the request fails, return a more specific error message from the API response
            error_message = response.get('json_response', {}).get('message', 'Payment initiation failed.')
            return False, error_message
    except Exception as e:
        print(f"Exception during MoMo payment: {e}")
        return False, f"An error occurred while processing the payment: {e}"

def check_payment_status(transaction_id):
    """
    Checks the status of a payment using the MTN MoMo API.
    This is a placeholder and should be implemented with an actual API call.
    """
    print(f"Checking status for transaction ID: {transaction_id}")
    return "pending" # Or "successful", "failed"
