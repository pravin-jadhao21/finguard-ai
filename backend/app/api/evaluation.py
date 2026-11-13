"""
Evaluation Lab API endpoint.
Exposes the evaluation runner to the frontend.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class EvaluationRunRequest(BaseModel):
    policy_path: Optional[str] = Field(default=None, description="Optional override policy path")


@router.post("/evaluation/run", summary="Run Full Evaluation Suite")
async def run_evaluation(request: Optional[EvaluationRunRequest] = None):
    """
    Executes the full red-team evaluation dataset against the active policy engine.
    Returns per-case results, accuracy, precision, recall, and latency metrics.
    """
    try:
        from app.eval.runner import RedTeamEvaluationRunner
        runner = RedTeamEvaluationRunner(
            policy_path=request.policy_path if request else None
        )
        result = runner.run_full_evaluation(
            policy_path=request.policy_path if request else None
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
