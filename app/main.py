import hmac
import hashlib
import json

from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel
import redis

from app.config import REDIS_URL, RAZORPAY_WEBHOOK_SECRET
from app.classifier import classify_failure, FailureType
from app.retry_scheduler import retry_payment
from app.rail_switch import generate_upi_fallback
from app.dunning_agent import send_dunning_message
from app.intent_extraction import extract_intent
from app.actions import handle_promise_to_pay, handle_churn_intent, handle_retry_now
from app.db import get_session, PaymentFailure, RailSwitchEvent, ConversationMessage, RecoveryLedger

app = FastAPI(title="RazorRescue")

# Connect to Redis for idempotency (dedup) checks
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def verify_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Recompute the HMAC-SHA256 signature and compare to the one Razorpay sent."""
    expected_signature = hmac.new(
        key=secret.encode(),
        msg=payload_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
):
    raw_body = await request.body()

    # 1. Verify the request actually came from Razorpay
    if not x_razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing signature header")

    if not verify_signature(raw_body, x_razorpay_signature, RAZORPAY_WEBHOOK_SECRET):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = json.loads(raw_body)

    # 2. Only handle payment.failed events
    event_type = payload.get("event")
    if event_type != "payment.failed":
        return {"status": "ignored", "event": event_type}

    payment_entity = payload["payload"]["payment"]["entity"]
    payment_id = payment_entity["id"]

    # 3. Idempotency check - has this payment_id already been processed?
    dedup_key = f"processed:{payment_id}"
    was_new = redis_client.set(dedup_key, "1", nx=True, ex=86400)  # 24hr expiry

    if not was_new:
        return {"status": "duplicate_ignored", "payment_id": payment_id}

    # 4. Classify the failure
    failure_type = classify_failure(payment_entity)
    print(f"New payment.failed received: {payment_id} -> classified as {failure_type.value}")
    print(json.dumps(payment_entity, indent=2))

    # 4b. Persist the failure record
    session = get_session()
    session.add(PaymentFailure(
        id=payment_id,
        error_code=payment_entity.get("error_code"),
        error_source=payment_entity.get("error_source"),
        amount=payment_entity.get("amount", 0),
        classification=failure_type.value,
    ))
    session.commit()
    session.close()

    # 5. Act on the classification
    fallback = None
    if failure_type == FailureType.TRANSIENT:
        retry_payment.apply_async(args=[payment_id, 1], countdown=5)  # 5s for local testing
        action_taken = "retry_scheduled"
    else:
        fallback = generate_upi_fallback(payment_entity)
        customer_phone = payment_entity.get("customer_phone", "+91XXXXXXXXXX")
        dunning_message = send_dunning_message(
            payment_id, customer_phone, fallback["upi_intent_link"]
        )
        action_taken = "rail_switch_and_dunning_sent"

        session = get_session()
        session.add(RailSwitchEvent(
            payment_id=payment_id,
            fallback_txn_ref=fallback["fallback_txn_ref"],
            upi_intent_link=fallback["upi_intent_link"],
        ))
        session.add(ConversationMessage(
            payment_id=payment_id,
            direction="outbound",
            message_text=dunning_message["message_sent"],
        ))
        session.commit()
        session.close()

    response_body = {
        "status": "received",
        "payment_id": payment_id,
        "classification": failure_type.value,
        "action": action_taken,
    }

    if failure_type == FailureType.HARD_FAILURE:
        response_body["upi_fallback"] = fallback

    return response_body


class InboundMessage(BaseModel):
    payment_id: str
    phone_number: str
    message_text: str


@app.post("/webhook/whatsapp-inbound")
async def whatsapp_inbound(msg: InboundMessage):
    result = extract_intent(msg.message_text)
    intent = result["intent"]
    confidence = result.get("confidence", 0.0)

    CONFIDENCE_THRESHOLD = 0.6

    if confidence < CONFIDENCE_THRESHOLD:
        print(f"[CONFIDENCE_GATE] Low confidence ({confidence}) for payment_id={msg.payment_id} - routing to needs_review instead of auto-acting")
        action_result = {"action": "needs_review", "payment_id": msg.payment_id, "reason": f"confidence {confidence} below threshold {CONFIDENCE_THRESHOLD}"}
    elif intent == "PROMISE_TO_PAY":
        action_result = handle_promise_to_pay(msg.payment_id, result.get("promised_timeframe"))
    elif intent == "CHURN_INTENT":
        action_result = handle_churn_intent(msg.payment_id)
    elif intent == "RETRY_NOW":
        action_result = handle_retry_now(msg.payment_id)
    else:
        action_result = {"action": "no_action_unclear_intent", "payment_id": msg.payment_id}


    session = get_session()
    session.add(ConversationMessage(
        payment_id=msg.payment_id,
        direction="inbound",
        message_text=msg.message_text,
        extracted_intent=intent,
        sentiment_score=result.get("sentiment_score"),
    ))
    session.add(RecoveryLedger(
        payment_id=msg.payment_id,
        recovered=(action_result["action"] in ("immediate_retry_triggered", "rescheduled")),
        recovery_channel="conversational_dunning",
        action=action_result["action"],
    ))
    session.commit()
    session.close()

    return {
        "payment_id": msg.payment_id,
        "phone_number": msg.phone_number,
        "message_text": msg.message_text,
        "extracted": result,
        "action_taken": action_result,
    }