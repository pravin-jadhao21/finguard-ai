from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DataClassificationTier(str, Enum):
    CRITICAL_PCI = "CRITICAL_PCI"
    CRITICAL_PII = "CRITICAL_PII"
    SENSITIVE_PII = "SENSITIVE_PII"


class TransformationStrategy(str, Enum):
    MASK = "MASK"
    REDACT = "REDACT"
    TOKENIZE = "TOKENIZE"


class SensitiveCandidateTrace(BaseModel):
    candidate_id: str = Field(..., description="Unique ID for candidate trace")
    candidate_type: str = Field(..., description="PAYMENT_CARD, AADHAAR, PAN, EMAIL, PHONE, ACCOUNT_NUMBER, OTP")
    classification_tier: DataClassificationTier = Field(...)
    start_index: int = Field(..., ge=0)
    end_index: int = Field(..., ge=0)
    checksum_validated: bool = Field(default=False)
    checksum_passed: Optional[bool] = Field(default=None)
    transformation_applied: TransformationStrategy = Field(...)
    safe_masked_fragment: str = Field(..., description="Format-preserving redacted placeholder (Zero Raw Secret)")


class DataProtectionConfigRequest(BaseModel):
    mask_cards: bool = True
    mask_aadhaar: bool = True
    mask_pan: bool = True
    mask_email: bool = True
    mask_phone: bool = True
    mask_account_numbers: bool = True
    mask_otp: bool = True
    transformation_strategy: TransformationStrategy = TransformationStrategy.MASK


class InboundDataProtectionRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Raw input prompt payload")
    config: Optional[DataProtectionConfigRequest] = Field(default_factory=DataProtectionConfigRequest)
    user_role: Optional[str] = Field(default="RetailCustomer")


class InboundDataProtectionResponse(BaseModel):
    request_id: str = Field(..., description="Unique request evaluation ID")
    original_prompt_length: int = Field(..., description="Length of original prompt string")
    transformed_prompt: str = Field(..., description="Prompt payload after inbound data protection transformations")
    candidates_found: int = Field(..., description="Count of sensitive data candidates detected")
    candidate_traces: List[SensitiveCandidateTrace] = Field(default_factory=list, description="Trace of detected candidates without raw secret leakage")
    policy_decision: str = Field(..., description="Decision output (ALLOW or MASK/REDACT/TOKENIZE)")
    latency_ms: float = Field(..., description="Processing overhead in milliseconds")
