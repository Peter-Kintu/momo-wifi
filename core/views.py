import uuid
import json
import requests
import os
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from .models import Plan, Payment, WifiSession


# This is a placeholder for your MikroTik integration.
def create_mikrotik_user(phone_number, plan):
    """
    This function will be implemented to connect to the MikroTik router
    and create a new user account for the paid session.
    """
    # Placeholder for the actual MikroTik API call
    token = str(uuid.uuid4())[:8].upper()
    end_time = timezone.now() + timezone.timedelta(minutes=plan.duration_minutes)

    # Save the session to your database
    WifiSession.objects.create(
        phone_number=phone_number,
        plan=plan,
        token=token,
        end_time=end_time
    )

    print(f"MikroTik user would be created with token: {token}")
    return token

@csrf_exempt
def hotspot_login_page(request):
    """
    Renders the main hotspot login page with available plans.
    """
    plans = Plan.objects.all().order_by('price')
    return render(request, 'core/hotspot_login.html', {'plans': plans})


@csrf_exempt
def verify_payment(request):
    """
    Receives the transaction ID from the frontend after a successful Flutterwave
    payment, verifies it with the Flutterwave API, and creates a MikroTik user
    if successful.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            transaction_id = data.get('transaction_id')
            tx_ref = data.get('tx_ref')
            phone_number = data.get('phone_number')
            plan_id = data.get('plan_id')
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if not all([transaction_id, tx_ref, phone_number, plan_id]):
            return JsonResponse({"error": "Missing required data"}, status=400)

        # Retrieve plan from database
        try:
            plan = Plan.objects.get(pk=plan_id)
        except Plan.DoesNotExist:
            return JsonResponse({"error": "Plan not found"}, status=404)

        # Verify the payment with Flutterwave
        url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
        headers = {
            "Authorization": f"Bearer {os.getenv('FLW_SECRET_KEY')}"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status() # Raise an HTTPError for bad responses
            result = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error during Flutterwave verification: {e}")
            return JsonResponse({"error": "Failed to verify payment with Flutterwave"}, status=500)

        # Check if the payment was successful and the transaction reference matches
        if result["status"] == "success" and result["data"]["tx_ref"] == tx_ref:
            # Create a user on the MikroTik router
            token = create_mikrotik_user(phone_number, plan)

            # Save payment record to the database
            Payment.objects.create(
                phone_number=phone_number,
                plan=plan,
                amount=plan.price, # Set amount from the plan
                transaction_id=tx_ref,
                status='successful'
            )
            return JsonResponse({"token": token})
        else:
            return JsonResponse({"error": "Payment not verified or failed"}, status=400)

    return JsonResponse({"error": "Invalid method. Only POST is allowed."}, status=405)
