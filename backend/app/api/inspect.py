import time
import uuid
from fastapi import APIRouter, HTTPException, status
from app.schemas.inspect import InboundInspectRequest, InboundInspectResponse
from app.core.sanitizer import TextSanitizer
from app.core.pii_redactor import PIIPCIRedactor
from app.config import settings

router = APIRouter()


@router.post("/inspect", response_model=InboundInspectResponse, summary="Inspect & Redact Inbound Prompt Payload")
async def inspect_prompt(request: InboundInspectRequest):
    """
    Intercepts raw user prompt text, normalizes character encoding, executes 
    deterministic PII/PCI redaction (with Luhn validation), and returns the sanitized text 
    along with detection metadata and latency metrics.
    """
    start_time = time.perf_counter()
    trace_id = f"tr-{uuid.uuid4().hex[:12]}"

    # Validate payload size limit
    raw_prompt_bytes = len(request.prompt.encode('utf-8'))
    if raw_prompt_bytes > settings.MAX_PAYLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Payload size {raw_prompt_bytes} bytes exceeds maximum limit of {settings.MAX_PAYLOAD_SIZE_BYTES} bytes."
        )

    # Step 1: Inbound Unicode & Control Character Sanitization
    sanitized_text, was_sanitized = TextSanitizer.sanitize(request.prompt)

    # Step 2: Deterministic PII & PCI Redaction Scan
    redacted_text, masked_entities, risk_score = PIIPCIRedactor.redact(sanitized_text)

    # Step 3: Determine Policy Output (Phase 2 Baseline)
    is_modified = was_sanitized or (len(masked_entities) > 0)
    policy_decision = "MASK" if is_modified else "ALLOW"

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)

    return InboundInspectResponse(
        policy_decision=policy_decision,
        original_prompt=request.prompt,
        sanitized_prompt=redacted_text,
        is_sanitized=is_modified,
        masked_entities=masked_entities,
        risk_score=risk_score,
        gateway_latency_ms=elapsed_ms,
        trace_id=trace_id
    )
