# wifi_hotspot/core/mikrotik_api.py

import os
import routeros_api
from django.conf import settings
from .models import Plan
import logging

logger = logging.getLogger(__name__)

def connect_to_mikrotik():
    """
    Establishes a connection to the MikroTik router using settings from .env.
    Returns the API object or None on failure.
    """
    try:
        api = routeros_api.RouterOsApiPool(
            host=settings.MIKROTIK_HOST,
            username=settings.MIKROTIK_USER,
            password=settings.MIKROTIK_PASSWORD,
            port=8728, # Default API port
            use_ssl=False
        )
        return api
    except Exception as e:
        logger.error(f"Failed to connect to MikroTik: {e}")
        return None

def create_mikrotik_user(username: str, password: str, plan: Plan):
    """
    Creates a new user on the MikroTik hotspot using the provided plan's profile.
    
    This function should be called by the admin action when generating a token.
    The user will be created but initially disabled.
    """
    api = connect_to_mikrotik()
    if not api:
        return False, "Failed to connect to MikroTik."

    try:
        # Use the plan's mikrotik_profile_name to map the user to the correct profile
        api_resource = api.get_api().get_resource('/ip/hotspot/user')
        api_resource.add(
            name=username,
            password=password,
            profile=plan.mikrotik_profile_name,
            # We add a comment to make it easier to identify the session later
            comment=f"Token for {username} - {plan.name}",
            # Set disabled=yes initially. The user will be enabled on token activation.
            disabled='yes'
        )
        api.disconnect()
        return True, "MikroTik user created successfully."
    except Exception as e:
        logger.error(f"Error creating MikroTik user: {e}")
        return False, f"Error creating MikroTik user: {e}"

def enable_mikrotik_user(username: str):
    """
    Enables a user on the MikroTik hotspot.
    
    This function should be called by the `activate_wifi` view.
    """
    api = connect_to_mikrotik()
    if not api:
        return False, "Failed to connect to MikroTik."

    try:
        api_resource = api.get_api().get_resource('/ip/hotspot/user')
        # Find the user by their name (the token)
        user_info = api_resource.get(name=username)

        if not user_info:
            api.disconnect()
            return False, f"MikroTik user '{username}' not found."
            
        user_id = user_info[0]['.id']

        # The set command expects keyword arguments.
        # The key for the ID is 'id', not '.id' as a string literal.
        api_resource.set(
            **{'id': user_id, 'disabled': 'no'}
        )
        api.disconnect()
        return True, "MikroTik user enabled successfully."
    except IndexError:
        logger.error(f"MikroTik user '{username}' not found.")
        api.disconnect()
        return False, f"MikroTik user '{username}' not found."
    except Exception as e:
        logger.error(f"Failed to enable MikroTik user '{username}': {e}")
        api.disconnect()
        return False, f"Failed to enable MikroTik user: {e}"