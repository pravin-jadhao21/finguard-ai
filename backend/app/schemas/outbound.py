from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class OutboundValidationAction(str, Enum):
    ALLOW = "ALLOW"
    MODIFY = "MODIFY"
    REDIRECT = "REDIRECT"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


class GroundingValidationDetail(BaseModel):
    product_key: str = Field(..., description="Product identifier (e.g. fixed_deposit)")
    claimed_rate: Optional[str] = Field(default=None, description="Rate claimed in LLM completion")
    ground_truth_rate: Optional[str] = Field(default=None, description="Actual rate in approved ground truth data")
    is_rate_matching: bool = Field(default=True, description="True if claimed rate matches ground truth rate")
    effective_date: Optional[str] = Field(default=None)


class OutboundValidationRequest(BaseModel):
    llm_response: str = Field(..., min_length=1, description="Raw generated LLM completion text to validate")
    prompt_context: Optional[str] = Field(default="", description="Original user prompt context if available")
    user_role: Optional[str] = Field(default="RetailCustomer")
    ground_truth_version: Optional[str] = Field(default="1.0.0")


class OutboundValidationResponse(BaseModel):
    request_id: str = Field(...)
    action_decision: OutboundValidationAction = Field(...)
    reason_code: str = Field(...)
    original_llm_response: str = Field(...)
    sanitized_llm_response: Optional[str] = Field(...)
    is_modified: bool = Field(default=False)
    leak_detected: bool = Field(default=False)
    unsafe_claim_detected: bool = Field(default=False)
    discrepancy_detected: bool = Field(default=False)
    grounding_details: List[GroundingValidationDetail] = Field(default_factory=list)
    fallback_applied: bool = Field(default=False)
    latency_ms: float = Field(...)
