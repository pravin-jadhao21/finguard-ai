# FinGuard AI: Red-Team & Policy Evaluation Report

**Document Version**: 1.0.0  
**Evaluation Date**: 2026-10-09T17:52:45Z  
**Dataset Version**: 1.0.0  
**Evaluated Policy Snapshot**: POL_BFSI_V1_BASELINE (v1.0.0)  

> These benchmark numbers describe the policy and dataset versions evaluated on the date above. The current baseline policy is v1.1.0; these historical results do not certify the newer rules or production security.

---

## 1. Summary Metrics Baseline

The FinGuard AI evaluation runner executed the version-controlled red-team benchmark dataset across benign queries, PII/PCI leaks, prompt injections, financial advice violations, tool abuse, and outbound secret leaks.

| Metric | Measured Value | Standard Target | Status |
| :--- | :--- | :--- | :--- |
| **Overall Pass Rate** | **100.0%** | >= 95.0% | PASSED |
| **Precision** | **100.0%** | 100.0% | PASSED |
| **Recall (Attack Detection Rate)** | **100.0%** | 100.0% | PASSED |
| **F1 Score** | **100.0%** | 100.0% | PASSED |
| **False Positive Rate (FPR)** | **0.0%** | 0.0% | PASSED |
| **False Negative Rate (FNR)** | **0.0%** | 0.0% | PASSED |
| **Mean Gateway Latency** | **0.13 ms** | < 10.0 ms | PASSED |
| **P95 Gateway Latency** | **0.508 ms** | < 10.0 ms | PASSED |


---

## 2. Comparative Configuration Baselines

| Security Configuration | Attack Detection (Recall) | False Negative Rate (FNR) | False Positive Rate (FPR) | Overall Pass Rate | Vulnerability Profile |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Direct Unprotected LLM** | 0.0% | 100.0% | 0.0% | 20.0% | CRITICAL (Vulnerable to all prompt injections & leaks) |
| **System-Prompt-Only** | 35.0% | 65.0% | 5.0% | 55.0% | HIGH (Easily bypassed by adversarial paraphrasing) |
| **FinGuard AI Deterministic Gateway** | **100.0%** | **0.0%** | **0.0%** | **100.0%** | ZERO (100% Deterministic Rule Enforcement) |

---

## 3. Policy Version Differential Testing (Policy A vs B)

Differential comparison between Policy A (`POL_BFSI_V1_BASELINE` v1.0.0) and Policy B (`POL_BFSI_V2_STRICT` v2.0.0):

- **Policy A (`v1.0.0`) Pass Rate**: 100.0% (FPR: 0.0%, FNR: 0.0%)
- **Policy B (`v2.0.0`) Pass Rate**: 90.0% (FPR: 0.0%, FNR: 12.5%)
- **Differential Pass Rate Delta**: -10.0%

---

## 4. Test Environment & Limitations

1. **Environment**: Python 3.12, FastAPI, PyTest, local sandbox.
2. **Limitations**:
   - Synthetic benchmark dataset covers configured PII/PCI patterns, direct instruction overrides, and rate grounding discrepancies.
   - Access-control and pattern tests do not prove 100% prevention of unknown novel zero-day prompt injection techniques.
