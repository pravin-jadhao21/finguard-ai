import os
import yaml
import copy
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Body
from app.config import settings
from app.schemas.policy import PolicyEvaluationRequest, PolicyEvaluationResponse, PolicyDefinition
from app.core.policy_validator import PolicyValidator, PolicyValidationError
from app.core.policy_engine import DeterministicPolicyEngine

router = APIRouter()

# Global cached policy engine state
_cached_policy_file: str = ""
_cached_engine: Optional[DeterministicPolicyEngine] = None
_policy_version_history: list = []


def get_policy_engine(policy_path: str = None) -> DeterministicPolicyEngine:
    global _cached_policy_file, _cached_engine
    target_path = policy_path or settings.POLICY_FILE_PATH

    if _cached_engine is None or _cached_policy_file != target_path:
        try:
            policy_def = PolicyValidator.load_from_file(target_path)
            _cached_engine = DeterministicPolicyEngine(policy_def)
            _cached_policy_file = target_path
        except PolicyValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Active policy configuration error: {str(e)}"
            )

    return _cached_engine


def reload_policy_engine():
    """Force reload the policy engine from the current file."""
    global _cached_engine, _cached_policy_file
    _cached_engine = None
    _cached_policy_file = ""
    return get_policy_engine()


@router.post("/policy/evaluate", response_model=PolicyEvaluationResponse, summary="Evaluate Request against Deterministic Policy")
async def evaluate_policy(request: PolicyEvaluationRequest):
    """
    Evaluates an inbound prompt and user context against the active versioned policy set.
    Returns deterministic policy decision (ALLOW, REDACT, TOKENIZE, REDIRECT, BLOCK, ESCALATE),
    reason codes, matched rules list, and execution latency.
    """
    engine = get_policy_engine()
    return engine.evaluate(request)


@router.get("/policies", summary="Get Active Versioned Policy Configuration")
async def get_current_policy():
    """
    Returns the active versioned policy metadata, rule list, and policy file content.
    """
    engine = get_policy_engine()
    policy = engine.policy
    rules_data = []
    for rule in policy.rules:
        rd = rule.model_dump()
        rd["enabled"] = True
        rules_data.append(rd)

    return {
        "policy_id": policy.policy_id,
        "policy_version": policy.version,
        "name": policy.name,
        "description": policy.description or "",
        "rules_count": len(policy.rules),
        "rules": rules_data,
    }


# Keep old path for backwards compatibility
@router.get("/policy/current", summary="Get Active Policy (Legacy Path)", include_in_schema=False)
async def get_current_policy_legacy():
    return await get_current_policy()


@router.post("/policies/validate", summary="Validate Policy YAML Before Apply")
async def validate_policy(yaml_content: str = Body(..., media_type="text/plain")):
    """
    Validates a YAML policy string against the schema. Returns validation result without applying.
    """
    try:
        policy_def = PolicyValidator.load_from_yaml_string(yaml_content)
        return {
            "valid": True,
            "policy_id": policy_def.policy_id,
            "version": policy_def.version,
            "name": policy_def.name,
            "rules_count": len(policy_def.rules),
            "errors": []
        }
    except PolicyValidationError as e:
        return {
            "valid": False,
            "policy_id": None,
            "version": None,
            "name": None,
            "rules_count": 0,
            "errors": [str(e)]
        }


@router.post("/policies/apply", summary="Apply New Policy Version")
async def apply_policy(yaml_content: str = Body(..., media_type="text/plain")):
    """
    Validates and applies a new policy version. Preserves previous version.
    Records policy change in version history.
    """
    global _cached_engine, _cached_policy_file, _policy_version_history

    # Validate first
    try:
        new_policy_def = PolicyValidator.load_from_yaml_string(yaml_content)
    except PolicyValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Policy validation failed: {str(e)}"
        )

    # Record previous version
    if _cached_engine is not None:
        old_policy = _cached_engine.policy
        _policy_version_history.append({
            "policy_id": old_policy.policy_id,
            "version": old_policy.version,
            "name": old_policy.name,
            "rules_count": len(old_policy.rules)
        })

    # Write new policy to active file
    target_path = settings.POLICY_FILE_PATH
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)
    except IOError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write policy file: {str(e)}"
        )

    # Reload engine
    engine = reload_policy_engine()

    return {
        "status": "applied",
        "policy_id": new_policy_def.policy_id,
        "version": new_policy_def.version,
        "name": new_policy_def.name,
        "rules_count": len(new_policy_def.rules),
        "previous_versions": len(_policy_version_history)
    }


@router.get("/policies/history", summary="Get Policy Version History")
async def get_policy_history():
    return {"versions": _policy_version_history}
