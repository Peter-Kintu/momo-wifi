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
    """
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
        return str(uuid.uuid4())[:8].upper()

    def save(self, *args, **kwargs):
        # We don't want to create a MikroTik user on every save,
        # so we'll use a signal to handle creation only when it's new.
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Session for {self.phone_number} ({self.token})"


@receiver(post_save, sender=WifiSession)
def create_mikrotik_user_on_save(sender, instance, created, **kwargs):
    """
    Signal handler to create a MikroTik user after a new WifiSession is created.
    """
    if created and not instance.token:
        # 1. Generate the token and calculate end time
        instance.token = WifiSession.generate_token()
        instance.end_time = timezone.now() + timezone.timedelta(minutes=instance.plan.duration_minutes)

        # 2. Create the user on the MikroTik router
        mikrotik_success, mikrotik_message = create_mikrotik_user(
            username=instance.token,
            password=instance.token,  # Using the token as the password for simplicity
            plan=instance.plan
        )

        if mikrotik_success:
            # 3. Send the token via SMS using Africa's Talking API
            message = f"Your WiFi token is: {instance.token}. It is valid for {instance.plan.duration_minutes // 60} hours. Use it to login to the hotspot."
            
            # This part is commented out for now as it needs real API keys
            # payload = {
            #     'username': settings.AFRICASTALKING_USERNAME,
            #     'to': instance.phone_number,
            #     'message': message,
            # }
            # headers = {'Accept': 'application/json', 'apiKey': settings.AFRICASTALKING_API_KEY}
            
            # try:
            #     requests.post('https://api.africastalking.com/version1/messaging', data=payload, headers=headers)
            #     logger.info(f"Token sent to {instance.phone_number} using Africa's Talking.")
            # except requests.exceptions.RequestException as e:
            #     logger.error(f"Failed to send SMS to {instance.phone_number}: {e}")

            # Save the instance again to persist the new token and end_time
            instance.save(update_fields=['token', 'end_time'])

        else:
            logger.error(f"Failed to create MikroTik user for {instance.phone_number}: {mikrotik_message}")
            # Consider rolling back or handling the error gracefully
            # For now, let's just delete the session since the MikroTik user failed
            instance.delete()
