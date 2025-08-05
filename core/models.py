# core/models.py

import uuid
from django.db import models
from django.utils import timezone
from .mikrotik_api import create_mikrotik_user, enable_mikrotik_user
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Plan(models.Model):
    """
    Represents a WiFi access plan with a specific duration and price.
    """
    name = models.CharField(max_length=50)
    price = models.IntegerField()  # UGX
    duration_minutes = models.IntegerField()
    mikrotik_profile_name = models.CharField(
        max_length=100,
        help_text="Corresponds to a user profile on the MikroTik router."
    )

    def __str__(self):
        return f"{self.name} ({self.price} UGX)"


class WifiSession(models.Model):
    """
    Represents an active or pending WiFi session tied to a token.
    """
    phone_number = models.CharField(max_length=15)
    token = models.CharField(max_length=10, unique=True, blank=True, null=True)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    end_time = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=False)

    @staticmethod
    def generate_token():
        """Generates a random 6-character alphanumeric token."""
        return str(uuid.uuid4())[:6].upper()

    def save(self, *args, **kwargs):
        # Only generate a token if one doesn't exist.
        if not self.token:
            self.token = self.generate_token()
            self.end_time = timezone.now() + timezone.timedelta(minutes=self.plan.duration_minutes)

            # This is where the MikroTik user is created and SMS is sent.
            # This logic might be better placed in a separate admin action or signal.
            # For now, we'll keep it here as per the original code's intention.
            mikrotik_success, mikrotik_message = create_mikrotik_user(
                username=self.token,
                password=self.token,
                plan=self.plan
            )

            if mikrotik_success:
                message = (f"Your WiFi token is: {self.token}. It is valid for "
                           f"{self.plan.duration_minutes // 60} hours. Use it to login to the hotspot.")
                
                payload = {
                    'username': settings.AFRICASTALKING_USERNAME,
                    'to': self.phone_number,
                    'message': message,
                }
                headers = {'Accept': 'application/json', 'apiKey': settings.AFRICASTALKING_API_KEY}
                
                try:
                    requests.post('https://api.africastalking.com/version1/messaging', data=payload, headers=headers)
                    logger.info(f"Token sent to {self.phone_number} using Africa's Talking.")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Failed to send SMS to {self.phone_number}: {e}")
            else:
                logger.error(f"Failed to create MikroTik user for {self.phone_number}: {mikrotik_message}")
                # You might want to raise a more specific exception here.
                raise Exception(mikrotik_message)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Session for {self.phone_number} ({self.token})"

