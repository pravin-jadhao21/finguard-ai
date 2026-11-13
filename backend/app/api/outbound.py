from fastapi import APIRouter
from app.schemas.outbound import (
    OutboundValidationRequest,
    OutboundValidationResponse
)
from app.core.outbound_enforcer import OutboundResponseEnforcer

router = APIRouter()
_enforcer = OutboundResponseEnforcer()


@router.post(
    "/outbound/validate",
    response_model=OutboundValidationResponse,
    summary="Validate LLM Response Output Completion against Compliance & Ground-Truth Baseline"
)
async def validate_outbound_response(request: OutboundValidationRequest):
    """
    Validates LLM output completions for sensitive secret leaks, PII/PCI leaks, unsafe claims,
    disclaimer requirements, and rate grounding discrepancies against versioned reference data.
    """
    return _enforcer.validate(request)
