from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ToolValidationAction(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


class UserAuthContext(BaseModel):
    user_id: str = Field(..., description="Unique authenticated user ID (e.g. USR-1001)")
    user_role: str = Field(default="RetailCustomer", description="User role (e.g. RetailCustomer, WealthManager)")
    step_up_authenticated: bool = Field(default=False, description="True if MFA/Step-up verification completed")
    approval_token: Optional[str] = Field(default=None, description="One-time approval token for sensitive transfers")


class ToolValidationRequest(BaseModel):
    tool_name: str = Field(..., description="Target tool identifier requested by LLM")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool call")
    user_prompt: str = Field(..., description="Original user prompt text for intent-parameter alignment")
    user_context: Optional[UserAuthContext] = Field(default=None, description="Simulated user authorization context")


class ToolValidationResponse(BaseModel):
    request_id: str = Field(...)
    action_decision: ToolValidationAction = Field(...)
    reason_code: str = Field(...)
    tool_name: str = Field(...)
    validated_arguments: Optional[Dict[str, Any]] = Field(default=None)
    result: Optional[Dict[str, Any]] = Field(default=None, description="Simulated execution response if ALLOWED")
    execution_success: bool = Field(default=False)
    latency_ms: float = Field(...)
