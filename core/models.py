# core/models.py

import uuid
from django.db import models
from django.utils import timezone
from .mikrotik_api import create_mikrotik_user
import requests
from django.conf import settings
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

class Company(models.Model):
    """
    Represents the company information to be displayed on the hotspot page.
    Using a UUID as the primary key to match the URL pattern.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

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
        # A simple token generator
        return str(uuid.uuid4())[:8].upper()
    
    def save(self, *args, **kwargs):
        # This will be triggered on a new object creation
        if not self.pk:
            # Generate token and end_time before saving
            self.token = self.generate_token()
            self.end_time = timezone.now() + timezone.timedelta(minutes=self.plan.duration_minutes)

            # Create the user on the MikroTik router
            mikrotik_success, mikrotik_message = create_mikrotik_user(
                username=self.token,
                password=self.token,
                plan=self.plan
            )

            if mikrotik_success:
                # Send the token via SMS using Africa's Talking API
                message = f"Your WiFi token is: {self.token}. It is valid for {self.plan.duration_minutes // 60} hours. Use it to login to the hotspot."
                
                # This part is commented out for now as it needs real API keys
                # payload = {
                #     'username': settings.AFRICASTALKING_USERNAME,
                #     'to': self.phone_number,
                #     'message': message,
                # }
                # headers = {'Accept': 'application/json', 'apiKey': settings.AFRICASTALKING_API_KEY}
                
                # try:
                #     requests.post('https://api.africastalking.com/version1/messaging', data=payload, headers=headers)
                #     logger.info(f"Token sent to {self.phone_number} using Africa's Talking.")
                # except requests.exceptions.RequestException as e:
                #     logger.error(f"Failed to send SMS to {self.phone_number}: {e}")

            else:
                logger.error(f"Failed to create MikroTik user for {self.phone_number}: {mikrotik_message}")
                raise Exception(mikrotik_message)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Session for {self.phone_number}"

@receiver(post_save, sender=WifiSession)
def create_mikrotik_user_on_save(sender, instance, created, **kwargs):
    """
    Signal receiver to handle MikroTik user creation after a WifiSession is saved.
    """
    if created and not instance.token:
        # Note: This block is now redundant because the save method handles it.
        # This is left here as a placeholder for a different logic flow if needed.
        pass
