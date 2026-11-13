import re
import time
import uuid
from typing import List, Tuple, Optional, Dict
from app.schemas.policy import (
    PolicyDefinition,
    PolicyRule,
    PolicyEvaluationRequest,
    PolicyEvaluationResponse,
    MatchedRuleDetail,
    DecisionEnum
)
from app.core.sanitizer import TextSanitizer


# Action Precedence Matrix (Higher integer = Higher precedence)
ACTION_PRECEDENCE: Dict[DecisionEnum, int] = {
    DecisionEnum.BLOCK: 100,
    DecisionEnum.ESCALATE: 80,
    DecisionEnum.REDIRECT: 60,
    DecisionEnum.TOKENIZE: 40,
    DecisionEnum.REDACT: 20,
    DecisionEnum.ALLOW: 0,
}


class DeterministicPolicyEngine:
    """
    100% Deterministic Security & Policy Enforcement Engine.
    Evaluates requests against loaded versioned policies without AI models.
    """

    def __init__(self, policy: PolicyDefinition):
        self.policy = policy
        # Pre-compile regexes for optimal performance
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        for rule in self.policy.rules:
            if rule.condition.pattern:
                self._compiled_patterns[rule.id] = re.compile(rule.condition.pattern, re.IGNORECASE)

    def evaluate(self, request: PolicyEvaluationRequest) -> PolicyEvaluationResponse:
        """
        Executes deterministic evaluation pipeline for an incoming request.
        Returns typed PolicyEvaluationResponse.
        """
        start_time = time.perf_counter()
        request_id = f"req-{uuid.uuid4().hex[:12]}"

        # 1. Normalize prompt text
        normalized_prompt, _ = TextSanitizer.sanitize(request.prompt)
        
        matched_details: List[MatchedRuleDetail] = []
        matched_rules: List[PolicyRule] = []
        cumulative_risk_score = 0
        transformed_prompt = normalized_prompt
        redirect_target: Optional[str] = None

        # 2. Evaluate all rules in policy
        for rule in self.policy.rules:
            is_matched, matched_substr = self._evaluate_rule_condition(
                rule=rule,
                prompt=normalized_prompt,
                user_role=request.user_role or "RetailCustomer",
                amount=request.transaction_amount,
                context=request.context or {}
            )

            if is_matched:
                matched_rules.append(rule)
                cumulative_risk_score += rule.weight
                
                matched_details.append(
                    MatchedRuleDetail(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        category=rule.category,
                        action=rule.action,
                        priority=rule.priority,
                        weight=rule.weight,
                        matched_substring=matched_substr
                    )
                )

                # Execute in-flight transformations for text manipulation rules
                if rule.action in (DecisionEnum.REDACT, DecisionEnum.TOKENIZE) and matched_substr:
                    replacement = rule.replacement_token or f"[{rule.action.value}_PROTECTED]"
                    transformed_prompt = transformed_prompt.replace(matched_substr, replacement)

                if rule.action == DecisionEnum.REDIRECT and rule.redirect_target:
                    redirect_target = rule.redirect_target

        # 3. Determine Final Policy Decision via Precedence & Priority Matrix
        if not matched_rules:
            final_decision = DecisionEnum.ALLOW
            winning_reason_code = "DEFAULT_ALLOW"
        else:
            # Deterministic Sorting Key:
            # Primary: Action Precedence Weight (descending)
            # Secondary: Rule Priority Integer (descending)
            # Tertiary: Rule ID string (ascending for alphabetical tie-break)
            def rule_sorting_key(r: PolicyRule) -> Tuple[int, int, str]:
                precedence_val = ACTION_PRECEDENCE.get(r.action, 0)
                # Reverse string for rule_id so min() or max() handles cleanly
                return (precedence_val, r.priority, r.id)

            # Sort matched rules descending by sorting key
            sorted_matched = sorted(
                matched_rules,
                key=lambda r: (ACTION_PRECEDENCE.get(r.action, 0), r.priority, r.id),
                reverse=True
            )
            
            # To handle strict tie-breaks on identical (precedence, priority):
            # Sort subset with same precedence & priority by rule_id alphabetically
            top_rule = sorted_matched[0]
            top_precedence = ACTION_PRECEDENCE.get(top_rule.action, 0)
            top_priority = top_rule.priority

            candidates = [
                r for r in sorted_matched
                if ACTION_PRECEDENCE.get(r.action, 0) == top_precedence and r.priority == top_priority
            ]
            candidates.sort(key=lambda r: r.id)
            winning_rule = candidates[0]

            final_decision = winning_rule.action
            winning_reason_code = winning_rule.reason_code
            if winning_rule.action == DecisionEnum.REDIRECT and winning_rule.redirect_target:
                redirect_target = winning_rule.redirect_target

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)

        return PolicyEvaluationResponse(
            request_id=request_id,
            policy_id=self.policy.policy_id,
            policy_version=self.policy.version,
            decision=final_decision,
            reason_code=winning_reason_code,
            risk_score=cumulative_risk_score,
            matched_rules=matched_details,
            transformed_prompt=transformed_prompt if final_decision != DecisionEnum.BLOCK else None,
            redirect_target=redirect_target,
            latency_ms=elapsed_ms
        )

    def _evaluate_rule_condition(
        self,
        rule: PolicyRule,
        prompt: str,
        user_role: str,
        amount: Optional[float],
        context: Dict
    ) -> Tuple[bool, Optional[str]]:
        cond = rule.condition

        # Check Required Role condition
        if cond.required_role and user_role != cond.required_role:
            return False, None

        # A rule with both keywords and an amount threshold requires both signals.
        if cond.max_amount is not None:
            amount_exceeded = amount is not None and amount > cond.max_amount
            if cond.keywords:
                matched_keyword = next(
                    (kw for kw in cond.keywords if kw.lower() in prompt.lower()),
                    None,
                )
                if amount_exceeded and matched_keyword:
                    return True, f"{matched_keyword}; amount={amount} > max={cond.max_amount}"
                return False, None
            if amount_exceeded:
                return True, f"amount={amount} > max={cond.max_amount}"
            if amount is None and cond.max_amount == 0:
                pass  # Continue checking other conditions if max_amount is specified

        # Check Keyword Substring condition
        if cond.keywords:
            for kw in cond.keywords:
                if kw.lower() in prompt.lower():
                    return True, kw

        # Check Regular Expression Pattern condition
        if rule.id in self._compiled_patterns:
            compiled_re = self._compiled_patterns[rule.id]
            match = compiled_re.search(prompt)
            if match:
                return True, match.group(0)

        # Handle amount-only rules (where max_amount was triggered)
        if cond.max_amount is not None and amount is not None and amount > cond.max_amount:
            return True, f"amount={amount}"

        return False, None
