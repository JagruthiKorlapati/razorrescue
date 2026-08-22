from app.celery_app import celery_app

# Backoff schedule in seconds: attempt 1 -> 5 min, attempt 2 -> 30 min, attempt 3 -> 2 hrs
BACKOFF_SCHEDULE = [300, 1800, 7200]
MAX_ATTEMPTS = len(BACKOFF_SCHEDULE)


@celery_app.task(name="retry_payment")
def retry_payment(payment_id: str, attempt: int = 1):
    """
    Simulates retrying a failed payment on the original rail.
    In production this would call the Razorpay Recurring/Charge API.
    """
    print(f"[RETRY] Attempting retry #{attempt} for payment_id={payment_id}")

    # --- Simulated outcome for now (Step 8 will replace this with real logic) ---
    success = False  # placeholder; we'll wire real payment status checks later

    if success:
        print(f"[RETRY] payment_id={payment_id} recovered on attempt {attempt}")
        return {"payment_id": payment_id, "recovered": True, "attempt": attempt}

    if attempt < MAX_ATTEMPTS:
        delay = BACKOFF_SCHEDULE[attempt - 1]
        print(f"[RETRY] payment_id={payment_id} failed attempt {attempt}, "
              f"scheduling retry #{attempt + 1} in {delay}s")
        retry_payment.apply_async(
            args=[payment_id, attempt + 1],
            countdown=delay,
        )
        return {"payment_id": payment_id, "recovered": False, "attempt": attempt, "next_retry_in": delay}

    print(f"[RETRY] payment_id={payment_id} exhausted all {MAX_ATTEMPTS} attempts, giving up on this rail")
    return {"payment_id": payment_id, "recovered": False, "attempt": attempt, "exhausted": True}