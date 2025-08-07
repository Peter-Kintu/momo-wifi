# wifi_hotspot/core/payment_services.py

import requests
import json
import logging
import uuid
from django.utils import timezone
from django.db import transaction

from .models import Company, WifiSession, Payment, Plan
from .savanna_api import create_savanna_user, disable_savanna_user

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
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes
        token_data = response.json()
        return token_data.get('access_token')
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting Airtel access token for company '{company.name}': {e}")
        return None

def initiate_airtel_payment(session: WifiSession):
    """
    Initiates a payment request with Airtel Money.
    This function is a placeholder and would be replaced with actual API calls.
    """
    company = session.company
    
    # Placeholder for a successful payment response from Airtel
    # In a real scenario, this would be an API call to Airtel, which returns a transaction ID.
    transaction_id = str(uuid.uuid4())
    
    # Create a pending payment record
    payment = Payment.objects.create(
        session=session,
        transaction_id=transaction_id,
        amount=session.plan.price,
        status='Pending'
    )
    
    logger.info(f"Simulated payment initiation for session {session.id}, transaction_id: {transaction_id}")
    return True, transaction_id


@transaction.atomic
def handle_airtel_payment_callback(company, transaction_id: str):
    """
    Handles the callback from the Airtel payment gateway.
    This function finds the pending payment and activates the session.
    """
    try:
        payment = Payment.objects.get(transaction_id=transaction_id)
        session = payment.session
        
        # Mark the payment as successful
        payment.status = 'Success'
        payment.save()
        
        # Activate the session and create the Savanna user
        session.activate(session.ip_address)
        
        return True, "Payment and session activation successful."
            
    except Payment.DoesNotExist:
        logger.error(f"Airtel callback received for non-existent transaction ID: {transaction_id}")
        return False, "Transaction not found."
    except Exception as e:
        logger.error(f"An unexpected error occurred processing Airtel callback for transaction {transaction_id}: {e}")
        return False, f"An internal error occurred: {e}"
