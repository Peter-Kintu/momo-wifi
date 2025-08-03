import uuid
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from .models import Plan, Payment, WifiSession
from .services import initiate_airtel_payment, create_mikrotik_user


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
    Initiates an Airtel payment request for a selected plan.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            plan_id = data.get('plan_id')

            if not phone_number or not plan_id:
                return JsonResponse({"error": "Phone number and plan ID are required."}, status=400)

            plan = Plan.objects.get(pk=plan_id)

            success, message_or_id = initiate_airtel_payment(phone_number, plan)

            if success:
                return JsonResponse({"message": "Payment initiated successfully.", "transaction_id": message_or_id}, status=202)
            else:
                return JsonResponse({"error": message_or_id}, status=500)

        except Plan.DoesNotExist:
            return JsonResponse({"error": "Invalid plan selected."}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format in request body."}, status=400)
        except Exception as e:
            print(f"Error during payment initiation: {e}")
            return JsonResponse({"error": "An internal server error occurred."}, status=500)

    return JsonResponse({"error": "Invalid request method. Only POST is allowed."}, status=405)


@csrf_exempt
def airtel_callback(request):
    """
    Receives the callback from Airtel after a payment is complete.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Use the exact structure from the Airtel documentation
            transaction_id = data.get("data", {}).get("transaction", {}).get("id")
            status = data.get("data", {}).get("transaction", {}).get("status")

            if not transaction_id or not status:
                return HttpResponse("Invalid callback data", status=400)

            try:
                payment = Payment.objects.get(transaction_id=transaction_id)
            except Payment.DoesNotExist:
                return HttpResponse("Payment not found", status=404)
            
            # The status should be normalized to lowercase for consistency
            payment.status = status.lower()
            payment.save()

            if status.lower() == "successful":
                # Create a user on the MikroTik router
                token = create_mikrotik_user(payment.phone_number, payment.plan)
                if token:
                    return HttpResponse(f"User created with token: {token}", status=200)
                else:
                    return HttpResponse("Payment successful, but user creation failed.", status=500)

            return HttpResponse(f"Payment status: {status}", status=200)

        except json.JSONDecodeError:
            return HttpResponse("Invalid JSON in callback", status=400)
        except Exception as e:
            print(f"Airtel callback error: {e}")
            return HttpResponse("Callback processing failed", status=500)

    return HttpResponse("Method not allowed", status=405)
