# FinGuard AI: Deterministic Security & Policy Enforcement Gateway for BFSI

## 1. Executive Summary
**FinGuard AI** is an enterprise-grade, deterministic security and policy enforcement gateway designed specifically for Large Language Model (LLM) deployments within Banking, Financial Services, and Insurance (BFSI) applications. 

As financial institutions rapidly adopt generative AI for customer support, wealth advisory assistance, internal knowledge discovery (RAG), and back-office process automation, they face unprecedented security, regulatory, and operational risks. Standard guardrail solutions often rely on secondary LLMs or cloud-based AI classification models. In a BFSI context, secondary AI guardrails introduce severe vulnerabilities: non-deterministic security outcomes, high latency penalties (100ms–1000ms+), recursive prompt injection susceptibility, unexpected API costs, and compliance auditing challenges.

FinGuard AI eliminates secondary AI dependencies by implementing a **100% deterministic security pipeline**. Utilizing high-performance rule engines, regular expression tries, abstract syntax tree (AST) parsers, token-level analyzers, dictionary matchers (Aho-Corasick), and cryptographically signed policy structures, FinGuard AI evaluates every inbound prompt and outbound LLM response against strict financial compliance and security rules in under 10 milliseconds.

---

## 2. Project Objectives
- **Zero-AI Security Decisions**: Guarantee that all safety, privacy, role-based access control, tool execution boundaries, and regulatory compliance decisions are made strictly via deterministic rules, heuristics, and structured state machines.
- **Ultra-Low Overhead**: Maintain sub-10ms gateway processing overhead per transaction, enabling real-time streaming and interactive banking experiences without disrupting SLAs.
- **Strict Data Protection**: Detect and transform Personally Identifiable Information (PII), Payment Card Industry data (PCI-DSS), and sensitive financial account Identifiers (PAN, CVV, IBAN, SSN) before payloads ever reach an upstream LLM.
- **Regulatory Boundary Enforcement**: Enforce financial advisory limits (e.g., SEBI / SEC / FINRA disclaimers, prohibitions on unauthorized investment advice) deterministically.
- **Autonomous Tool Safeguards**: Enforce rigid role-based access control (RBAC), dollar-value velocity limits, dual-control workflows, and schema validation for LLM-driven function calls and financial tool executions.
- **Immutable Auditability**: Generate cryptographically structured audit logs for every request, payload transformation, rule evaluation, and policy decision to satisfy regulatory examinations (e.g., SOC2, PCI-DSS 4.0, RBI, FCA, GDPR).

---

## 3. Problem Statement & Risk Landscape in BFSI
LLM integration in financial services exposes institutions to critical failure modes:

| Threat / Risk Vector | Description in BFSI Context | Impact without FinGuard AI |
| :--- | :--- | :--- |
| **Direct & Indirect Prompt Injection** | Attackers hijack LLM execution context via prompt smuggling or malicious retrieved documents in RAG. | Unauthorized account access, system prompt exfiltration, arbitrary tool execution. |
| **PII & PCI-DSS Data Leakage** | Users or downstream RAG pipelines ingest credit card numbers, SSNs, or account numbers into model context. | Mass privacy breach, GDPR/PCI-DSS non-compliance fines, catastrophic reputation loss. |
| **Unsanctioned Financial Advice** | LLM generates specific buy/sell stock advice or tax advice without required regulatory disclaimers. | Regulatory enforcement actions (SEC/FINRA/SEBI), corporate legal liability. |
| **Over-Privileged Tool Execution** | Agentic LLMs invoke payment APIs or database queries with incorrect arguments or escalated user privileges. | Fraudulent wire transfers, unauthorized database updates, account takeover. |
| **RAG Privilege Escalation** | LLM retrieves and incorporates internal sensitive documents intended for restricted user tiers. | Insider threat exploitation, leaks of confidential financial reports or M&A data. |
| **Outbound Data Smuggling** | LLM outputs confidential system configurations, API credentials, or internal proprietary data. | Security boundary collapse, downstream compromise of infrastructure. |

---

## 4. Architectural Philosophy: The Deterministic Imperative
FinGuard AI adheres to five core security design principles:

1. **Non-AI Authority**: Security decisions must be reproducible, auditable, and mathematical. If an inputs or state matches Rule $R_i$, the system MUST deterministically produce Decision $D_i$. No secondary model probabilistic scoring is allowed for final policy decisions.
2. **Fail-Safe Defaults (Fail-Closed)**: In any error condition—such as a missing policy file, malformed payload, parsing error, or internal engine panic—the gateway defaults to `DENY` or `ESCALATE_TO_HUMAN`.
3. **Inbound & Outbound Dual Containment**: Security inspection occurs at both ingress (before LLM processing) and egress (before delivery to client).
4. **Least-Privilege Context Delivery (Permission-Aware RAG)**: Information fed to the LLM is deterministically filtered based on user identity, claims, and entitlement tokens prior to context assembly.
5. **Zero-Trust Tool Interception**: Function calls emitted by LLMs are treated as unverified user inputs and MUST pass deterministic schema, parameter range, and RBAC validation.

