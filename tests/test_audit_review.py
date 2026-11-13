import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.risk_engine import RiskAssessmentEngine
from app.core.audit_logger import AuditLogger
from app.core.review_queue import SimulatedReviewQueue
from app.schemas.audit_review import (
    RiskLevel,
    ReviewStatus,
    TrafficDirection,
    TicketTransitionRequest
)
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def risk_engine():
    return RiskAssessmentEngine()


@pytest.fixture
def audit_logger():
    return AuditLogger()


@pytest.fixture
def review_queue():
    return SimulatedReviewQueue()


# 1. Risk Scoring Independence Test
def test_risk_scoring_independence(risk_engine):
    meta = risk_engine.evaluate_risk(
        intent_category="HIGH_RISK",
        data_classification="CRITICAL_PCI",
        has_prompt_injection=True,
        amount=10000.0
    )
    assert meta.risk_score == 100.0
    assert meta.risk_level == RiskLevel.CRITICAL
    assert len(meta.triggers) >= 4


# 2. Log Integrity & Policy Version Traceability Test
def test_log_integrity_and_policy_version_traceability(audit_logger, risk_engine):
    risk_meta = risk_engine.evaluate_risk(intent_category="TRANSACTIONAL")
    entry = audit_logger.log_decision(
        request_id="req-test-99",
        direction=TrafficDirection.INBOUND,
        policy_id="v1_baseline_policy",
        policy_version="1.0.0",
        decision="ALLOW",
        reason_code="RULE_MATCHED_ALLOW",
        matched_rule_id="RULE-101",
        risk_metadata=risk_meta,
        latency_ms=0.15
    )

    assert entry.request_id == "req-test-99"
    assert entry.policy_version == "1.0.0"
    assert entry.policy_id == "v1_baseline_policy"
    assert entry.decision == "ALLOW"
    assert entry.matched_rule_id == "RULE-101"
    assert entry.fallback_active is False


# 3. Decision Explainability Inspection Test
def test_decision_explainability_inspection(audit_logger, risk_engine):
    risk_meta = risk_engine.evaluate_risk(intent_category="PERSONALIZED_RECOMMENDATION")
    audit_logger.log_decision(
        request_id="req-explain-01",
        direction=TrafficDirection.INBOUND,
        policy_id="v1_baseline_policy",
        policy_version="1.0.0",
        decision="REDIRECT",
        reason_code="RULE_PERSONALIZED_ADVICE_REDIRECT",
        matched_rule_id="RULE-302",
        risk_metadata=risk_meta,
        latency_ms=0.22
    )

    explanation = audit_logger.explain_decision("req-explain-01")
    assert explanation is not None
    assert explanation["reason_code"] == "RULE_PERSONALIZED_ADVICE_REDIRECT"
    assert explanation["matched_rule_id"] == "RULE-302"
    assert explanation["confidential_data_stored"] is False
    assert explanation["risk_summary"]["risk_score"] > 0


# 4. Audit Logger Fail-Safe Backup Fallback Test
def test_audit_logger_fail_safe_backup_fallback(risk_engine):
    failing_logger = AuditLogger(simulate_storage_failure=True)
    risk_meta = risk_engine.evaluate_risk(intent_category="EDUCATIONAL")

    # Storage failure should be caught safely without throwing exception to gateway caller
    entry = failing_logger.log_decision(
        request_id="req-failsafe-01",
        direction=TrafficDirection.OUTBOUND,
        policy_id="v1_baseline_policy",
        policy_version="1.0.0",
        decision="BLOCK",
        reason_code="OUTBOUND_SECRET_KEY_LEAK_BLOCKED",
        risk_metadata=risk_meta,
        latency_ms=0.45
    )

    assert entry.fallback_active is True
    assert len(failing_logger._backup_logs) == 1


# 5. Review Queue Enqueue & Transition Success Test
def test_review_queue_enqueue_and_transition_success(review_queue):
    ticket = review_queue.enqueue_ticket(
        request_id="req-review-100",
        policy_id="v1_baseline_policy",
        policy_version="1.0.0",
        reason_code="HIGH_RISK_TRANSACTION_ESCALATED",
        risk_score=85.0,
        risk_level=RiskLevel.CRITICAL
    )

    assert ticket.status == ReviewStatus.PENDING
    assert ticket.reviewer_id is None

    # Transition to APPROVED
    updated = review_queue.transition_ticket(
        ticket_id=ticket.ticket_id,
        new_status=ReviewStatus.APPROVED,
        reviewer_id="REV-USR-99",
        notes="Verified identity via out-of-band call"
    )

    assert updated.status == ReviewStatus.APPROVED
    assert updated.reviewer_id == "REV-USR-99"
    assert updated.reviewer_notes == "Verified identity via out-of-band call"


# 6. Review Queue Transition Rejection Test
def test_review_queue_transition_rejected(review_queue):
    ticket = review_queue.enqueue_ticket(
        request_id="req-review-101",
        policy_id="v1_baseline_policy",
        policy_version="1.0.0",
        reason_code="HIGH_RISK_TRANSACTION_ESCALATED",
        risk_score=90.0,
        risk_level=RiskLevel.CRITICAL
    )

    updated = review_queue.transition_ticket(
        ticket_id=ticket.ticket_id,
        new_status=ReviewStatus.REJECTED,
        reviewer_id="REV-USR-99",
        notes="Unverified recipient account"
    )

    assert updated.status == ReviewStatus.REJECTED
    assert updated.reviewer_id == "REV-USR-99"


# 7. Missing Reviewer Identity Fails Test
def test_review_queue_transition_missing_reviewer_id_fails(review_queue):
    ticket = review_queue.enqueue_ticket(
        request_id="req-review-102",
        policy_id="v1_baseline_policy",
        policy_version="1.0.0",
        reason_code="HIGH_RISK_TRANSACTION_ESCALATED",
        risk_score=75.0,
        risk_level=RiskLevel.HIGH
    )

    with pytest.raises(ValueError, match="Reviewer identity is strictly required"):
        review_queue.transition_ticket(
            ticket_id=ticket.ticket_id,
            new_status=ReviewStatus.APPROVED,
            reviewer_id="",  # Empty reviewer ID
            notes="Missing reviewer ID"
        )


# 8. FastAPI Audit & Review Queue Endpoints Integration Test
def test_fastapi_audit_and_review_endpoints():
    client = TestClient(app)

    # Query audit logs
    audit_res = client.get("/api/v1/audit/logs")
    assert audit_res.status_code == 200

    # Query review queue
    review_res = client.get("/api/v1/review/queue")
    assert review_res.status_code == 200
