import uuid

def initiate_momo_payment(collections, phone_number, amount, message="Payment for Wi-Fi"):
    transaction_id = str(uuid.uuid4())

    try:
        response = collections.requestToPay(
            mobile=phone_number,
            amount=str(amount),
            external_id=transaction_id,
            payer_message=message,
            payee_note="Wi-Fi Hotspot Service"
        )
        return transaction_id, response
    except Exception as e:
        print("Payment error:", e)
        return None, str(e)

def check_payment_status(collections, transaction_id):
    try:
        status = collections.getTransactionStatus(transaction_id)
        return status
    except Exception as e:
        print("Status check error:", e)
        return str(e)