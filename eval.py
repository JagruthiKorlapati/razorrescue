"""
RazorRescue Evaluation Script
Compares recovery outcomes: naive same-rail retry vs. RazorRescue's
classify -> cross-rail fallback / conversational dunning -> intent-based action.

Runs entirely offline against data/mock_transactions.json — no live server needed.
"""

import json
import random
import statistics
random.seed(7)

from app.classifier import classify_failure, FailureType
from app.intent_extraction import extract_intent


def load_transactions(path="data/mock_transactions.json"):
    with open(path) as f:
        return json.load(f)


def simulate_baseline(transactions):
    """
    Naive strategy: fixed T+1/T+2/T+3 retry on the same rail, no fallback,
    no conversational dunning. Recovery only happens if the same rail
    happens to be back up in time - we simulate this at a flat probability.
    """
    SAME_RAIL_RECOVERY_PROB = {
        "TRANSIENT": 0.55,   # transient issues often self-resolve on retry
        "HARD_FAILURE": 0.15,  # same-rail retry rarely fixes a hard failure
    }

    results = []
    for txn in transactions:
        payment_entity = {"error_code": txn["error_code"], "error_source": txn["error_source"]}
        classification = classify_failure(payment_entity).value

        recovered = random.random() < SAME_RAIL_RECOVERY_PROB[classification]
        time_to_recovery_days = random.choice([1, 2, 3]) if recovered else None

        results.append({
            "payment_id": txn["payment_id"],
            "classification": classification,
            "recovered": recovered,
            "time_to_recovery_days": time_to_recovery_days,
            "channel": "same_rail_retry" if recovered else None,
        })

    return results


def simulate_razorrescue(transactions):
    """
    RazorRescue strategy: classify -> transient gets backoff retry (same
    recovery odds as baseline for that branch) -> hard failure gets
    cross-rail fallback + conversational dunning, with recovery odds
    depending on the customer's simulated reply intent.
    """
    TRANSIENT_RECOVERY_PROB = 0.55  # same as baseline for apples-to-apples on this branch

    # Recovery odds conditioned on how the customer actually responds
    HARD_FAILURE_RECOVERY_BY_INTENT = {
        "PROMISE_TO_PAY": 0.75,  # scheduled prompt on promised date, high recovery
        "RETRY_NOW": 0.90,       # immediate 1-tap retry, very high recovery
        "CHURN_INTENT": 0.0,     # correctly halted - not counted as recovery, but avoids a chargeback
        "NO_REPLY": 0.20,        # cross-rail UPI Intent link alone still recovers some
    }

    results = []
    for txn in transactions:
        payment_entity = {"error_code": txn["error_code"], "error_source": txn["error_source"]}
        classification = classify_failure(payment_entity).value

        if classification == "TRANSIENT":
            recovered = random.random() < TRANSIENT_RECOVERY_PROB
            time_to_recovery_days = round(random.uniform(0.05, 0.3), 2) if recovered else None
            channel = "same_rail_retry" if recovered else None
            chargeback_avoided = False
        else:
            reply_intent = txn["customer_reply_intent"] or "NO_REPLY"

            # Run through the real (mocked) intent extraction if there's a reply,
            # to prove the LLM pipeline actually drives the outcome
            if txn["customer_reply_text"]:
                extracted = extract_intent(txn["customer_reply_text"])
                reply_intent = extracted["intent"] if extracted["intent"] != "UNCLEAR" else reply_intent

            prob = HARD_FAILURE_RECOVERY_BY_INTENT.get(reply_intent, 0.20)
            recovered = random.random() < prob
            time_to_recovery_days = round(random.uniform(0.1, 1.0), 2) if recovered else None
            channel = "cross_rail_or_promise_to_pay" if recovered else None
            chargeback_avoided = (reply_intent == "CHURN_INTENT")

        results.append({
            "payment_id": txn["payment_id"],
            "classification": classification,
            "recovered": recovered,
            "time_to_recovery_days": time_to_recovery_days,
            "channel": channel,
            "chargeback_avoided": chargeback_avoided,
        })

    return results


def summarize(label, results):
    total = len(results)
    recovered = [r for r in results if r["recovered"]]
    recovery_rate = len(recovered) / total * 100

    recovery_times = [r["time_to_recovery_days"] for r in recovered if r["time_to_recovery_days"] is not None]
    median_time = statistics.median(recovery_times) if recovery_times else None

    print(f"\n--- {label} ---")
    print(f"Recovered:              {len(recovered)} / {total}   ({recovery_rate:.1f}%)")
    if median_time is not None:
        print(f"Median time-to-recovery: {median_time:.2f} days")

    return {
        "recovered_count": len(recovered),
        "total": total,
        "recovery_rate": round(recovery_rate, 1),
        "median_time_days": round(median_time, 2) if median_time is not None else None,
    }


def main():
    transactions = load_transactions()
    print(f"=== RazorRescue Evaluation ===")
    print(f"Transactions simulated: {len(transactions)}")

    baseline_results = simulate_baseline(transactions)
    baseline_summary = summarize("Baseline (naive retry)", baseline_results)

    razorrescue_results = simulate_razorrescue(transactions)
    rr_summary = summarize("RazorRescue", razorrescue_results)

    cross_rail_recoveries = sum(
        1 for r in razorrescue_results if r["recovered"] and r["classification"] == "HARD_FAILURE"
    )
    chargebacks_avoided = sum(1 for r in razorrescue_results if r.get("chargeback_avoided"))

    print(f"\n--- RazorRescue Breakdown ---")
    print(f"Hard-failure recoveries (cross-rail/dunning): {cross_rail_recoveries}")
    print(f"Chargeback-risk cancellations avoided:         {chargebacks_avoided}")

    lift = round(rr_summary["recovery_rate"] - baseline_summary["recovery_rate"], 1)
    print(f"\n--- Net Lift ---")
    print(f"+{lift:.1f} percentage points recovered vs. baseline")

    # Save results for the README / reporting
    output = {
        "baseline": baseline_summary,
        "razorrescue": rr_summary,
        "cross_rail_recoveries": cross_rail_recoveries,
        "chargebacks_avoided": chargebacks_avoided,
        "lift_percentage_points": lift,
    }
    with open("eval_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nFull results saved to eval_results.json")


if __name__ == "__main__":
    main()