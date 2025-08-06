# core/models.py

import uuid
from django.db import models
from django.utils import timezone
import logging
import requests
from django.conf import settings

# Import create_mikrotik_user here, but handle potential circular imports or initial setup
try:
    from .mikrotik_api import create_mikrotik_user
except ImportError:
    create_mikrotik_user = None
    logging.warning("Could not import create_mikrotik_user. This is expected during initial migrations.")


logger = logging.getLogger(__name__)

class Company(models.Model):
    """
    Represents a company that owns a hotspot.
    Each company will have its own MikroTik and potentially payment gateway credentials.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    
    # MikroTik API Credentials (specific to this company)
    mikrotik_host = models.CharField(max_length=255, default='192.168.88.1')
    mikrotik_username = models.CharField(max_length=100, default='admin')
    mikrotik_password = models.CharField(max_length=100, blank=True, default='')

    # Airtel API Credentials (specific to this company) - placeholders for now
    airtel_consumer_key = models.CharField(max_length=255, blank=True, default='')
    airtel_consumer_secret = models.CharField(max_length=255, blank=True, default='')
    airtel_business_account = models.CharField(max_length=255, blank=True, default='') # Your Airtel business account ID

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name

class Plan(models.Model):
    """
    Represents a WiFi access plan with a specific duration and price,
    associated with a specific company.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True) # Temporarily nullable
    name = models.CharField(max_length=50)
    price = models.IntegerField()  # UGX
    duration_minutes = models.IntegerField()
    mikrotik_profile_name = models.CharField(
        max_length=100,
        help_text="Corresponds to a user profile on the MikroTik router."
    )

    def __str__(self):
        return f"{self.name} ({self.price} UGX) for {self.company.name if self.company else 'N/A'}"


class WifiSession(models.Model):
    """
    Represents an active or pending WiFi session tied to a token,
    associated with a specific company.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True) # Temporarily nullable
    phone_number = models.CharField(max_length=15)
    token = models.CharField(max_length=10, unique=True, blank=True, null=True)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    end_time = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=False)

    @staticmethod
    def generate_token():
        """Generates a random 8-character alphanumeric token."""
        return str(uuid.uuid4())[:8].upper()

    def save(self, *args, **kwargs):
        # Only generate a token and create MikroTik user if it's a new session
        # and a token hasn't been explicitly set (e.g., during admin creation).
        if not self.pk and not self.token:
            self.token = self.generate_token()
            self.end_time = timezone.now() + timezone.timedelta(minutes=self.plan.duration_minutes)

            if create_mikrotik_user:
                mikrotik_success, mikrotik_message = create_mikrotik_user(
                    company=self.company, # Pass the company object here
                    username=self.token,
                    password=self.token,
                    plan=self.plan
                )

                if mikrotik_success:
                    message = (f"Your WiFi token is: {self.token}. It is valid for "
                               f"{self.plan.duration_minutes // 60} hours. Use it to login to the hotspot.")
                    
                    # This part is commented out for now as it needs real API keys
                    # if requests and settings.AFRICASTALKING_USERNAME and settings.AFRICASTALKING_API_KEY:
                    #     payload = {
                    #         'username': settings.AFRICASTALKING_USERNAME,
                    #         'to': self.phone_number,
                    #         'message': message,
                    #     }
                    #     headers = {'Accept': 'application/json', 'apiKey': settings.AFRICASTALKING_API_KEY}
                        
                    #     try:
                    #         requests.post('https://api.africastalking.com/version1/messaging', data=payload, headers=headers)
                    #         logger.info(f"Token sent to {self.phone_number} using Africa's Talking.")
                    #     except requests.exceptions.RequestException as e:
                    #         logger.error(f"Failed to send SMS to {self.phone_number}: {e}")
                    # else:
                    #     logger.warning("Africa's Talking credentials missing or requests library not available, skipping SMS send.")
                else:
                    logger.error(f"Failed to create MikroTik user for {self.phone_number}: {mikrotik_message}")
                    # If MikroTik user creation fails, prevent saving the WifiSession
                    raise Exception(f"MikroTik user creation failed: {mikrotik_message}")
            else:
                logger.warning("mikrotik_api not available, skipping MikroTik user creation for new session.")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Session for {self.phone_number} ({self.token or 'Pending'})"

