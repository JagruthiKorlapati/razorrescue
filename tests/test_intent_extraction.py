import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.intent_extraction import extract_intent


def test_promise_to_pay_with_day():
    result = extract_intent("Salary abhi tak nahi aaya, Friday ko pay kar dunga")
    assert result["intent"] == "PROMISE_TO_PAY"
    assert result["promised_timeframe"] == "Friday"


def test_churn_intent():
    result = extract_intent("Please cancel this, I don't want it anymore")
    assert result["intent"] == "CHURN_INTENT"
    assert result["sentiment_score"] < 0


def test_retry_now():
    result = extract_intent("Please retry now, I have funds")
    assert result["intent"] == "RETRY_NOW"


def test_unclear_message():
    result = extract_intent("hmm okay")
    assert result["intent"] == "UNCLEAR"


def test_result_has_required_keys():
    result = extract_intent("test message")
    assert "intent" in result
    assert "promised_timeframe" in result
    assert "sentiment_score" in result
    assert "confidence" in result