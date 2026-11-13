# FinGuard AI: Functional Requirements Specification

**Document Version**: 1.0.0  
**Specification Standard**: Enterprise Deterministic Security Baseline  

---

## 1. Overview & Classification Matrix

Requirements are divided into two distinct tiers:
1. **Mandatory Features (MVP)**: Core security capabilities required for operational baseline.
2. **Optional Extensions (Phase 2+)**: Advanced capability modules for enterprise scale and multi-tenant RAG architectures.

Every feature specification explicitly details: **Purpose**, **Inputs**, **Outputs**, **Policy Decisions**, **Failure Cases**, and **Acceptance Criteria**.

---

## 2. Mandatory Features (MVP)

### FR-1.1: Inbound Payload Sanitization & Encoding Normalization
- **Purpose**: Normalize raw user request text, remove character obfuscation tricks (homoglyphs, invisible zero-width spaces), enforce body size constraints, and parse JSON structures.
- **Inputs**: Raw HTTP Request (Headers, Body JSON string).
- **Outputs**: Normalized Prompt String, Cleaned JSON Payload object.
- **Policy Decisions**:
  - `ALLOW`: Payload is structurally valid, within size limits, and properly encoded.
  - `DENY`: Payload exceeds maximum size (e.g., > 64KB), contains invalid UTF-8 sequences, or malformed JSON syntax.
- **Failure Cases**:
  - Deeply nested recursive JSON objects designed to cause parser stack overflow.
  - Mixed encoding payloads combining UTF-8, UTF-16, and URL encoding tricks.
- **Acceptance Criteria**:
  - 100% of incoming prompts are converted to Unicode NFKC normalized form before downstream analysis.
  - Malformed JSON requests return HTTP 400 Bad Request within < 1ms without invoking downstream rules.

---

### FR-1.2: Sensitive Data Detection & Transformation (PII / PCI-DSS / Accounts)
- **Purpose**: Detect credit card numbers (PAN), CVVs, Social Security Numbers (SSN), International Bank Account Numbers (IBAN), email addresses, and phone numbers in prompts, replacing them with deterministic format-preserving masks.
- **Inputs**: Normalized Prompt String.
- **Outputs**: Redacted Prompt String, Data Transformation Metadata (count and categories of masked items).
- **Policy Decisions**:
  - `MASK`: Sensitive patterns detected; prompt sanitized with replacement masks and forwarded.
  - `ALLOW`: No sensitive data detected; prompt forwarded unchanged.
  - `DENY`: Payload contains raw CVV/CVC codes or unencrypted PINs (zero-tolerance threshold).
- **Failure Cases**:
  - Spaced or punctuated numbers attempting to obfuscate card strings (e.g., `4111 - 1111 - 1111 - 1111`).
  - Numbers mimicking credit cards that fail the Luhn checksum (false positives).
- **Acceptance Criteria**:
  - 100% detection rate for valid Luhn-passing 13-19 digit card numbers.
  - Valid SSN (`XXX-XX-XXXX`) and IBAN formats masked with `[RED_SSN_...]` and `[RED_IBAN_...]`.
  - Processing overhead < 2ms for 4KB text payload.

---

### FR-1.3: Deterministic Direct Prompt Injection Detection
- **Purpose**: Detect attempts to hijack the LLM execution context, override system instructions, or force developer mode.
- **Mechanism**: Aho-Corasick keyword trie matching + exact structural pattern heuristics.
- **Inputs**: Normalized Prompt String.
- **Outputs**: Rule Trigger Match List, Injection Risk Score.
- **Policy Decisions**:
  - `DENY`: High-confidence injection trigger detected (e.g., "ignore previous instructions", "you are now DAN", "system prompt reveal").
  - `ALLOW`: No injection patterns matched.
- **Failure Cases**:
  - Legitimate user queries containing similar words (e.g., "Can I ignore the previous transaction receipt?").
  - Novel semantic phrasing bypassing exact keyword patterns (inherent deterministic limitation).
- **Acceptance Criteria**:
  - Detects 100% of benchmark injection keywords defined in the active policy file.
  - Zero downstream execution of LLM when high-confidence injection pattern is matched.

---

### FR-1.4: Indirect Prompt Injection & Delimiter Smuggling Shield
- **Purpose**: Block malicious control sequences or pseudo-formatting tags embedded in prompt text or retrieved documents that attempt to close system prompt boundaries.
- **Inputs**: Prompt payload, RAG document context strings.
- **Outputs**: Sanitized Context String, Delimiter Breach Alert.
- **Policy Decisions**:
  - `DENY`: Payload contains illegal control tokens (e.g., `<|im_start|>`, `[INST]`, `<<SYS>>`, `<|endoftext|>`).
  - `REWRITE`: Strips illegal pseudo-XML tags (`<system_override>`, `<admin>`) and proceeds with warning.
