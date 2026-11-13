from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re


class DecisionEnum(str, Enum):
    ALLOW = "ALLOW"
    REDACT = "REDACT"
    TOKENIZE = "TOKENIZE"
    REDIRECT = "REDIRECT"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


class RuleCondition(BaseModel):
    pattern: Optional[str] = Field(default=None, description="Regular expression pattern to match.")
    keywords: Optional[List[str]] = Field(default=None, description="List of exact keywords for trie/substring match.")
    max_amount: Optional[float] = Field(default=None, description="Maximum dollar amount threshold.")
    required_role: Optional[str] = Field(default=None, description="User role required to pass rule.")

    @field_validator("pattern")
    @classmethod
    def validate_regex_pattern(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f"Invalid regular expression pattern '{v}': {str(e)}")
        return v


class PolicyRule(BaseModel):
    id: str = Field(..., description="Unique rule identifier (e.g., INJ_001_BLOCK)")
    name: str = Field(..., description="Human-readable rule name")
    category: str = Field(..., description="Security category (PromptInjection, DataPrivacy, Compliance, FinancialThreshold)")
    action: DecisionEnum = Field(..., description="Action decision: ALLOW, REDACT, TOKENIZE, REDIRECT, BLOCK, ESCALATE")
    priority: int = Field(default=10, ge=1, le=1000, description="Rule evaluation priority (higher integer = higher priority)")
    weight: int = Field(default=10, ge=0, description="Risk weight assigned when rule matches")
    reason_code: str = Field(..., description="Reason code returned when this rule determines the policy decision")
    condition: RuleCondition = Field(..., description="Matching condition parameters")
    redirect_target: Optional[str] = Field(default=None, description="Target text/URL if action is REDIRECT")
    replacement_token: Optional[str] = Field(default=None, description="Replacement mask if action is REDACT/TOKENIZE")


class PolicyDefinition(BaseModel):
    policy_id: str = Field(..., description="Unique identifier for the policy set")
    version: str = Field(..., description="Semantic version string (e.g. 1.0.0)")
    name: str = Field(..., description="Policy title")
    description: Optional[str] = Field(default=None)
    rules: List[PolicyRule] = Field(default_factory=list, description="Ordered list of policy rules")

    @field_validator("rules")
    @classmethod
    def validate_unique_rule_ids(cls, v: List[PolicyRule]) -> List[PolicyRule]:
        rule_ids = set()
        for rule in v:
            if rule.id in rule_ids:
                raise ValueError(f"Duplicate rule ID found in policy: '{rule.id}'")
            rule_ids.add(rule.id)
        return v


class PolicyEvaluationRequest(BaseModel):
    prompt: str = Field(..., description="Raw text prompt payload to evaluate", min_length=1)
    user_id: Optional[str] = Field(default="anonymous", description="User identity token")
    user_role: Optional[str] = Field(default="RetailCustomer", description="User role entitlement")
    transaction_amount: Optional[float] = Field(default=None, ge=0, description="Financial transaction dollar amount if applicable")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary key-value metadata context")
    policy_id: Optional[str] = Field(default=None, description="Optional override policy ID to evaluate against")


class MatchedRuleDetail(BaseModel):
    rule_id: str
    rule_name: str
    category: str
    action: DecisionEnum
    priority: int
    weight: int
    matched_substring: Optional[str] = None


class PolicyEvaluationResponse(BaseModel):
    request_id: str = Field(..., description="Unique request evaluation tracking ID")
    policy_id: str = Field(..., description="Policy ID used for evaluation")
    policy_version: str = Field(..., description="Semantic version of the active policy")
    decision: DecisionEnum = Field(..., description="Final policy decision: ALLOW, REDACT, TOKENIZE, REDIRECT, BLOCK, ESCALATE")
    reason_code: str = Field(..., description="Explanation reason code for the final policy decision")
    risk_score: int = Field(default=0, description="Cumulative risk score of all triggered rules")
    matched_rules: List[MatchedRuleDetail] = Field(default_factory=list, description="List of all rules triggered by request")
    transformed_prompt: Optional[str] = Field(default=None, description="Sanitized/redacted/tokenized prompt if modified")
    redirect_target: Optional[str] = Field(default=None, description="Redirect message/URL if decision is REDIRECT")
    latency_ms: float = Field(..., description="Deterministic policy evaluation latency in milliseconds")
