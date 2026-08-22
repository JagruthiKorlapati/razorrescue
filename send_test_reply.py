import httpx

payload = {
    "payment_id": "pay_demo_001",
    "phone_number": "+919999999999",
    "message_text": "Sorry yaar, salary abhi tak nahi aaya. Friday ko aa jayegi, tab pay kar dunga.",
}

response = httpx.post(
    "http://127.0.0.1:8000/webhook/whatsapp-inbound",
    json=payload,
)

print("Status code:", response.status_code)
print("Response:", response.json())