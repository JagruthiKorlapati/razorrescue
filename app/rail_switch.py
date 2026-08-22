import uuid


def generate_upi_fallback(payment_entity: dict) -> dict:
    """
    Simulates generating a fallback UPI Intent payload for an alternate
    VPA/app, instead of retrying the same failed rail.

    In production this would call Razorpay's UPI Intent creation API
    with the merchant's registered VPA(s) and return a real deep link
    (e.g. upi://pay?pa=...&pn=...&am=...&tr=...).
    """
    payment_id = payment_entity["id"]
    amount = payment_entity.get("amount", 0)

    fallback_txn_ref = f"rr_{uuid.uuid4().hex[:12]}"

    # Simulated alternate VPA pool — in production this comes from merchant config
    fallback_vpa = "merchant.fallback@upi"

    upi_intent_link = (
        f"upi://pay?pa={fallback_vpa}"
        f"&pn=RazorRescue"
        f"&am={amount / 100:.2f}"
        f"&tr={fallback_txn_ref}"
        f"&cu=INR"
    )

    print(f"[RAIL_SWITCH] Generated fallback UPI Intent for payment_id={payment_id}")
    print(f"[RAIL_SWITCH] Link: {upi_intent_link}")

    return {
        "payment_id": payment_id,
        "fallback_txn_ref": fallback_txn_ref,
        "fallback_vpa": fallback_vpa,
        "upi_intent_link": upi_intent_link,
    }