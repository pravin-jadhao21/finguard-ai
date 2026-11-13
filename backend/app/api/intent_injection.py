from fastapi import APIRouter
from app.schemas.intent_injection import (
    FinancialIntentRequest,
    FinancialIntentResponse,
    InjectionDetectionRequest,
    InjectionDetectionResponse
)
from app.core.financial_intent import FinancialIntentClassifier
from app.core.prompt_injection import PromptInjectionDetector

router = APIRouter()


@router.post(
    "/intent/classify",
    response_model=FinancialIntentResponse,
    summary="Classify Financial Intent via Multi-Signal Matrix"
)
async def classify_financial_intent(request: FinancialIntentRequest):
    """
    Classifies prompt payload into EDUCATIONAL, COMPARATIVE, PERSONALIZED_ANALYSIS,
    PERSONALIZED_RECOMMENDATION, TRANSACTIONAL, HIGH_RISK, or AMBIGUOUS categories.
    """
    return FinancialIntentClassifier.classify(request)


@router.post(
    "/injection/detect",
    response_model=InjectionDetectionResponse,
    summary="Detect Direct & Indirect Prompt Injection Attacks"
)
async def detect_prompt_injection(request: InjectionDetectionRequest):
    """
    Scans prompt payload for instruction overrides, system exfiltration, policy bypasses,
    and character obfuscation attacks while maintaining resilience on benign queries.
    """
    return PromptInjectionDetector.scan(request)
