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
            # 1. Generate the token and calculate end time. The save() method handles this.
            session.save()

            # 2. Since the save() method now handles MikroTik user creation and SMS sending,
            #    we only need to check if it was successful. This is handled by the
            #    exception from the save() method.
            success_count += 1
            messages.success(request, f"Token generated and sent to {session.phone_number}.")

        except Exception as e:
            failure_count += 1
            logger.error(f"Error processing session for {session.phone_number}: {e}")
            messages.error(request, f"An error occurred for {session.phone_number}: {e}")

    if success_count > 0:
        messages.success(request, f"Successfully processed {success_count} sessions.")
    if failure_count > 0:
        messages.error(request, f"Failed to process {failure_count} sessions.")


class PlanAdmin(admin.ModelAdmin):
    """Admin view for the Plan model."""
    list_display = ('name', 'price', 'duration_minutes', 'mikrotik_profile_name')
    search_fields = ('name',)


class WifiSessionAdmin(admin.ModelAdmin):
    """Admin view for the WifiSession model."""
    list_display = ('phone_number', 'token', 'plan', 'end_time', 'is_active')
    list_filter = ('is_active', 'plan')
    search_fields = ('phone_number', 'token')
    actions = [generate_and_send_token]
    
    # These fields will be displayed in the form
    fields = ('phone_number', 'plan')
    
    # Exclude these fields from being editable in the admin
    readonly_fields = ('token', 'end_time', 'is_active')


# Register your models with the custom admin classes
admin.site.register(Plan, PlanAdmin)
admin.site.register(WifiSession, WifiSessionAdmin)

