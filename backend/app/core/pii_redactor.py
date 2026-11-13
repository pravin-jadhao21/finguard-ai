import re
from typing import List, Tuple
from app.schemas.inspect import MaskedEntity


def luhn_checksum(card_number_str: str) -> bool:
    """
    Validates a credit card number using the Luhn (Mod 10) Algorithm.
    """
    digits = [int(c) for c in card_number_str if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    
    checksum = 0
    reverse_digits = digits[::-1]
    
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit
            
    return checksum % 10 == 0


class PIIPCIRedactor:
    """
    Deterministic PII & PCI-DSS Data Redaction Engine.
    Identifies credit cards (with Luhn check), SSNs, IBANs, emails, and phone numbers.
    Replaces matched sensitive data with format-preserving redacted tokens.
    """

    # PCI-DSS Credit Card Pattern: 13 to 19 digits, allowing optional hyphens or spaces
    CARD_RE = re.compile(
        r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11}|[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{1,7})\b'
    )

    # US Social Security Number: XXX-XX-XXXX
    SSN_RE = re.compile(
        r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b'
    )

    # International Bank Account Number (IBAN): e.g. GB33BUKB20201555555555, DE89370400440532013000
    IBAN_RE = re.compile(
        r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b', re.IGNORECASE
    )

    # Email Address
    EMAIL_RE = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    )

    # Phone Number (10+ digits with optional international prefix/dashes)
    PHONE_RE = re.compile(
        r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    )

    @classmethod
    def redact(cls, text: str) -> Tuple[str, List[MaskedEntity], int]:
        """
        Scans and redacts sensitive PII & PCI data from text.
        Returns: (redacted_text, list_of_masked_entities, cumulative_risk_weight)
        """
        if not text:
            return "", [], 0

        masked_entities: List[MaskedEntity] = []
        redacted_text = text
        total_risk_weight = 0

        # 1. PCI-DSS Credit Cards (with Luhn Validation)
        for match in cls.CARD_RE.finditer(text):
            raw_match = match.group(0)
            digits_only = re.sub(r'\D', '', raw_match)
            
            # Check Luhn validity
            if luhn_checksum(digits_only):
                first4 = digits_only[:4]
                last4 = digits_only[-4:]
                masked_token = f"[RED_CARD_{first4}-XXXX-XXXX-{last4}]"
                
                masked_entities.append(
                    MaskedEntity(
                        rule_id="PCI_CARD_MASK",
                        category="PCI-DSS",
                        entity_type="CreditCard",
                        original_fragment=raw_match,
                        masked_fragment=masked_token,
                        luhn_valid=True
                    )
                )
                redacted_text = redacted_text.replace(raw_match, masked_token)
                total_risk_weight += 20

        # 2. SSN Redaction
        for match in cls.SSN_RE.finditer(text):
            raw_match = match.group(0)
            # Avoid re-matching already masked strings or card numbers
            if "[RED_" in raw_match:
                continue
            
            digits_only = re.sub(r'\D', '', raw_match)
            last4 = digits_only[-4:]
            masked_token = f"[RED_SSN_XXX-XX-{last4}]"
            
            masked_entities.append(
                MaskedEntity(
                    rule_id="PII_SSN_MASK",
                    category="PII",
                    entity_type="SSN",
                    original_fragment=raw_match,
                    masked_fragment=masked_token,
                    luhn_valid=False
                )
            )
            redacted_text = redacted_text.replace(raw_match, masked_token)
            total_risk_weight += 15

        # 3. IBAN Redaction
        for match in cls.IBAN_RE.finditer(text):
            raw_match = match.group(0)
            if "[RED_" in raw_match:
                continue
            
            country_code = raw_match[:2].upper()
            last4 = raw_match[-4:]
            masked_token = f"[RED_IBAN_{country_code}...{last4}]"
            
            masked_entities.append(
                MaskedEntity(
                    rule_id="PII_IBAN_MASK",
                    category="PII",
                    entity_type="IBAN",
                    original_fragment=raw_match,
                    masked_fragment=masked_token,
                    luhn_valid=False
                )
            )
            redacted_text = redacted_text.replace(raw_match, masked_token)
            total_risk_weight += 15

        # 4. Email Redaction
        for match in cls.EMAIL_RE.finditer(text):
            raw_match = match.group(0)
            if "[RED_" in raw_match:
                continue
            
            parts = raw_match.split("@")
            username = parts[0]
            domain = parts[1]
            user_prefix = username[:2] if len(username) >= 2 else username[:1]
            masked_token = f"[RED_EMAIL_{user_prefix}***@{domain}]"
            
            masked_entities.append(
                MaskedEntity(
                    rule_id="PII_EMAIL_MASK",
                    category="PII",
                    entity_type="Email",
                    original_fragment=raw_match,
                    masked_fragment=masked_token,
                    luhn_valid=False
                )
            )
            redacted_text = redacted_text.replace(raw_match, masked_token)
            total_risk_weight += 10

        # 5. Phone Redaction
        for match in cls.PHONE_RE.finditer(text):
            raw_match = match.group(0)
            if "[RED_" in raw_match:
                continue
            
            digits_only = re.sub(r'\D', '', raw_match)
            if len(digits_only) >= 10:
                last4 = digits_only[-4:]
                masked_token = f"[RED_PHONE_...{last4}]"
                
                # Check if raw_match is inside redacted_text to prevent duplicate replacements
                if raw_match in redacted_text:
                    masked_entities.append(
                        MaskedEntity(
                            rule_id="PII_PHONE_MASK",
                            category="PII",
                            entity_type="Phone",
                            original_fragment=raw_match,
                            masked_fragment=masked_token,
                            luhn_valid=False
                        )
                    )
                    redacted_text = redacted_text.replace(raw_match, masked_token)
                    total_risk_weight += 10

        return redacted_text, masked_entities, total_risk_weight
