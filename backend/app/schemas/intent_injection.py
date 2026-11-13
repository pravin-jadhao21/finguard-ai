from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class FinancialIntentCategory(str, Enum):
    EDUCATIONAL = "EDUCATIONAL"
    COMPARATIVE = "COMPARATIVE"
    PERSONALIZED_ANALYSIS = "PERSONALIZED_ANALYSIS"
    PERSONALIZED_RECOMMENDATION = "PERSONALIZED_RECOMMENDATION"
    TRANSACTIONAL = "TRANSACTIONAL"
    HIGH_RISK = "HIGH_RISK"
    AMBIGUOUS = "AMBIGUOUS"


class IntentSignalTrace(BaseModel):
    financial_topic: bool = False
    personal_context: bool = False
    recommendation_language: bool = False
    explicit_amount: bool = False
    comparative_language: bool = False
    educational_language: bool = False
    high_risk_language: bool = False
    detected_signals: List[str] = Field(default_factory=list)


class FinancialIntentRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Raw prompt to classify for financial intent")
    transaction_amount: Optional[float] = Field(default=None, ge=0)
    user_role: Optional[str] = Field(default="RetailCustomer")


class FinancialIntentResponse(BaseModel):
    request_id: str = Field(...)
    intent_category: FinancialIntentCategory = Field(...)
    action_decision: str = Field(..., description="ALLOW, REDIRECT, ESCALATE, or BLOCK")
    reason_code: str = Field(...)
    confidence_score: float = Field(default=1.0, description="1.0 for deterministic signal matching")
    signal_trace: IntentSignalTrace = Field(...)
    suggested_disclaimer: Optional[str] = Field(default=None)
    latency_ms: float = Field(...)


class InjectionCategory(str, Enum):
    DIRECT_OVERRIDE = "DIRECT_OVERRIDE"
    SYSTEM_EXFILTRATION = "SYSTEM_EXFILTRATION"
    POLICY_BYPASS = "POLICY_BYPASS"
    CHARACTER_OBFUSCATION = "CHARACTER_OBFUSCATION"
    BENIGN = "BENIGN"


class InjectionDetectionRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Raw prompt payload to scan for prompt injection")


class InjectionMatchDetail(BaseModel):
    rule_id: str
    category: InjectionCategory
    severity: str
    matched_pattern: str
    reason_code: str


class InjectionDetectionResponse(BaseModel):
    request_id: str = Field(...)
    is_injection_detected: bool = Field(...)
    highest_severity: str = Field(default="NONE")
    primary_reason_code: str = Field(...)
    matches: List[InjectionMatchDetail] = Field(default_factory=list)
    action_decision: str = Field(..., description="BLOCK or ALLOW")
    latency_ms: float = Field(...)
