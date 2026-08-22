from app.retry_scheduler import retry_payment


def handle_promise_to_pay(payment_id: str, promised_timeframe: str) -> dict:
    """
    Pauses active retries and schedules a single-tap prompt for the promised date.
    For local testing we simulate 'Friday' etc as a short delay instead of
    resolving real calendar dates.
    """
    # Simplified: in production, resolve promised_timeframe -> actual datetime.
    simulated_delay_seconds = 15  # stand-in for "wait until Friday" in local testing

    print(f"[ACTION] Promise-to-Pay: pausing retries for {payment_id}, "
          f"rescheduling prompt in {simulated_delay_seconds}s (represents '{promised_timeframe}')")

    retry_payment.apply_async(args=[payment_id, 1], countdown=simulated_delay_seconds)

    return {
        "action": "rescheduled",
        "payment_id": payment_id,
        "promised_timeframe": promised_timeframe,
        "next_attempt_in_seconds": simulated_delay_seconds,
    }


def handle_churn_intent(payment_id: str) -> dict:
    """
    Halts all retries and calls the merchant cancellation API.
    Simulated here — no real Razorpay subscription cancel call yet.
    """
    print(f"[ACTION] Churn Intent detected for {payment_id} -> halting retries + cancelling mandate")

    # TODO: call real Razorpay subscription cancel API here
    return {
        "action": "cancelled",
        "payment_id": payment_id,
    }


def handle_retry_now(payment_id: str) -> dict:
    """
    Triggers an immediate 1-tap retry instead of waiting for the backoff schedule.
    """
    print(f"[ACTION] Retry-Now requested for {payment_id} -> triggering immediate retry")

    retry_payment.apply_async(args=[payment_id, 1], countdown=0)

    return {
        "action": "immediate_retry_triggered",
        "payment_id": payment_id,
    }