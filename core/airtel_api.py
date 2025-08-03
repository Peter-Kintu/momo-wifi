import os
import requests
import json
import base64
from django.conf import settings

# Placeholder functions for message signing. You will need to replace these
# with actual implementations based on Airtel's documentation. The `cryptography`
# or `PyCryptodome` libraries are good choices for this.

def generate_signature(payload):
    """
    Generates a signature for the request payload using the RSA public key.
    
    The actual implementation will depend on the specific hashing and padding
    scheme required by Airtel.
    
    Args:
        payload (dict): The request body to be signed.
    
    Returns:
        str: The generated signature as a Base64 encoded string.
    """
    if not settings.AIRTEL_MESSAGE_SIGNING_ENABLED:
        return None

    # Example:
    # from cryptography.hazmat.primitives import hashes
    # from cryptography.hazmat.primitives.asymmetric import padding
    # from cryptography.hazmat.primitives.serialization import load_pem_private_key
    
    # private_key = load_pem_private_key(settings.AIRTEL_RSA_PRIVATE_KEY.encode(), password=None)
    # serialized_payload = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    # signature = private_key.sign(
    #     serialized_payload,
    #     padding.PSS(
    #         mgf=padding.MGF1(hashes.SHA256()),
    #         salt_length=padding.PSS.MAX_LENGTH
    #     ),
    #     hashes.SHA256()
    # )
    # return base64.b64encode(signature).decode('utf-8')
    
    # For now, we will return a placeholder.
    return "YOUR_GENERATED_SIGNATURE_HERE"

def generate_encrypted_key():
    """
    Generates and encrypts a symmetric key for the message.
    
    This is typically done by generating a random AES key, encrypting it with
    Airtel's public key, and then Base64 encoding the result.
    
    Returns:
        str: The encrypted key as a Base64 encoded string.
    """
    if not settings.AIRTEL_MESSAGE_SIGNING_ENABLED:
        return None
    
    # For now, we will return a placeholder.
    return "YOUR_ENCRYPTED_KEY_HERE"

def initiate_airtel_payment_request(payload):
    """
    Makes the low-level API call to the Airtel Collection API.

    Args:
        payload (dict): The payment request body.

    Returns:
        tuple: A tuple containing a boolean for success and the response object.
    """
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "X-Country": "UG",  # Assuming Uganda as the country
        "X-Currency": "UGX", # Assuming UGX as the currency
        "Authorization": settings.AIRTEL_ACCESS_TOKEN
    }

    if settings.AIRTEL_MESSAGE_SIGNING_ENABLED:
        headers["x-signature"] = generate_signature(payload)
        headers["x-key"] = generate_encrypted_key()

    try:
        response = requests.post(
            f"{settings.AIRTEL_API_BASE_URL}/merchant/v2/payments/",
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        return True, response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error initiating Airtel payment: {e}")
        return False, {"error": str(e)}

