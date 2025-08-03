# wifi_hotspot/core/mikrotik_api.py

import os
import routeros_api
from django.conf import settings
# The Plan import is moved inside the function to avoid circular dependency
import logging

logger = logging.getLogger(__name__)

def create_mikrotik_user(username, password, plan):
    """
    Creates a new user on the MikroTik router.
    """
    try:
        connection = routeros_api.RouterOsApiPool(
            host=settings.MIKROTIK_HOST,
            username=settings.MIKROTIK_USERNAME,
            password=settings.MIKROTIK_PASSWORD,
            plaintext_login=True
        )
        api = connection.get_api()

        # Check if the user already exists
        if api.get_resource('/ip/hotspot/user').get(name=username):
            return False, f"User {username} already exists."

        # Add the new user
        api.get_resource('/ip/hotspot/user').add(
            name=username,
            password=password,
            profile=plan.mikrotik_profile_name
        )
        
        return True, f"User {username} created successfully."

    except routeros_api.exceptions.RouterOsApiError as e:
        logger.error(f"MikroTik API Error: {e}")
        return False, f"MikroTik API Error: {e}"
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False, f"An unexpected error occurred: {e}"
    finally:
        if connection:
            connection.disconnect()