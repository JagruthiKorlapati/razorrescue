import json
import google.generativeai as genai
from app.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

EXTRACTION_SYSTEM_PROMPT = """You are an intent classifier for a payment recovery system in India.
Customers reply to payment failure messages via WhatsApp, often in Hindi/English mix (Hinglish).

Classify the customer's reply into exactly one intent:
- PROMISE_TO_PAY: customer indicates they will pay later, and gives or implies a timeframe
- CHURN_INTENT: customer wants to cancel, is unhappy, or says they no longer want the service
- RETRY_NOW: customer wants to pay immediately or asks to retry now
- UNCLEAR: intent cannot be confidently determined

If PROMISE_TO_PAY, extract the promised date/timeframe as a short string (e.g. "Friday", "next week", "2026-08-28"). Otherwise set it to null.
Also give a sentiment_score from -1.0 (very negative) to 1.0 (very positive), and a confidence score from 0.0 to 1.0 reflecting how certain you are of this classification.

Respond ONLY with valid JSON, no other text, no markdown code fences, in this exact shape:
{"intent": "...", "promised_timeframe": "..." or null, "sentiment_score": 0.0, "confidence": 0.0}
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=EXTRACTION_SYSTEM_PROMPT,
)


def extract_intent(message_text: str) -> dict:
    """
    Calls the Google Gemini API to classify a customer's WhatsApp reply
    into an intent, with sentiment and confidence. Falls back to a safe
    UNCLEAR/low-confidence result if the API call fails for any reason,
    so a flaky external API never crashes the recovery pipeline.
    """
    try:
        response = model.generate_content(message_text)
        raw_text = response.text.strip()

        # Gemini sometimes wraps JSON in markdown code fences - strip if present
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()

        result = json.loads(raw_text)

        required_keys = {"intent", "promised_timeframe", "sentiment_score", "confidence"}
        if not required_keys.issubset(result.keys()):
            raise ValueError("Gemini response missing required keys")

    except Exception as e:
        print(f"[INTENT_EXTRACTION] AI call failed or malformed response: {e}")
        result = {
            "intent": "UNCLEAR",
            "promised_timeframe": None,
            "sentiment_score": 0.0,
            "confidence": 0.0,
        }

    print(f"[INTENT_EXTRACTION - GEMINI] Input: {message_text!r}")
    print(f"[INTENT_EXTRACTION - GEMINI] Result: {result}")

    return result