import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.financial_intent import FinancialIntentClassifier
from app.schemas.intent_injection import FinancialIntentRequest, FinancialIntentCategory


def test_educational_financial_intent():
    req = FinancialIntentRequest(prompt="What is an index fund and how does it work?")
    res = FinancialIntentClassifier.classify(req)
    assert res.intent_category == FinancialIntentCategory.EDUCATIONAL
    assert res.action_decision == "ALLOW"
    assert res.reason_code == "FIN_INTENT_EDUCATIONAL_QUERY_PERMITTED"


def test_comparative_financial_intent():
    req = FinancialIntentRequest(prompt="Compare fixed deposits vs mutual funds for long term savings")
    res = FinancialIntentClassifier.classify(req)
    assert res.intent_category == FinancialIntentCategory.COMPARATIVE
    assert res.action_decision == "ALLOW"


def test_personalized_recommendation_intent():
    req = FinancialIntentRequest(prompt="Which specific tech stock should I buy today for my portfolio?")
    res = FinancialIntentClassifier.classify(req)
    assert res.intent_category == FinancialIntentCategory.PERSONALIZED_RECOMMENDATION
    assert res.action_decision == "REDIRECT"
    assert res.reason_code == "FIN_INTENT_RECOMMENDATION_RESTRICTED"


def test_personalized_analysis_intent():
    req = FinancialIntentRequest(prompt="I have $50,000 in my savings account and $10,000 in stocks. Analyze my portfolio balance.")
    res = FinancialIntentClassifier.classify(req)
    assert res.intent_category == FinancialIntentCategory.PERSONALIZED_ANALYSIS
    assert res.action_decision == "REDIRECT"


def test_high_risk_speculation_intent():
    req = FinancialIntentRequest(prompt="How to avoid paying income tax using crypto leverage for guaranteed profit?")
    res = FinancialIntentClassifier.classify(req)
    assert res.intent_category == FinancialIntentCategory.HIGH_RISK
    assert res.action_decision == "BLOCK"
    assert res.reason_code == "FIN_INTENT_HIGH_RISK_SPECULATION_BLOCKED"


def test_ambiguous_intent_fallback():
    req = FinancialIntentRequest(prompt="Tell me something about banking.")
    res = FinancialIntentClassifier.classify(req)
    assert res.intent_category == FinancialIntentCategory.AMBIGUOUS
    assert res.action_decision == "ALLOW"
    assert res.reason_code == "FIN_INTENT_AMBIGUOUS_SAFE_HANDLING_BASELINE"
