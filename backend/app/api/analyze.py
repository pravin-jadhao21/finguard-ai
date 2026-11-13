"""
Unified end-to-end analysis API endpoints.
Provides the primary /analyze/inbound, /analyze/outbound, and /demo/end-to-end endpoints.
"""
import time
import uuid
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.config import settings
from app.core.policy_engine import DeterministicPolicyEngine
from app.core.policy_validator import PolicyValidator, PolicyValidationError
from app.core.inbound_data_protection import InboundDataProtectionEngine
from app.core.prompt_injection import PromptInjectionDetector
from app.core.financial_intent import FinancialIntentClassifier
from app.core.outbound_enforcer import OutboundResponseEnforcer
from app.core.risk_engine import RiskAssessmentEngine
from app.core.rag_guard import SecureRAGGuard
from app.core.llm_adapter import LLMAdapter
from app.core.audit_logger import AuditLogger
from app.schemas.data_protection import InboundDataProtectionRequest
from app.schemas.intent_injection import (
    FinancialIntentRequest,
    InjectionDetectionRequest,
)
from app.schemas.outbound import OutboundValidationRequest
from app.schemas.rag import RAGRequest, RAGUserContext
from app.schemas.audit_review import TrafficDirection, RiskMetadata

router = APIRouter()

# Shared instances
_risk_engine = RiskAssessmentEngine()
_outbound_enforcer = OutboundResponseEnforcer()
_llm_adapter = LLMAdapter()
_rag_guard = SecureRAGGuard()


def _get_policy_engine():
    from app.api.policy import get_policy_engine
    return get_policy_engine()


def _get_audit_logger():
    from app.api.audit_review import _audit_logger
    return _audit_logger


# --- Request/Response schemas ---

class InboundAnalysisRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=65536)
    user_id: Optional[str] = Field(default="anonymous")
    user_role: Optional[str] = Field(default="RetailCustomer")
    transaction_amount: Optional[float] = Field(default=None, ge=0)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class OutboundAnalysisRequest(BaseModel):
    llm_response: str = Field(..., min_length=1, max_length=65536)
    prompt_context: Optional[str] = Field(default="")
    user_role: Optional[str] = Field(default="RetailCustomer")
    ground_truth_version: Optional[str] = Field(default="1.0.0")


class EndToEndRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=65536)
    user_id: Optional[str] = Field(default="demo-user")
    user_role: Optional[str] = Field(default="RetailCustomer")
    transaction_amount: Optional[float] = Field(default=None, ge=0)
    include_rag: bool = Field(default=False)


# --- Endpoints ---

