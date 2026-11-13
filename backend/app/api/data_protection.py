from fastapi import APIRouter, HTTPException, status
from app.schemas.data_protection import (
    InboundDataProtectionRequest,
    InboundDataProtectionResponse
)
from app.core.inbound_data_protection import InboundDataProtectionEngine
from app.api.policy import get_policy_engine
from app.schemas.policy import PolicyEvaluationRequest

router = APIRouter()


@router.post(
    "/data-protection/inspect",
    response_model=InboundDataProtectionResponse,
    summary="Inspect & Transform Inbound Payload Sensitive Data Candidates"
)
async def inspect_and_protect_data(request: InboundDataProtectionRequest):
    """
    Executes inbound data protection scanning for Payment Cards (Luhn), Aadhaar (Verhoeff),
    PAN, Email, Phone, Account Numbers, and OTPs.
    Returns transformed prompt payload alongside candidate traces (zero raw secrets logged).
    """
    return InboundDataProtectionEngine.process(request)
