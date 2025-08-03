import uuid
import json
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from .models import Plan, Payment, WifiSession
from .services import initiate_momo_payment
from .routeros_api import create_mikrotik_user # Corrected import from the new file


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
    Handles the initiation of a payment request.
    """
    print(">>> Received a request to initiate payment.")
    if request.method == 'POST':
        try:
            # We expect a JSON payload from the frontend.
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            plan_id = data.get('plan_id')
            print(f">>> Request Data: phone_number={phone_number}, plan_id={plan_id}")

        except json.JSONDecodeError:
            print(">>> Error: Invalid JSON in request body.")
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)

        # Basic validation
        if not phone_number or not plan_id:
            return JsonResponse({'error': 'Phone number and plan are required.'}, status=400)

        try:
            plan = Plan.objects.get(pk=plan_id)
        except Plan.DoesNotExist:
            return JsonResponse({'error': 'Invalid plan selected.'}, status=404)

        # Create a new payment record in the database
        transaction_id = str(uuid.uuid4()) # Create a unique transaction ID

        try:
            with transaction.atomic():
                payment = Payment.objects.create(
                    phone_number=phone_number,
                    plan=plan,
                    amount=plan.price,
                    transaction_id=transaction_id,
                    status='pending'
                )
                print(f">>> Created pending payment record with ID: {payment.transaction_id}")

                # Initiate payment with MTN MoMo
                success, message = initiate_momo_payment(
                    phone_number=phone_number,
                    amount=plan.price,
                    transaction_id=payment.transaction_id
                )

                if success:
                    print(f">>> Payment initiated successfully for transaction ID: {payment.transaction_id}")
                    payment.status = 'sent' # Update status to 'sent'
                    payment.save()
                    return JsonResponse({'message': 'Payment request sent successfully. Please approve the payment on your phone.'})
                else:
                    print(f">>> Failed to initiate payment: {message}")
                    payment.status = 'failed'
                    payment.save()
                    return JsonResponse({"error": message}, status=500)
        except Exception as e:
            print(f">>> An unexpected error occurred during payment initiation: {e}")
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
            return HttpResponse("Payment failed or was rejected.", status=200)

    return HttpResponse(status=405)
