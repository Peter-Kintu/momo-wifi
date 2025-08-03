import os
import requests
import json
import uuid
import routeros_api
from django.conf import settings
from django.utils import timezone
from .models import Payment, WifiSession, Plan
from requests.exceptions import RequestException
import logging

# Set up logging for better error tracking
logger = logging.getLogger(__name__)

# This is a placeholder for your MikroTik integration.
def create_mikrotik_user(phone_number, plan: Plan):
    """
    This function connects to the MikroTik router and creates a new user
    account for the paid session.
    """
    try:
        # Load MikroTik credentials from settings
        mikrotik_host = settings.MIKROTIK_HOST
        mikrotik_user = settings.MIKROTIK_USER
        mikrotik_password = settings.MIKROTIK_PASSWORD
        mikrotik_port = 8728 # Default API port

        # Connect to the MikroTik router API
        api = routeros_api.RouterOsApiPool(
            host=mikrotik_host,
            username=mikrotik_user,
            password=mikrotik_password,
            port=mikrotik_port,
            use_ssl=False,
        )

        # Create a new user in the hotspot user list
        api.get_api().get_resource('/ip/hotspot/user').add(
            name=phone_number,
            password=str(uuid.uuid4())[:8],  # Generate a simple, random password
            profile=plan.mikrotik_profile_name,
            limit_uptime=f"{plan.duration_minutes}m"
        )
        api.disconnect()

        # Generate a unique token for the user session
        token = str(uuid.uuid4())[:8].upper()
        end_time = timezone.now() + timezone.timedelta(minutes=plan.duration_minutes)

        # Save the session to your Django database
        WifiSession.objects.create(
            phone_number=phone_number,
            plan=plan,
            token=token,
            end_time=end_time
        )
        logger.info(f"MikroTik user and WifiSession created for {phone_number} with token: {token}")
        return token
    except Exception as e:
        logger.error(f"Error creating MikroTik user: {e}")
        raise RuntimeError("Failed to create MikroTik user.")


def initiate_flutterwave_payment_backend(phone_number, plan_id):
    """
    Prepares the necessary data for the Flutterwave checkout.
    This function creates a unique transaction reference and fetches the plan details.
    """
    try:
        plan = Plan.objects.get(id=plan_id)
        # Create a unique transaction reference
        tx_ref = f"WIFI_PAYMENT_{uuid.uuid4().hex}"

        # Create a placeholder payment record in the database
        Payment.objects.create(
            phone_number=phone_number,
            plan=plan,
            amount=plan.price,
            status='pending',
            transaction_id=tx_ref
        )

        # Prepare data for the frontend Flutterwave checkout popup
        return {
            "public_key": settings.FLUTTERWAVE_PUBLIC_KEY,
            "tx_ref": tx_ref,
            "amount": float(plan.price),
            "currency": "UGX",  # Hardcoded for Ugandan Shillings as per the user's context
            "phone_number": phone_number,
            # Placeholder values for customer details
            "email": "customer@example.com",
            "name": "WiFi User"
        }
    except Plan.DoesNotExist:
        logger.error(f"Plan with id {plan_id} not found.")
        raise ValueError("Selected plan does not exist.")
    except Exception as e:
        logger.error(f"Error initiating Flutterwave payment backend: {e}")
        raise RuntimeError("An internal server error occurred.")


def verify_flutterwave_payment(tx_ref, transaction_id):
    """
    Verifies a payment with Flutterwave's API and updates the payment status.
    """
    try:
        # Build the verification URL
        url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"
        }

        # Make the request to Flutterwave's API
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        payment_data = response.json()

        if payment_data['status'] == 'success' and payment_data['data']['status'] == 'successful':
            payment = Payment.objects.get(transaction_id=tx_ref)
            payment.status = 'successful'
            payment.save()
            logger.info(f"Payment verification successful for transaction {tx_ref}")

            # Now that payment is confirmed, create the MikroTik user
            token = create_mikrotik_user(payment.phone_number, payment.plan)
            return token
        else:
            payment = Payment.objects.get(transaction_id=tx_ref)
            payment.status = 'failed'
            payment.save()
            logger.warning(f"Payment verification failed for transaction {tx_ref}. Status: {payment_data.get('data', {}).get('status')}")
            raise ValueError("Payment verification failed.")

    except Payment.DoesNotExist:
        logger.error(f"Payment record with transaction_id {tx_ref} not found.")
        raise ValueError("Payment transaction not found.")
    except RequestException as e:
        logger.error(f"Flutterwave API request failed: {e}")
        raise RuntimeError("Failed to connect to the payment gateway.")
    except Exception as e:
        logger.error(f"Unexpected error during payment verification: {e}")
        raise RuntimeError("An internal server error occurred.")
