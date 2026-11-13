import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.outbound_enforcer import OutboundResponseEnforcer
from app.schemas.outbound import OutboundValidationRequest, OutboundValidationAction


@pytest.fixture
def enforcer():
    return OutboundResponseEnforcer()


# 1. Valid Answer Test
def test_valid_answer_matching_ground_truth(enforcer):
    req = OutboundValidationRequest(
        llm_response="Our standard fixed deposit interest rate is 6.5% for a 12-month term."
    )
    res = enforcer.validate(req)
    assert res.action_decision in (OutboundValidationAction.ALLOW, OutboundValidationAction.MODIFY)
    assert res.discrepancy_detected is False
    assert len(res.grounding_details) == 1
    assert res.grounding_details[0].is_rate_matching is True


# 2. Conflicting Rate Test (Hallucinated rate correction)
def test_conflicting_rate_correction(enforcer):
    req = OutboundValidationRequest(
        llm_response="Our fixed deposit interest rate is 7.5% per annum."
    )
    res = enforcer.validate(req)
    assert res.action_decision == OutboundValidationAction.MODIFY
    assert res.discrepancy_detected is True
    assert res.reason_code == "OUTBOUND_GROUNDING_RATE_DISCREPANCY_CORRECTED"
    assert "6.5%" in res.sanitized_llm_response
    assert res.grounding_details[0].is_rate_matching is False


# 3. Stale Source Version Test
def test_stale_ground_truth_version_escalation(enforcer):
    req = OutboundValidationRequest(
        llm_response="Our fixed deposit rate is 6.5%",
        ground_truth_version="0.9.0"  # Stale version
    )
    res = enforcer.validate(req)
    assert res.action_decision == OutboundValidationAction.ESCALATE
    assert res.reason_code == "OUTBOUND_STALE_GROUND_TRUTH_VERSION_ESCALATED"
    assert res.fallback_applied is True


# 4. Sensitive Data / Secret Key Leakage Test
def test_outbound_secret_key_leak_blocked(enforcer):
    req = OutboundValidationRequest(
        llm_response="Connection string: aws_key=AKIAIOSFODNN7EXAMPLE_SECRET for database access"
    )
    res = enforcer.validate(req)
    assert res.action_decision == OutboundValidationAction.BLOCK
    assert res.reason_code == "OUTBOUND_SECRET_KEY_LEAK_BLOCKED"
    assert res.leak_detected is True
    assert res.sanitized_llm_response is None


def test_outbound_pii_card_leak_masked(enforcer):
    req = OutboundValidationRequest(
        llm_response="Your card on file is 4532-0123-8594-9981."
    )
    res = enforcer.validate(req)
    assert res.action_decision == OutboundValidationAction.MODIFY
    assert res.reason_code == "OUTBOUND_PII_PCI_LEAK_MASKED"
    assert res.leak_detected is True
    assert "[RED_CARD_4532-XXXX-XXXX-9981]" in res.sanitized_llm_response


# 5. Unsafe Financial Claim Test
def test_unsafe_financial_claim_blocked(enforcer):
    req = OutboundValidationRequest(
        llm_response="Invest in this zero risk investment for guaranteed 100% profit today."
    )
    res = enforcer.validate(req)
    assert res.action_decision == OutboundValidationAction.BLOCK
    assert res.reason_code == "OUTBOUND_UNSAFE_FINANCIAL_CLAIM_BLOCKED"
    assert res.unsafe_claim_detected is True


# 6. Restricted Financial Advice Test (REDIRECT)
def test_restricted_financial_advice_redirect(enforcer):
    req = OutboundValidationRequest(
        llm_response="You should buy stock in Acme Corp right now for quick gains."
    )
    res = enforcer.validate(req)
    assert res.action_decision == OutboundValidationAction.REDIRECT
    assert res.reason_code == "OUTBOUND_RESTRICTED_ADVICE_REDIRECTED"
    assert res.fallback_applied is True
    assert "certified financial advisor" in res.sanitized_llm_response


# 7. General Guidance Disclaimer Test (MODIFY)
def test_financial_advice_disclaimer_appended(enforcer):
    req = OutboundValidationRequest(
        llm_response="We recommend opening a high yield savings account to maximize interest."
    )
    res = enforcer.validate(req)
    assert res.action_decision == OutboundValidationAction.MODIFY
    assert res.reason_code == "OUTBOUND_DISCLAIMER_APPENDED"
    assert "Statutory Disclaimer" in res.sanitized_llm_response


# 8. Missing Reference Data Handling Test
def test_missing_reference_data_safe_handling(enforcer):
    req = OutboundValidationRequest(
        llm_response="Our commercial credit card annual fee is $95."
    )
    res = enforcer.validate(req)
    # Fee field is not in product grounding list, evaluates safely without crash
    assert res.action_decision in (OutboundValidationAction.ALLOW, OutboundValidationAction.MODIFY)
    assert res.discrepancy_detected is False

