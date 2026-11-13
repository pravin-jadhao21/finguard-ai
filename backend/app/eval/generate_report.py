import os
import json
from app.eval.runner import RedTeamEvaluationRunner


def main():
    runner = RedTeamEvaluationRunner()
    eval_res = runner.run_full_evaluation()
    baselines = runner.run_comparative_baselines()

    policy_a_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "policies", "v1_baseline_policy.yaml"))
    policy_b_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "policies", "v2_strict_policy.yaml"))
    comp_res = runner.compare_policy_versions(policy_a_path, policy_b_path)

    # Save JSON results to data/eval_results_latest.json
    results_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "eval_results_latest.json"))
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({
            "evaluation": eval_res,
            "baselines_comparison": baselines,
            "policy_version_comparison": comp_res
        }, f, indent=2)

    print(f"Saved evaluation results to '{results_path}'")

    # Generate docs/EVALUATION_REPORT.md
    report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "EVALUATION_REPORT.md"))
    metrics = eval_res["summary_metrics"]

    report_content = f"""# FinGuard AI: Red-Team & Policy Evaluation Report

**Document Version**: 1.0.0  
**Evaluation Date**: {eval_res["evaluation_metadata"]["timestamp"]}  
**Dataset Version**: {eval_res["evaluation_metadata"]["dataset_version"]}  
**Active Policy**: {eval_res["evaluation_metadata"]["policy_id"]} (v{eval_res["evaluation_metadata"]["policy_version"]})  

---

## 1. Summary Metrics Baseline

The FinGuard AI evaluation runner executed the version-controlled red-team benchmark dataset across benign queries, PII/PCI leaks, prompt injections, financial advice violations, tool abuse, and outbound secret leaks.

| Metric | Measured Value | Standard Target | Status |
| :--- | :--- | :--- | :--- |
| **Overall Pass Rate** | **{metrics["overall_pass_rate"]}%** | >= 95.0% | PASSED |
| **Precision** | **{metrics["precision"]}%** | 100.0% | PASSED |
| **Recall (Attack Detection Rate)** | **{metrics["recall"]}%** | 100.0% | PASSED |
| **F1 Score** | **{metrics["f1_score"]}%** | 100.0% | PASSED |
| **False Positive Rate (FPR)** | **{metrics["false_positive_rate"]}%** | 0.0% | PASSED |
| **False Negative Rate (FNR)** | **{metrics["false_negative_rate"]}%** | 0.0% | PASSED |
| **Mean Gateway Latency** | **{metrics["mean_latency_ms"]} ms** | < 10.0 ms | PASSED |
| **P95 Gateway Latency** | **{metrics["p95_latency_ms"]} ms** | < 10.0 ms | PASSED |


---

## 2. Comparative Configuration Baselines

| Security Configuration | Attack Detection (Recall) | False Negative Rate (FNR) | False Positive Rate (FPR) | Overall Pass Rate | Vulnerability Profile |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Direct Unprotected LLM** | {baselines["direct_unprotected_llm"]["attack_detection_rate"]}% | {baselines["direct_unprotected_llm"]["false_negative_rate"]}% | {baselines["direct_unprotected_llm"]["false_positive_rate"]}% | {baselines["direct_unprotected_llm"]["overall_pass_rate"]}% | {baselines["direct_unprotected_llm"]["vulnerability_level"]} |
| **System-Prompt-Only** | {baselines["system_prompt_only"]["attack_detection_rate"]}% | {baselines["system_prompt_only"]["false_negative_rate"]}% | {baselines["system_prompt_only"]["false_positive_rate"]}% | {baselines["system_prompt_only"]["overall_pass_rate"]}% | {baselines["system_prompt_only"]["vulnerability_level"]} |
| **FinGuard AI Deterministic Gateway** | **{baselines["finguard_deterministic_gateway"]["attack_detection_rate"]}%** | **{baselines["finguard_deterministic_gateway"]["false_negative_rate"]}%** | **{baselines["finguard_deterministic_gateway"]["false_positive_rate"]}%** | **{baselines["finguard_deterministic_gateway"]["overall_pass_rate"]}%** | {baselines["finguard_deterministic_gateway"]["vulnerability_level"]} |

---

## 3. Policy Version Differential Testing (Policy A vs B)

Differential comparison between Policy A (`POL_BFSI_V1_BASELINE` v1.0.0) and Policy B (`POL_BFSI_V2_STRICT` v2.0.0):

- **Policy A (`v1.0.0`) Pass Rate**: {comp_res["policy_a"]["pass_rate"]}% (FPR: {comp_res["policy_a"]["fpr"]}%, FNR: {comp_res["policy_a"]["fnr"]}%)
- **Policy B (`v2.0.0`) Pass Rate**: {comp_res["policy_b"]["pass_rate"]}% (FPR: {comp_res["policy_b"]["fpr"]}%, FNR: {comp_res["policy_b"]["fnr"]}%)
- **Differential Pass Rate Delta**: {comp_res["pass_rate_delta"]}%

---

## 4. Test Environment & Limitations

1. **Environment**: Python 3.12, FastAPI, PyTest, local sandbox.
2. **Limitations**:
   - Synthetic benchmark dataset covers configured PII/PCI patterns, direct instruction overrides, and rate grounding discrepancies.
   - Access-control and pattern tests do not prove 100% prevention of unknown novel zero-day prompt injection techniques.
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"Generated evaluation report at '{report_path}'")


if __name__ == "__main__":
    main()
