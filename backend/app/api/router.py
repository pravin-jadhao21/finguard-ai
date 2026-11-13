from fastapi import APIRouter
from app.api import health, inspect, policy, data_protection, intent_injection, outbound, tool_firewall, rag, audit_review, analyze, evaluation

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(analyze.router, tags=["Unified Analysis"])
api_router.include_router(inspect.router, tags=["Security Pipeline"])
api_router.include_router(policy.router, tags=["Deterministic Policy Engine"])
api_router.include_router(data_protection.router, tags=["Inbound Data Protection"])
api_router.include_router(intent_injection.router, tags=["Financial Intent & Injection Shield"])
api_router.include_router(outbound.router, tags=["Outbound Response Enforcement"])
api_router.include_router(tool_firewall.router, tags=["Tool & Action Firewall"])
api_router.include_router(rag.router, tags=["Secure Pre-Context RAG"])
api_router.include_router(audit_review.router, tags=["Audit Logging & Review Queue"])
api_router.include_router(evaluation.router, tags=["Evaluation Lab"])
