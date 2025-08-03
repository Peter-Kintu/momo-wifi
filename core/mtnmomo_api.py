import os
import requests
import json
from django.conf import settings
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin

# Helper function to get the MTN MoMo API credentials
def get_momo_credentials():
    """
    Retrieves MTN MoMo API credentials from Django settings.
    """
    return {
        'MOMO_API_USER_ID': settings.MOMO_API_USER_ID,
        'MOMO_API_KEY': settings.MOMO_API_KEY,
        'MOMO_TARGET_ENVIRONMENT': settings.MOMO_TARGET_ENVIRONMENT,
        'MOMO_COLLECTIONS_PRIMARY_KEY': settings.COLLECTION_PRIMARY_KEY,
        'MOMO_CALLBACK_URL': os.getenv('MOMO_CALLBACK_URL')
    }

def get_access_token():
    """
    Retrieves an access token from the MTN MoMo API.
    """
    credentials = get_momo_credentials()
    api_user_id = credentials.get('MOMO_API_USER_ID')
    api_key = credentials.get('MOMO_API_KEY')
    collections_primary_key = credentials.get('MOMO_COLLECTIONS_PRIMARY_KEY')

    url = "https://sandbox.momodeveloper.mtn.com/collection/token/"

    try:
        response = requests.post(
            url,
            auth=HTTPBasicAuth(api_user_id, api_key),
            headers={
                'Ocp-Apim-Subscription-Key': collections_primary_key,
                'Content-Type': 'application/json'
            }
        )
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving MTN MoMo access token: {e}")
        return None

def request_to_pay(access_token, phone_number, amount, transaction_id):
    """
    Initiates a payment request using the MTN MoMo API.
    """
    credentials = get_momo_credentials()
    collections_primary_key = credentials.get('MOMO_COLLECTIONS_PRIMARY_KEY')
    target_environment = credentials.get('MOMO_TARGET_ENVIRONMENT')
    callback_url = credentials.get('MOMO_CALLBACK_URL')

    url = "https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay"

    # Per your instructions, the payload is constructed with the correct sandbox values.
    # The 'partyId' is hardcoded to a valid sandbox test MSISDN.
    payload = {
        "amount": str(amount),
        "currency": "UGX",
        "externalId": transaction_id,
        "payer": {
            "partyIdType": "MSISDN",
            # This is the hardcoded sandbox test MSISDN as per your guidance.
            "partyId": "46733123454"
        },
        "payerMessage": "WiFi Payment",
        "payeeNote": "Testing MoMo API"
    }

    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Reference-Id': transaction_id,
        'X-Target-Environment': target_environment,
        'Ocp-Apim-Subscription-Key': collections_primary_key,
        'Content-Type': 'application/json',
        'X-Callback-Url': callback_url
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"MTN MoMo API Response: {response.status_code}")
        return True, "Payment request sent successfully."

    except requests.exceptions.RequestException as e:
        print(f"Error initiating payment request: {e}")
        return False, "Failed to initiate payment."

def get_payment_status(access_token, transaction_id):
    """
    Checks the status of a specific payment request.
    """
    credentials = get_momo_credentials()
    collections_primary_key = credentials.get('MOMO_COLLECTIONS_PRIMARY_KEY')
    target_environment = credentials.get('MOMO_TARGET_ENVIRONMENT')
    
    url = f"https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay/{transaction_id}"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Target-Environment': target_environment,
        'Ocp-Apim-Subscription-Key': collections_primary_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        payment_data = response.json()
        return True, payment_data.get('status')
    except requests.exceptions.RequestException as e:
        print(f"Error checking payment status: {e}")
        return False, "Failed to check payment status."
