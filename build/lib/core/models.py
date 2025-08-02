from django.db import models
from django.utils import timezone
from datetime import timedelta

class Plan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.IntegerField()
    mikrotik_profile_name = models.CharField(
        max_length=100,
        help_text="Corresponds to a user profile on the MikroTik router."
    )

    def __str__(self):
        return self.name


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ]

    phone_number = models.CharField(max_length=15)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.phone_number} - {self.status}"


class WifiSession(models.Model):
    phone_number = models.CharField(max_length=15)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    token = models.CharField(max_length=50, unique=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['token']),
        ]

    def save(self, *args, **kwargs):
        if not self.end_time:
            self.end_time = timezone.now() + timezone.timedelta(minutes=self.plan.duration_minutes)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Session for {self.phone_number} - Token: {self.token}"

