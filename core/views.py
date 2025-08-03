# wifi_hotspot/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from .models import Plan, Payment, WifiSession
from .services import initiate_momo_payment, create_mikrotik_user
import uuid
import json


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
def initiate_payment(request):
    """
    Initiates a payment with MTN MoMo.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            plan_id = data.get('plan_id')

            if not phone_number or not plan_id:
                return JsonResponse({"error": "Missing phone number or plan ID."}, status=400)

            print(f">>> Received a request to initiate payment. Request Data: phone_number={phone_number}, plan_id={plan_id}")

            # --- CHANGE FOR SANDBOX TESTING ---
            # To test with the MTN MoMo sandbox, we must use a test MSISDN.
            # We are overriding the user-provided phone number with a known sandbox test number.
            # A common test number is 256772123456.
            # For production, you would remove this line.
            phone_number = '256772123456'
            # ---------------------------------
            
            try:
                plan = Plan.objects.get(id=plan_id)
            except Plan.DoesNotExist:
                return JsonResponse({"error": "Selected plan does not exist."}, status=404)

            # Create a unique transaction ID
            transaction_id = str(uuid.uuid4())

            with transaction.atomic():
                # Create a pending payment record
                payment = Payment.objects.create(
                    phone_number=phone_number,
                    plan=plan,
                    amount=plan.price,
                    transaction_id=transaction_id,
                    status='pending'
                )
                print(f">>> Created pending payment record with ID: {transaction_id}")

                success, message = initiate_momo_payment(phone_number, plan.price, transaction_id)

                if success:
                    print(f">>> Payment initiated successfully. Transaction ID: {transaction_id}")
                    # Return the transaction ID and a status code indicating the request was accepted
                    # and the payment is pending. The client-side will use this ID to poll for status.
                    return JsonResponse({"message": message, "transaction_id": transaction_id}, status=202)
                else:
                    print(f">>> Failed to initiate payment: {message}")
                    payment.status = 'failed'
                    payment.save()
                    return JsonResponse({"error": message}, status=500)

        except json.JSONDecodeError:
            print(">>> Invalid JSON in request body.")
            return JsonResponse({"error": "Invalid JSON in request body."}, status=400)
        except Exception as e:
            print(f"Error during payment initiation: {e}")
            payment.status = 'failed'
            payment.save()
            return JsonResponse({"error": "An internal server error occurred."}, status=500)

    print(">>> Invalid request method. Not a POST request.")
    return JsonResponse({"error": "Invalid request method. Only POST is allowed."}, status=405)


@csrf_exempt
def payment_callback(request):
    """
    Receives the callback from MTN MoMo after a payment is complete.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        # Assuming the MTN MoMo callback structure
        transaction_id = data.get('externalId')
        payment_status = data.get('status')

        if not transaction_id or not payment_status:
            return HttpResponse(status=400)

        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
        except Payment.DoesNotExist:
            return HttpResponse(status=404)

        payment.status = payment_status
        payment.save()

        if payment_status == 'successful':
            # Create a user on the MikroTik router
            token = create_mikrotik_user(payment.phone_number, payment.plan)
            return HttpResponse(f"Payment successful, user created with token: {token}", status=200)
        else:
            return HttpResponse(f"Payment status: {payment_status}", status=200)

    return HttpResponse(status=405)
