import os
import requests
import json
import uuid
import routeros_api
from django.conf import settings
from django.utils import timezone
from .models import Payment, WifiSession, Plan
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

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
            use_ssl=False
        )
        api.get_api().get_resource('/ip/hotspot/user').add(
            name=phone_number,
            password=str(uuid.uuid4())[:8],
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
        logger.info(f"MikroTik user successfully created for {phone_number} with token: {token}")
        return token
    except Exception as e:
        logger.error(f"Failed to create MikroTik user: {e}", exc_info=True)
        return None

def get_momo_access_token():
    """
    Retrieves an access token for the MoMo API.
    """
    headers = {
        'Ocp-Apim-Subscription-Key': settings.MOMO_COLLECTIONS_API_KEY,
        'Authorization': f'Basic {settings.MOMO_CLIENT_ID}',
    }
    
    url = f"https://{settings.MOMO_TARGET_ENVIRONMENT}.mtn.com/oauth2/token"
    data = {'grant_type': 'client_credentials'}

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting MoMo access token: {e}", exc_info=True)
        return None

def initiate_momo_payment(phone_number, amount, transaction_id):
    """
    Initiates a payment request using direct HTTP calls to the MTN MoMo API.
    """
    access_token = get_momo_access_token()
    if not access_token:
        return False, "Failed to get MoMo access token."

    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Reference-Id': transaction_id,
        'X-Target-Environment': settings.MOMO_TARGET_ENVIRONMENT,
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': settings.MOMO_COLLECTIONS_API_KEY,
    }

    payload = {
        "amount": str(amount),
        "currency": "EUR",  # Adjust currency if needed
        "externalId": transaction_id,
        "payer": {
            "partyIdType": "MSISDN",
            "partyId": phone_number
        },
        "payerMessage": "Payment for Wi-Fi hotspot",
        "payeeNote": "Wi-Fi Hotspot Service"
    }

    url = f"https://{settings.MOMO_TARGET_ENVIRONMENT}.mtn.com/collection/v1_0/requesttopay"
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        logger.info("--- MoMo API Response Start ---")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Body: {response.text}")
        logger.info("--- MoMo API Response End ---")

        if response.status_code == 202:
            return True, "Payment request sent successfully."
        else:
            try:
                error_message = response.json().get('message', 'Payment initiation failed.')
            except json.JSONDecodeError:
                error_message = f"Payment initiation failed with status code {response.status_code}."
            return False, error_message
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception during MoMo payment initiation: {e}", exc_info=True)
        return False, f"An error occurred while initiating the payment: {e}"

def check_payment_status(transaction_id):
    """
    Checks the status of a payment using the MTN MoMo API.
    """
    access_token = get_momo_access_token()
    if not access_token:
        return None

    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Target-Environment': settings.MOMO_TARGET_ENVIRONMENT,
        'Ocp-Apim-Subscription-Key': settings.MOMO_COLLECTIONS_API_KEY,
    }
    
    url = f"https://{settings.MOMO_TARGET_ENVIRONMENT}.mtn.com/collection/v1_0/requesttopay/{transaction_id}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('status')
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception during MoMo payment status check: {e}", exc_info=True)
        return None
