from typing import List, Optional
from pydantic import BaseModel, Field


class InboundInspectRequest(BaseModel):
    prompt: str = Field(..., description="Raw text prompt to sanitize and inspect for PII/PCI sensitive data.", min_length=1)
    user_id: Optional[str] = Field(default=None, description="Optional user identifier for auditing context.")
    user_role: Optional[str] = Field(default="RetailCustomer", description="User security role entitlement.")


class MaskedEntity(BaseModel):
    rule_id: str = Field(..., json_schema_extra={"example": "PCI_CARD_MASK"})
    category: str = Field(..., json_schema_extra={"example": "PCI-DSS"})
    entity_type: str = Field(..., json_schema_extra={"example": "CreditCard"})
    original_fragment: str = Field(..., json_schema_extra={"example": "4532-0123-8594-9981"})
    masked_fragment: str = Field(..., json_schema_extra={"example": "[RED_CARD_4532-XXXX-XXXX-9981]"})
    luhn_valid: bool = Field(default=True)


class InboundInspectResponse(BaseModel):
    policy_decision: str = Field(..., json_schema_extra={"example": "MASK"}, description="Decision: ALLOW, MASK, or DENY.")
    original_prompt: str = Field(...)
    sanitized_prompt: str = Field(...)
    is_sanitized: bool = Field(..., description="True if any PII/PCI data was masked or control chars stripped.")
    masked_entities: List[MaskedEntity] = Field(default_factory=list)
    risk_score: int = Field(default=0, description="Calculated cumulative risk score.")
    gateway_latency_ms: float = Field(..., description="Deterministic inspection execution time in milliseconds.")
    trace_id: str = Field(..., description="Unique transaction audit trace ID.")

