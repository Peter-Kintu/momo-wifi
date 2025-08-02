# wifi_hotspot/views.py

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from .models import Plan, Payment, WifiSession
from .services import initiate_momo_payment, create_mikrotik_user
import uuid
import json

# This function is now correctly imported from services.py
# The local implementation is removed to avoid conflicts.

def hotspot_login_page(request):
    """
    Renders the main hotspot login page.
    """
    print(">>> Rendering hotspot_login_page...")
    plans = Plan.objects.all()
    context = {
        'plans': plans
    }
    # This is a placeholder for a real template render.
    # In a real app, you would render a template like `render(request, 'hotspot/login.html', context)`.
    return JsonResponse(
        {
            "message": "This is a placeholder for the login page. Available plans are in the 'plans' key.",
            "plans": [
                {'id': p.id, 'name': p.name, 'price': str(p.price)} for p in plans
            ]
        }
    )


@csrf_exempt
def hotspot_payment(request):
    """
    Handles payment requests from the hotspot login page.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            plan_id = data.get('plan_id')

            if not phone_number or not plan_id:
                print(">>> Missing phone number or plan ID.")
                return JsonResponse({"error": "Phone number and plan ID are required."}, status=400)

            try:
                plan = Plan.objects.get(id=plan_id)
            except Plan.DoesNotExist:
                print(f">>> Plan with ID {plan_id} not found.")
                return JsonResponse({"error": "Invalid plan ID."}, status=404)

            # Generate a unique transaction ID
            transaction_id = str(uuid.uuid4())

            # Initiate the MoMo payment
            print(f">>> Initiating payment for phone: {phone_number}, plan: {plan.name}")
            success, message = initiate_momo_payment(
                phone_number=phone_number,
                amount=plan.price,
                transaction_id=transaction_id
            )
            
            if success:
                # Save the payment record with a 'pending' status
                with transaction.atomic():
                    Payment.objects.create(
                        phone_number=phone_number,
                        plan=plan,
                        amount=plan.price,
                        transaction_id=transaction_id,
                        status='pending'
                    )
                return JsonResponse({"message": message, "transaction_id": transaction_id}, status=202)
            else:
                return JsonResponse({"error": message}, status=400)

        except json.JSONDecodeError:
            print(">>> Invalid JSON in request body.")
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
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
        # The user's code had `payment_status = data.get('status')`. The actual MoMo callback
        # uses `status`. This is a good sanity check.

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

        return HttpResponse(f"Payment status updated to: {payment_status}", status=200)
    
    return HttpResponse(status=405)
