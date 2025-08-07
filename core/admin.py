# wifi_hotspot/core/admin.py

from django.contrib import admin
from .models import Company, Plan, WifiSession, Payment

# Register your models here.
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """
    Admin view for the Company model.
    """
    list_display = ('name', 'savanna_host')
    search_fields = ('name', 'savanna_host')


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """
    Admin view for the Plan model.
    """
    list_display = ('name', 'company', 'price', 'duration_minutes')
    list_filter = ('company',)
    search_fields = ('name', 'company__name')


@admin.register(WifiSession)
class WifiSessionAdmin(admin.ModelAdmin):
    """
    Admin view for the WifiSession model.
    """
    list_display = ('phone_number', 'company', 'token', 'plan', 'is_active', 'start_time', 'end_time')
    list_filter = ('is_active', 'company', 'plan')
    search_fields = ('phone_number', 'token')
    readonly_fields = ('token', 'ip_address', 'is_active', 'start_time', 'end_time')
    
    # Custom form to only show relevant fields for adding a new session
    fields = ('company', 'phone_number', 'plan')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin view for the Payment model.
    """
    list_display = ('id', 'session', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('session__phone_number', 'transaction_id')
    readonly_fields = ('session', 'transaction_id', 'amount', 'status', 'created_at', 'updated_at')
