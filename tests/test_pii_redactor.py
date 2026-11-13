import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.pii_redactor import PIIPCIRedactor, luhn_checksum
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_luhn_algorithm_validation():
    # Valid Visa Card (passing Luhn)
    assert luhn_checksum("4532012385949981") is True
    # Invalid card number (failing Luhn)
    assert luhn_checksum("4532012385949982") is False


def test_credit_card_redaction():
    text = "My card is 4532-0123-8594-9981 for payment."
    redacted, entities, risk = PIIPCIRedactor.redact(text)
    assert "[RED_CARD_4532-XXXX-XXXX-9981]" in redacted
    assert len(entities) == 1
    assert entities[0].entity_type == "CreditCard"
    assert entities[0].luhn_valid is True
    assert risk == 20


def test_ssn_redaction():
    text = "User SSN is 219-09-8821."
    redacted, entities, risk = PIIPCIRedactor.redact(text)
    assert "[RED_SSN_XXX-XX-8821]" in redacted
    assert len(entities) == 1
    assert entities[0].entity_type == "SSN"



def test_email_and_phone_redaction():
    text = "Contact john.doe@bankdomain.com or call 800-555-0199."
    redacted, entities, risk = PIIPCIRedactor.redact(text)
    assert "[RED_EMAIL_jo***@bankdomain.com]" in redacted
    assert "[RED_PHONE_...0199]" in redacted
    assert len(entities) == 2


def test_full_inspection_api_endpoint():
    payload = {
        "prompt": "Check balance for card 4532 0123 8594 9981 and email alice@test.com",
        "user_role": "RetailCustomer"
    }
    response = client.post("/api/v1/inspect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["policy_decision"] == "MASK"
    assert data["is_sanitized"] is True
    assert len(data["masked_entities"]) == 2
    assert data["gateway_latency_ms"] < 25.0
    assert "RED_CARD_" in data["sanitized_prompt"]
    assert "RED_EMAIL_" in data["sanitized_prompt"]
