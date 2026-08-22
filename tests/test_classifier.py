import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.classifier import classify_failure, FailureType


def test_gateway_timeout_is_transient():
    payment = {"error_code": "GATEWAY_TIMEOUT", "error_source": "issuer"}
    assert classify_failure(payment) == FailureType.TRANSIENT


def test_bank_system_error_is_transient():
    payment = {"error_code": "BANK_SYSTEM_ERROR", "error_source": "issuer"}
    assert classify_failure(payment) == FailureType.TRANSIENT


def test_bad_request_is_hard_failure():
    payment = {"error_code": "BAD_REQUEST_ERROR", "error_source": "issuer"}
    assert classify_failure(payment) == FailureType.HARD_FAILURE


def test_insufficient_funds_is_hard_failure():
    payment = {"error_code": "INSUFFICIENT_FUNDS", "error_source": "issuer"}
    assert classify_failure(payment) == FailureType.HARD_FAILURE


def test_unknown_code_from_issuer_defaults_to_transient():
    payment = {"error_code": "SOME_NEW_UNKNOWN_CODE", "error_source": "issuer"}
    assert classify_failure(payment) == FailureType.TRANSIENT


def test_unknown_code_unknown_source_defaults_to_hard_failure():
    payment = {"error_code": "SOME_NEW_UNKNOWN_CODE", "error_source": "unknown"}
    assert classify_failure(payment) == FailureType.HARD_FAILURE


def test_case_insensitive_error_code():
    payment = {"error_code": "gateway_timeout", "error_source": "issuer"}
    assert classify_failure(payment) == FailureType.TRANSIENT