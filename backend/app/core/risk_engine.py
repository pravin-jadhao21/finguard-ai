from typing import Dict, Any, Optional, List
from app.schemas.audit_review import RiskMetadata, RiskLevel


class RiskAssessmentEngine:
    """
    Configurable Risk Assessment Engine for BFSI AI Gateway.
    Evaluates contextual risk signals independently from policy enforcement decisions.
    Calculates weighted risk score (0.0 to 100.0) and assigns risk levels.
    """

    # Configurable Risk Factor Weights & Thresholds
    INTENT_WEIGHTS = {
        "HIGH_RISK": 40.0,
        "TRANSACTIONAL": 30.0,
        "PERSONALIZED_RECOMMENDATION": 20.0,
        "PERSONALIZED_ANALYSIS": 15.0,
        "COMPARATIVE": 10.0,
        "AMBIGUOUS": 15.0,
        "EDUCATIONAL": 0.0
    }

    SENSITIVITY_WEIGHTS = {
        "CRITICAL_PCI": 35.0,
        "CRITICAL_PII": 25.0,
        "SENSITIVE_PII": 15.0,
        "GENERAL_DATA": 0.0
    }

    def evaluate_risk(
        self,
        intent_category: Optional[str] = None,
        data_classification: Optional[str] = None,
        has_prompt_injection: bool = False,
        has_secret_leak: bool = False,
        has_rate_discrepancy: bool = False,
        amount: Optional[float] = None
    ) -> RiskMetadata:
        """
        Calculates cumulative risk score and risk level from contextual signals.
        Returns typed RiskMetadata.
        """
        triggers: List[str] = []

        # 1. Intent Risk Points
        intent_pts = self.INTENT_WEIGHTS.get(intent_category, 0.0) if intent_category else 0.0
        if intent_pts > 0:
            triggers.append(f"Intent category '{intent_category}' (+{intent_pts} pts)")

        # 2. Data Sensitivity Risk Points
        sens_pts = self.SENSITIVITY_WEIGHTS.get(data_classification, 0.0) if data_classification else 0.0
        if sens_pts > 0:
            triggers.append(f"Data sensitivity '{data_classification}' (+{sens_pts} pts)")

        # 3. Prompt Injection & Key Leak Risk Points
        inj_pts = 0.0
        if has_prompt_injection:
            inj_pts += 50.0
            triggers.append("Prompt injection attempt detected (+50 pts)")
        if has_secret_leak:
            inj_pts += 40.0
            triggers.append("Secret API key leak detected (+40 pts)")

        # 4. Monetary Amount Risk Points
        amt_pts = 0.0
        if amount is not None:
            if amount >= 5000.0:
                amt_pts = 35.0
                triggers.append(f"High transfer amount ${amount:.2f} (+35 pts)")
            elif amount >= 1000.0:
                amt_pts = 20.0
                triggers.append(f"Medium transfer amount ${amount:.2f} (+20 pts)")
            elif amount > 0:
                amt_pts = 5.0

        # 5. Outbound Rate Discrepancy
        if has_rate_discrepancy:
            inj_pts += 25.0
            triggers.append("Ground-truth rate discrepancy detected (+25 pts)")

        # Total cumulative score capped at 100.0
        total_score = min(100.0, intent_pts + sens_pts + inj_pts + amt_pts)

        # Categorize Risk Level
        if total_score >= 80.0:
            level = RiskLevel.CRITICAL
        elif total_score >= 60.0:
            level = RiskLevel.HIGH
        elif total_score >= 30.0:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return RiskMetadata(
            risk_score=round(total_score, 1),
            risk_level=level,
            intent_risk_points=intent_pts,
            sensitivity_risk_points=sens_pts,
            injection_risk_points=inj_pts,
            amount_risk_points=amt_pts,
            triggers=triggers
        )
