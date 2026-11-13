# FinGuard AI — Deterministic Security & Policy Enforcement Gateway

[![PyTest Test Suite](https://img.shields.io/badge/PyTest-93%20Passed-brightgreen)](https://pytest.org/)
[![React + Vite UI](https://img.shields.io/badge/Frontend-React%20%2B%20Vite%20%2B%20Tailwind-blue)](https://vitejs.dev/)
[![FastAPI Sidecar](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-purple)](#license)

**FinGuard AI** is an enterprise-grade, zero-LLM deterministic security and policy enforcement gateway sidecar designed specifically for Banking, Financial Services, and Insurance (BFSI) AI applications. It operates inline between user prompt submitters, LLMs, external RAG context stores, and core banking tool execution services to guarantee mathematical determinism, confidential PII/PCI masking, financial advice compliance, prompt-injection shielding, and tool parameter alignment.

---

> ⚠️ **IMPORTANT DISCLAIMER**
> FinGuard AI is an academic research & security engineering prototype designed for local simulation and sandbox evaluation.
> All account numbers (`ACC-1001`, `ACC-1002`, `ACC-1003`), transaction IDs, card numbers, and banking balances are synthetic test data.
> FinGuard AI does **NOT** perform live payment card validation or connect to real money-movement rails. Do **NOT** claim production-grade banking security or regulatory compliance without institutional audit and hardware security module (HSM) deployment.

---

## 🏛️ System Architecture

```
                                +-----------------------------------+
                                |    React + Vite Security UI       |
                                | (Dashboard, Audit, Playground)    |
                                +-----------------+-----------------+
                                                  |
                                                  v  HTTP REST API
+-------------------------------------------------+-------------------------------------------------+
|                                FINGUARD AI SECURITY GATEWAY (FastAPI)                            |
|                                                                                                   |
|  +---------------------------+  +---------------------------+  +-------------------------------+  |
|  | Inbound Data Protection   |  | Financial Intent &        |  | Deterministic Policy Engine   |  |
|  |  * Payment Card (Luhn)    |  | Prompt Injection Shield   |  |  * Precedence Matrix          |  |
|  |  * Aadhaar (Verhoeff)     |  |  * 6 Intent Categories    |  |  * BLOCK > ESCALATE > REDIRECT|  |
|  |  * Email/Phone/PAN/SSN    |  |  * System Override Shield |  |    > TOKENIZE > REDACT > ALLOW|  |
|  +-------------+-------------+  +-------------+-------------+  +---------------+---------------+  |
|                |                              |                                |                  |
|                +------------------------------+--------------------------------+                  |
|                                               |                                                   |
|  +---------------------------+  +-------------v-------------+  +-------------------------------+  |
|  | Outbound Response Enforcer|  | Secure Pre-Context RAG    |  | Tool & Action Firewall        |  |
|  |  * Rate Correction        |  |  * Access Tier Filtering  |  |  * Schema & Parameter Align   |  |
|  |  * Unsafe Claims & Secrets|  |  * Indirect Injection Scan|  |  * Simulated Banking Sandbox  |  |
|  +---------------------------+  +---------------------------+  +-------------------------------+  |
|                                               |                                                   |
|                                 +-------------v-------------+                                     |
|                                 | Immutable Audit Logger    |                                     |
|                                 | & Human Review Queue      |                                     |
|                                 +---------------------------+                                     |
+---------------------------------------------------------------------------------------------------+
```

---

## 🚀 Key Features

* **Zero-LLM Policy Engine**: Uses 100% deterministic rule evaluations (YAML-defined) with explicit action precedence hierarchy (`BLOCK [100]` > `ESCALATE [80]` > `REDIRECT [60]` > `TOKENIZE [40]` > `REDACT [20]` > `ALLOW [0]`).
* **Inbound Data Protection**: Scans incoming prompts for payment card numbers (Luhn algorithm), Aadhaar numbers (Verhoeff algorithm), SSNs, PANs, emails, phone numbers, and OTPs. Replaces sensitive candidate spans with safe placeholders without logging raw values.
* **Financial Intent & Injection Shield**: Categorizes user requests into financial intent classes (`EDUCATIONAL`, `COMPARATIVE`, `PERSONALIZED_ANALYSIS`, `PERSONALIZED_RECOMMENDATION`, `TRANSACTIONAL`, `HIGH_RISK`, `AMBIGUOUS`) and blocks direct prompt injection overrides.
* **Outbound Grounding Enforcement**: Validates LLM-generated completions against authoritative rate ledgers, injecting required regulatory disclaimers and correcting hallucinated interest rates (e.g. correcting `7.5%` to `6.5%`).
* **Tool Action Firewall**: Pre-executes schema validation, prompt-parameter alignment, and step-up auth checks for banking tool invocations (`get_demo_balance`, `get_demo_statement`, `initiate_demo_transfer`). Prevents models from executing unauthorized transactions or code execution payloads.
* **Secure Pre-Context RAG**: Filters retrieval-augmented generation context based on document classification tiers (`PUBLIC`, `INTERNAL`, `RESTRICTED_CUSTOMER`) and customer ownership boundaries before context construction.
* **Audit Logger & Human Review Queue**: Maintains structured decision logs and a simulated step-up review workflow requiring reviewer identification.

---

## 📋 Prerequisites

* **Python**: `3.12+`
* **Node.js**: `20.0+` & `npm 10.0+`
* **Docker & Docker Compose** (Optional, for containerized execution)

---

## 🛠️ Quick Start & Setup

### Option 1: Local Development Setup

#### 1. Clone & Setup Python Virtual Environment
```bash
git clone https://github.com/your-repo/finguard-ai.git
cd finguard-ai

python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

#### 2. Start Backend API Server
```bash
source .venv/bin/activate
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend API Docs will be live at*: [http://localhost:8000/docs](http://localhost:8000/docs)

#### 3. Start Frontend Dashboard
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
*Frontend Web Application will be live at*: [http://localhost:5173](http://localhost:5173)

---

### Option 2: Docker Compose Setup

```bash
docker-compose up --build -d
```
* Access Backend API: [http://localhost:8000](http://localhost:8000)
* Access Frontend UI: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Running Tests & Verification

### 1. Backend PyTest Suite (93 Unit & Integration Tests)
```bash
source .venv/bin/activate
pytest tests/ -v
```

### 2. Run Interactive Security Demonstration Script
```bash
source .venv/bin/activate
PYTHONPATH=backend python scripts/demo_scenarios.py
```

### 3. Run Red-Team Evaluation Framework Benchmark
```bash
source .venv/bin/activate
PYTHONPATH=backend python backend/app/eval/runner.py
```

### 4. Frontend Production Build Check
```bash
cd frontend
npm run build
```

---

## 📡 API Endpoint Reference & Examples

### 1. Evaluate Policy Engine
`POST /api/v1/policy/evaluate`

```bash
curl -X POST "http://localhost:8000/api/v1/policy/evaluate" \
     -H "Content-Type: application/json" \
     -d '{
           "prompt": "Tell me how interest works on savings accounts",
           "user_role": "RetailCustomer"
         }'
```
**Response**:
```json
{
  "request_id": "req-18a39b4c0d12",
  "policy_id": "pol-v1-baseline",
  "policy_version": "1.0.0",
  "decision": "ALLOW",
  "reason_code": "POLICY_ALLOW_SANCTIONED_QUERY",
  "matched_rule_id": "RULE_ALLOW_EDUCATION",
  "transformed_prompt": "Tell me how interest works on savings accounts",
  "latency_ms": 0.124
}
```

---

### 2. Inbound Data Protection
`POST /api/v1/inspect`

```bash
curl -X POST "http://localhost:8000/api/v1/inspect" \
     -H "Content-Type: application/json" \
     -d '{
           "prompt": "My credit card is 4532-0123-8594-9981.",
           "user_role": "RetailCustomer"
         }'
```
**Response**:
```json
{
  "request_id": "dp-482a1b09",
  "policy_decision": "MASK",
  "is_sanitized": true,
  "transformed_prompt": "My credit card is [RED_CARD_4532-XXXX-XXXX-9981].",
  "masked_entities": [
    {
      "candidate_type": "PAYMENT_CARD",
      "masked_span": "[RED_CARD_4532-XXXX-XXXX-9981]",
      "start_index": 18,
      "end_index": 37,
      "checksum_verified": true
    }
  ],
  "latency_ms": 0.185
}
```

---

### 3. Tool Firewall Execution & Parameter Guard
`POST /api/v1/tool/execute`

```bash
curl -X POST "http://localhost:8000/api/v1/tool/execute" \
     -H "Content-Type: application/json" \
     -d '{
           "tool_name": "initiate_demo_transfer",
           "arguments": {
             "from_account_id": "ACC-1001",
             "to_account_id": "ACC-1002",
             "amount": 500.0
           },
           "user_prompt": "Transfer $500 to ACC-1002",
           "user_context": {
             "user_id": "USR-1001",
             "user_role": "RetailCustomer",
             "step_up_authenticated": true
           }
         }'
```
**Response**:
```json
{
  "request_id": "tool-7c89f1a23b01",
  "action_decision": "ALLOW",
  "reason_code": "TOOL_VALIDATION_PASSED",
  "tool_name": "initiate_demo_transfer",
  "execution_success": true,
  "result": {
    "status": "COMPLETED",
    "transaction_id": "TXN-8A91F2C3",
    "from_account_id": "ACC-1001",
    "to_account_id": "ACC-1002",
    "amount": 500.0,
    "remaining_balance": 9500.0
  },
  "latency_ms": 0.412
}
```

---

## ⚠️ Known Limitations & Boundaries

1. **Checksum Heuristics**: Luhn and Verhoeff algorithm matches validate numeric format structure only; they do not verify live card issuing bank records.
2. **Deterministic Rate Checking**: Outbound rate comparisons rely on structured lookup ledgers for configured deposit products. Free-text financial reasoning is not verified by string comparison.
3. **Simulated Sandbox**: All core banking balance ledgers (`ACC-1001`, `ACC-1002`, `ACC-1003`) are in-memory synthetic objects. No real funds or APIs are connected.

---

## 🛠️ Troubleshooting Guide

* **CORS Error in Frontend**: Ensure backend is running at `http://localhost:8000` and `CORS_ORIGINS` in `.env` includes `http://localhost:5173`.
* **Port 8000/5173 Already in Use**: Kill existing processes using `fuser -k 8000/tcp` and `fuser -k 5173/tcp`.
* **ModuleNotFoundError on Execution**: Make sure you have activated `.venv` and included `PYTHONPATH=backend` when executing standalone scripts outside `pytest`.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
