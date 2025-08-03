import uuid
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from .models import Plan, Payment, WifiSession
from .services import initiate_momo_payment


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
    Handles the payment initiation request from the hotspot login page.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            plan_id = data.get('plan_id')
            phone_number = data.get('phone_number')

            if not plan_id or not phone_number:
                return JsonResponse({"error": "Plan ID and phone number are required."}, status=400)

            with transaction.atomic():
                plan = Plan.objects.get(pk=plan_id)
                amount = plan.price
                transaction_id = str(uuid.uuid4())

                payment = Payment.objects.create(
                    phone_number=phone_number,
                    plan=plan,
                    transaction_id=transaction_id,
                    status='pending'
                )

                success, message = initiate_momo_payment(phone_number, amount, transaction_id)
                
                if success:
                    return JsonResponse({"message": message, "transaction_id": transaction_id}, status=202)
                else:
                    payment.status = 'failed'
                    payment.save()
                    return JsonResponse({"error": message}, status=500)

        except Plan.DoesNotExist:
            return JsonResponse({"error": "Invalid plan selected."}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            print(f">>> Error during payment initiation: {e}")
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
        
        return HttpResponse(f"Payment status: {payment_status}", status=200)

    return HttpResponse(status=405)
