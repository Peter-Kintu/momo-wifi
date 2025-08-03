# wifi_hotspot/core/admin.py

from django.contrib import admin
from django.utils import timezone
from .models import WifiSession, Plan
from .mikrotik_api import create_mikrotik_user
from django.contrib import messages
import requests
import logging

logger = logging.getLogger(__name__)

# Action to generate and send a token to a user
@admin.action(description='Generate and send WiFi token')
def generate_and_send_token(modeladmin, request, queryset):
    """
    Admin action to generate a token, create a MikroTik user,
    and send the token via SMS (using a placeholder for Africa's Talking).
    """
    success_count = 0
    failure_count = 0
    for session in queryset:
        # Check if a token has already been generated
        if session.token:
            messages.warning(request, f"Session for {session.phone_number} already has a token. Skipping.")
            continue

        try:
            # 1. Generate the token and calculate end time
            session.token = WifiSession.generate_token()
            session.end_time = timezone.now() + timezone.timedelta(minutes=session.plan.duration_minutes)

            # 2. Create the user on the MikroTik router
            mikrotik_success, mikrotik_message = create_mikrotik_user(
                username=session.token,
                password=session.token,  # Using the token as the password for simplicity
                plan=session.plan
            )

            if mikrotik_success:
                # 3. Save the session in the database
                session.save()

                # 4. Send the token via SMS (placeholder)
                # Note: You'll need to configure Africa's Talking API credentials
                message = f"Your WiFi token is: {session.token}. It is valid for {session.plan.duration_minutes // 60} hours. Use it to login to the hotspot."
                payload = {
                    'to': session.phone_number,
                    'message': message,
                    'apiKey': 'your_api_key',
                    'username': 'your_username'
                }
                # requests.post('https://api.africastalking.com/version1/messaging', data=payload)
                
                success_count += 1
                messages.success(request, f"Token generated and (simulated) sent to {session.phone_number}.")
            else:
                failure_count += 1
                messages.error(request, f"Failed to create MikroTik user for {session.phone_number}: {mikrotik_message}")

        except Exception as e:
            failure_count += 1
            logger.error(f"Error processing session for {session.phone_number}: {e}")
            messages.error(request, f"An error occurred for {session.phone_number}: {e}")

    if success_count > 0:
        messages.success(request, f"Successfully processed {success_count} sessions.")
    if failure_count > 0:
        messages.error(request, f"Failed to process {failure_count} sessions.")


class WifiSessionAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'token', 'plan', 'end_time', 'is_active')
    list_filter = ('is_active', 'plan')
    search_fields = ('phone_number', 'token')
    actions = [generate_and_send_token]
    
    # These fields will be displayed in the form
    fields = ('phone_number', 'plan')
    
    # These fields will not be editable by the user
    readonly_fields = ('token', 'end_time', 'is_active')

admin.site.register(WifiSession, WifiSessionAdmin)
admin.site.register(Plan)