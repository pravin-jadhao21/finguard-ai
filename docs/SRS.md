# Software Requirements Specification (SRS) for FinGuard AI

**Document Version**: 1.0.0  
**Status**: Architecture Baseline  
**Classification**: Internal Technical Specification  

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) defines the functional, structural, interface, performance, and compliance requirements for **FinGuard AI**, a deterministic security and policy enforcement gateway designed to protect LLM-powered banking and financial applications.

### 1.2 Scope
FinGuard AI sits inline between client applications (web/mobile banking apps, internal banker portals, automated agentic pipelines) and Large Language Models (LLMs). The gateway intercepts all inbound user prompts, RAG document contexts, function calling requests, and outbound LLM completions. 

The software strictly enforces security policies without relying on secondary AI models, employing deterministic algorithms including regular expression tries, Aho-Corasick pattern matchers, tokenizers, AST parsers, and static permission matrices.

### 1.3 Definitions, Acronyms, and Abbreviations
- **BFSI**: Banking, Financial Services, and Insurance.
- **LLM**: Large Language Model.
- **PII**: Personally Identifiable Information (Names, SSNs, Email Addresses, Phone Numbers).
- **PCI-DSS**: Payment Card Industry Data Security Standard (PAN, CVV, Expiry Dates).
- **RAG**: Retrieval-Augmented Generation.
- **RBAC**: Role-Based Access Control.
- **AST**: Abstract Syntax Tree.
- **Luhn Algorithm**: Formula used to validate primary account numbers (PANs) on payment cards.
- **ReDoS**: Regular Expression Denial of Service.
- **Fail-Closed**: Operational state where system failures result in blocking access/denying requests.

### 1.4 System Overview
FinGuard AI acts as a reverse security proxy. It parses payloads, executes a multi-stage deterministic inspection pipeline, logs auditable event telemetry, and controls request forwarding to upstream LLMs or human review escalation workflows.

---

## 2. General Description

### 2.1 Product Perspective
FinGuard AI operates as a self-contained microservice or sidecar proxy. It intercepts standard REST (OpenAPI/Swagger) and gRPC requests directed at LLM providers (e.g., OpenAI API standard endpoints, local Ollama/vLLM instances, enterprise gateway routers).

```
[ Banking App ] ----> [ FinGuard AI Proxy ] ----> [ LLM Engine ]
                              |
                    +---------+---------+
                    |                   |
            [ Policy Engine ]    [ Audit Store ]
```

### 2.2 Product Functions
1. **Inbound Payload Sanitization**: Structural, encoding, and delimiter validation.
2. **Sensitive Data Redaction & Masking**: Deterministic detection of PII, PCI-DSS, and account details using format-preserving tokenization or masking.
3. **Deterministic Injection Defense**: Direct and indirect prompt injection detection via pattern tries, character anomaly rules, and grammar constraints.
4. **Permission-Aware RAG Filtering**: Metadata-driven entitlement checks on document chunks prior to prompt construction.
5. **Financial Advice Guard**: Enforcing regulatory disclaimers and blocking forbidden individual investment/stock advice.
6. **Tool & Action Boundary Interception**: Schema, RBAC, dollar threshold, and velocity limit validation on function calls.
7. **Outbound Leakage Prevention**: Scanning generated completions for accidental PII leaks, system prompt snippets, or raw API keys.
8. **Deterministic Risk Assessment**: Weighted scoring system aggregating policy rule hits into actionable security directives (`ALLOW`, `MASK`, `REDIRECT`, `ESCALATE_TO_HUMAN`, `DENY`).
9. **Tamper-Evident Audit Logging**: Emitting cryptographically hashed JSON telemetry for compliance tracking.
10. **Hot-Reloadable Policy Engine**: Dynamically updating rule sets with semantic versioning without process restart.

### 2.3 User Classes and Characteristics
- **Client Application / API Consumer**: Automated software client sending user queries to the proxy.
- **Security Administrator**: Responsible for updating policy files, rule patterns, and threshold configs.
- **Compliance Officer**: Reviews audit logs, risk score reports, and human-escalation queues.
- **Human Reviewer / Operator**: Receives escalated requests requiring manual approval before tool execution or LLM dispatch.