- **Failure Cases**:
  - User asking questions about prompt engineering syntax in legitimate support contexts.
- **Acceptance Criteria**:
  - Intercepts and strips 100% of defined LLM control tokens across OpenAI, Anthropic, Llama, and Mistral formats.

---

### FR-1.5: Financial Advice Boundary & Regulatory Disclaimer Guard
- **Purpose**: Block unauthorized requests for specific stock trading picks or personalized tax strategies, and automatically inject required statutory disclaimers for general financial queries.
- **Inputs**: Normalized Prompt String, Outbound LLM Response String.
- **Outputs**: Final Response String (with injected disclaimers if required), Policy Decision Record.
- **Policy Decisions**:
  - `DENY`: User requests explicit illegal/unauthorized financial recommendations (e.g., "Which specific penny stock should I buy today for guaranteed 100% profit?").
  - `REWRITE`: Ingest general financial query (e.g., "How do index funds work?"), forward to LLM, and inject mandatory SEBI/SEC disclaimer to output.
  - `ALLOW`: General non-financial conversation.
- **Failure Cases**:
  - Metaphorical or indirect financial queries misclassified as specific stock requests.
- **Acceptance Criteria**:
  - Mandatory disclaimer ("*Disclaimer: Information provided is for educational purposes only and does not constitute financial or investment advice.*") appended to 100% of responses tagged with financial category rules.

---

### FR-1.6: Tool Execution Validation & Transaction Dollar Thresholds
- **Purpose**: Intercept LLM function call requests (tool calls) and enforce JSON Schema validation, role-based execution rights, dollar transaction limits, and velocity caps.
- **Inputs**: LLM Output Tool Call JSON (Function Name, Arguments), User Context (`UserRole`, `AccountBalance`).
- **Outputs**: Validated Function Call, Execution Authorization Status.
- **Policy Decisions**:
  - `ALLOW`: Function parameters match schema, user has RBAC rights, transaction amount $\le$ single-tx threshold, and velocity cap not exceeded.
  - `DENY`: Invalid parameter type, unauthorized function for user role, or velocity cap exceeded.
  - `ESCALATE_TO_HUMAN`: Transaction amount exceeds dollar threshold (e.g., Amount > \$5,000) requiring step-up auth or human review.
- **Failure Cases**:
  - Malformed JSON arguments generated by LLM (e.g., string passed for integer balance field).
- **Acceptance Criteria**:
  - Blocks 100% of tool executions failing JSON Schema parameter checks.
  - Any transfer exceeding \$5,000 triggers `ESCALATE_TO_HUMAN` decision state.

---

### FR-1.7: Outbound LLM Response Inspection & Data Leak Shield
- **Purpose**: Scan LLM-generated completions before delivering to client to prevent exfiltration of internal system prompts, database connection strings, API keys, or raw PII.
- **Inputs**: Raw LLM Response Completion Text.
- **Outputs**: Sanitized Response Text, Data Leak Alert Metadata.
- **Policy Decisions**:
  - `ALLOW`: Completion contains no sensitive system information or raw PII.
  - `MASK`: Completion contains PII generated by LLM; redacts PII and returns.
  - `DENY`: Completion contains system prompt fragments, private keys (`-----BEGIN RSA PRIVATE KEY-----`), or AWS/database credentials.
- **Failure Cases**:
  - Partial matches on code snippets generated for legitimate developer questions.
- **Acceptance Criteria**:
  - 100% blocking of completions containing detected secret keys or exact system prompt string sequences.

---

### FR-1.8: Deterministic Weighted Risk Scoring & Policy Decision Engine
- **Purpose**: Aggregate rule evaluations from all pipeline modules and execute a deterministic state machine to issue the unified policy decision.
- **Inputs**: Array of Triggered Rule Violations $[R_1, R_2, \dots, R_k]$ with weights $[w_1, w_2, \dots, w_k]$.
- **Outputs**: Total Cumulative Risk Score, Final Policy Decision (`ALLOW`, `MASK`, `REWRITE`, `ESCALATE_TO_HUMAN`, `DENY`).
- **Policy Decisions**:
  - State Machine Matrix:
    - Score $0 - 9$: `ALLOW`
    - Score $10 - 29$: `MASK`
    - Score $30 - 59$: `REWRITE`
    - Score $60 - 89$: `ESCALATE_TO_HUMAN`
    - Score $\ge 90$: `DENY`
- **Failure Cases**:
  - Conflicting rule weights resulting in unexpected edge-case score boundary.
- **Acceptance Criteria**:
  - Identical input rule arrays MUST produce 100% identical risk scores and policy decision outputs across execution runs.

---

