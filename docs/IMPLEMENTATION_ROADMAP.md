# FinGuard AI: Implementation Roadmap & Evaluation Matrix

**Document Version**: 1.0.0  
**Project Phase**: Phase 1 Architecture & Design Baseline  

---

## 1. Execution Roadmap Overview

The implementation of FinGuard AI is structured across six sequential execution phases. Each phase establishes a verifiable architectural milestone, moving from core pipeline initialization to testing and verification against synthetic BFSI threat vectors.

```
+-----------------------------------------------------------------------------------+
| PHASE 1: Architecture, Policy Schemas & Structural Engine Setup (Current Phase)   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 2: Core Inbound Proxy, Tokenizer & PII/PCI Redaction Engine                 |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 3: Deterministic Prompt Injection Shield & Rule Trie Engine                 |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 4: Financial Advice Guard, RAG Permission & Tool Execution Validator        |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 5: Outbound Leak Shield, Immutable Audit Logging & Telemetry                |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| PHASE 6: Testing Suite, Benchmark Matrix & Local Simulation Evaluation            |
+-----------------------------------------------------------------------------------+
```

---

## 2. Phase-by-Phase Execution Details

### Phase 1: Architecture, Policy Schemas & Structural Baseline (COMPLETED)
- **Goal**: Establish technical design documents, system specs, policy schema definitions, and threat boundaries.
- **Key Deliverables**:
  - `PROJECT_OVERVIEW.md`
  - `SRS.md`
  - `ARCHITECTURE.md`
  - `FUNCTIONAL_REQUIREMENTS.md`
  - `NON_FUNCTIONAL_REQUIREMENTS.md`
  - `USE_CASES.md`
  - `IMPLEMENTATION_ROADMAP.md`
  - `THREAT_MODEL.md`

---

### Phase 2: Core Inbound Proxy & PII/PCI Redaction Engine
- **Goal**: Implement high-throughput sidecar proxy server with Unicode NFKC normalization and deterministic PII/PCI data masking.
- **Tasks**:
  - Implement HTTP REST / gRPC reverse proxy listener (`POST /v1/chat/completions`).
  - Integrate Unicode NFKC normalization parser and zero-width character stripper.
  - Implement Regex RE2 trie for PCI-DSS credit card detection paired with **Luhn checksum algorithm**.
  - Implement pattern matchers for SSN, IBAN, Tax IDs, Emails, and Phone Numbers.
  - Build format-preserving masker (`[RED_CARD_...]`, `[RED_SSN_...]`).
- **Milestone 2 Acceptance**: 100% of Luhn-valid credit card numbers masked in sub-3ms execution budget.

---

### Phase 3: Deterministic Prompt Injection Shield & Rule Trie Engine
- **Goal**: Construct Aho-Corasick multi-pattern trie matcher and AST parser for direct prompt injections and delimiter smuggling.
- **Tasks**:
  - Build Aho-Corasick dictionary compiler for injection triggers ("ignore previous instructions", "DAN mode", "system prompt reveal").
  - Implement control token detector (`<|im_start|>`, `[INST]`, `<<SYS>>`).
  - Implement entropy and encoding anomaly scanner (Base64/Hex payload injection detector).
  - Integrate Rule Weight Aggregator and State Machine decision core (`ALLOW`, `DENY`).
- **Milestone 3 Acceptance**: Blocks 100% of benchmark injection strings in policy dictionary without secondary AI calls.

---

### Phase 4: Financial Advice Guard, RAG Entitlement & Tool Validator
- **Goal**: Enforce financial advisory boundaries, permission-aware RAG context filtering, and function call boundary validation.
- **Tasks**:
  - Build Intent Taxonomy matcher for stock advice queries and regulatory disclaimer injector.
  - Implement RAG Context Chunk Entitlement matcher evaluating user claims against chunk metadata tags.
  - Implement Tool Execution Gateway with JSON Schema parser, velocity caps, and dollar transaction limiters (\$5,000 threshold).
  - Implement `ESCALATE_TO_HUMAN` decision router for threshold breaches.
