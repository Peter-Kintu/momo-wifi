import os
import requests
import json
import uuid
from requests.auth import HTTPBasicAuth
from django.conf import settings

# This file contains the logic for interacting with the MTN MoMo API directly using the requests library.
# This version includes fixes based on a detailed analysis of the API's behavior in the sandbox environment.

def get_access_token():
    """
    Requests an access token from the MTN MoMo API using HTTPBasicAuth.
    This is the first step in making any API call.
    """
    url = f"https://{settings.MOMO_TARGET_ENVIRONMENT}.momodeveloper.mtn.com/collection/token/"
    
    # These are the credentials for basic authentication, specific to the sandbox environment.
    api_user = settings.MOMO_API_USER_ID
    api_key = settings.MOMO_API_KEY
    
    # This is your API subscription key.
    subscription_key = settings.MOMO_COLLECTIONS_API_KEY
    
    if not all([api_user, api_key, subscription_key]):
        print("Error: Missing MTN MoMo API credentials in environment variables.")
        return None

    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/json"
    }
    
    try:
        # Use HTTPBasicAuth to send the credentials for the token request.
        response = requests.post(
            url,
            headers=headers,
            auth=HTTPBasicAuth(api_user, api_key)
        )
        response.raise_for_status()
        
        # The access token is in the response body.
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error getting MoMo access token: {e}")
        return None

def request_to_pay(phone_number, amount, transaction_id):
    """
    Sends a request-to-pay to the MTN MoMo API.
    
    Args:
        phone_number (str): The user's phone number (e.g., '0789746493' or '256789746493').
        amount (str): The amount to be requested.
        transaction_id (str): A unique transaction ID (UUID).
    
    Returns:
        tuple: (success, message)
    """
    access_token = get_access_token()
    if not access_token:
        return False, "Failed to get access token."

    url = f"https://{settings.MOMO_TARGET_ENVIRONMENT}.momodeveloper.mtn.com/collection/v1_0/requesttopay"
    
    subscription_key = settings.MOMO_COLLECTIONS_API_KEY
    # The callback URL is not needed for the requesttopay call itself,
    # it's configured in the API user settings, but we still need the
    # value for other callbacks, so we'll leave it in the settings.
    currency = settings.MOMO_CURRENCY
    
    if not all([subscription_key, currency]):
        print("Error: Missing subscription key or currency for payment request.")
        return False, "Missing configuration."

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Reference-Id": transaction_id,
        "X-Target-Environment": settings.MOMO_TARGET_ENVIRONMENT,
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/json",
    }
    
    # Normalize the phone number format
    formatted_phone_number = phone_number.strip()
    if formatted_phone_number.startswith('07'):
        # If it starts with '07', remove the '0' and prepend '256'
        formatted_phone_number = '256' + formatted_phone_number[1:]
    elif formatted_phone_number.startswith('256'):
        # If it already starts with '256', use it as is
        pass
    else:
        # Invalid format
        return False, "Invalid phone number format. Expected format: '07xxxxxxxx' or '2567xxxxxxxx'."
        
    if not formatted_phone_number.isdigit() or len(formatted_phone_number) != 12:
        return False, "Invalid phone number format. The number must be 12 digits long."
        
    payload = {
        "amount": str(amount),
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
        # Add debugging statements to see the full request and response
        print(">>> MoMo API Request Details")
        print("URL:", url)
        print("Headers:", headers)
        print("Payload:", payload)
        
        # Use json=payload for requests, which automatically sets the Content-Type header
        response = requests.post(url, headers=headers, json=payload)

        print(">>> MoMo API Response Details")
        print("Response Status:", response.status_code)
        print("Response Text:", response.text)

        response.raise_for_status()
        
        if response.status_code == 202:
            return True, "Payment request accepted"
        else:
            return False, f"Unexpected response status: {response.status_code}"
    except requests.exceptions.RequestException as e:
        print(f"Error in request_to_pay: {e}")
        return False, f"An error occurred: {e}"

def get_payment_status(transaction_id):
    """
    Checks the status of a request-to-pay transaction.
    """
    access_token = get_access_token()
    if not access_token:
        return False, "Failed to get access token."

    url = f"https://{settings.MOMO_TARGET_ENVIRONMENT}.momodeveloper.mtn.com/collection/v1_0/requesttopay/{transaction_id}"
    
    subscription_key = settings.MOMO_COLLECTIONS_API_KEY
    if not subscription_key:
        print("Error: Missing subscription key for payment status check.")
        return False, "Missing configuration."

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Target-Environment": settings.MOMO_TARGET_ENVIRONMENT,
        "Ocp-Apim-Subscription-Key": subscription_key,
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return True, response.json().get("status")
    except requests.exceptions.RequestException as e:
        print(f"Error in get_payment_status: {e}")
        return False, f"An error occurred: {e}"
