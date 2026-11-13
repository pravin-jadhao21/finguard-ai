import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.verhoeff import validate_verhoeff, generate_verhoeff_check_digit
from app.core.inbound_data_protection import InboundDataProtectionEngine, luhn_checksum
from app.schemas.data_protection import (
    InboundDataProtectionRequest,
    DataProtectionConfigRequest,
    TransformationStrategy,
    DataClassificationTier
)


# --- 1. VERHOEFF CHECKSUM TESTS ---

def test_verhoeff_checksum_validation():
    # Construct valid Verhoeff 12-digit string
    base_11_digits = "23456789012"
    check_digit = generate_verhoeff_check_digit(base_11_digits)
    valid_aadhaar = base_11_digits + check_digit

    assert validate_verhoeff(valid_aadhaar) is True
    # Modify last digit to corrupt checksum
    invalid_aadhaar = valid_aadhaar[:-1] + str((int(valid_aadhaar[-1]) + 1) % 10)
    assert validate_verhoeff(invalid_aadhaar) is False


# --- 2. PAYMENT CARD DETECTOR TESTS ---

def test_luhn_payment_card_positive_and_negative():
    # Luhn valid synthetic card
    valid_card = "4532 0123 8594 9981"
    assert luhn_checksum(valid_card) is True

    # Luhn invalid synthetic card
    invalid_card = "4532 0123 8594 9982"
    assert luhn_checksum(invalid_card) is False

    req = InboundDataProtectionRequest(prompt=f"Cards: {valid_card} and {invalid_card}")
    res = InboundDataProtectionEngine.process(req)

    assert "[RED_CARD_4532-XXXX-XXXX-9981]" in res.transformed_prompt
    assert len(res.candidate_traces) == 2
    
    # Trace 1 (Valid Luhn)
    trace_valid = [t for t in res.candidate_traces if t.checksum_passed is True][0]
    assert trace_valid.candidate_type == "PAYMENT_CARD"
    assert trace_valid.classification_tier == DataClassificationTier.CRITICAL_PCI

    # Trace 2 (Invalid Luhn)
    trace_invalid = [t for t in res.candidate_traces if t.checksum_passed is False][0]
    assert trace_invalid.candidate_type == "PAYMENT_CARD"


# --- 3. AADHAAR CANDIDATE DETECTOR TESTS ---

def test_aadhaar_verhoeff_detection():
    base_11_digits = "23456789012"
    check_digit = generate_verhoeff_check_digit(base_11_digits)
    valid_aadhaar = f"2345-6789-012{check_digit}"

    req = InboundDataProtectionRequest(prompt=f"Aadhaar identity number: {valid_aadhaar}")
    res = InboundDataProtectionEngine.process(req)

    assert f"[RED_AADHAAR_XXXX-XXXX-012{check_digit}]" in res.transformed_prompt
    assert res.candidates_found == 1
    assert res.candidate_traces[0].checksum_passed is True


def test_aadhaar_starting_with_zero_or_one_excluded():
    # Aadhaar numbers cannot start with 0 or 1
    invalid_format = "0123 4567 8901"
    req = InboundDataProtectionRequest(prompt=f"Number: {invalid_format}")
    res = InboundDataProtectionEngine.process(req)
    assert res.candidates_found == 0


# --- 4. PAN (PERMANENT ACCOUNT NUMBER) TESTS ---

def test_pan_detection_and_masking():
    valid_pan = "ABCPE1234F"
    req = InboundDataProtectionRequest(prompt=f"Customer PAN is {valid_pan}")
    res = InboundDataProtectionEngine.process(req)

    assert "[RED_PAN_AB***234F]" in res.transformed_prompt
    assert res.candidates_found == 1
    assert res.candidate_traces[0].candidate_type == "PAN"
    assert res.candidate_traces[0].checksum_passed is True  # 'P' in 4th char is valid Individual PAN



# --- 5. EMAIL & PHONE DETECTOR TESTS ---

def test_email_and_phone_detection():
    prompt = "Reach me at contact.test@securebank.com or call +1-800-555-0199."
    req = InboundDataProtectionRequest(prompt=prompt)
    res = InboundDataProtectionEngine.process(req)

    assert "[RED_EMAIL_co***@securebank.com]" in res.transformed_prompt
    assert "[RED_PHONE_...0199]" in res.transformed_prompt
    assert res.candidates_found == 2


# --- 6. BANK ACCOUNT NUMBER & OTP TESTS ---

def test_account_number_and_otp_context_detection():
    prompt = "Please transfer money from account # 9876543210 using OTP: 4921"
    req = InboundDataProtectionRequest(prompt=prompt)
    res = InboundDataProtectionEngine.process(req)

    assert "[RED_ACCT_...3210]" in res.transformed_prompt
    assert "[RED_OTP_****]" in res.transformed_prompt
    assert res.candidates_found == 2


# --- 7. OVERLAPPING CANDIDATE RESOLUTION ---

def test_overlapping_candidate_resolution():
    # Prompt where a phone number or card might match inside account context
    prompt = "Check account # 4532012385949981"
    req = InboundDataProtectionRequest(prompt=prompt)
    res = InboundDataProtectionEngine.process(req)

    # Should cleanly replace without corrupted double-replacements
    assert res.candidates_found > 0
    assert "[RED_" in res.transformed_prompt


# --- 8. TRANSFORMATION STRATEGIES (MASK vs REDACT vs TOKENIZE) ---

def test_transformation_strategies():
    prompt = "Customer email is alice@test.com"

    # Strategy 1: MASK
    req_mask = InboundDataProtectionRequest(
        prompt=prompt,
        config=DataProtectionConfigRequest(transformation_strategy=TransformationStrategy.MASK)
    )
    res_mask = InboundDataProtectionEngine.process(req_mask)
    assert "[RED_EMAIL_al***@test.com]" in res_mask.transformed_prompt

    # Strategy 2: REDACT
    req_redact = InboundDataProtectionRequest(
        prompt=prompt,
        config=DataProtectionConfigRequest(transformation_strategy=TransformationStrategy.REDACT)
    )
    res_redact = InboundDataProtectionEngine.process(req_redact)
    assert "[REDACTED_EMAIL]" in res_redact.transformed_prompt

    # Strategy 3: TOKENIZE
    req_tok = InboundDataProtectionRequest(
        prompt=prompt,
        config=DataProtectionConfigRequest(transformation_strategy=TransformationStrategy.TOKENIZE)
    )
    res_tok = InboundDataProtectionEngine.process(req_tok)
    assert "[TOKEN_EMAIL_" in res_tok.transformed_prompt


# --- 9. ZERO-RAW SENSITIVE DATA LEAKAGE IN TRACES ---

def test_zero_raw_sensitive_data_in_traces():
    raw_secret_card = "4532012385949981"
    req = InboundDataProtectionRequest(prompt=f"Card is {raw_secret_card}")
    res = InboundDataProtectionEngine.process(req)

    # Convert entire JSON trace to string
    trace_json_str = res.model_dump_json()

    # Raw secret MUST NOT appear anywhere in the output audit trace structure!
    assert raw_secret_card not in trace_json_str
    assert "[RED_CARD_" in trace_json_str
