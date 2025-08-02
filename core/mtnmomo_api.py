import requests
import json
from django.conf import settings

def get_access_token():
    """
    Retrieves an access token from the MTN MoMo API.
    """
    try:
        api_user_id = settings.MOMO_API_USER_ID
        api_key = settings.MOMO_API_KEY
        target_env = settings.MOMO_TARGET_ENVIRONMENT

        # Check if environment variables are set
        if not all([api_user_id, api_key, target_env]):
            print("Error: Missing MTN MoMo API credentials in settings.")
            return None
        
        # NOTE: Using a hardcoded URL for demonstration. In a real-world scenario,
        # this should be configurable via settings.
        url = f"https://{target_env}.mtn.com/collection/token/"
        headers = {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': api_key
        }
        auth = (api_user_id, api_key)

        print("Attempting to get MoMo access token...")
        response = requests.post(url, headers=headers, auth=auth)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        access_token_data = response.json()
        print("MoMo access token retrieved successfully.")
        return access_token_data.get('access_token')

    except requests.exceptions.ConnectionError as e:
        print(f"ConnectionError getting MoMo access token: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error getting MoMo access token: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while getting access token: {e}")
        return None

def request_to_pay(access_token, mobile, amount, external_id):
    """
    Sends a request-to-pay to the MTN MoMo API.
    """
    try:
        api_key = settings.MOMO_API_KEY
        target_env = settings.MOMO_TARGET_ENVIRONMENT

        url = f"https://{target_env}.mtn.com/collection/v1_0/requesttopay"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Reference-Id': external_id,
            'X-Target-Environment': target_env,
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': api_key
        }

        payload = {
            "amount": amount,
            "currency": "EUR", # NOTE: Change this to your local currency code.
            "externalId": external_id,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": mobile
            },
            "payerMessage": "Payment for Wi-Fi hotspot",
            "payeeNote": "Wi-Fi Hotspot Service"
        }

        print(f"Attempting MoMo payment for mobile: {mobile}, amount: {amount}, transaction_id: {external_id}")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        # Log the full response for debugging
        print("--- MoMo API RequestToPay Response Start ---")
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response Body: {response.json()}")
        except json.JSONDecodeError:
            print(f"Response Body (non-JSON): {response.text}")
        print("--- MoMo API RequestToPay Response End ---")

        if response.status_code in [200, 201, 202]:
            return True, "Payment request sent successfully."
        else:
            error_message = response.json().get('message', 'Payment initiation failed.')
            return False, error_message
    
    except requests.exceptions.ConnectionError as e:
        print(f"ConnectionError during RequestToPay: {e}")
        return False, "Server network error. Unable to connect to the payment gateway."
    except Exception as e:
        print(f"An unexpected error occurred during MoMo payment: {e}")
        return False, "An unexpected error occurred while initiating payment."


def get_payment_status(access_token, external_id):
    """
    Checks the status of a payment.
    """
    try:
        api_key = settings.MOMO_API_KEY
        target_env = settings.MOMO_TARGET_ENVIRONMENT

        url = f"https://{target_env}.mtn.com/collection/v1_0/requesttopay/{external_id}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Target-Environment': target_env,
            'Ocp-Apim-Subscription-Key': api_key
        }

        print(f"Checking status for transaction ID: {external_id}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        status_data = response.json()
        print(f"Status check response: {status_data}")
        return True, status_data.get('status')
    
    except requests.exceptions.ConnectionError as e:
        print(f"ConnectionError during status check: {e}")
        return False, "Server network error. Unable to connect to the payment gateway."
    except requests.exceptions.RequestException as e:
        print(f"Error checking payment status: {e}")
        return False, "Failed to check payment status."
    except Exception as e:
        print(f"An unexpected error occurred while checking payment status: {e}")
        return False, "An unexpected error occurred while checking payment status."
