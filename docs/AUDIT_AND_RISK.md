# FinGuard AI: Risk Assessment, Audit Logging, Policy Versioning, & Simulated Human Review

**Document Version**: 1.0.0  
**Domain**: Risk Scoring, Policy Version Traceability, Decision Explainability, & Human Review Workflows  

---

## 1. Configurable Risk Assessment Engine

FinGuard AI evaluates contextual risk factors independently from deterministic policy enforcement.

```
[ Request Context ] ----> [ Policy Engine ] ----------> [ Action Decision (ALLOW/BLOCK/etc.) ]
        |                                                              |
        +---------------> [ Risk Assessment Engine ] ---> [ Advisory Risk Score & Triggers ]
```

> [!IMPORTANT]
> **RISK SCORING DECOUPLING RULE**
> Risk scoring evaluates advisory metrics (0.0 to 100.0) based on intent categories, sensitivity tiers, prompt injection flags, rate discrepancies, and monetary transfer amounts. **High risk alone does NOT silently override explicit policy decisions.** High-risk transactions add risk metadata to audit traces and enqueue tickets into the simulated human-review queue without altering deterministic policy evaluation.

### Risk Factor Weights & Thresholds

| Risk Factor | Trigger Condition | Points |
| :--- | :--- | :--- |
| **Intent Category** | `HIGH_RISK` | +40 pts |
| **Intent Category** | `TRANSACTIONAL` | +30 pts |
| **Data Sensitivity** | `CRITICAL_PCI` (Card data) | +35 pts |
| **Data Sensitivity** | `CRITICAL_PII` (SSN/Aadhaar) | +25 pts |
| **Security Threat** | Prompt injection attempt detected | +50 pts |
| **Security Threat** | Secret API key leak detected | +40 pts |
| **Ground-Truth Discrepancy** | Hallucinated product rate detected | +25 pts |
| **Transfer Amount** | Transfer amount $\ge \$5,000$ | +35 pts |
| **Transfer Amount** | Transfer amount $\ge \$1,000$ | +20 pts |

### Risk Tiers

- **`LOW`**: 0.0 - 29.9
- **`MEDIUM`**: 30.0 - 59.9
- **`HIGH`**: 60.0 - 79.9
- **`CRITICAL`**: 80.0 - 100.0

---

## 2. Immutable Audit Logger & Decision Explainability

### Log Record Schema

Every gateway decision records structured audit fields without storing raw confidential payloads:

- `request_id`: Unique transaction correlation ID.
- `timestamp`: ISO 8601 UTC timestamp.
- `direction`: `INBOUND` or `OUTBOUND`.
- `policy_id`: Identifier of active policy file (e.g. `v1_baseline_policy`).
- `policy_version`: Exact version string loaded at evaluation time (e.g. `1.0.0`).
- `decision`: Action decision (`ALLOW`, `BLOCK`, `REDIRECT`, `REDACT`, `TOKENIZE`, `ESCALATE`).
- `reason_code`: Standardized gateway reason code.
- `matched_rule_id`: Identifier of matched policy rule (or `None`).
- `risk_metadata`: Risk score, level, and fired triggers.
- `latency_ms`: Processing latency in milliseconds.
- `fallback_active`: Boolean indicating if fail-safe backup logger was utilized.

> [!TIP]
> **ZERO CONFIDENTIAL PAYLOAD STORAGE**
> The audit logger never stores raw prompts, unmasked credit cards, SSNs, or LLM completion strings by default.

### Decision Explainability Inspection API

The `/api/v1/audit/logs/{request_id}/explain` endpoint allows compliance administrators to inspect **why** a decision occurred (matched rule ID, reason code, risk breakdown) without revealing confidential customer payload content.

### Storage Fail-Safe Behavior

If the primary audit log database experiences connection failure or disk write errors, the logger automatically redirects log entries to a local secondary backup buffer (`fallback_active=True`) without throwing uncaught exceptions or disrupting gateway request processing.

---

## 3. Simulated Human-Review Queue

High-risk requests (`HIGH` or `CRITICAL` risk) or requests assigned to human review (`ESCALATE`) are enqueued as review tickets.

- **Statuses**: `PENDING`, `APPROVED`, `REJECTED`
- **Reviewer Identity Requirement**: Every status transition from `PENDING` to `APPROVED` or `REJECTED` **strictly requires** a non-empty `reviewer_id` (e.g. `REV-USR-99`). Transition attempts without a reviewer identity raise a validation error.

> [!WARNING]
> **SIMULATED REVIEW QUEUE DISCLAIMER**  
> The review queue is a simulated sandbox demonstration feature designed for testing human-in-the-loop workflows. **It is NOT a certified banking approval workflow** and must not be used as a substitute for production core-banking maker-checker rails.
