from enum import Enum


class FailureType(str, Enum):
    TRANSIENT = "TRANSIENT"
    HARD_FAILURE = "HARD_FAILURE"


# Error codes that indicate a temporary bank/gateway problem — safe to retry
TRANSIENT_ERROR_CODES = {
    "GATEWAY_TIMEOUT",
    "BANK_SYSTEM_ERROR",
    "SERVER_ERROR",
    "NETWORK_ERROR",
    "ISSUER_TIMEOUT",
}

# Error codes that mean the payment genuinely can't go through on this rail
HARD_FAILURE_ERROR_CODES = {
    "BAD_REQUEST_ERROR",       # e.g. invalid mandate/account state
    "INSUFFICIENT_FUNDS",
    "MANDATE_NOT_ACTIVE",
    "CARD_DECLINED",
    "AUTHENTICATION_FAILED",
}


def classify_failure(payment_entity: dict) -> FailureType:
    """
    Decide whether a failed payment is a transient issue (retry same rail)
    or a hard failure (switch rails / start conversational dunning).
    """
    error_code = (payment_entity.get("error_code") or "").upper()
    error_source = (payment_entity.get("error_source") or "").lower()

    if error_code in TRANSIENT_ERROR_CODES:
        return FailureType.TRANSIENT

    if error_code in HARD_FAILURE_ERROR_CODES:
        return FailureType.HARD_FAILURE

    # Fallback heuristic: bank-side/issuer-side errors with unknown codes
    # are treated as transient (safer to retry than to abandon)
    if error_source in ("issuer", "bank"):
        return FailureType.TRANSIENT

    # Default: treat unknown errors as hard failures so they get human/agent attention
    return FailureType.HARD_FAILURE