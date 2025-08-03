import os
import requests
import json
import uuid
from django.conf import settings
from django.utils import timezone
from .models import Payment, WifiSession, Plan
from .mtnmomo_api import request_to_pay, get_payment_status

# This is no longer imported from this file, but from the new routeros_api.py
# from .routeros_api import create_mikrotik_user


def initiate_momo_payment(phone_number, amount, transaction_id):
    """
    Initiates a payment request using the MTN MoMo API.

    This function now calls the refactored `request_to_pay` which handles its own
    access token internally, simplifying the call.
    """
    try:
        # The new request_to_pay function only requires these three arguments.
        # This is the line that was causing the error previously.
        success, message = request_to_pay(phone_number, str(amount), transaction_id)

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

    This function now calls the refactored `get_payment_status` which handles its own
    access token internally, simplifying the call.
    """
    try:
        # The new get_payment_status function only requires the transaction_id.
        success, status = get_payment_status(transaction_id)

        if success:
            return True, status
        else:
            return False, status

    except Exception as e:
        print(f"Error in check_momo_payment_status: {e}")
        return False, "An unexpected error occurred while checking payment status."