### FR-1.9: Immutable Audit Trail & Telemetry Logging
- **Purpose**: Record cryptographically hashed, structured audit events for every transaction to enable non-repudiation and compliance reporting.
- **Inputs**: Request Context, Sanitized Prompt Digest, Rule Trigger Records, Policy Decision, Timestamp.
- **Outputs**: Immutable JSON Audit Log Entry.
- **Policy Decisions**:
  - `AUDIT_RECORD`: Emits log line for every processed request regardless of decision.
- **Failure Cases**:
  - Disk full or stdout pipe backpressure.
- **Acceptance Criteria**:
  - Log line includes SHA-256 hash of original input, SHA-256 hash of output, execution latency, and exact rule trigger IDs.
  - Zero unmasked PII printed to audit logs.

---

### FR-1.10: Dynamic Policy Loading & SemVer Versioning
- **Purpose**: Update active policy rule definitions dynamically without restarting the gateway process.
- **Inputs**: Signed Policy YAML/JSON File, Policy Hash, Version Number.
- **Outputs**: Policy Load Status, Active Policy Version Metric.
- **Policy Decisions**:
  - `ALLOW`: Policy signature valid and SemVer compatible; atomic RCU update executed.
  - `DENY`: Policy signature invalid or malformed YAML syntax; retains active policy version.
- **Failure Cases**:
  - Corrupted policy file upload during hot-reload.
- **Acceptance Criteria**:
  - Policy reloaded in memory within < 50ms without dropping active network requests.

---

### FR-1.11: Fail-Safe Defaults & Circuit Breaker Engine
- **Purpose**: Enforce a strict fail-closed security posture if any pipeline module panics, times out, or encounters unexpected exceptions.
- **Inputs**: Exception State, Timeout Signal, Memory Exhaustion Event.
- **Outputs**: HTTP 500/403 Failure Payload, Emergency System Log.
- **Policy Decisions**:
  - `DENY`: All execution halts; client receives standardized security refusal response.
- **Failure Cases**:
  - Gateway thread crash during high-concurrency burst.
- **Acceptance Criteria**:
  - Under no circumstances does an unhandled exception result in bypassing security checks or forwarding uninspected prompts to the upstream LLM.

---

## 3. Optional Extensions (Phase 2+)

### FR-2.1: Permission-Aware RAG Context Filtering & Entitlement Matcher
- **Purpose**: Filter retrieved vector database document chunks based on user entitlement tokens prior to constructing the LLM prompt.
- **Inputs**: Vector Search Result Chunks (with metadata attributes), User Entitlement Matrix.
- **Outputs**: Filtered RAG Context Array.
- **Policy Decisions**:
  - `ALLOW`: Chunks matching user security level retained.
  - `MASK`: Chunks failing entitlement checks removed from prompt context.
- **Failure Cases**:
  - Missing metadata tags on ingested RAG chunks defaulting to unrestricted access (Mitigation: mandatory metadata schema check).
- **Acceptance Criteria**:
  - 100% of chunks lacking matching user role attributes are excluded from LLM context payload.

---

### FR-2.2: Dual-Control / Human-in-the-Loop Escalation Routing
- **Purpose**: Route high-risk requests or transactions exceeding financial thresholds to an external human review portal.
- **Inputs**: Escalated Policy Request Payload, Risk Score.
- **Outputs**: Asynchronous Ticket Object, Queue Notification.
- **Policy Decisions**:
  - `ESCALATE_TO_HUMAN`: Request held in pending state until human sign-off token received.
- **Failure Cases**:
  - Human review timeout (Default action: `DENY` after 15 minutes).
- **Acceptance Criteria**:
  - Escalated transactions successfully queued with full audit trace.

---

### FR-2.3: Approved Source & Fact-Attribution Hash Verifier
- **Purpose**: Verify that facts or claims cited in LLM output match pre-approved knowledge base source hashes.
- **Inputs**: LLM Output Citations, Document Hash Table.
- **Outputs**: Verification Score, Attribution Status.
- **Policy Decisions**:
  - `ALLOW`: Citations match approved source hashes.
  - `REWRITE`: Unverified citations flagged with warning banner.
- **Failure Cases**:
  - Hallucinated source URLs generated by LLM.
- **Acceptance Criteria**:
  - Detects and flags ungrounded URLs or fake source references.

---

### FR-2.4: Cryptographic Audit Trail with Merkle-Tree Proofs
- **Purpose**: Construct append-only Merkle tree roots of audit log blocks for cryptographic proof of history.
- **Inputs**: Audit Event Records stream.
- **Outputs**: Merkle Tree Root Hashes written to immutable storage.
- **Policy Decisions**: `AUDIT_RECORD`.
- **Acceptance Criteria**:
  - Mathematical proof of log integrity verifiable via CLI tool.
