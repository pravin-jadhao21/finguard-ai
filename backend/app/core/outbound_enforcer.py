import re
import time
import uuid
from typing import List, Tuple, Optional
from app.core.ground_truth import GroundTruthStore
from app.core.pii_redactor import PIIPCIRedactor
from app.schemas.outbound import (
    OutboundValidationAction,
    GroundingValidationDetail,
    OutboundValidationRequest,
    OutboundValidationResponse
)


class OutboundResponseEnforcer:
    """
    Deterministic Outbound Response Validation Engine.
    Executes 4-phase egress inspection pipeline:
    1. Secret & Sensitive Data Leak Scanning (PII/PCI, API keys, Private RSA keys)
    2. Unsafe Financial Claim Enforcement ("guaranteed 100% profit", "zero risk")
    3. Regulatory Financial Disclaimer Enforcement
    4. Ground-Truth Fact & Rate Verification (against versioned synthetic reference data)
    """

    # Secret API Keys / Private Key regex patterns
    SECRET_KEY_RE = re.compile(
        r'(?i)(?:AKIA[0-9A-Z]{16}|-----BEGIN\s+RSA\s+PRIVATE\s+KEY-----|secret_api_key\s*=\s*["\']?[A-Za-z0-9_\-]{16,}|\b[a-zA-Z0-9_-]{32}\.ey[a-zA-Z0-9_-]{30,}\b)'
    )

    # Unsafe Financial Claims Regex
    UNSAFE_CLAIM_RE = re.compile(
        r'(?i)\b(?:guaranteed\s+(?:100%|profit|returns|stock\s*pick)|zero\s*risk\s*(?:investment|stock|fund)|tax-free\s+offshore\s+scheme)\b'
    )

    # Restricted Direct Financial Advice (Mandates REDIRECT)
    RESTRICTED_DIRECT_ADVICE_RE = re.compile(
        r'(?i)\b(?:buy\s+stock|sell\s+stock|invest\s+in\s+crypto|purchase\s+shares\s+of|buy\s+shares\s+of|specific\s+stock\s+pick)\b'
    )

    # General Financial Guidance Language (Appends Mandatory Disclaimer)
    ADVICE_LANGUAGE_RE = re.compile(
        r'(?i)\b(?:we\s+recommend|i\s+recommend|you\s+should\s+invest|guaranteed\s+growth)\b'
    )

    MANDATORY_DISCLAIMER = "\n\n--- \n*Statutory Disclaimer: Information provided is for educational reference only and does not constitute formal financial, investment, or tax advice.*"

    SAFE_FALLBACK_RESPONSE = "Security & Grounding Notice: The generated completion failed outbound compliance or factual grounding validation. Please refer to official bank product documentation."

    RESTRICTED_ADVICE_REDIRECT_RESPONSE = "Security & Policy Notice: Direct stock or personalized investment advice cannot be provided by this AI gateway. Please consult a certified financial advisor or visit our official wealth management portal."

    # Product Rate Claim Extraction Regexes
    PRODUCT_PATTERNS = {
        "fixed_deposit": (re.compile(r'(?i)\b(?:fixed\s+deposit|fd)\b.*?\b(\d+(?:\.\d+)?%)'), "6.5%"),
        "savings_account": (re.compile(r'(?i)\b(?:savings\s+account)\b.*?\b(\d+(?:\.\d+)?%)'), "3.5%"),
        "personal_loan": (re.compile(r'(?i)\b(?:personal\s+loan)\b.*?\b(\d+(?:\.\d+)?%)'), "8.9%"),
        "home_loan": (re.compile(r'(?i)\b(?:home\s+loan|mortgage)\b.*?\b(\d+(?:\.\d+)?%)'), "6.8%"),
    }


    def __init__(self, ground_truth_store: Optional[GroundTruthStore] = None):
        self.ground_truth = ground_truth_store or GroundTruthStore()

    def validate(self, request: OutboundValidationRequest) -> OutboundValidationResponse:
        """
        Executes outbound validation pipeline.
        Returns typed OutboundValidationResponse.
        """
        start_time = time.perf_counter()
        req_id = f"out-{uuid.uuid4().hex[:12]}"
        llm_text = request.llm_response
        sanitized_text = llm_text

        leak_detected = False
        unsafe_claim_detected = False
        discrepancy_detected = False
        fallback_applied = False
        is_modified = False

        grounding_details: List[GroundingValidationDetail] = []
        action = OutboundValidationAction.ALLOW
        reason_code = "OUTBOUND_VALIDATION_PASSED"

        # --- STEP 1: Secret & Sensitive Data Leak Scanning ---
        if self.SECRET_KEY_RE.search(llm_text):
            leak_detected = True
            action = OutboundValidationAction.BLOCK
            reason_code = "OUTBOUND_SECRET_KEY_LEAK_BLOCKED"
            sanitized_text = self.SAFE_FALLBACK_RESPONSE
            fallback_applied = True
            is_modified = True

        if not leak_detected:
            # Check PII/PCI Data Redaction
            redacted_text, masked_entities, _ = PIIPCIRedactor.redact(llm_text)
            if masked_entities:
                leak_detected = True
                sanitized_text = redacted_text
                is_modified = True
                action = OutboundValidationAction.MODIFY
                reason_code = "OUTBOUND_PII_PCI_LEAK_MASKED"

        # --- STEP 2: Unsafe Financial Claim Enforcement ---
        if not leak_detected and self.UNSAFE_CLAIM_RE.search(sanitized_text):
            unsafe_claim_detected = True
            action = OutboundValidationAction.BLOCK
            reason_code = "OUTBOUND_UNSAFE_FINANCIAL_CLAIM_BLOCKED"
            sanitized_text = self.SAFE_FALLBACK_RESPONSE
            fallback_applied = True
            is_modified = True

        # --- STEP 3: Restricted Financial Advice Policy Enforcement ---
        if action not in (OutboundValidationAction.BLOCK, OutboundValidationAction.ESCALATE):
            if self.RESTRICTED_DIRECT_ADVICE_RE.search(sanitized_text):
                action = OutboundValidationAction.REDIRECT
                reason_code = "OUTBOUND_RESTRICTED_ADVICE_REDIRECTED"
                sanitized_text = self.RESTRICTED_ADVICE_REDIRECT_RESPONSE
                fallback_applied = True
                is_modified = True

        # --- STEP 4: Ground-Truth Rate Verification ---
        if action not in (OutboundValidationAction.BLOCK, OutboundValidationAction.ESCALATE, OutboundValidationAction.REDIRECT):

            # Check Stale or Missing Reference Data Version
            if request.ground_truth_version and request.ground_truth_version != self.ground_truth.version:
                action = OutboundValidationAction.ESCALATE
                reason_code = "OUTBOUND_STALE_GROUND_TRUTH_VERSION_ESCALATED"
                sanitized_text = self.SAFE_FALLBACK_RESPONSE
                fallback_applied = True
                is_modified = True

            else:
                for p_key, (pattern, expected_rate) in self.PRODUCT_PATTERNS.items():
                    gt_rate = self.ground_truth.get_product_rate(p_key) or expected_rate
                    match = pattern.search(sanitized_text)

                    if match:
                        claimed_rate = match.group(1)
                        is_match = (claimed_rate == gt_rate)

                        grounding_details.append(
                            GroundingValidationDetail(
                                product_key=p_key,
                                claimed_rate=claimed_rate,
                                ground_truth_rate=gt_rate,
                                is_rate_matching=is_match,
                                effective_date=self.ground_truth.data.get("dataset_metadata", {}).get("effective_date")
                            )
                        )

                        if not is_match:
                            discrepancy_detected = True
                            # Replace hallucinated rate with approved ground-truth rate
                            sanitized_text = pattern.sub(f"{p_key.replace('_', ' ').title()} interest rate is {gt_rate}", sanitized_text)
                            action = OutboundValidationAction.MODIFY
                            reason_code = "OUTBOUND_GROUNDING_RATE_DISCREPANCY_CORRECTED"
                            is_modified = True

        # --- STEP 5: Financial Advice Disclaimer Enforcement ---
        if action in (OutboundValidationAction.ALLOW, OutboundValidationAction.MODIFY):
            if self.ADVICE_LANGUAGE_RE.search(sanitized_text) and "Statutory Disclaimer" not in sanitized_text:
                sanitized_text += self.MANDATORY_DISCLAIMER
                is_modified = True
                if action == OutboundValidationAction.ALLOW:
                    action = OutboundValidationAction.MODIFY
                    reason_code = "OUTBOUND_DISCLAIMER_APPENDED"

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)

        return OutboundValidationResponse(
            request_id=req_id,
            action_decision=action,
            reason_code=reason_code,
            original_llm_response=llm_text,
            sanitized_llm_response=sanitized_text if action != OutboundValidationAction.BLOCK else None,
            is_modified=is_modified,
            leak_detected=leak_detected,
            unsafe_claim_detected=unsafe_claim_detected,
            discrepancy_detected=discrepancy_detected,
            grounding_details=grounding_details,
            fallback_applied=fallback_applied,
            latency_ms=elapsed_ms
        )
