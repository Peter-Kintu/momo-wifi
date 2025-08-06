# wifi_hotspot/core/mikrotik_api.py

import os
import routeros_api
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def connect_to_mikrotik(company):
    """
    Establishes a connection to the MikroTik router for a specific company.
    Returns the API object or None on failure.
    """
    try:
        api = routeros_api.RouterOsApiPool(
            host=company.mikrotik_host,
            username=company.mikrotik_username,
            password=company.mikrotik_password,
            port=8728, # Default API port
            plaintext_login=True # Set to True if not using SSL
        )
        return api
    except Exception as e:
        logger.error(f"Failed to connect to MikroTik for company '{company.name}': {e}")
        return None

def create_mikrotik_user(company, username, password, plan):
    """
    Creates a new user on the MikroTik hotspot using the provided plan's profile
    for a specific company.
    
    The user will be created but initially disabled.
    """
    api = connect_to_mikrotik(company)
    if not api:
        return False, "Failed to connect to MikroTik."

    try:
        api_resource = api.get_api().get_resource('/ip/hotspot/user')
        
        # Check if the user already exists
        if api_resource.get(name=username):
            api.disconnect()
            return False, f"User '{username}' already exists on MikroTik for company '{company.name}'."

        # Add the new user with its profile
        api_resource.add(
            name=username,
            password=password,
            profile=plan.mikrotik_profile_name,
            # Set the user as disabled initially, it will be enabled on token activation
            disabled='yes'
        )
        api.disconnect()
        return True, "MikroTik user created successfully."
    except Exception as e:
        logger.error(f"Error creating MikroTik user for company '{company.name}': {e}")
        return False, f"Error creating MikroTik user: {e}"

def enable_mikrotik_user(company, username: str):
    """
    Enables a user on the MikroTik hotspot for a specific company.
    """
    api = connect_to_mikrotik(company)
    if not api:
        return False, "Failed to connect to MikroTik."

    try:
        api_resource = api.get_api().get_resource('/ip/hotspot/user')
        # Find the user by their name (the token)
        user_info = api_resource.get(name=username)

        if not user_info:
            api.disconnect()
            return False, f"MikroTik user '{username}' not found for company '{company.name}'."
            
        user_id = user_info[0]['.id']

        # Enable the user
        api_resource.set(
            **{'id': user_id, 'disabled': 'no'}
        )
        api.disconnect()
        return True, "MikroTik user enabled successfully."
    except IndexError:
        logger.error(f"MikroTik user '{username}' not found for company '{company.name}'.")
        api.disconnect()
        return False, f"MikroTik user '{username}' not found."
    except Exception as e:
        logger.error(f"Error enabling MikroTik user for company '{company.name}': {e}")
        api.disconnect()
        return False, f"Error enabling MikroTik user: {e}"

