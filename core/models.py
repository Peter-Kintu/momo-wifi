# wifi_hotspot/core/models.py

import uuid
from django.db import models
from django.utils import timezone
import logging
from datetime import timedelta
import random
import string
from django.db import transaction

# Import the Savanna API and router control functions
try:
    from .savanna_api import create_savanna_user, disable_savanna_user
    from .router_control import create_router_user, enable_router_user, block_mac_on_router
except ImportError:
    create_savanna_user = None
    disable_savanna_user = None
    create_router_user = None
    enable_router_user = None
    block_mac_on_router = None
    logging.warning("Could not import Savanna API functions. This is expected during initial migrations.")

logger = logging.getLogger(__name__)

class Company(models.Model):
    """
    Represents a company that owns a hotspot, with credentials for their Savanna router.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    
    # Savanna Router Credentials
    savanna_host = models.CharField(max_length=255, default='192.168.1.1')
    savanna_username = models.CharField(max_length=100, default='admin')
    savanna_password = models.CharField(max_length=100, blank=True, default='')

    # Airtel API Credentials
    airtel_consumer_key = models.CharField(max_length=255, blank=True)
    airtel_consumer_secret = models.CharField(max_length=255, blank=True)
    airtel_business_account = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Plan(models.Model):
    """
    Represents a WiFi plan with a specific duration and price.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='plans')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.IntegerField(help_text="Duration in minutes")

    def __str__(self):
        return f"{self.name} ({self.duration_minutes} mins)"


class WifiSession(models.Model):
    """
    Represents an active WiFi session for a user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sessions')
    phone_number = models.CharField(max_length=20)
    token = models.CharField(max_length=50, blank=True, unique=True)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=17, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        Custom save method to generate a token if one doesn't exist.
        """
        if not self.token:
            duration_hours = int(self.plan.duration_minutes / 60)
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            self.token = f"{duration_hours}H-{random_suffix}"
            logger.info(f"Generated new token: {self.token}")
        super().save(*args, **kwargs)

    @transaction.atomic
    def activate(self, ip_address, mac_address):
        """
        Activates the session and creates a user on the router.
        """
        if not self.is_active:
            self.start_time = timezone.now()
            self.end_time = self.start_time + timedelta(minutes=self.plan.duration_minutes)
            self.is_active = True
            self.ip_address = ip_address
            self.mac_address = mac_address
            self.save()

            # Use the Savanna API to create the user with their details
            if create_savanna_user:
                success, message = create_savanna_user(self.company, self.token, self.ip_address, self.plan)
                if success:
                    logger.info(f"Savanna user created for session {self.id}")
                    # Enable the router user
                    enable_success, enable_message = enable_router_user(self.company, self.token, self.mac_address, self.ip_address)
                    if enable_success:
                        logger.info(f"Router user enabled for session {self.id}")
                    else:
                        logger.error(f"Failed to enable router user: {enable_message}")
                else:
                    logger.error(f"Failed to create Savanna user for session {self.id}: {message}")
            else:
                logger.warning("Savanna API functions are not available.")

    def deactivate(self):
        """
        Deactivates the session and removes the user's IP from the router.
        """
        if self.is_active:
            self.is_active = False
            self.save()
            
            # Use the Savanna API to disable the user's access
            if disable_savanna_user:
                success, message = disable_savanna_user(self.company, self.token)
                if not success:
                    logger.error(f"Failed to deactivate session {self.id}: {message}")
            else:
                logger.warning("Savanna API functions are not available.")
    
    def __str__(self):
        return f"Session for {self.phone_number} ({self.token}) on {self.company.name}"


class Payment(models.Model):
    """
    Records payment transactions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(WifiSession, on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50) # e.g., 'Success', 'Failed', 'Pending'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for {self.session.phone_number} - {self.status}"
