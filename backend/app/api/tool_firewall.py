from fastapi import APIRouter
from app.schemas.tool_firewall import ToolValidationRequest, ToolValidationResponse
from app.core.tool_firewall import ToolActionFirewall

router = APIRouter()
_firewall = ToolActionFirewall()


@router.post(
    "/tool/execute",
    response_model=ToolValidationResponse,
    summary="Validate and Execute LLM Tool Requests against Firewall & Core Banking Sandbox"
)
async def validate_and_execute_tool(request: ToolValidationRequest):
    """
    Validates LLM tool invocations against strict tool allowlist, JSON schemas, role permissions,
    user-prompt parameter consistency (amount & recipient alignment), and step-up approval states.
    Executes allowed tools safely against the simulated core banking sandbox.
    """
    return _firewall.validate_and_execute(request)
