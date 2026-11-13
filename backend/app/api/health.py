from fastapi import APIRouter
from datetime import datetime, timezone
from app.config import settings
from app.schemas.health import HealthResponse

router = APIRouter()


def _get_active_policy_version() -> str:
    try:
        from app.api.policy import get_policy_engine
        engine = get_policy_engine()
        return engine.policy.version
    except Exception:
        return "unknown"


@router.get("/health", response_model=HealthResponse, summary="Get Gateway Health Status")
async def health_check():
    """
    Returns FinGuard AI gateway health status, active policy version, environment, and service uptime metadata.
    """
    return HealthResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
        active_policy_version=_get_active_policy_version(),
        engine_mode="Deterministic Rule Engine (Zero AI)"
    )


@router.get("/overview/stats", summary="Get Gateway Runtime Overview Statistics")
async def get_overview_stats():
    """
    Calculates summary metrics from actual backend audit logs and review queues.
    """
    from app.api.audit_review import _audit_logger, _review_queue

    all_logs = _audit_logger.get_logs(limit=1000)
    all_tickets = _review_queue.list_tickets()

    decisions_count = {
        "ALLOW": len([l for l in all_logs if l.decision == "ALLOW"]),
        "BLOCK": len([l for l in all_logs if l.decision == "BLOCK"]),
        "REDACT": len([l for l in all_logs if l.decision == "REDACT"]),
        "TOKENIZE": len([l for l in all_logs if l.decision == "TOKENIZE"]),
        "REDIRECT": len([l for l in all_logs if l.decision == "REDIRECT"]),
        "ESCALATE": len([l for l in all_logs if l.decision == "ESCALATE"]),
        "MODIFY": len([l for l in all_logs if l.decision == "MODIFY"]),
    }

    avg_latency = (
        round(sum(l.latency_ms for l in all_logs) / len(all_logs), 2)
        if all_logs else 0.0
    )

    pending_reviews = len([t for t in all_tickets if t.status == "PENDING"])

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "active_policy_id": "v1_baseline_policy",
        "active_policy_version": _get_active_policy_version(),
        "engine_mode": "Deterministic Gateway (Zero Secondary AI)",
        "total_requests_processed": len(all_logs),
        "avg_latency_ms": avg_latency,
        "decisions_breakdown": decisions_count,
        "total_review_tickets": len(all_tickets),
        "pending_review_tickets": pending_reviews,
        "simulated_banking_sandbox": True
    }
