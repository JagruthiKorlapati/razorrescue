import hmac
import hashlib
import json
import httpx

WEBHOOK_SECRET = "your_webhook_secret"  # must match RAZORPAY_WEBHOOK_SECRET in your .env

payload = {
    "event": "payment.failed",
    "payload": {
        "payment": {
            "entity": {
                "id": "pay_demo_001",
                "error_code": "BAD_REQUEST_ERROR",
                "error_source": "issuer",
                "error_description": "The payment was not completed",
                "amount": 50000,
            }
        }
    },
}

body = json.dumps(payload).encode()

signature = hmac.new(
    key=WEBHOOK_SECRET.encode(),
    msg=body,
    digestmod=hashlib.sha256,
).hexdigest()

response = httpx.post(
    "http://127.0.0.1:8000/webhook/razorpay",
    content=body,
    headers={
        "Content-Type": "application/json",
        "X-Razorpay-Signature": signature,
    },
)

print("Status code:", response.status_code)
print("Response:", response.json())