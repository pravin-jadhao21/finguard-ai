# FinGuard AI: Tool & Action Firewall Specification

**Document Version**: 1.0.0  
**Domain**: Agentic LLM Tool Call Security, Parameter Alignment, & Core Banking Sandbox Execution  

---

## 1. Architectural Architecture & Boundary Isolation

The FinGuard AI **Tool & Action Firewall** acts as an inline policy security gateway intercepting model-generated tool calls before execution against core banking services.

```
[ LLM Agent Tool Call ] ----> [ Tool & Action Firewall ] ----> [ Simulated Core Banking ]
                                       |
                   +-------------------+-------------------+
                   |                   |                   |
            [ Allowlist Check ] [ Schema Validation ] [ Parameter Alignment ]
            [ Code Guard ]      [ Auth & Role Check ] [ Step-Up Approval ]
```

> [!IMPORTANT]
> **SIMULATED CORE BANKING ISOLATION**
> Core banking authorization is kept conceptually separate from AI security. The Simulated Banking Service operates exclusively on synthetic, in-memory mock ledgers with zero real money movement. The gateway provides an additional AI-specific policy checkpoint.

---

## 2. Allowed Tool Allowlist (`v1.0.0`)

All incoming tool calls must match a strict allowlist. Unknown tool names, arbitrary code execution strings, shell commands, or SQL statements are immediately rejected (`BLOCK`).

| Tool Identifier | Description | Sensitive Action | Allowed Roles |
| :--- | :--- | :--- | :--- |
| `get_demo_balance` | Fetch account balance and metadata | No | `RetailCustomer`, `WealthManager`, `ComplianceOfficer`, `Admin` |
| `get_demo_statement` | Fetch recent account transactions statement | No | `RetailCustomer`, `WealthManager`, `ComplianceOfficer`, `Admin` |
| `initiate_demo_transfer` | Initiate simulated money transfer between fake accounts | **Yes** (Requires Step-Up Approval) | `RetailCustomer`, `WealthManager`, `Admin` |

---

## 3. Mandatory Firewall Validation Pipeline

Every tool call undergoes a 6-step deterministic validation sequence prior to execution:

1. **Strict Tool Allowlist & Code Execution Guard**: Rejects unknown tool names, SQL commands (`SELECT`, `DROP`), shell commands, and code strings (`TOOL_UNAUTHORIZED_NAME_BLOCKED` / `TOOL_CODE_INJECTION_ATTEMPT_BLOCKED`).
2. **JSON Schema & Argument Constraints**: Validates required parameters, data types, value constraints (e.g. positive transfer amount), and regex patterns (`TOOL_SCHEMA_VALIDATION_FAILED`).
3. **User Authentication & Role Authorization**: Verifies authenticated `user_id` and checks if `user_role` is permitted for the specific tool (`TOOL_AUTH_CONTEXT_MISSING_BLOCKED` / `TOOL_ROLE_UNAUTHORIZED_BLOCKED`).
4. **User-Prompt vs. Parameter Consistency Check**:
   - **Amount Alignment**: Compares monetary values extracted from original user prompt against tool argument `amount`. Returns `TOOL_PARAMETER_AMOUNT_MISMATCH_BLOCKED` if inconsistent.
   - **Recipient Alignment**: Compares recipient account IDs extracted from original user prompt against tool argument `to_account_id`. Returns `TOOL_PARAMETER_RECIPIENT_MISMATCH_BLOCKED` if inconsistent.
5. **Sensitive Action Step-Up Approval**: Tools flagged as `is_sensitive` (e.g. `initiate_demo_transfer`) require `step_up_authenticated=True` or a valid `approval_token`. If absent, triggers `ESCALATE` with `TOOL_APPROVAL_REQUIRED_ESCALATED`.
6. **Simulated Sandbox Execution**: If all checks pass (`ALLOW`), executes the call against `SimulatedBankingService` and returns execution results.

---

## 4. Reason Codes Reference

| Reason Code | Action | Trigger Condition |
| :--- | :--- | :--- |
| `TOOL_VALIDATION_PASSED` | `ALLOW` | All schema, parameter alignment, authorization, and approval checks passed. |
| `TOOL_UNAUTHORIZED_NAME_BLOCKED` | `BLOCK` | Requested tool name is not in the strict allowlist. |
| `TOOL_CODE_INJECTION_ATTEMPT_BLOCKED` | `BLOCK` | SQL, shell, or code strings detected in tool name or arguments. |
| `TOOL_SCHEMA_VALIDATION_FAILED` | `BLOCK` | Missing required parameters, type mismatch, or constraint violation. |
| `TOOL_AUTH_CONTEXT_MISSING_BLOCKED` | `BLOCK` | User authentication context missing or unauthenticated. |
| `TOOL_ROLE_UNAUTHORIZED_BLOCKED` | `BLOCK` | User role lacks permission for the requested tool. |
| `TOOL_PARAMETER_AMOUNT_MISMATCH_BLOCKED` | `BLOCK` | Tool argument `amount` conflicts with amount requested in prompt. |
| `TOOL_PARAMETER_RECIPIENT_MISMATCH_BLOCKED` | `BLOCK` | Tool argument `to_account_id` conflicts with recipient requested in prompt. |
| `TOOL_APPROVAL_REQUIRED_ESCALATED` | `ESCALATE` | Sensitive action requested without required step-up authorization or token. |
