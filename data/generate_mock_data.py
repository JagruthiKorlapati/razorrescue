import json
import random

random.seed(42)  # reproducible results

TRANSIENT_CODES = ["GATEWAY_TIMEOUT", "BANK_SYSTEM_ERROR", "SERVER_ERROR", "NETWORK_ERROR", "ISSUER_TIMEOUT"]
HARD_CODES = ["BAD_REQUEST_ERROR", "INSUFFICIENT_FUNDS", "MANDATE_NOT_ACTIVE", "CARD_DECLINED", "AUTHENTICATION_FAILED"]

# Simulated customer reply templates per intent, with rough real-world frequency
REPLY_TEMPLATES = {
    "PROMISE_TO_PAY": [
        "Salary abhi tak nahi aaya, Friday ko pay kar dunga",
        "I'll pay next week once my account has funds",
        "Sorry, will clear this by Monday",
    ],
    "CHURN_INTENT": [
        "Please cancel this, I don't want it anymore",
        "Stop charging me, not interested",
    ],
    "RETRY_NOW": [
        "Please retry now, I have funds",
        "Try charging again now",
    ],
    "NO_REPLY": [None],  # customer never responds
}

# Rough distribution of how customers respond to dunning (used for hard failures)
REPLY_DISTRIBUTION = [
    ("PROMISE_TO_PAY", 0.30),
    ("RETRY_NOW", 0.20),
    ("CHURN_INTENT", 0.10),
    ("NO_REPLY", 0.40),
]


def weighted_choice(options):
    r = random.random()
    cumulative = 0.0
    for value, weight in options:
        cumulative += weight
        if r <= cumulative:
            return value
    return options[-1][0]


def generate_transactions(n=100):
    transactions = []
    for i in range(1, n + 1):
        is_transient = random.random() < 0.55  # ~55% transient, 45% hard failure

        error_code = random.choice(TRANSIENT_CODES) if is_transient else random.choice(HARD_CODES)

        reply_intent = weighted_choice(REPLY_DISTRIBUTION) if not is_transient else None
        reply_text = random.choice(REPLY_TEMPLATES[reply_intent]) if reply_intent else None

        transactions.append({
            "payment_id": f"pay_sim_{i:04d}",
            "error_code": error_code,
            "error_source": "issuer",
            "amount": random.choice([29900, 49900, 99900, 149900]),  # in paise
            "classification_expected": "TRANSIENT" if is_transient else "HARD_FAILURE",
            "customer_reply_intent": reply_intent,
            "customer_reply_text": reply_text,
        })

    return transactions


if __name__ == "__main__":
    data = generate_transactions(100)
    with open("data/mock_transactions.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Generated {len(data)} mock transactions -> data/mock_transactions.json")