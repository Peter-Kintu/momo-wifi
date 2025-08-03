import os
import requests
import json
from django.conf import settings
from requests.auth import HTTPBasicAuth


# Helper function to get the MTN MoMo API credentials
def get_momo_credentials():
    return {
        'MOMO_API_USER_ID': settings.MOMO_API_USER_ID,
        'MOMO_API_KEY': settings.MOMO_API_KEY,
        'MOMO_TARGET_ENVIRONMENT': settings.MOMO_TARGET_ENVIRONMENT,
        'MOMO_COLLECTIONS_PRIMARY_KEY': settings.COLLECTION_PRIMARY_KEY
    }

# This is a placeholder for your MTN MoMo integration.
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
        response.raise_for_status() # Raise an exception for bad status codes
        token_data = response.json()
        return token_data.get('access_token')

    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {e}")
        return None

def request_to_pay(phone_number, amount, transaction_id):
    """
    Initiates a payment request to the user's phone.
    """
    access_token = get_access_token()
    if not access_token:
        return False, "Failed to get access token."

    credentials = get_momo_credentials()
    collections_primary_key = credentials.get('MOMO_COLLECTIONS_PRIMARY_KEY')
    target_environment = credentials.get('MOMO_TARGET_ENVIRONMENT')

    url = f"https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Reference-Id': transaction_id,
        'X-Target-Environment': target_environment,
        'Ocp-Apim-Subscription-Key': collections_primary_key,
        'Content-Type': 'application/json'
    }

    payload = {
        "amount": amount,
        "currency": settings.MOMO_CURRENCY, # This is the missing setting
        "externalId": transaction_id,
        "payer": {
            "partyIdType": "MSISDN",
            "partyId": phone_number
        },
        "payerMessage": "Payment for WiFi Hotspot",
        "payeeNote": "WiFi Hotspot"
    }
    print(f"MTN MoMo API Request Payload: {payload}")

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"MTN MoMo API Response: {response.status_code}")
        return True, "Payment request sent successfully."

    except requests.exceptions.RequestException as e:
        print(f"Error initiating payment request: {e}")
        return False, "Failed to initiate payment."


def get_payment_status(transaction_id):
    """
    Checks the status of a specific payment request.
    """
    access_token = get_access_token()
    if not access_token:
        return False, "Failed to get access token."

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