- **Milestone 4 Acceptance**: Function calls exceeding \$5,000 deterministically routed to escalation state.

---

### Phase 5: Outbound Leak Shield, Immutable Audit Logging & Telemetry
- **Goal**: Add egress safety checks, cryptographically hashed telemetry logger, and Prometheus metric exporters.
- **Tasks**:
  - Build Outbound Data Leak Shield scanning LLM completions for system prompt fragments or leaked secrets.
  - Implement SHA-256 digest calculator for prompt, context, decisions, and outputs.
  - Build structured JSONL audit logger and OpenTelemetry span provider.
  - Implement hot-reloading policy engine with SemVer verification.
- **Milestone 5 Acceptance**: Audit log entries emitted for 100% of requests with zero raw PII leaks.

---

### Phase 6: Testing Suite, Benchmark Matrix & Local Simulation Evaluation
- **Goal**: Execute comprehensive benchmark testing, rule regression suites, and load testing in local simulation environment.
- **Tasks**:
  - Run synthetic test dataset containing 1,000+ prompt injection variants, PII samples, and financial queries.
  - Benchmark gateway latency (Target: P99 < 10ms) and throughput (Target: > 2,500 RPS/core).
  - Conduct failure mode testing (memory pressure, invalid regex time limits, malformed payloads).
- **Milestone 6 Acceptance**: All benchmark criteria satisfied; report generated.

---

## 3. Comprehensive Evaluation & Testing Matrix

To ensure deterministic precision, FinGuard AI relies on four evaluation layers:

| Testing Layer | Test Focus & Methodology | Target Metric / Benchmark |
| :--- | :--- | :--- |
| **1. Deterministic Rule Regression** | Unit test suite validating exact pattern matchers, Luhn checks, and AST parsers against edge case inputs. | 100% test pass rate across 500+ pattern regression cases. |
| **2. Synthetic Threat Dataset** | Batch execution of synthetic prompt injection datasets (Direct Injections, Delimiter Smuggling, System Exfiltration). | $> 95\%$ injection block rate on standard pattern dataset. |
| **3. False Positive Matrix** | Evaluating benign financial queries ("How to open a savings account?") to ensure valid requests are not misclassified. | $< 1.0\%$ false positive refusal rate on normal banking queries. |
| **4. Performance Profiling** | Load testing with `wrk` / `k6` measuring P50, P95, and P99 gateway overhead under burst load. | P99 latency $< 10\text{ ms}$; Throughput $> 2,500\text{ RPS/core}$. |

---

## 4. Dependencies, Risks & Mitigation Strategy

| Risk Factor | Impact Level | Deterministic Limitation / Root Cause | Mitigation Strategy in FinGuard AI |
| :--- | :--- | :--- | :--- |
| **Semantic Evasion of Injection Patterns** | **High** | Attackers rephrase prompt injection using novel metaphors not present in regex/trie dictionary. | Combine Aho-Corasick dictionary with character entropy heuristics, structural tag bounds, and multi-pattern rules; maintain dynamic policy updates. |
| **Regular Expression Backtracking (ReDoS)** | **High** | Malicious long payloads cause exponential regex processing time, stalling gateway. | Enforce strictly compiled linear-time regex engines (RE2 algorithm) with 1.5ms per-rule execution timeout budget. |
| **False Positive Disclaimer Over-Injection** | **Medium** | General questions incorrectly tagged as stock advice receive repetitive disclaimer text. | Refine Intent Taxonomy rules; use negative matching patterns to exclude pure definitions (e.g., "What is a bond?"). |
| **Overly Restrictive PII Masking** | **Low** | Legitimate non-sensitive numbers (e.g., transaction IDs or timestamps) misidentified as SSN or Card numbers. | Mandatory validation filters (e.g., Luhn check for card numbers, strict hyphenated formatting rules for SSNs). |