### 2.4 Operating Environment
- **Operating System**: POSIX-compliant Linux (Ubuntu 22.04 LTS / RHEL 9+).
- **Execution Target**: Native compiled binary or containerized sidecar (Docker/Kubernetes pod container).
- **Hardware Footprint**: Minimal overhead footprint (Target: < 2 CPU cores, < 512MB RAM for gateway instance).
- **Dependencies**: No external cloud service or secondary AI service required.

### 2.5 Design and Implementation Constraints
1. **Zero Secondary AI Models**: No machine learning model or LLM may be invoked inside the security path.
2. **Sub-10ms Gateway Latency**: P99 gateway overhead must not exceed 10ms for payloads up to 32KB.
3. **ReDoS Protection**: All regular expression patterns must be compiled using linear-time regex engines (e.g., RE2 / Rust regex) to prevent regular expression denial-of-service attacks.
4. **Fail-Closed State**: Network, memory, or parsing failures must cause immediate request abort with HTTP 403 / 500 equivalent policy refusal.
5. **Simulation Sandbox**: Operating exclusively with simulated banking APIs and synthetic test data during validation.

---

## 3. External Interface Requirements

### 3.1 User & Admin Interfaces
- **Admin CLI**: Command-line tool `finguard-cli` for policy linting, policy hot-reloading, and rule testing.
- **Metrics Dashboard Endpoint**: `/metrics` exposing Prometheus-compatible metrics (total requests, rule hit counts, latency histogram, decision distribution).

### 3.2 Software Interfaces
- **Inbound Proxy Interface**:
  - `POST /v1/chat/completions`: OpenAI-compatible HTTP REST endpoint accepting JSON payloads.
  - Headers: `Authorization: Bearer <token>`, `X-User-ID`, `X-User-Role`, `X-Tenant-ID`.
- **Upstream LLM Interface**:
  - Proxy forwards sanitized payload to configurable upstream URL (e.g., `http://localhost:8080/v1/chat/completions` or mock provider).
- **Audit Logging Interface**:
  - `STDOUT` structured JSON or file sink `/var/log/finguard/audit.jsonl`.

---

## 4. System Attributes & Non-Functional Requirements Summary

| Attribute | Requirement Specification |
| :--- | :--- |
| **Performance** | Ingest processing latency < 5ms (P50), < 10ms (P99). |
| **Throughput** | Minimum 1,000 requests/second per core. |
| **Memory Footprint** | Static memory usage < 256MB under baseline load. |
| **Availability** | 99.999% uptime for sidecar proxy container. |
| **Safety** | Memory safety guaranteed (Rust / Go implementation standard). |

---

## 5. Security & Regulatory Compliance Mapping

| Regulatory / Security Standard | Standard Requirement | FinGuard AI Technical Mechanism |
| :--- | :--- | :--- |
| **PCI-DSS 4.0 (Req 3.4 & 4.2)** | Protect primary account numbers (PAN) wherever stored or transmitted. | Deterministic Luhn algorithm + regex detection; formats PAN to `XXXX-XXXX-XXXX-1234` prior to LLM submission. |
| **GDPR (Article 32 & 5)** | Security of processing; Data Minimization. | PII Masking Engine redacting names, SSNs, phone numbers, and addresses at ingress. |
| **SOC2 Type II (Trust Principles)** | Confidentiality, Processing Integrity, Security. | Cryptographic structured log entries containing hash of raw request, rule hit trail, and decision code. |
| **SEBI / SEC / FINRA** | Prohibition of unauthorized automated investment advice. | Financial Advice Guard enforcing rule-based disclaimers and blocking unsanctioned stock recommendations. |
| **NIST AI Risk Management Framework** | AI System Safety, Trustworthiness, Transparency. | Deterministic, fully reproducible security policy execution with clear human escalation pathways. |