---

## 5. System Boundary & Explicit Scope Disclaimer

> [!IMPORTANT]
> **SIMULATION & BOUNDARY DISCLAIMER**
> 1. **Simulation Scope**: FinGuard AI operates strictly in a local sandbox simulation environment for evaluation and validation. It does **not** interface with live production core banking systems, live payment rails (ACH/SWIFT/SEPA), or real customer funds during this phase.
> 2. **Deterministic Limitations**: Deterministic rules (regex, tries, grammar parsers, character heuristics) provide robust, ultra-fast structural boundaries. However, **no deterministic rule engine can guarantee 100% detection of all natural language semantic evasions, zero-day prompt injections, or subtle linguistic circumventions** without inducing false positives.
> 3. **No Complete Hallucination Prevention**: Deterministic gateways validate structural claims, ground-truth presence, and approved source hashes, but **cannot prevent all conceptual LLM hallucinations**.
> 4. **No Turnkey Compliance Claim**: FinGuard AI is a technical gateway component. It does **not** single-handedly guarantee compliance with banking regulations (e.g., PCI-DSS, SOC2, GDPR). Institutional compliance requires broader enterprise security controls, policy governance, and operational oversight.

---

## 6. Target Audience & Stakeholders
- **Chief Information Security Officers (CISOs) & Risk Officers**: Requiring verifiable, auditable AI guardrails that comply with financial oversight bodies.
- **Enterprise Security Engineers**: Seeking ultra-low-latency API proxies with clear failure modes and zero external AI dependencies.
- **BFSI Software Architects & Developers**: Building LLM-powered conversational interfaces, wealth advisors, and back-office agents.
- **Compliance & Audit Teams**: Needing structured, tamper-evident logs mapping directly to compliance frameworks.

---

## 7. Key Capabilities Summary Matrix

| Capability Module | Deterministic Mechanism | Primary Policy Decision Output |
| :--- | :--- | :--- |
| **Inbound Request Inspector** | JSON schema parsing, delimiter sanitization, length bounds. | `ALLOW`, `DENY` |
| **PII & Sensitive Data Engine** | Regex patterns (Luhn check for credit cards, SSN, IBAN), dictionary lookup. | `MASK`, `REWRITE` |
| **Prompt Injection Shield** | Character-set analysis, delimiter smuggling rules, keyword tries, AST checks. | `DENY`, `REDIRECT` |
| **Financial Advice Guard** | Intent keyword taxonomy, regulatory rule engine, mandatory disclaimers. | `ALLOW`, `REWRITE`, `DENY` |
| **Permission-Aware RAG Filter** | Entitlement bitmap / RBAC matrix filtering on document chunks. | `ALLOW`, `MASK` |
| **Tool Execution Validator** | JSON Schema enforcement, dollar threshold check, rate limiter. | `ALLOW`, `DENY`, `ESCALATE_TO_HUMAN` |
| **Outbound Leakage Shield** | Reverse PII pattern scanning, regex payload verifier, API key patterns. | `ALLOW`, `MASK`, `DENY` |
| **Audit & Telemetry Engine** | Cryptographically hashed JSON log formatter, OpenTelemetry span exporter. | `AUDIT_RECORD` |

---

## 8. High-Level System Topology

```
                  +-----------------------------------+
                  |   Client Application / User       |
                  +-----------------------------------+
                                    |
                       Inbound Request (HTTP/gRPC)
                                    v
+-----------------------------------------------------------------------+
|                         FINGUARD AI GATEWAY                           |
|                                                                       |
|  [Inbound Sanitizer] --> [PII/PCI Masker] --> [Injection Shield]     |
|                                                     |                 |
|  [Financial Advice Guard] <-- [Permission-Aware RAG Filter]           |
|            |                                                          |
|            v                                                          |
|  +-------------------+        +----------------------------------+    |
|  | Risk & Policy     | -----> | Immutable Audit & Telemetry Log  |    |
|  | Decision Engine   |        +----------------------------------+    |
|  +-------------------+                                                |
|            |                                                          |
+------------|----------------------------------------------------------+
             | (ALLOW / MASKED Prompt)
             v
  +--------------------+               +-----------------------+
  |  Upstream LLM      | ------------> | Tool Execution Guard  |
  |  (Local/Mock/API)  |               | (Function Call Validator)
  +--------------------+               +-----------------------+
             | (LLM Response)                      |
             v                                     v
+-----------------------------------------------------------------------+
|  Outbound Response Inspection & Data Leak Shield                      |
+-----------------------------------------------------------------------+
             |
   Sanitized Response
             v
  +--------------------+
  | Client Application |
  +--------------------+
```
