import re
import time
import uuid
from typing import List, Tuple, Optional
from app.schemas.intent_injection import (
    InjectionCategory,
    InjectionMatchDetail,
    InjectionDetectionRequest,
    InjectionDetectionResponse
)


class PromptInjectionDetector:
    """
    Deterministic Prompt Injection & System Override Detector.
    Scans prompts for direct overrides, system prompt exfiltration, policy bypasses,
    and character obfuscation tricks while preserving resilience against benign queries.
    """

    # 1. Direct System Override Rules
    OVERRIDE_PATTERNS = [
        (
            "INJ_DIR_001",
            re.compile(r'(?i)\b(?:ignore|disregard|forget)\s+(?:all\s+|all\s+prior\s+|previous\s+|everything\s+|all\s+rules\s+)?(?:instructions|rules|prompts|safety\s+guidelines|safety\s+rules|constraints)?\b'),
            InjectionCategory.DIRECT_OVERRIDE,
            "CRITICAL",
            "SECURITY_INJECTION_DIRECT_INSTRUCTION_OVERRIDE"
        ),
        (
            "INJ_DIR_002",
            re.compile(r'(?i)\b(?:you\s+are\s+now|operating\s+as|act\s+as)\s+(?:in\s+)?(?:dan|developer\s+mode|unrestricted\s+mode|jailbroken|unconstrained)\b'),
            InjectionCategory.DIRECT_OVERRIDE,
            "CRITICAL",
            "SECURITY_INJECTION_JAILBREAK_MODE_TRIGGER"
        ),
        (
            "INJ_DIR_003",
            re.compile(r'(?i)\b(?:disregard|forget)\s+(?:everything|all\s+rules|previous\s+prompts|safety\s+guidelines)\b'),
            InjectionCategory.DIRECT_OVERRIDE,
            "HIGH",
            "SECURITY_INJECTION_DISREGARD_RULES"
        ),
    ]

    # 2. System Prompt Exfiltration Rules
    EXFILTRATION_PATTERNS = [
        (
            "INJ_EXF_001",
            re.compile(r'(?i)\b(?:reveal|print|output|display|show|repeat)\s+(?:your\s+|all\s+|full\s+|initial\s+|system\s+|developer\s+|hidden\s+|secret\s+)*(?:prompt|instructions|config|rules|settings|keys|setup)\b'),
            InjectionCategory.SYSTEM_EXFILTRATION,
            "HIGH",
            "SECURITY_INJECTION_SYSTEM_PROMPT_EXFILTRATION"
        ),
        (
            "INJ_EXF_002",
            re.compile(r'(?i)\bwhat\s+(?:are|is)\s+(?:your\s+|the\s+)*(?:system\s+instructions|initial\s+prompt|developer\s+prompt|hidden\s+instructions)\b'),
            InjectionCategory.SYSTEM_EXFILTRATION,
            "HIGH",
            "SECURITY_INJECTION_SYSTEM_INSTRUCTION_QUERY"
        ),
    ]

    # 3. Policy & Safety Bypass Rules
    BYPASS_PATTERNS = [
        (
            "INJ_BYP_001",
            re.compile(r'(?i)\b(?:bypass|disable|turn\s+off|override)\s+(?:safety\s+filter|security\s+gateway|policy\s+enforcement|policy\s+filter|finguard|security\s+checks|transaction\s+limits|rules)\b'),
            InjectionCategory.POLICY_BYPASS,
            "CRITICAL",
            "SECURITY_INJECTION_SAFETY_FILTER_BYPASS"
        ),
        (
            "INJ_BYP_002",
            re.compile(r'(?i)(?:<\|im_start\|>|\[INST\]|<system_override>|system:\s*ignore|system:\s*you|system:\s*turn)'),
            InjectionCategory.POLICY_BYPASS,
            "CRITICAL",
            "SECURITY_INJECTION_DELIMITER_SMUGGLING"
        ),
    ]

    # 4. Character Obfuscation Rules (Long Base64 strings or hex blocks attempting injection)
    OBFUSCATION_PATTERNS = [
        (
            "INJ_OBF_001",
            re.compile(r'\b[A-Za-z0-9+/]{60,}={0,2}\b'),
            InjectionCategory.CHARACTER_OBFUSCATION,
            "MEDIUM",
            "SECURITY_INJECTION_HIGH_ENTROPY_BASE64"
        ),
    ]

    @classmethod
    def scan(cls, request: InjectionDetectionRequest) -> InjectionDetectionResponse:
        """
        Scans prompt text for prompt injection vectors.
        Returns typed InjectionDetectionResponse.
        """
        start_time = time.perf_counter()
        req_id = f"inj-{uuid.uuid4().hex[:12]}"
        prompt = request.prompt

        # Special check: benign queries containing 'ignore' in non-instruction context
        # e.g., "Can I ignore the previous bank statement/receipt"
        is_benign_ignore = bool(re.search(r'(?i)\bignore\s+(?:the\s+)?(?:previous\s+)?(?:bank\s+)?(?:receipt|statement|transaction|check|email|notice|fee)\b', prompt))

        matches: List[InjectionMatchDetail] = []
        highest_severity = "NONE"
        primary_reason_code = "INJECTION_SCAN_BENIGN_CLEAN"

        severity_weights = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}

        if not is_benign_ignore:
            all_rules = (
                cls.OVERRIDE_PATTERNS +
                cls.EXFILTRATION_PATTERNS +
                cls.BYPASS_PATTERNS +
                cls.OBFUSCATION_PATTERNS
            )

            for rule_id, pattern, category, severity, reason_code in all_rules:
                m = pattern.search(prompt)
                if m:
                    matched_substr = m.group(0)
                    matches.append(
                        InjectionMatchDetail(
                            rule_id=rule_id,
                            category=category,
                            severity=severity,
                            matched_pattern=matched_substr,
                            reason_code=reason_code
                        )
                    )

                    if severity_weights.get(severity, 0) > severity_weights.get(highest_severity, 0):
                        highest_severity = severity
                        primary_reason_code = reason_code

        is_detected = len(matches) > 0
        action_decision = "BLOCK" if is_detected else "ALLOW"
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)

        return InjectionDetectionResponse(
            request_id=req_id,
            is_injection_detected=is_detected,
            highest_severity=highest_severity,
            primary_reason_code=primary_reason_code,
            matches=matches,
            action_decision=action_decision,
            latency_ms=elapsed_ms
        )
