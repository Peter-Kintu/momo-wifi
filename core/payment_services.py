# wifi_hotspot/core/payment_services.py

import requests
import json
import logging
import uuid
from django.utils import timezone
from .models import Company, WifiSession, Payment, Plan
from .mikrotik_api import create_mikrotik_user, enable_mikrotik_user # Corrected import

logger = logging.getLogger(__name__)

def get_airtel_access_token(company: Company):
    """
    Authenticates with the Airtel API to get an access token for a given company.
    """
    url = "https://openapi.airtel.africa/auth/oauth2/token"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "client_id": company.airtel_consumer_key,
        "client_secret": company.airtel_consumer_secret,
        "grant_type": "client_credentials"
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Raise an exception for bad status codes
        token_data = response.json()
        return token_data.get('access_token')
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting Airtel access token for company '{company.name}': {e}")
        return None

def initiate_airtel_payment(session: WifiSession, phone_number: str):
    """
    Initiates a "Request to Pay" via the Airtel API.
    """
    company = session.company
    token = get_airtel_access_token(company)
    if not token:
        return False, "Failed to get Airtel access token."

    url = "https://openapi.airtel.africa/merchant/v1/payments/request-to-pay"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-Country": "UG", # Assuming Uganda based on your previous examples
        "X-Currency": "UGX"
    }

    # Generate a unique transaction ID
    transaction_id = str(uuid.uuid4())
    
    # Create the payment entry in our database
    payment = Payment.objects.create(
        company=company,
        session=session,
        airtel_transaction_id=transaction_id,
        status='Pending',
        amount=session.plan.price
    )
    
    payload = {
        "reference": transaction_id,
        "subscriptionId": company.airtel_business_account,
        "amount": session.plan.price,
        "msisdn": phone_number,
        "transactionId": transaction_id
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        payment_data = response.json()
        
        # Check the response status
        if payment_data.get('status', {}).get('code') == 'TS-000':
            return True, "Payment request initiated successfully. Awaiting user approval."
        else:
            payment.status = 'Failed'
            payment.save()
            logger.error(f"Airtel API returned an error for payment: {payment_data}")
            return False, payment_data.get('status', {}).get('message', 'Airtel API Error')

    except requests.exceptions.RequestException as e:
        payment.status = 'Failed'
        payment.save()
        logger.error(f"HTTP request error for Airtel payment for session {session.id}: {e}")
        return False, "An error occurred while communicating with the payment provider."


def handle_airtel_callback(callback_data: dict):
    """
    Processes the callback from the Airtel API to confirm a payment and activate a session.
    """
    transaction_id = callback_data.get('transactionId')
    
    if not transaction_id:
        logger.error("Airtel callback received without a transactionId.")
        return False, "Invalid callback data."
        
    try:
        payment = Payment.objects.get(airtel_transaction_id=transaction_id)
        session = payment.session
        company = session.company
        
        # We assume a successful payment if this function is called and the data is valid.
        payment.status = 'Success'
        payment.save()
        
        # Update the session to reflect a successful payment
        session.payment_status = WifiSession.PAYMENT_SUCCESS
        session.end_time = timezone.now() + timezone.timedelta(minutes=session.plan.duration_minutes)
        session.save()
        
        # Create and enable the user on the MikroTik router
        mikrotik_success, mikrotik_message = create_mikrotik_user(
            company, 
            username=session.token, 
            password=session.token, 
            plan=session.plan
        )
        
        if mikrotik_success:
            # At this point, the user is created but still disabled. We need to enable them.
            enable_mikrotik_success, enable_mikrotik_message = enable_mikrotik_user(
                company, 
                username=session.token
            )
            if enable_mikrotik_success:
                session.is_active = True
                session.save()
                return True, "Payment and session activation successful."
            else:
                logger.error(f"Failed to enable MikroTik user for session {session.id}: {enable_mikrotik_message}")
                return False, f"Payment successful, but failed to enable WiFi: {enable_mikrotik_message}"
        else:
            logger.error(f"Failed to create MikroTik user for session {session.id}: {mikrotik_message}")
            return False, f"Payment successful, but failed to create WiFi user: {mikrotik_message}"
            
    except Payment.DoesNotExist:
        logger.error(f"Airtel callback received for non-existent transaction ID: {transaction_id}")
        return False, "Transaction not found."
    except Exception as e:
        logger.error(f"An unexpected error occurred processing Airtel callback for transaction {transaction_id}: {e}")
        return False, "An internal error occurred."
