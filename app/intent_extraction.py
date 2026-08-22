import re


def extract_intent(message_text: str) -> dict:
    """
    MOCKED intent extraction — simulates what the Claude API would return,
    using simple keyword rules. Swap this out for the real Anthropic API
    call once billing/API key is set up (see intent_extraction_real.py).
    """
    text = message_text.lower()

    churn_keywords = ["cancel", "stop", "don't want", "not interested", "band karo", "nahi chahiye"]
    promise_keywords = ["salary", "friday", "next week", "will pay", "pay karunga", "pay kar dunga", "later"]
    retry_keywords = ["pay now", "retry", "abhi kar do", "try again", "charge now", "charging again", "try charging"]

    if any(k in text for k in churn_keywords):
        intent = "CHURN_INTENT"
        sentiment_score = -0.7
        promised_timeframe = None
        confidence = 0.85
    elif any(k in text for k in promise_keywords):
        intent = "PROMISE_TO_PAY"
        sentiment_score = 0.1
        confidence = 0.8
        # very simple timeframe extraction
        match = re.search(r"(friday|monday|tuesday|wednesday|thursday|saturday|sunday|next week|tomorrow)", text)
        promised_timeframe = match.group(1).capitalize() if match else "unspecified"
    elif any(k in text for k in retry_keywords):
        intent = "RETRY_NOW"
        sentiment_score = 0.3
        promised_timeframe = None
        confidence = 0.8
    else:
        intent = "UNCLEAR"
        sentiment_score = 0.0
        promised_timeframe = None
        confidence = 0.3

    result = {
        "intent": intent,
        "promised_timeframe": promised_timeframe,
        "sentiment_score": sentiment_score,
        "confidence": confidence,
    }

    print(f"[INTENT_EXTRACTION - MOCKED] Input: {message_text!r}")
    print(f"[INTENT_EXTRACTION - MOCKED] Result: {result}")

    return result