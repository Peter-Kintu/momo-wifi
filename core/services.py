import os
import requests
import json
import uuid
import routeros_api
from django.conf import settings
from django.utils import timezone
from .models import Payment, WifiSession, Plan
from .airtel_api import initiate_airtel_payment_request # Import the new Airtel API functions


def create_mikrotik_user(phone_number, plan: Plan):
    """
    This function connects to the MikroTik router and creates a new user
    account for the paid session.
    """
    try:
        api = routeros_api.RouterOsApiPool(
            host=settings.MIKROTIK_HOST,
            username=settings.MIKROTIK_USER,
            password=settings.MIKROTIK_PASSWORD,
            port=8728,
            use_ssl=False,
        )
        api.get_api().get_resource('/ip/hotspot/user').add(
            name=phone_number,
            password=str(uuid.uuid4())[:8],  # A simple, random password
            profile=plan.mikrotik_profile_name,
            limit_uptime=f"{plan.duration_minutes}m"
        )
        api.disconnect()

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
    except Exception as e:
        print(f"Error connecting to MikroTik or creating user: {e}")
        # In a real-world scenario, you would handle this gracefully,
        # perhaps by marking the payment as 'pending_mikrotik_creation'
        # and retrying later.
        return None

def initiate_airtel_payment(phone_number, plan: Plan):
    """
    Orchestrates the payment process with the Airtel API.
    
    Args:
        phone_number (str): The phone number to charge.
        plan (Plan): The plan object selected by the user.

    Returns:
        tuple: A boolean for success and a message or transaction ID.
    """
    try:
        # Create a unique transaction ID for our records
        transaction_id = f"AIRTEL_{uuid.uuid4().hex}"

        # Create a new payment record in our database
        Payment.objects.create(
            phone_number=phone_number,
            plan=plan,
            amount=plan.price,
            status='pending',
            transaction_id=transaction_id
        )

        # Construct the payload for the Airtel API call
        payload = {
            "reference": "WiFi Access",
            "subscriber": {
                "country": "UG",
                "currency": "UGX",
                "msisdn": phone_number[-9:] # Airtel requires msisdn without country code
            },
            "transaction": {
                "amount": str(plan.price), # Ensure amount is a string
                "id": transaction_id
            }
        }

        # Make the API call to Airtel
        success, response = initiate_airtel_payment_request(payload)

        if success and response.get("status", {}).get("success"):
            return True, transaction_id
        else:
            error_message = response.get("status", {}).get("message", "Airtel API error")
            # Update the payment status to failed if the API call was unsuccessful
            payment = Payment.objects.get(transaction_id=transaction_id)
            payment.status = 'failed'
            payment.save()
            return False, error_message

    except Exception as e:
        print(f"Airtel payment initiation failed: {e}")
        return False, "Failed to initiate Airtel payment."
