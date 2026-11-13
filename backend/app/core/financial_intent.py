import re
import time
import uuid
from typing import Tuple, List, Optional
from app.schemas.intent_injection import (
    FinancialIntentCategory,
    FinancialIntentRequest,
    FinancialIntentResponse,
    IntentSignalTrace
)


class FinancialIntentClassifier:
    """
    Deterministic Multi-Signal Financial Intent Classifier.
    Evaluates prompts across 4 distinct signal vectors:
    1. Financial Topic Taxonomy
    2. Personal Context (First-person pronouns / my portfolio / my savings)
    3. Recommendation / Advice Language
    4. Explicit Financial Amounts / Transactions
    """

    # 1. Financial Topics (Stocks, Mutual Funds, Savings, Bonds, Interest, Crypto, Tax)
    FINANCIAL_TOPIC_RE = re.compile(
        r'(?i)\b(?:stock|stocks|mutual\s*fund|mutual\s*funds|etf|index\s*fund|bonds|fixed\s*deposit|savings|equity|portfolio|shares|crypto|bitcoin|tax|taxes|interest\s*rate|wire\s*transfer|dividend)\b'
    )

    # 2. Personal Context (First-person pronouns, my portfolio, my money, for me)
    PERSONAL_CONTEXT_RE = re.compile(
        r'(?i)\b(?:my|mine|i\s*have|for\b\s*me|my\s*portfolio|my\s*savings|my\s*money|my\s*account|i\s*own|i\s*should)\b'
    )

    # 3. Recommendation / Advisory Language (which stock should I buy, recommend, tell me where to invest, best stock)
    RECOMMENDATION_RE = re.compile(
        r'(?i)\b(?:which\s*stock|should\s*i\s*buy|should\s*i\s*sell|recommend|best\s*investment|where\s*to\s*invest|guaranteed\s*return|target\s*price|stock\s*pick)\b'
    )

    # 4. Comparative Language (compare, vs, difference between, better than)
    COMPARATIVE_RE = re.compile(
        r'(?i)\b(?:compare|vs\.?|versus|difference\s*between|better\s*than|compared\s*to)\b'
    )

    # 5. Educational / Definition Language (what is, how does, explain, definition, meaning of)
    EDUCATIONAL_RE = re.compile(
        r'(?i)\b(?:what\s*is|how\s*does|explain|definition\s*of|meaning\s*of|how\s*do|what\s*are)\b'
    )

    # 6. Transactional Verbs (transfer, send, wire, pay, deposit, withdraw)
    TRANSACTIONAL_RE = re.compile(
        r'(?i)\b(?:transfer|send|wire|pay|deposit|withdraw)\b'
    )

    # 7. High Risk / Speculative Language (tax evasion, guaranteed profit, 100x return, insider)
    HIGH_RISK_RE = re.compile(
        r'(?i)\b(?:tax\s*evasion|avoid\s*paying\s*tax|guaranteed\s*(?:profit|100%|return)|insider\s*tip|crypto\s*leverage|100x)\b'
    )

    # 8. Explicit Amount Regex
    AMOUNT_RE = re.compile(
        r'(?:\$|\u20b9)?\b\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s*(?:k|m|million|thousand|dollars|rupees|lakh|crore)?\b'
    )

    @classmethod
    def classify(cls, request: FinancialIntentRequest) -> FinancialIntentResponse:
        """
        Classifies prompt using multi-signal combinatorial matrix.
        Returns typed FinancialIntentResponse with signal trace and reason code.
        """
        start_time = time.perf_counter()
        req_id = f"fi-{uuid.uuid4().hex[:12]}"
        prompt = request.prompt

        # Extract signal vectors
        has_topic = bool(cls.FINANCIAL_TOPIC_RE.search(prompt))
        has_personal = bool(cls.PERSONAL_CONTEXT_RE.search(prompt))
        has_recommendation = bool(cls.RECOMMENDATION_RE.search(prompt))
        has_comparative = bool(cls.COMPARATIVE_RE.search(prompt))
        has_educational = bool(cls.EDUCATIONAL_RE.search(prompt))
        has_transactional = bool(cls.TRANSACTIONAL_RE.search(prompt))
        has_high_risk = bool(cls.HIGH_RISK_RE.search(prompt))
        has_amount = bool(cls.AMOUNT_RE.search(prompt)) or (request.transaction_amount is not None)

        detected_signals: List[str] = []
        if has_topic: detected_signals.append("FINANCIAL_TOPIC")
        if has_personal: detected_signals.append("PERSONAL_CONTEXT")
        if has_recommendation: detected_signals.append("RECOMMENDATION_LANGUAGE")
        if has_comparative: detected_signals.append("COMPARATIVE_LANGUAGE")
        if has_educational: detected_signals.append("EDUCATIONAL_LANGUAGE")
        if has_transactional: detected_signals.append("TRANSACTIONAL_VERB")
        if has_high_risk: detected_signals.append("HIGH_RISK_TERMS")
        if has_amount: detected_signals.append("EXPLICIT_AMOUNT")

        trace = IntentSignalTrace(
            financial_topic=has_topic,
            personal_context=has_personal,
            recommendation_language=has_recommendation,
            explicit_amount=has_amount,
            comparative_language=has_comparative,
            educational_language=has_educational,
            high_risk_language=has_high_risk,
            detected_signals=detected_signals
        )

        # Multi-Signal Classification Decision Matrix

        # 1. HIGH RISK (Takes top priority for security)
        if has_high_risk:
            category = FinancialIntentCategory.HIGH_RISK
            action = "BLOCK"
            reason_code = "FIN_INTENT_HIGH_RISK_SPECULATION_BLOCKED"
            disclaimer = None

        # 2. TRANSACTIONAL
        elif has_transactional and (has_amount or has_topic):
            category = FinancialIntentCategory.TRANSACTIONAL
            if request.transaction_amount and request.transaction_amount > 5000.0:
                action = "ESCALATE"
                reason_code = "FIN_INTENT_TRANSACTION_THRESHOLD_ESCALATE"
            else:
                action = "ALLOW"
                reason_code = "FIN_INTENT_TRANSACTIONAL_PERMITTED"
            disclaimer = None

        # 3. PERSONALIZED RECOMMENDATION (Combination: Topic + Recommendation OR Personal + Recommendation)
        elif has_recommendation and (has_topic or has_personal):
            category = FinancialIntentCategory.PERSONALIZED_RECOMMENDATION
            action = "REDIRECT"
            reason_code = "FIN_INTENT_RECOMMENDATION_RESTRICTED"
            disclaimer = "Statutory Disclaimer: FinGuard AI policy prohibits automated personalized stock recommendations. Please consult a licensed financial advisor."

        # 4. PERSONALIZED ANALYSIS (Combination: Topic + Personal Context + Amount/Portfolio, but NO explicit recommendation request)
        elif has_topic and has_personal and (has_amount or "portfolio" in prompt.lower()):
            category = FinancialIntentCategory.PERSONALIZED_ANALYSIS
            action = "REDIRECT"
            reason_code = "FIN_INTENT_PERSONAL_ANALYSIS_DISCLAIMER_REQUIRED"
            disclaimer = "Disclaimer: Information generated is for educational reference only and does not constitute a personalized portfolio audit."

        # 5. COMPARATIVE (Topic + Comparative Language, NO personal context)
        elif has_topic and has_comparative and not has_personal:
            category = FinancialIntentCategory.COMPARATIVE
            action = "ALLOW"
            reason_code = "FIN_INTENT_COMPARATIVE_QUERY_PERMITTED"
            disclaimer = "Disclaimer: Comparative analysis is based on historical reference data."

        # 6. EDUCATIONAL (Topic + Educational Language, NO personal context)
        elif has_topic and (has_educational or not (has_personal or has_recommendation)):
            category = FinancialIntentCategory.EDUCATIONAL
            action = "ALLOW"
            reason_code = "FIN_INTENT_EDUCATIONAL_QUERY_PERMITTED"
            disclaimer = "Disclaimer: General financial education only."

        # 7. AMBIGUOUS (Conflicting or weak signals -> Safe handling rule)
        else:
            category = FinancialIntentCategory.AMBIGUOUS
            action = "ALLOW"
            reason_code = "FIN_INTENT_AMBIGUOUS_SAFE_HANDLING_BASELINE"
            disclaimer = "Disclaimer: Standard financial communication terms apply."

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)

        return FinancialIntentResponse(
            request_id=req_id,
            intent_category=category,
            action_decision=action,
            reason_code=reason_code,
            confidence_score=1.0,
            signal_trace=trace,
            suggested_disclaimer=disclaimer,
            latency_ms=elapsed_ms
        )
