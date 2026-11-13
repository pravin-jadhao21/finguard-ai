# FinGuard AI: Non-Functional Requirements (NFR) Specification

**Document Version**: 1.0.0  
**Quality Model Standard**: ISO/IEC 25010 System Quality Requirements  

---

## 1. Performance & Latency Budgets

In high-frequency BFSI application environments, security proxies must not introduce palpable latency delays. FinGuard AI imposes strict performance targets:

### 1.1 Latency Budgets (per Request)

| Pipeline Phase | Target P50 Latency | Target P95 Latency | Target P99 Latency | Maximum Allocation |
| :--- | :--- | :--- | :--- | :--- |
| **Inbound Sanitization & Normalization** | 0.5 ms | 1.0 ms | 1.5 ms | 2.0 ms |
| **Sensitive Data Inspection (PII/PCI)** | 1.2 ms | 2.5 ms | 3.5 ms | 4.0 ms |
| **Prompt Injection Trie Matching** | 0.8 ms | 1.5 ms | 2.0 ms | 2.5 ms |
| **Financial Advice & Boundary Rules** | 0.5 ms | 1.0 ms | 1.5 ms | 2.0 ms |
| **Risk Scoring & State Evaluation** | 0.2 ms | 0.4 ms | 0.5 ms | 1.0 ms |
| **Outbound Data Leak Scan** | 1.0 ms | 2.0 ms | 3.0 ms | 3.5 ms |
| **TOTAL GATEWAY OVERHEAD** | **< 4.2 ms** | **< 8.4 ms** | **< 10.0 ms** | **15.0 ms Max** |

*Note: Latency targets measured on single-core Intel Xeon / AMD EPYC 2.5GHz CPU for 16KB payload size.*

### 1.2 Throughput & Scalability
- **Single Instance Capacity**: A single FinGuard AI gateway process instance MUST process a minimum of **2,500 requests per second (RPS)** per CPU core.
- **Linear Scaling**: The gateway MUST exhibit near-linear horizontal scaling characteristics ($> 92\%$ efficiency) when deployed behind standard load balancers across multi-core container nodes.
- **Resource Utilization**: Peak CPU utilization must remain $< 75\%$ under 2,000 RPS burst load. Memory usage MUST be bounded to $< 256\text{ MB}$ static RSS under steady-state baseline.

---

## 2. Reliability, Availability & Resiliency

### 2.1 Availability SLA
- **Target Uptime**: **99.999% ("Five Nines")** availability for the gateway sidecar service, representing $< 5.26$ minutes of unscheduled downtime per year.

### 2.2 Fault Tolerance & Circuit Breakers
- **Fail-Closed Default**: If an internal error, unhandled exception, or memory allocation failure occurs in any component, the gateway MUST immediately issue an HTTP 500 / 403 response with policy decision `DENY`.
- **ReDoS Protection Circuit Breaker**: Regular expression evaluations MUST be executed with a strict execution deadline of **1.5 milliseconds** per pattern execution. If an execution exceeds this deadline, the worker thread MUST abort regex processing, register a pattern timeout event, and escalate policy decision to `DENY`.
- **Upstream Connection Resiliency**: The gateway must implement TCP keep-alives, connection pooling, and exponential backoff retry algorithms for transient network faults between gateway and upstream LLM.

---

## 3. Security, Privacy & Isolation

### 3.1 Zero-AI Security Autonomy
- **Strict Prohibition**: FinGuard AI MUST NOT issue requests to external machine learning endpoints, cloud classification APIs, or secondary LLM instances to determine security or policy outcomes. 100% of policy evaluations MUST remain local and deterministic.

### 3.2 Memory & Execution Safety
- **Memory Safety**: Core engine code MUST be implemented using memory-safe programming constructs (e.g., Rust / Go memory guarantees) to prevent buffer overflows, use-after-free, or dangling pointer vulnerabilities.
- **Process Isolation**: The gateway MUST run as a non-root, low-privilege system daemon within container environments (`uid:gid = 10001:10001`), operating inside a read-only root filesystem.

### 3.3 Data Privacy & Zero-PII Persistence
- **Zero-PII Storage**: Under no circumstances shall raw, unmasked PII or PCI-DSS cardholder data be written to disk, stored in memory caches, or emitted into log streams.
- **Format-Preserving Encryption / Masking**: All PII detected at ingress MUST be masked in-memory before payload serialization.

---

## 4. Observability & Auditability

### 4.1 Telemetry & Metrics
- **Prometheus Metrics**: Expose standardized metrics on `/metrics` endpoint:
  - `finguard_requests_total{status, decision}`: Counter of total processed requests.
  - `finguard_latency_seconds_bucket`: Histogram of request latency broken down by pipeline phase.
  - `finguard_rule_hits_total{rule_id, category}`: Counter of individual policy rule triggers.
  - `finguard_active_policy_version`: Gauge displaying current loaded policy semantic version.

### 4.2 Audit Logging Standard
- **Format**: Structured JSON lines (JSONL).
- **Mandatory Fields**:
  - `timestamp`: ISO 8601 UTC timestamp with microsecond precision.
  - `trace_id`: W3C compliant trace identifier (`0af7651916cd43dd8448eb211c80319c`).
  - `client_id` / `user_role`: Anonymous identifier and client role.
  - `input_hash`: SHA-256 hex digest of raw incoming prompt.
  - `sanitized_hash`: SHA-256 hex digest of masked prompt forwarded to LLM.
  - `rules_triggered`: Array of triggered rule IDs and assigned risk weights.
  - `risk_score`: Total aggregated risk score.
  - `policy_decision`: `ALLOW` | `MASK` | `REWRITE` | `ESCALATE_TO_HUMAN` | `DENY`.
  - `gateway_latency_ms`: Total execution latency in milliseconds.

---

## 5. Maintainability & Extensibility

### 5.1 Rule Configuration Standard
- **Declarative Rule Format**: Policy rules MUST be specified in human-readable, declarative YAML or JSON files.
- **Rule Hot-Reloading**: The engine MUST support zero-downtime hot-reloading of policy rule files via `SIGHUP` signal or admin API invocation. Active in-flight requests MUST complete using the prior policy version while new requests utilize the newly loaded policy.

### 5.2 Testability & Determinism Verification
- **100% Reproducibility**: Given identical input strings and policy configuration files, the gateway MUST produce identical outputs, risk scores, log digests, and decisions across different operating environments and platform architectures.
