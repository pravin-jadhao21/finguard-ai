import re
import time
import uuid
from typing import Dict, Any, Optional, List, Tuple
from app.core.tool_registry import ToolRegistry
from app.services.simulated_banking import SimulatedBankingService
from app.schemas.tool_firewall import (
    ToolValidationAction,
    ToolValidationRequest,
    ToolValidationResponse,
    UserAuthContext
)


class ToolActionFirewall:
    """
    Deterministic Tool & Action Firewall Gateway for BFSI Applications.
    Enforces strict allowlist, JSON schema validation, user role authorization,
    prompt-parameter alignment, step-up approval verification, and safe execution sandbox.
    """

    # Suspicious code/shell/SQL patterns in tool names or argument payloads
    SUSPICIOUS_EXEC_PATTERNS = re.compile(
        r'(?i)\b(?:select\s+.*?\s+from|drop\s+table|delete\s+from|insert\s+into|exec\s+|system\(|popen\(|eval\(|import\s+os|__import__|subprocess)\b'
    )

    # Prompt Parameter Extraction Regexes
    AMOUNT_PROMPT_RE = re.compile(r'(?i)\$\s*(\d+(?:\.\d+)?)|(?:\b(\d+(?:\.\d+)?)\s*(?:usd|dollars?|bucks?))\b')
    ACCOUNT_PROMPT_RE = re.compile(r'\b(ACC-\d{4})\b')

    def __init__(self, banking_service: Optional[SimulatedBankingService] = None):
        self.banking_service = banking_service or SimulatedBankingService()

    def validate_and_execute(self, request: ToolValidationRequest) -> ToolValidationResponse:
        """
        Executes full tool/action firewall validation pipeline.
        If ALLOWED, invokes simulated core banking service and returns result.
        """
        start_time = time.perf_counter()
        req_id = f"tool-{uuid.uuid4().hex[:12]}"
        tool_name = request.tool_name.strip() if request.tool_name else ""
        args = request.arguments or {}
        user_prompt = request.user_prompt or ""
        context = request.user_context

        # --- STEP 1: Tool Allowlist & Code Execution Guard ---
        if not tool_name or not ToolRegistry.is_tool_allowed(tool_name):
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
            return ToolValidationResponse(
                request_id=req_id,
                action_decision=ToolValidationAction.BLOCK,
                reason_code="TOOL_UNAUTHORIZED_NAME_BLOCKED",
                tool_name=tool_name,
                validated_arguments=args,
                result=None,
                execution_success=False,
                latency_ms=elapsed_ms
            )

        # Check for code/SQL/shell injection attempts inside args or tool name
        str_args_repr = str(args)
        if self.SUSPICIOUS_EXEC_PATTERNS.search(tool_name) or self.SUSPICIOUS_EXEC_PATTERNS.search(str_args_repr):
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
            return ToolValidationResponse(
                request_id=req_id,
                action_decision=ToolValidationAction.BLOCK,
                reason_code="TOOL_CODE_INJECTION_ATTEMPT_BLOCKED",
                tool_name=tool_name,
                validated_arguments=args,
                result=None,
                execution_success=False,
                latency_ms=elapsed_ms
            )

        # --- STEP 2: JSON Schema & Argument Constraints Validation ---
        is_valid_schema, schema_err = ToolRegistry.validate_arguments(tool_name, args)
        if not is_valid_schema:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
            return ToolValidationResponse(
                request_id=req_id,
                action_decision=ToolValidationAction.BLOCK,
                reason_code=f"TOOL_SCHEMA_VALIDATION_FAILED: {schema_err}",
                tool_name=tool_name,
                validated_arguments=args,
                result=None,
                execution_success=False,
                latency_ms=elapsed_ms
            )

        # --- STEP 3: User Authentication & Role Authorization Context ---
        if not context or not context.user_id:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
            return ToolValidationResponse(
                request_id=req_id,
                action_decision=ToolValidationAction.BLOCK,
                reason_code="TOOL_AUTH_CONTEXT_MISSING_BLOCKED",
                tool_name=tool_name,
                validated_arguments=args,
                result=None,
                execution_success=False,
                latency_ms=elapsed_ms
            )

        tool_spec = ToolRegistry.get_tool_schema(tool_name)
        allowed_roles = tool_spec.get("allowed_roles", []) if tool_spec else []
        if context.user_role not in allowed_roles:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
            return ToolValidationResponse(
                request_id=req_id,
                action_decision=ToolValidationAction.BLOCK,
                reason_code=f"TOOL_ROLE_UNAUTHORIZED_BLOCKED: Role '{context.user_role}' not permitted for tool '{tool_name}'",
                tool_name=tool_name,
                validated_arguments=args,
                result=None,
                execution_success=False,
                latency_ms=elapsed_ms
            )

        # --- STEP 4: Prompt-Parameter Alignment Checks ---
        # A. Amount Mismatch Validation
        if "amount" in args and user_prompt:
            prompt_amounts = []
            for m in self.AMOUNT_PROMPT_RE.finditer(user_prompt):
                amt_str = m.group(1) or m.group(2)
                if amt_str:
                    try:
                        prompt_amounts.append(float(amt_str))
                    except ValueError:
                        pass

            arg_amount = float(args["amount"])
            if prompt_amounts and not any(abs(arg_amount - p_amt) < 0.01 for p_amt in prompt_amounts):
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
                return ToolValidationResponse(
                    request_id=req_id,
                    action_decision=ToolValidationAction.BLOCK,
                    reason_code=f"TOOL_PARAMETER_AMOUNT_MISMATCH_BLOCKED: Tool amount {arg_amount} does not match prompt amount(s) {prompt_amounts}",
                    tool_name=tool_name,
                    validated_arguments=args,
                    result=None,
                    execution_success=False,
                    latency_ms=elapsed_ms
                )

        # B. Recipient Mismatch Validation
        if "to_account_id" in args and user_prompt:
            prompt_accounts = self.ACCOUNT_PROMPT_RE.findall(user_prompt)
            arg_dest = args["to_account_id"]
            # If prompt mentions specific account(s) and arg_dest is not among them (or when 2 accounts mentioned, destination isn't match)
            if prompt_accounts and arg_dest not in prompt_accounts:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
                return ToolValidationResponse(
                    request_id=req_id,
                    action_decision=ToolValidationAction.BLOCK,
                    reason_code=f"TOOL_PARAMETER_RECIPIENT_MISMATCH_BLOCKED: Recipient '{arg_dest}' does not match recipient specified in prompt {prompt_accounts}",
                    tool_name=tool_name,
                    validated_arguments=args,
                    result=None,
                    execution_success=False,
                    latency_ms=elapsed_ms
                )

        # --- STEP 5: Sensitive Action & Step-Up Approval Verification ---
        is_sensitive = tool_spec.get("is_sensitive", False) if tool_spec else False
        if is_sensitive:
            has_approval = context.step_up_authenticated or bool(context.approval_token and context.approval_token.strip())
            if not has_approval:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
                return ToolValidationResponse(
                    request_id=req_id,
                    action_decision=ToolValidationAction.ESCALATE,
                    reason_code="TOOL_APPROVAL_REQUIRED_ESCALATED: Sensitive action requires step-up authentication or valid approval token.",
                    tool_name=tool_name,
                    validated_arguments=args,
                    result=None,
                    execution_success=False,
                    latency_ms=elapsed_ms
                )

        # --- STEP 6: Execute Tool in Simulated Core Banking Sandbox ---
        execution_result = None
        exec_success = False
        try:
            if tool_name == "get_demo_balance":
                execution_result = self.banking_service.get_balance(account_id=args["account_id"])
            elif tool_name == "get_demo_statement":
                execution_result = self.banking_service.get_statement(
                    account_id=args["account_id"],
                    limit=args.get("limit", 5)
                )
            elif tool_name == "initiate_demo_transfer":
                execution_result = self.banking_service.initiate_transfer(
                    from_account_id=args["from_account_id"],
                    to_account_id=args["to_account_id"],
                    amount=float(args["amount"]),
                    memo=args.get("memo")
                )
            exec_success = True

        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
            return ToolValidationResponse(
                request_id=req_id,
                action_decision=ToolValidationAction.BLOCK,
                reason_code=f"TOOL_EXECUTION_ERROR_BLOCKED: Core banking execution failed: {str(exc)}",
                tool_name=tool_name,
                validated_arguments=args,
                result=None,
                execution_success=False,
                latency_ms=elapsed_ms
            )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
        return ToolValidationResponse(
            request_id=req_id,
            action_decision=ToolValidationAction.ALLOW,
            reason_code="TOOL_VALIDATION_PASSED",
            tool_name=tool_name,
            validated_arguments=args,
            result=execution_result,
            execution_success=exec_success,
            latency_ms=elapsed_ms
        )
