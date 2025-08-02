import os
import requests
import base64
import uuid
from django.conf import settings

# This file contains the low-level functions for interacting with the MTN MoMo API directly
# without relying on the third-party 'mtnmomo' library.

def get_access_token():
    """
    Retrieves an access token from the MTN MoMo API.
    
    Returns:
        str: The access token string if successful, otherwise None.
    """
    try:
        api_user_id = settings.MOMO_API_USER_ID
        api_key = settings.MOMO_API_KEY
        
        # Base64 encode the API user ID and API key
        auth_string = f"{api_user_id}:{api_key}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        # API endpoint for token
        token_url = f"https://{settings.MOMO_TARGET_ENVIRONMENT}.mtn.com/collection/token/"
        
        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Ocp-Apim-Subscription-Key": settings.MOMO_COLLECTIONS_API_KEY
        }

        print(">>> Attempting to get MoMo access token...")
        response = requests.post(token_url, headers=headers)
        
        response.raise_for_status()  # Raise an exception for bad status codes
        
        token = response.json().get('access_token')
        print(">>> MoMo access token retrieved successfully.")
        return token
        
    except requests.exceptions.RequestException as e:
        print(f"Error getting MoMo access token: {e}")
        return None

def request_to_pay(access_token, phone_number, amount, external_id):
    """
    Initiates a payment request using the MTN MoMo API.
    
    Args:
        access_token (str): The valid access token.
        phone_number (str): The mobile number of the payer.
        amount (str): The amount to request.
        external_id (str): A unique identifier for the transaction.
        
    Returns:
        tuple: (success, message)
    """
    if not access_token:
        return False, "Failed to get access token."

    try:
        request_to_pay_url = f"https://{settings.MOMO_TARGET_ENVIRONMENT}.mtn.com/collection/v1_0/requesttopay"
        
        # Generate a unique reference for the transaction
        transaction_ref = str(uuid.uuid4())

        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Reference-Id": transaction_ref,
            "X-Target-Environment": settings.MOMO_TARGET_ENVIRONMENT,
            "Ocp-Apim-Subscription-Key": settings.MOMO_COLLECTIONS_API_KEY,
            "Content-Type": "application/json"
        }
        
        data = {
            "amount": amount,
            "currency": "EUR", # NOTE: This should be configured based on the API requirements
            "externalId": external_id,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone_number
            },
            "payerMessage": "Payment for Wi-Fi Hotspot",
            "payeeNote": "Wi-Fi Hotspot Service"
        }
        
        print(f">>> Attempting MoMo payment for phone: {phone_number}, amount: {amount}, external_id: {external_id}")
        response = requests.post(request_to_pay_url, headers=headers, json=data)
        
        print("--- MoMo API Response Start ---")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        print("--- MoMo API Response End ---")
        
        if response.status_code == 202:
            return True, "Payment request sent successfully."
        else:
            error_message = response.json().get('message', 'Payment initiation failed.')
            return False, error_message
    
    except requests.exceptions.RequestException as e:
        print(f"Error making request to pay: {e}")
        return False, "Failed to communicate with the payment gateway."
        
def get_payment_status(access_token, external_id):
    """
    Checks the status of a payment request.
    
    Args:
        access_token (str): The valid access token.
        external_id (str): The unique identifier for the transaction.
        
    Returns:
        tuple: (success, status) where status is the payment state or an error message.
    """
    if not access_token:
        return False, "Failed to get access token."
        
    try:
        check_status_url = f"https://{settings.MOMO_TARGET_ENVIRONMENT}.mtn.com/collection/v1_0/requesttopay/{external_id}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Target-Environment": settings.MOMO_TARGET_ENVIRONMENT,
            "Ocp-Apim-Subscription-Key": settings.MOMO_COLLECTIONS_API_KEY,
        }
        
        response = requests.get(check_status_url, headers=headers)
        response.raise_for_status()
        
        payment_status = response.json().get('status')
        return True, payment_status
        
    except requests.exceptions.RequestException as e:
        print(f"Error checking payment status: {e}")
        return False, "Failed to retrieve payment status."
