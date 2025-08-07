# wifi_hotspot/core/savanna_api.py

import requests
import logging

logger = logging.getLogger(__name__)

def connect_to_savanna(company):
    """
    Establishes a connection or returns the base URL and credentials for a Savanna router.
    
    This is a placeholder function. In a real-world scenario, you would
    implement the actual connection logic (e.g., using a specific Savanna SDK
    or a well-defined REST API endpoint and authentication method).
    """
    host = company.savanna_host
    username = company.savanna_username
    password = company.savanna_password
    
    # We will simulate a REST API base URL
    base_url = f"http://{host}/api/v1"
    
    if not host or not username or not password:
        logger.error(f"Missing Savanna credentials for company '{company.name}'.")
        return None, "Missing Savanna credentials."

    # In a real implementation, you would authenticate and return a session object or similar.
    # For now, we'll just return the base URL and credentials.
    return {
        'url': base_url, 
        'auth': (username, password)
    }, "Connected successfully."


def create_savanna_user(company, username: str, ip_address: str, plan):
    """
    Creates a user on the Savanna hotspot using the provided plan's profile.
    
    This is a placeholder for the actual API call. The user is associated with a
    session and their IP address is whitelisted for the plan's duration.
    """
    api_details, message = connect_to_savanna(company)
    if not api_details:
        return False, message

    url = f"{api_details['url']}/users"
    payload = {
        "username": username,
        "password": username, # Using the token as a password for simplicity
        "ip_address": ip_address,
        "profile": plan.name, # Use the plan's name as the profile
        "duration": plan.duration_minutes
    }

    try:
        # Simulate a successful API response
        # response = requests.post(url, json=payload, auth=api_details['auth'], timeout=5)
        # response.raise_for_status() 
        logger.info(f"Simulated creation of Savanna user '{username}' with IP '{ip_address}' for company '{company.name}'.")
        return True, "Savanna user created successfully."
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating Savanna user for company '{company.name}': {e}")
        return False, f"Error creating Savanna user: {e}"


def disable_savanna_user(company, username: str):
    """
    Disables or deletes a user on the Savanna hotspot.
    
    This is a placeholder for the actual API call.
    """
    api_details, message = connect_to_savanna(company)
    if not api_details:
        return False, message
    
    url = f"{api_details['url']}/users/{username}"
    
    try:
        # Simulate a successful API response
        # response = requests.delete(url, auth=api_details['auth'], timeout=5)
        # response.raise_for_status() 
        logger.info(f"Simulated deletion of Savanna user '{username}' for company '{company.name}'.")
        return True, "Savanna user disabled successfully."
    except requests.exceptions.RequestException as e:
        logger.error(f"Error disabling Savanna user '{username}' for company '{company.name}': {e}")
        return False, f"Error disabling Savanna user: {e}"
