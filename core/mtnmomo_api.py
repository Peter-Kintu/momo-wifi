import os
import requests
import json
import uuid
from requests.auth import HTTPBasicAuth
from django.conf import settings

def get_access_token():
    """
    Requests an access token from the MTN MoMo API using HTTPBasicAuth.
    """
    url = f"https://sandbox.momodeveloper.mtn.com/collection/token/"
    
    # Load credentials from environment variables
    api_user = os.getenv("MOMO_COLLECTION_API_USER")
    api_key = os.getenv("MOMO_COLLECTION_API_KEY")
    subscription_key = os.getenv("MOMO_COLLECTION_SUBSCRIPTION_KEY")
    
    # Check if credentials are set
    if not all([api_user, api_key, subscription_key]):
        print("Error: Missing MTN MoMo API credentials in environment variables.")
        return None

    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
    }
    
    try:
        # Use HTTPBasicAuth for the username and password
        response = requests.post(
            url,
            headers=headers,
            auth=HTTPBasicAuth(api_user, api_key)
        )
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        
        # The token is in the response body
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error getting MoMo access token: {e}")
        return None

def request_to_pay(access_token, phone_number, amount, transaction_id):
    """
    Sends a request-to-pay to the MTN MoMo API.
    
    Args:
        access_token (str): The access token for the API.
        phone_number (str): The user's phone number.
        amount (str): The amount to be requested.
        transaction_id (str): A unique transaction ID.
    
    Returns:
        tuple: (success, message)
    """
    url = f"https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay"
    
    subscription_key = os.getenv("MOMO_COLLECTION_SUBSCRIPTION_KEY")
    callback_url = os.getenv("MOMO_CALLBACK_URL")
    currency = os.getenv("MOMO_CURRENCY", "UGX") # Default to UGX if not set
    
    if not all([subscription_key, callback_url]):
        print("Error: Missing subscription key or callback URL for payment request.")
        return False, "Missing configuration."

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Reference-Id": transaction_id,
        "X-Target-Environment": "sandbox",
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/json",
        "X-Callback-Url": callback_url,
    }
    
    # The API expects the phone number in MSISDN format without the leading '0'
    # The `lstrip('0')` is a good start, but we add a check to be more robust
    formatted_phone_number = phone_number.lstrip('0')
    if not formatted_phone_number.isdigit() or len(formatted_phone_number) < 8:
        return False, "Invalid phone number format."
        
    payload = {
        "amount": str(amount), # Amount must be a string
        "currency": currency,
        "externalId": transaction_id,
        "payer": {
            "partyIdType": "MSISDN",
            "partyId": formatted_phone_number
        },
        "payerMessage": "Payment for WiFi access",
        "payeeNote": "WiFi Access"
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        # If the request is accepted, the status code is 202
        if response.status_code == 202:
            return True, "Payment request accepted"
        else:
            return False, f"Unexpected response status: {response.status_code}"
    except requests.exceptions.RequestException as e:
        print(f"Error in request_to_pay: {e}")
        return False, f"An error occurred: {e}"

def get_payment_status(access_token, transaction_id):
    """
    Checks the status of a request-to-pay transaction.
    """
    url = f"https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay/{transaction_id}"
    
    subscription_key = os.getenv("MOMO_COLLECTION_SUBSCRIPTION_KEY")
    if not subscription_key:
        print("Error: Missing subscription key for payment status check.")
        return False, "Missing configuration."

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Target-Environment": "sandbox",
        "Ocp-Apim-Subscription-Key": subscription_key,
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # The status is in the response body
        return True, response.json().get("status")
    except requests.exceptions.RequestException as e:
        print(f"Error in get_payment_status: {e}")
        return False, f"An error occurred: {e}"
