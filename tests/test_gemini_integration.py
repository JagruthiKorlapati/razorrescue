import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import patch, MagicMock
import json

from app.intent_extraction import extract_intent


def make_mock_response(json_text):
    """Builds a fake Gemini response object matching the real SDK's shape."""
    mock_response = MagicMock()
    mock_response.text = json_text
    return mock_response


@patch("app.intent_extraction.model")
def test_promise_to_pay_schema(mock_model):
    mock_model.generate_content.return_value = make_mock_response(
        json.dumps({
            "intent": "PROMISE_TO_PAY",
            "promised_timeframe": "Monday",
            "sentiment_score": 0.7,
            "confidence": 0.94,
        })
    )

    result = extract_intent("I'll pay on Monday once salary comes")

    assert result["intent"] == "PROMISE_TO_PAY"
    assert result["promised_timeframe"] == "Monday"
    assert result["confidence"] == 0.94


@patch("app.intent_extraction.model")
def test_churn_intent_schema(mock_model):
    mock_model.generate_content.return_value = make_mock_response(
        json.dumps({
            "intent": "CHURN_INTENT",
            "promised_timeframe": None,
            "sentiment_score": -0.85,
            "confidence": 0.97,
        })
    )

    result = extract_intent("Cancel this, I don't want it")

    assert result["intent"] == "CHURN_INTENT"
    assert result["sentiment_score"] < 0
    assert result["confidence"] > 0.9


@patch("app.intent_extraction.model")
def test_retry_now_schema(mock_model):
    mock_model.generate_content.return_value = make_mock_response(
        json.dumps({
            "intent": "RETRY_NOW",
            "promised_timeframe": None,
            "sentiment_score": 0.3,
            "confidence": 0.9,
        })
    )

    result = extract_intent("Please charge me now")

    assert result["intent"] == "RETRY_NOW"


@patch("app.intent_extraction.model")
def test_ambiguous_message_low_confidence(mock_model):
    mock_model.generate_content.return_value = make_mock_response(
        json.dumps({
            "intent": "UNCLEAR",
            "promised_timeframe": None,
            "sentiment_score": 0.0,
            "confidence": 0.3,
        })
    )

    result = extract_intent("hmm ok maybe")

    assert result["intent"] == "UNCLEAR"
    assert result["confidence"] < 0.5


@patch("app.intent_extraction.model")
def test_hinglish_input_returns_valid_schema(mock_model):
    mock_model.generate_content.return_value = make_mock_response(
        json.dumps({
            "intent": "PROMISE_TO_PAY",
            "promised_timeframe": "Friday",
            "sentiment_score": 0.2,
            "confidence": 0.92,
        })
    )

    result = extract_intent("Salary abhi tak nahi aaya, Friday ko pay kar dunga")

    required_keys = {"intent", "promised_timeframe", "sentiment_score", "confidence"}
    assert required_keys.issubset(result.keys())


@patch("app.intent_extraction.model")
def test_api_failure_falls_back_safely(mock_model):
    # Simulate the Gemini client raising an exception (e.g. network error, quota exceeded)
    mock_model.generate_content.side_effect = Exception("429 quota exceeded")

    result = extract_intent("Any message")

    assert result["intent"] == "UNCLEAR"
    assert result["confidence"] == 0.0
    assert result["promised_timeframe"] is None


@patch("app.intent_extraction.model")
def test_malformed_json_response_falls_back_safely(mock_model):
    # Simulate Gemini returning text that isn't valid JSON
    mock_model.generate_content.return_value = make_mock_response("not valid json at all")

    result = extract_intent("Any message")

    assert result["intent"] == "UNCLEAR"
    assert result["confidence"] == 0.0


@patch("app.intent_extraction.model")
def test_missing_required_keys_falls_back_safely(mock_model):
    # Simulate Gemini returning valid JSON but missing a required field
    mock_model.generate_content.return_value = make_mock_response(
        json.dumps({"intent": "RETRY_NOW"})  # missing confidence, sentiment_score, promised_timeframe
    )

    result = extract_intent("Any message")

    assert result["intent"] == "UNCLEAR"
    assert result["confidence"] == 0.0