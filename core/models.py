# wifi_hotspot/core/models.py

import uuid
from django.db import models
from django.utils import timezone

class Plan(models.Model):
    """
    Represents a WiFi access plan with a specific duration and price.
    """
    name = models.CharField(max_length=50)
    price = models.IntegerField()  # UGX
    duration_minutes = models.IntegerField()
    # This field is crucial for mapping a plan to a MikroTik user profile
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

    def __str__(self):
        return f"Session for {self.phone_number} ({self.token})"