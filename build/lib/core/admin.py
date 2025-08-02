from django.contrib import admin
from .models import Plan, Payment, WifiSession

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_minutes', 'mikrotik_profile_name')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'plan', 'amount', 'status', 'transaction_id', 'created_at')
    list_filter = ('status', 'plan')
    search_fields = ('phone_number', 'transaction_id')

@admin.register(WifiSession)
class WifiSessionAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'plan', 'token', 'start_time', 'end_time')
    list_filter = ('plan',)
    search_fields = ('phone_number', 'token')