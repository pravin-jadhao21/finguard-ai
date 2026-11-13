from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.schemas.audit_review import (
    AuditLogEntry,
    ReviewTicket,
    TicketTransitionRequest,
    ReviewStatus
)
from app.core.audit_logger import AuditLogger
from app.core.review_queue import SimulatedReviewQueue

router = APIRouter()

# Global singleton instances for API state
_audit_logger = AuditLogger()
_review_queue = SimulatedReviewQueue()


@router.get(
    "/audit/logs",
    response_model=List[AuditLogEntry],
    summary="Query Immutable Gateway Decision Audit Logs"
)
async def query_audit_logs(
    policy_version: Optional[str] = Query(None, description="Filter by policy version (e.g. 1.0.0)"),
    decision: Optional[str] = Query(None, description="Filter by decision (ALLOW, BLOCK, etc.)"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Returns zero-data-leakage audit records with policy version traceability.
    Does not expose raw payload content.
    """
    return _audit_logger.get_logs(policy_version=policy_version, decision=decision, limit=limit)


@router.get(
    "/audit/logs/{request_id}/explain",
    summary="Inspect Decision Explainability for a Specific Gateway Request"
)
async def explain_decision(request_id: str):
    """
    Returns granular decision reasoning (matched rule ID, reason code, risk score breakdown)
    without revealing confidential PII/PCI payload text.
    """
    explanation = _audit_logger.explain_decision(request_id)
    if not explanation:
        raise HTTPException(status_code=404, detail=f"Audit record for request ID '{request_id}' not found.")
    return explanation


@router.get(
    "/review/queue",
    response_model=List[ReviewTicket],
    summary="List Simulated Human-Review Queue Tickets"
)
async def list_review_tickets(
    status: Optional[ReviewStatus] = Query(None, description="Filter tickets by status (PENDING, APPROVED, REJECTED)")
):
    """
    Lists human-review queue tickets for high-risk gateway transactions.
    """
    return _review_queue.list_tickets(status_filter=status)


@router.post(
    "/review/queue/{ticket_id}/transition",
    response_model=ReviewTicket,
    summary="Transition Review Ticket Status (Requires Reviewer Identity)"
)
async def transition_review_ticket(ticket_id: str, request: TicketTransitionRequest):
    """
    Transitions a PENDING review ticket to APPROVED or REJECTED.
    Strictly mandates a non-empty reviewer_id.
    """
    try:
        return _review_queue.transition_ticket(
            ticket_id=ticket_id,
            new_status=request.new_status,
            reviewer_id=request.reviewer_id,
            notes=request.notes
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
