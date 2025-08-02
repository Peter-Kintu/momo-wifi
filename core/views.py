from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from .models import Plan, Payment, WifiSession
from .services import initiate_momo_payment
import uuid
import json
from mtnmomo.collection import Collection

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

def hotspot_login_page(request):
    """
    Renders the main hotspot login page.
    """
    print(">>> Rendering hotspot_login_page...")
    plans = Plan.objects.all()
    context = {
        'plans': plans
    }
    return render(request, 'core/hotspot_login.html', context)

@csrf_exempt
def initiate_payment(request):
    """
    Handles the payment initiation request from the front-end.
    """
    print(">>> initiate_payment view reached!")
    if request.method == 'POST':
        print(">>> Request method is POST.")
        try:
            data = json.loads(request.body)
            print(f">>> Received data: {data}")
            plan_id = data.get('plan_id')
            phone_number = data.get('phone_number')

            if not plan_id or not phone_number:
                print(">>> Missing plan_id or phone_number.")
                return JsonResponse({"error": "Plan ID and phone number are required."}, status=400)

            plan = Plan.objects.get(id=plan_id)
            print(f">>> Plan found: {plan.name}")
            
            # Generate a unique transaction ID
            transaction_id = str(uuid.uuid4())

            # Create a pending payment record
            with transaction.atomic():
                payment = Payment.objects.create(
                    phone_number=phone_number,
                    plan=plan,
                    amount=plan.price,
                    transaction_id=transaction_id,
                    status='pending'
                )
                print(">>> Payment record created.")

                # Call the payment service
                success, message = initiate_momo_payment(phone_number, plan.price, transaction_id)
            
            if success:
                print(">>> MoMo payment initiation successful.")
                return JsonResponse({"message": "Payment request sent. Please approve the request on your phone.", "transaction_id": transaction_id}, status=202)
            else:
                # If MoMo initiation fails, mark the payment as failed
                print(f">>> MoMo payment initiation failed: {message}")
                payment.status = 'failed'
                payment.save()
                return JsonResponse({"error": message}, status=500)

        except json.JSONDecodeError:
            print(">>> Invalid JSON in request body.")
            return JsonResponse({"error": "Invalid JSON in request body."}, status=400)
        except Plan.DoesNotExist:
            print(">>> Invalid plan selected.")
            return JsonResponse({"error": "Invalid plan selected."}, status=404)
        except Exception as e:
            print(f">>> An unexpected error occurred: {e}")
            return JsonResponse({"error": "An unexpected server error occurred."}, status=500)
    
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

        return HttpResponse(f"Payment status is {payment_status}", status=200)
    
    return HttpResponse(status=405)