@router.post("/analyze/inbound", summary="Full Inbound Analysis Pipeline")
async def analyze_inbound(request: InboundAnalysisRequest):
    """
    Runs the complete inbound security pipeline:
    1. Data protection (PII/PCI detection & transformation)
    2. Prompt injection detection
    3. Financial intent classification
    4. Policy engine evaluation
    5. Risk scoring
    6. Audit logging
    """
    start_time = time.perf_counter()
    request_id = f"inb-{uuid.uuid4().hex[:12]}"

    prompt = request.prompt

    # Step 1: Data Protection
    dp_result = InboundDataProtectionEngine.process(
        InboundDataProtectionRequest(prompt=prompt)
    )
    transformed_prompt = dp_result.transformed_prompt
    data_categories = list(set(
        t.candidate_type for t in dp_result.candidate_traces
    ))
    highest_classification = None
    if dp_result.candidate_traces:
        highest_classification = dp_result.candidate_traces[0].classification_tier.value

    # Step 2: Prompt Injection Detection
    injection_result = PromptInjectionDetector.scan(
        InjectionDetectionRequest(prompt=prompt)
    )

    # Step 3: Financial Intent Classification
    intent_result = FinancialIntentClassifier.classify(
        FinancialIntentRequest(
            prompt=prompt,
            transaction_amount=request.transaction_amount,
        )
    )

    # Step 4: Policy Engine Evaluation
    from app.schemas.policy import PolicyEvaluationRequest
    engine = _get_policy_engine()
    policy_result = engine.evaluate(
        PolicyEvaluationRequest(
            prompt=transformed_prompt,
            user_id=request.user_id,
            user_role=request.user_role,
            transaction_amount=request.transaction_amount,
            context=request.context or {},
        )
    )

    # Step 5: Risk Scoring
    risk = _risk_engine.evaluate_risk(
        intent_category=intent_result.intent_category.value,
        data_classification=highest_classification,
        has_prompt_injection=injection_result.is_injection_detected,
        amount=request.transaction_amount,
    )

    # Step 6: Determine final decision (highest precedence wins)
    decisions_precedence = {
        "BLOCK": 100, "ESCALATE": 80, "REDIRECT": 60,
        "TOKENIZE": 40, "REDACT": 20, "ALLOW": 0,
    }
    candidate_decisions = [
        (policy_result.decision.value, "POLICY_ENGINE"),
        (injection_result.action_decision, "INJECTION_DETECTOR"),
        (intent_result.action_decision, "INTENT_CLASSIFIER"),
    ]
    if dp_result.candidates_found > 0:
        candidate_decisions.append(("REDACT", "DATA_PROTECTION"))

    final_decision = "ALLOW"
    final_source = "DEFAULT"
    for dec, src in candidate_decisions:
        if decisions_precedence.get(dec, 0) > decisions_precedence.get(final_decision, 0):
            final_decision = dec
            final_source = src

    # Use the transformed prompt from data protection
    final_transformed = transformed_prompt
    if policy_result.transformed_prompt and final_decision not in ("BLOCK",):
        final_transformed = policy_result.transformed_prompt

    # Step 7: Audit
    audit_logger = _get_audit_logger()
    matched_rule_id = (
        policy_result.matched_rules[0].rule_id if policy_result.matched_rules else None
    )
    audit_logger.log_decision(
        request_id=request_id,
        direction=TrafficDirection.INBOUND,
        policy_id=policy_result.policy_id,
        policy_version=policy_result.policy_version,
        decision=final_decision,
        reason_code=policy_result.reason_code,
        risk_metadata=risk,
        latency_ms=round((time.perf_counter() - start_time) * 1000, 3),
        matched_rule_id=matched_rule_id,
    )

    total_latency = round((time.perf_counter() - start_time) * 1000, 3)

    # Build reason codes list
    reason_codes = [policy_result.reason_code]
    if injection_result.is_injection_detected:
        reason_codes.append(injection_result.primary_reason_code)
    if intent_result.action_decision != "ALLOW":
        reason_codes.append(intent_result.reason_code)

    return {
        "request_id": request_id,
        "decision": final_decision,
        "decision_source": final_source,
        "reason_codes": reason_codes,
        "risk_score": risk.risk_score,
        "risk_level": risk.risk_level.value,
        "risk_triggers": risk.triggers,
        "policy_id": policy_result.policy_id,
        "policy_version": policy_result.policy_version,
        "matched_rules": [r.model_dump() for r in policy_result.matched_rules],
        "data_protection": {
            "candidates_found": dp_result.candidates_found,
            "categories": data_categories,
            "traces": [t.model_dump() for t in dp_result.candidate_traces],
        },
        "injection_detection": {
            "detected": injection_result.is_injection_detected,
            "severity": injection_result.highest_severity,
            "matches": [m.model_dump() for m in injection_result.matches],
        },
        "intent_classification": {
            "category": intent_result.intent_category.value,
            "action": intent_result.action_decision,
            "reason_code": intent_result.reason_code,
            "signal_trace": intent_result.signal_trace.model_dump(),
            "disclaimer": intent_result.suggested_disclaimer,
        },
        "transformed_prompt": final_transformed if final_decision != "BLOCK" else None,
        "original_prompt_length": len(prompt),
        "redirect_target": policy_result.redirect_target,
        "explanation": _build_explanation(final_decision, final_source, reason_codes, risk),
        "latency_ms": total_latency,
    }


@router.post("/analyze/outbound", summary="Full Outbound Analysis Pipeline")
async def analyze_outbound(request: OutboundAnalysisRequest):
    """
    Runs the complete outbound security pipeline on an LLM response.
    """
    start_time = time.perf_counter()
    request_id = f"out-{uuid.uuid4().hex[:12]}"

    result = _outbound_enforcer.validate(
        OutboundValidationRequest(
            llm_response=request.llm_response,
            prompt_context=request.prompt_context,
            user_role=request.user_role,
            ground_truth_version=request.ground_truth_version,
        )
    )

    total_latency = round((time.perf_counter() - start_time) * 1000, 3)

    return {
        "request_id": request_id,
        "decision": result.action_decision.value,
        "reason_code": result.reason_code,
        "original_response": result.original_llm_response,
        "sanitized_response": result.sanitized_llm_response,
        "is_modified": result.is_modified,
        "leak_detected": result.leak_detected,
        "unsafe_claim_detected": result.unsafe_claim_detected,
        "discrepancy_detected": result.discrepancy_detected,
        "grounding_details": [g.model_dump() for g in result.grounding_details],
        "fallback_applied": result.fallback_applied,
        "latency_ms": total_latency,
    }


