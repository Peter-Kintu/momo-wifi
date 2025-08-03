# services.py

import os
import requests
import json
import uuid
import routeros_api
from django.conf import settings
from django.utils import timezone
from .models import WifiSession, Plan

def create_mikrotik_user(phone_number, plan: Plan):
    """
    This function connects to the MikroTik router and creates a new user
    account for the paid session. The token generated now includes the
    plan's duration for easy identification.
    """
    try:
        # Generate a secure, random password for the MikroTik user.
        mikrotik_password = str(uuid.uuid4())[:8]
        
        api = routeros_api.RouterOsApiPool(
            host=settings.MIKROTIK_HOST,
            username=settings.MIKROTIK_USER,
            password=settings.MIKROTIK_PASSWORD,
            port=8728,
            use_ssl=False,
        )
        
        api.get_api().get_resource('/ip/hotspot/user').add(
            name=phone_number,
            password=mikrotik_password,  # Use the secure random password
            profile=plan.mikrotik_profile_name,
            limit_uptime=f"{plan.duration_minutes}m"
        )
        api.disconnect()

        # Generate a new token format: e.g., '8H-A1B2'
        duration_hours = int(plan.duration_minutes / 60)
        random_suffix = str(uuid.uuid4())[:4].upper()
        session_token = f"{duration_hours}H-{random_suffix}"
        
        end_time = timezone.now() + timezone.timedelta(minutes=plan.duration_minutes)

        # Save the session to your database with the new, descriptive token
        WifiSession.objects.create(
            phone_number=phone_number,
            plan=plan,
            token=session_token,
            end_time=end_time
        )

        print(f"MikroTik user created with token: {session_token}")
        return session_token

    except Exception as e:
        print(f"Error creating MikroTik user: {e}")
        # In a real-world scenario, you might want to log this error and
        # handle it gracefully, perhaps by refunding the user or retrying.
        return None