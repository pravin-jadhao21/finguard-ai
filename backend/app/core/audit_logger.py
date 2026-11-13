import sys
import copy
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.schemas.audit_review import AuditLogEntry, TrafficDirection, RiskMetadata

logger = logging.getLogger("finguard.audit")


class AuditLogger:
    """
    Fail-Safe Immutable Audit Logger for FinGuard AI Gateway.
    Stores structured audit traces with policy version traceability, decision explainability,
    zero confidential payload data, and automatic backup fallback logging.
    """

    def __init__(self, simulate_storage_failure: bool = False):
        self._logs: Dict[str, AuditLogEntry] = {}
        self._backup_logs: List[Dict[str, Any]] = []
        self.simulate_storage_failure = simulate_storage_failure

    def log_decision(
        self,
        request_id: str,
        direction: TrafficDirection,
        policy_id: str,
        policy_version: str,
        decision: str,
        reason_code: str,
        risk_metadata: RiskMetadata,
        latency_ms: float,
        matched_rule_id: Optional[str] = None
    ) -> AuditLogEntry:
        """
        Logs structured audit record.
        Falls back safely to local backup log if primary storage fails.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        entry = AuditLogEntry(
            request_id=request_id,
            timestamp=now_iso,
            direction=direction,
            policy_id=policy_id,
            policy_version=policy_version,
            decision=decision,
            reason_code=reason_code,
            matched_rule_id=matched_rule_id,
            risk_metadata=risk_metadata,
            latency_ms=latency_ms,
            fallback_active=False
        )

        try:
            if self.simulate_storage_failure:
                raise IOError("Simulated primary audit database connection timeout.")

            # Store in primary audit log storage
            self._logs[request_id] = entry

        except Exception as exc:
            # Safe fail-safe fallback logging
            entry_copy = entry.model_copy()
            entry_copy.fallback_active = True

            backup_record = entry_copy.model_dump()
            self._backup_logs.append(backup_record)
            self._logs[request_id] = entry_copy

            sys.stderr.write(f"[AUDIT FAILSAFE BACKUP LOG] {now_iso} - Req: {request_id} - {str(exc)}\n")

        return self._logs[request_id]

    def get_logs(
        self,
        policy_version: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 50
    ) -> List[AuditLogEntry]:
        """Queries audit log records with optional filtering."""
        logs = list(self._logs.values())
        if policy_version:
            logs = [l for l in logs if l.policy_version == policy_version]
        if decision:
            logs = [l for l in logs if l.decision == decision]

        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]

    def explain_decision(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns decision explainability details for a given request ID.
        Provides full reasoning without exposing raw confidential text payload.
        """
        if request_id not in self._logs:
            return None

        log = self._logs[request_id]
        return {
            "request_id": log.request_id,
            "timestamp": log.timestamp,
            "direction": log.direction.value,
            "policy_id": log.policy_id,
            "policy_version": log.policy_version,
            "decision": log.decision,
            "reason_code": log.reason_code,
            "matched_rule_id": log.matched_rule_id or "NONE",
            "risk_summary": {
                "risk_score": log.risk_metadata.risk_score,
                "risk_level": log.risk_metadata.risk_level.value,
                "triggers": log.risk_metadata.triggers
            },
            "latency_ms": log.latency_ms,
            "fallback_active": log.fallback_active,
            "confidential_data_stored": False  # Zero confidential payload guarantee
        }
