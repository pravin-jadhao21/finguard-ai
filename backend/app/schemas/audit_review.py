from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TrafficDirection(str, Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class RiskMetadata(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Calculated risk score 0.0 to 100.0")
    risk_level: RiskLevel = Field(...)
    intent_risk_points: float = Field(default=0.0)
    sensitivity_risk_points: float = Field(default=0.0)
    injection_risk_points: float = Field(default=0.0)
    amount_risk_points: float = Field(default=0.0)
    triggers: List[str] = Field(default_factory=list, description="List of risk triggers fired")


class AuditLogEntry(BaseModel):
    request_id: str = Field(...)
    timestamp: str = Field(...)
    direction: TrafficDirection = Field(...)
    policy_id: str = Field(...)
    policy_version: str = Field(...)
    decision: str = Field(..., description="Decision action (ALLOW, BLOCK, REDIRECT, REDACT, TOKENIZE, ESCALATE)")
    reason_code: str = Field(...)
    matched_rule_id: Optional[str] = Field(default=None)
    risk_metadata: RiskMetadata = Field(...)
    latency_ms: float = Field(...)
    fallback_active: bool = Field(default=False, description="True if audit storage used fail-safe backup")


class ReviewTicket(BaseModel):
    ticket_id: str = Field(...)
    request_id: str = Field(...)
    status: ReviewStatus = Field(default=ReviewStatus.PENDING)
    policy_id: str = Field(...)
    policy_version: str = Field(...)
    reason_code: str = Field(...)
    risk_score: float = Field(...)
    risk_level: RiskLevel = Field(...)
    reviewer_id: Optional[str] = Field(default=None, description="Identity of reviewer who processed ticket")
    reviewer_notes: Optional[str] = Field(default=None)
    created_at: str = Field(...)
    updated_at: str = Field(...)


class TicketTransitionRequest(BaseModel):
    reviewer_id: str = Field(..., min_length=1, description="Identity of the reviewer (e.g. REV-USR-99)")
    new_status: ReviewStatus = Field(..., description="Target status: APPROVED or REJECTED")
    notes: Optional[str] = Field(default="", description="Optional reviewer decision notes")
