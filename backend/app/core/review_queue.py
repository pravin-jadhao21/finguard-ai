import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.audit_review import ReviewTicket, ReviewStatus, RiskLevel


class SimulatedReviewQueue:
    """
    Simulated Human-Review Queue Manager for High-Risk Gateway Transactions.
    Maintains PENDING, APPROVED, and REJECTED review tickets.
    Requires an explicit reviewer identity for all status transitions.
    """

    SIMULATED_DISCLAIMER = "Simulated review sandbox feature -- not a certified banking approval workflow."

    def __init__(self):
        self._tickets: Dict[str, ReviewTicket] = {}

    def enqueue_ticket(
        self,
        request_id: str,
        policy_id: str,
        policy_version: str,
        reason_code: str,
        risk_score: float,
        risk_level: RiskLevel
    ) -> ReviewTicket:
        """Creates a new PENDING review ticket for a high-risk request."""
        ticket_id = f"REV-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        ticket = ReviewTicket(
            ticket_id=ticket_id,
            request_id=request_id,
            status=ReviewStatus.PENDING,
            policy_id=policy_id,
            policy_version=policy_version,
            reason_code=reason_code,
            risk_score=risk_score,
            risk_level=risk_level,
            reviewer_id=None,
            reviewer_notes=None,
            created_at=now_iso,
            updated_at=now_iso
        )

        self._tickets[ticket_id] = ticket
        return ticket

    def list_tickets(self, status_filter: Optional[ReviewStatus] = None) -> List[ReviewTicket]:
        """Lists review queue tickets with optional status filtering."""
        tickets = list(self._tickets.values())
        if status_filter:
            tickets = [t for t in tickets if t.status == status_filter]
        return sorted(tickets, key=lambda x: x.created_at, reverse=True)

    def get_ticket(self, ticket_id: str) -> Optional[ReviewTicket]:
        """Fetches a review ticket by ID."""
        return self._tickets.get(ticket_id)

    def transition_ticket(
        self,
        ticket_id: str,
        new_status: ReviewStatus,
        reviewer_id: str,
        notes: Optional[str] = None
    ) -> ReviewTicket:
        """
        Transitions ticket status to APPROVED or REJECTED.
        Strictly mandates a non-empty reviewer_id.
        """
        if not reviewer_id or not reviewer_id.strip():
            raise ValueError("Reviewer identity is strictly required for review queue transitions.")

        if new_status not in (ReviewStatus.APPROVED, ReviewStatus.REJECTED):
            raise ValueError(f"Invalid target status '{new_status}'. Allowed transitions: APPROVED, REJECTED.")

        ticket = self.get_ticket(ticket_id)
        if not ticket:
            raise KeyError(f"Review ticket '{ticket_id}' not found.")

        if ticket.status != ReviewStatus.PENDING:
            raise ValueError(f"Ticket '{ticket_id}' is already finalized with status '{ticket.status.value}'.")

        ticket.status = new_status
        ticket.reviewer_id = reviewer_id.strip()
        ticket.reviewer_notes = notes or ""
        ticket.updated_at = datetime.now(timezone.utc).isoformat()

        return ticket
