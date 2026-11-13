import re
import hashlib
import uuid
import time
from typing import List, Tuple, Optional, Dict
from app.core.verhoeff import validate_verhoeff
from app.schemas.data_protection import (
    DataClassificationTier,
    TransformationStrategy,
    SensitiveCandidateTrace,
    DataProtectionConfigRequest,
    InboundDataProtectionRequest,
    InboundDataProtectionResponse
)


def luhn_checksum(card_number_str: str) -> bool:
    """
    Validates a credit card candidate using Luhn (Mod 10) algorithm.
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


class CandidateMatch:
    def __init__(
        self,
        candidate_type: str,
        classification_tier: DataClassificationTier,
        start_index: int,
        end_index: int,
        raw_fragment: str,
        checksum_validated: bool = False,
        checksum_passed: Optional[bool] = None
    ):
        self.candidate_type = candidate_type
        self.classification_tier = classification_tier
        self.start_index = start_index
        self.end_index = end_index
        self.raw_fragment = raw_fragment
        self.checksum_validated = checksum_validated
        self.checksum_passed = checksum_passed


class InboundDataProtectionEngine:
    """
    Independent, deterministic Inbound Data Protection Engine.
    Intercepts prompt payloads, identifies sensitive data candidates (Payment Cards, Aadhaar, PAN, SSN, Emails, Phones, Accounts, OTPs),
    and applies format-preserving masking, redaction, or placeholder tokenization.
    """

    # 1. Payment Card Candidate Regex: 13-19 digits with optional hyphens/spaces
    CARD_RE = re.compile(
        r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11}|[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{1,7})\b'
    )

    # 2. Indian Aadhaar Candidate Regex: 12 digits starting with 2-9 with optional hyphens or spaces
    AADHAAR_RE = re.compile(
        r'\b[2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4}\b'
    )

    # 3. Indian PAN Candidate Regex: 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F)
    PAN_RE = re.compile(
        r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
    )

    # 4. Email Regex
    EMAIL_RE = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    )

    # 5. Phone Number Regex (10-12 digits with optional country prefix)
    PHONE_RE = re.compile(
        r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    )

    # 6. Bank Account Number Regex (with preceding/following context keywords)
    ACCOUNT_CONTEXT_RE = re.compile(
        r'(?i)\b(?:account|acct|a/c|acc\s*no\.?)\s*#?\s*:?\s*([0-9]{9,18})\b'
    )

    # 7. OTP / Verification Code Regex (4-8 digits with preceding/following OTP context keywords)
    OTP_CONTEXT_RE = re.compile(
        r'(?i)\b(?:otp|passcode|verification\s*code|auth\s*code|pin)\s*(?:is|:|=)?\s*([0-9]{4,8})\b'
    )

    @classmethod
    def scan_candidates(cls, text: str, config: DataProtectionConfigRequest) -> List[CandidateMatch]:
        """
        Scans input prompt string for all sensitive data candidates.
        Returns list of CandidateMatch objects sorted by start index.
        """
        candidates: List[CandidateMatch] = []

        # 1. Payment Cards
        if config.mask_cards:
            for m in cls.CARD_RE.finditer(text):
                raw = m.group(0)
                digits = re.sub(r'\D', '', raw)
                if 13 <= len(digits) <= 19:
                    passed = luhn_checksum(digits)
                    candidates.append(
                        CandidateMatch(
                            candidate_type="PAYMENT_CARD",
                            classification_tier=DataClassificationTier.CRITICAL_PCI,
                            start_index=m.start(),
                            end_index=m.end(),
                            raw_fragment=raw,
                            checksum_validated=True,
                            checksum_passed=passed
                        )
                    )

        # 2. Aadhaar Candidates
        if config.mask_aadhaar:
            for m in cls.AADHAAR_RE.finditer(text):
                raw = m.group(0)
                digits = re.sub(r'\D', '', raw)
                if len(digits) == 12:
                    passed = validate_verhoeff(digits)
                    candidates.append(
                        CandidateMatch(
                            candidate_type="AADHAAR",
                            classification_tier=DataClassificationTier.CRITICAL_PII,
                            start_index=m.start(),
                            end_index=m.end(),
                            raw_fragment=raw,
                            checksum_validated=True,
                            checksum_passed=passed
                        )
                    )

        # 3. PAN Candidates
        if config.mask_pan:
            for m in cls.PAN_RE.finditer(text):
                raw = m.group(0)
                # 4th character validation (P, C, H, F, A, T, B, L, J, G)
                fourth_char = raw[3].upper()
                valid_type = fourth_char in "PCHFATBLJG"
                candidates.append(
                    CandidateMatch(
                        candidate_type="PAN",
                        classification_tier=DataClassificationTier.CRITICAL_PII,
                        start_index=m.start(),
                        end_index=m.end(),
                        raw_fragment=raw,
                        checksum_validated=True,
                        checksum_passed=valid_type
                    )
                )

        # 4. Email Candidates
        if config.mask_email:
            for m in cls.EMAIL_RE.finditer(text):
                raw = m.group(0)
                candidates.append(
                    CandidateMatch(
                        candidate_type="EMAIL",
                        classification_tier=DataClassificationTier.SENSITIVE_PII,
                        start_index=m.start(),
                        end_index=m.end(),
                        raw_fragment=raw
                    )
                )

        # 5. Phone Candidates
        if config.mask_phone:
            for m in cls.PHONE_RE.finditer(text):
                raw = m.group(0)
                digits = re.sub(r'\D', '', raw)
                if len(digits) >= 10:
                    candidates.append(
                        CandidateMatch(
                            candidate_type="PHONE",
                            classification_tier=DataClassificationTier.SENSITIVE_PII,
                            start_index=m.start(),
                            end_index=m.end(),
                            raw_fragment=raw
                        )
                    )

        # 6. Account Number Candidates
        if config.mask_account_numbers:
            for m in cls.ACCOUNT_CONTEXT_RE.finditer(text):
                account_num = m.group(1)
                match_start = m.start(1)
                match_end = m.end(1)
                candidates.append(
                    CandidateMatch(
                        candidate_type="ACCOUNT_NUMBER",
                        classification_tier=DataClassificationTier.CRITICAL_PII,
                        start_index=match_start,
                        end_index=match_end,
                        raw_fragment=account_num
                    )
                )

        # 7. OTP Candidates
        if config.mask_otp:
            for m in cls.OTP_CONTEXT_RE.finditer(text):
                otp_code = m.group(1)
                match_start = m.start(1)
                match_end = m.end(1)
                candidates.append(
                    CandidateMatch(
                        candidate_type="OTP",
                        classification_tier=DataClassificationTier.CRITICAL_PII,
                        start_index=match_start,
                        end_index=match_end,
                        raw_fragment=otp_code
                    )
                )

        # Priority values for classification tiers
        tier_priority = {
            DataClassificationTier.CRITICAL_PCI: 30,
            DataClassificationTier.CRITICAL_PII: 20,
            DataClassificationTier.SENSITIVE_PII: 10,
        }

        # Sort candidates: primary by start index ascending, secondary by classification tier priority descending, tertiary by length descending
        candidates.sort(
            key=lambda c: (
                c.start_index,
                -tier_priority.get(c.classification_tier, 0),
                -(c.end_index - c.start_index)
            )
        )

        # Resolve overlapping candidates (keep highest priority non-overlapping match)
        non_overlapping: List[CandidateMatch] = []
        last_end = 0

        for c in candidates:
            if c.start_index >= last_end:
                non_overlapping.append(c)
                last_end = c.end_index

        return non_overlapping


    @classmethod
    def transform_candidate(
        cls,
        candidate: CandidateMatch,
        strategy: TransformationStrategy
    ) -> str:
        """
        Applies requested transformation strategy to raw fragment.
        Returns safe placeholder token (format-preserving).
        """
        raw = candidate.raw_fragment

        if strategy == TransformationStrategy.REDACT:
            return f"[REDACTED_{candidate.candidate_type}]"

        elif strategy == TransformationStrategy.TOKENIZE:
            hash_token = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8].upper()
            return f"[TOKEN_{candidate.candidate_type}_{hash_token}]"

        # Strategy: MASK (Format-Preserving Masking)
        if candidate.candidate_type == "PAYMENT_CARD":
            digits = re.sub(r'\D', '', raw)
            first4 = digits[:4] if len(digits) >= 4 else "XXXX"
            last4 = digits[-4:] if len(digits) >= 4 else "XXXX"
            return f"[RED_CARD_{first4}-XXXX-XXXX-{last4}]"

        elif candidate.candidate_type == "AADHAAR":
            digits = re.sub(r'\D', '', raw)
            last4 = digits[-4:] if len(digits) >= 4 else "XXXX"
            return f"[RED_AADHAAR_XXXX-XXXX-{last4}]"

        elif candidate.candidate_type == "PAN":
            first2 = raw[:2]
            last4 = raw[-4:]
            return f"[RED_PAN_{first2}***{last4}]"

        elif candidate.candidate_type == "EMAIL":
            parts = raw.split("@")
            uname = parts[0]
            domain = parts[1]
            prefix = uname[:2] if len(uname) >= 2 else uname[:1]
            return f"[RED_EMAIL_{prefix}***@{domain}]"

        elif candidate.candidate_type == "PHONE":
            digits = re.sub(r'\D', '', raw)
            last4 = digits[-4:] if len(digits) >= 4 else "XXXX"
            return f"[RED_PHONE_...{last4}]"

        elif candidate.candidate_type == "ACCOUNT_NUMBER":
            last4 = raw[-4:] if len(raw) >= 4 else "XXXX"
            return f"[RED_ACCT_...{last4}]"

        elif candidate.candidate_type == "OTP":
            return "[RED_OTP_****]"

        return f"[RED_{candidate.candidate_type}]"

    @classmethod
    def process(cls, request: InboundDataProtectionRequest) -> InboundDataProtectionResponse:
        """
        Executes full Inbound Data Protection pipeline.
        Returns transformed prompt payload, candidate traces (zero-raw secret exposure), and decision metrics.
        """
        start_time = time.perf_counter()
        req_id = f"dp-{uuid.uuid4().hex[:12]}"

        config = request.config or DataProtectionConfigRequest()
        prompt_text = request.prompt

        # 1. Scan for non-overlapping candidates
        candidates = cls.scan_candidates(prompt_text, config)

        # 2. Rebuild prompt string replacing candidates with transformed placeholders
        transformed_prompt = ""
        current_idx = 0
        candidate_traces: List[SensitiveCandidateTrace] = []

        for idx, c in enumerate(candidates):
            transformed_placeholder = cls.transform_candidate(c, config.transformation_strategy)
            
            # Append preceding unmasked text
            transformed_prompt += prompt_text[current_idx:c.start_index]
            # Append safe masked placeholder
            transformed_prompt += transformed_placeholder
            current_idx = c.end_index

            # Build trace entry (Zero raw sensitive data included!)
            candidate_traces.append(
                SensitiveCandidateTrace(
                    candidate_id=f"cand-{idx+1}",
                    candidate_type=c.candidate_type,
                    classification_tier=c.classification_tier,
                    start_index=c.start_index,
                    end_index=c.end_index,
                    checksum_validated=c.checksum_validated,
                    checksum_passed=c.checksum_passed,
                    transformation_applied=config.transformation_strategy,
                    safe_masked_fragment=transformed_placeholder
                )
            )

        # Append remaining tail of text
        transformed_prompt += prompt_text[current_idx:]

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
        policy_decision = config.transformation_strategy.value if candidates else "ALLOW"

        return InboundDataProtectionResponse(
            request_id=req_id,
            original_prompt_length=len(prompt_text),
            transformed_prompt=transformed_prompt,
            candidates_found=len(candidates),
            candidate_traces=candidate_traces,
            policy_decision=policy_decision,
            latency_ms=elapsed_ms
        )
