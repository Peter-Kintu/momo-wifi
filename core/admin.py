# wifi_hotspot/core/admin.py

from django.contrib import admin
from django.utils import timezone
from .models import WifiSession, Plan, Company
from .mikrotik_api import create_mikrotik_user # Keep this import if needed for actions
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
            # The save() method of WifiSession now handles token generation and MikroTik user creation.
            # It will also raise an exception if MikroTik user creation fails.
            session.save()
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


class CompanyAdmin(admin.ModelAdmin):
    """Admin view for the Company model."""
    list_display = ('name', 'mikrotik_host', 'mikrotik_username')
    search_fields = ('name', 'mikrotik_host')
    # Make sure to include all credentials fields in the form
    fields = (
        'name',
        'mikrotik_host',
        'mikrotik_username',
        'mikrotik_password',
        'airtel_consumer_key',
        'airtel_consumer_secret',
        'airtel_business_account'
    )


class PlanAdmin(admin.ModelAdmin):
    """Admin view for the Plan model."""
    list_display = ('name', 'company', 'price', 'duration_minutes', 'mikrotik_profile_name')
    list_filter = ('company',) # Allow filtering plans by company
    search_fields = ('name', 'company__name') # Allow searching by company name
    fields = ('company', 'name', 'price', 'duration_minutes', 'mikrotik_profile_name')


class WifiSessionAdmin(admin.ModelAdmin):
    """Admin view for the WifiSession model."""
    list_display = ('phone_number', 'company', 'token', 'plan', 'end_time', 'is_active')
    list_filter = ('is_active', 'plan', 'company') # Allow filtering sessions by company
    search_fields = ('phone_number', 'token', 'company__name')
    actions = [generate_and_send_token]
    
    # These fields will be displayed in the form for adding/changing a session
    fields = ('company', 'phone_number', 'plan')
    
    # These fields are automatically set and should not be editable in the admin form
    readonly_fields = ('token', 'end_time', 'is_active')


# Register your models with the custom admin classes
admin.site.register(Company, CompanyAdmin)
admin.site.register(Plan, PlanAdmin)
admin.site.register(WifiSession, WifiSessionAdmin)

