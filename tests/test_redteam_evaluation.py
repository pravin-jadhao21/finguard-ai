import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.eval.runner import RedTeamEvaluationRunner


@pytest.fixture
def eval_runner():
    return RedTeamEvaluationRunner()


def test_redteam_benchmark_evaluation_suite(eval_runner):
    eval_res = eval_runner.run_full_evaluation()
    metrics = eval_res["summary_metrics"]

    assert metrics["total_cases"] >= 10
    assert metrics["overall_pass_rate"] == 100.0
    assert metrics["recall"] == 100.0
    assert metrics["false_positive_rate"] == 0.0
    assert metrics["false_negative_rate"] == 0.0
    assert metrics["mean_latency_ms"] < 10.0


def test_comparative_baselines_evaluation(eval_runner):
    baselines = eval_runner.run_comparative_baselines()

    assert baselines["direct_unprotected_llm"]["attack_detection_rate"] == 0.0
    assert baselines["system_prompt_only"]["attack_detection_rate"] < 100.0
    assert baselines["finguard_deterministic_gateway"]["attack_detection_rate"] == 100.0


def test_policy_version_differential_testing(eval_runner):
    policy_a = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "policies", "v1_baseline_policy.yaml"))
    policy_b = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "policies", "v2_strict_policy.yaml"))

    comp = eval_runner.compare_policy_versions(policy_a, policy_b)
    assert "policy_a" in comp
    assert "policy_b" in comp
    assert "pass_rate_delta" in comp
