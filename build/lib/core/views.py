# wifi_hotspot/views.py

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from .models import Plan, Payment
from .services import initiate_momo_payment, create_mikrotik_user
import uuid
import json

# This import is no longer needed here as the function is moved to services.py
# from mtnmomo.collection import Collection

# Note: The following lines of test code are removed for a clean production build.
# The functionality is now integrated into the `hotspot_payment` view.
# from core.utils.momo import initiate_momo_payment, check_payment_status
# txn_id, response = initiate_momo_payment(Collection, "256789746493", 1000)
# print(txn_id)
# print(response)
# status = check_payment_status(Collection, txn_id)
# print(status)

def hotspot_login_page(request):
    """
    Renders the main hotspot login page with available plans.
    This is now a placeholder for a real template render.
    """
    plans = Plan.objects.all()
    context = {
        'plans': plans
    }
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
    Handles the payment initiation request from the hotspot login page.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            plan_id = data.get('plan_id')
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

        if not phone_number or not plan_id:
            return JsonResponse({"error": "Phone number and plan ID are required."}, status=400)

        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            return JsonResponse({"error": "Invalid plan selected."}, status=404)

        # Generate a unique transaction ID
        transaction_id = str(uuid.uuid4())

        # Ensure the payment is created within a transaction to handle potential race conditions
        with transaction.atomic():
            payment = Payment.objects.create(
                phone_number=phone_number,
                plan=plan,
                amount=plan.price,
                transaction_id=transaction_id,
                status='pending'
            )
            success, message = initiate_momo_payment(phone_number, plan.price, transaction_id)

        if success:
            return JsonResponse({"message": "Payment request sent. Waiting for confirmation.", "transaction_id": transaction_id}, status=202)
        else:
            payment.status = 'failed'
            payment.save()
            return JsonResponse({"error": message}, status=500)

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