@router.post("/demo/end-to-end", summary="Full End-to-End Demo Pipeline")
async def end_to_end_demo(request: EndToEndRequest):
    """
    Full end-to-end demo flow:
    1. Inbound checks on user request
    2. Data protection transformations
    3. Optional RAG retrieval with access control
    4. Simulated LLM generates response from sanitized input
    5. Outbound checks on generated response
    6. Returns final user-facing response with all decision traces
    """
    start_time = time.perf_counter()
    request_id = f"e2e-{uuid.uuid4().hex[:12]}"

    prompt = request.prompt

    # === INBOUND PHASE ===
    inbound_req = InboundAnalysisRequest(
        prompt=prompt,
        user_id=request.user_id,
        user_role=request.user_role,
        transaction_amount=request.transaction_amount,
    )
    inbound_result = await analyze_inbound(inbound_req)

    inbound_decision = inbound_result["decision"]

    # If inbound is BLOCK, stop here
    if inbound_decision == "BLOCK":
        total_latency = round((time.perf_counter() - start_time) * 1000, 3)
        return {
            "request_id": request_id,
            "final_decision": "BLOCK",
            "final_response": "Your request has been blocked by the security gateway. "
                            + inbound_result.get("explanation", "Policy violation detected."),
            "inbound": inbound_result,
            "rag": None,
            "llm_response": None,
            "outbound": None,
            "latency_ms": total_latency,
        }

    sanitized_input = inbound_result.get("transformed_prompt") or prompt

    # === RAG PHASE ===
    rag_result = None
    rag_context = ""
    if request.include_rag:
        rag_response = _rag_guard.process_rag_request(
            RAGRequest(
                query=prompt,
                user_context=RAGUserContext(
                    user_id=request.user_id or "demo-user",
                    user_role=request.user_role or "RetailCustomer",
                ),
                top_k=3,
            )
        )
        rag_context = rag_response.sanitized_context_block
        rag_result = {
            "request_id": rag_response.request_id,
            "retrieved_count": rag_response.retrieved_count,
            "authorized_count": rag_response.authorized_count,
            "audit_trace": [a.model_dump() for a in rag_response.audit_trace],
            "latency_ms": rag_response.latency_ms,
        }

    # === LLM SIMULATION PHASE ===
    llm_output = _llm_adapter.generate(
        sanitized_input=sanitized_input,
        rag_context=rag_context,
    )
    llm_response_text = llm_output["response"]

    # === OUTBOUND PHASE ===
    outbound_req = OutboundAnalysisRequest(
        llm_response=llm_response_text,
        prompt_context=sanitized_input,
        user_role=request.user_role,
    )
    outbound_result = await analyze_outbound(outbound_req)

    outbound_decision = outbound_result["decision"]

    # Determine final user-facing response
    if outbound_decision == "BLOCK":
        final_response = (
            "The generated response was blocked by outbound security checks. "
            "Please refer to official bank documentation for accurate information."
        )
    elif outbound_result.get("sanitized_response"):
        final_response = outbound_result["sanitized_response"]
    else:
        final_response = llm_response_text

    # Add redirect info if inbound was REDIRECT
    if inbound_decision == "REDIRECT":
        redirect_msg = inbound_result.get("redirect_target") or ""
        disclaimer = inbound_result.get("intent_classification", {}).get("disclaimer", "")
        if disclaimer:
            final_response = f"{disclaimer}\n\n{final_response}"

    # Overall decision is the highest precedence between inbound and outbound
    precedence = {"BLOCK": 100, "ESCALATE": 80, "REDIRECT": 60, "MODIFY": 50, "REDACT": 20, "ALLOW": 0}
    if precedence.get(outbound_decision, 0) > precedence.get(inbound_decision, 0):
        overall_decision = outbound_decision
    else:
        overall_decision = inbound_decision

    total_latency = round((time.perf_counter() - start_time) * 1000, 3)

    return {
        "request_id": request_id,
        "final_decision": overall_decision,
        "final_response": final_response,
        "inbound": inbound_result,
        "rag": rag_result,
        "llm_response": {
            "raw_response": llm_response_text,
            "model": llm_output["model"],
            "is_simulated": llm_output["is_simulated"],
            "matched_topic": llm_output["matched_topic"],
            "disclaimer": llm_output["disclaimer"],
        },
        "outbound": outbound_result,
        "latency_ms": total_latency,
    }


def _build_explanation(decision: str, source: str, reason_codes: list, risk: RiskMetadata) -> str:
    """Build a human-readable explanation of the decision."""
    parts = [f"Decision: {decision} (determined by {source})."]

    if decision == "ALLOW":
        parts.append("The request passed all security checks and is permitted.")
    elif decision == "BLOCK":
        parts.append("The request was blocked due to a security policy violation.")
    elif decision == "REDIRECT":
        parts.append("The request was redirected to approved guidance per compliance policy.")
    elif decision == "ESCALATE":
        parts.append("The request requires human review before proceeding.")
    elif decision == "REDACT":
        parts.append("Sensitive data was detected and redacted from the request.")

    if risk.triggers:
        parts.append(f"Risk factors: {', '.join(risk.triggers[:3])}")

    return " ".join(parts)
