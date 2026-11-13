import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.rag_guard import SecureRAGGuard
from app.core.rag_store import RAGDocumentStore
from app.schemas.rag import (
    RAGRequest,
    RAGUserContext,
    AccessDecision
)
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def rag_store():
    return RAGDocumentStore()


@pytest.fixture
def rag_guard(rag_store):
    return SecureRAGGuard(document_store=rag_store)


# 1. Legitimate Retrieval (Public FAQ)
def test_legitimate_retrieval_public_faq(rag_guard):
    req = RAGRequest(
        query="savings account APY",
        user_context=RAGUserContext(user_id="USR-1001", user_role="RetailCustomer")
    )
    res = rag_guard.process_rag_request(req)
    assert res.authorized_count >= 1
    assert "<retrieved_reference_documents>" in res.sanitized_context_block
    assert "DOC-FAQ-001" in res.sanitized_context_block
    allowed_logs = [log for log in res.audit_trace if log.doc_id == "DOC-FAQ-001"]
    assert len(allowed_logs) == 1
    assert allowed_logs[0].access_decision == AccessDecision.ALLOWED


# 2. Legitimate Retrieval (Own Customer Document)
def test_legitimate_retrieval_own_customer_doc(rag_guard):
    req = RAGRequest(
        query="Alice Smith Wealth Portfolio Summary",
        user_context=RAGUserContext(user_id="USR-1001", user_role="RetailCustomer")
    )
    res = rag_guard.process_rag_request(req)
    assert res.authorized_count >= 1
    assert "DOC-CUST-1001-A" in res.sanitized_context_block
    own_doc_logs = [log for log in res.audit_trace if log.doc_id == "DOC-CUST-1001-A"]
    assert own_doc_logs[0].access_decision == AccessDecision.ALLOWED


# 3. Cross-Customer Access Blocked
def test_cross_customer_access_blocked(rag_guard):
    # Customer USR-1001 attempts to access USR-1002's statement
    req = RAGRequest(
        query="Bob Jones Checking Statement Detail DOC-CUST-1002-A",
        user_context=RAGUserContext(user_id="USR-1001", user_role="RetailCustomer")
    )
    res = rag_guard.process_rag_request(req)
    assert "DOC-CUST-1002-A" not in res.sanitized_context_block
    blocked_logs = [log for log in res.audit_trace if log.doc_id == "DOC-CUST-1002-A"]
    assert len(blocked_logs) == 1
    assert blocked_logs[0].access_decision == AccessDecision.DENIED_OWNER
    assert "CROSS_CUSTOMER_ISOLATION" in blocked_logs[0].reason_code


# 4. Role Restriction Blocked
def test_role_restriction_blocked(rag_guard):
    # RetailCustomer attempts to retrieve Internal AML Compliance Playbook
    req = RAGRequest(
        query="AML Fraud Investigation Playbook DOC-COMPLIANCE-001",
        user_context=RAGUserContext(user_id="USR-1001", user_role="RetailCustomer")
    )
    res = rag_guard.process_rag_request(req)
    assert "DOC-COMPLIANCE-001" not in res.sanitized_context_block
    role_logs = [log for log in res.audit_trace if log.doc_id == "DOC-COMPLIANCE-001"]
    assert len(role_logs) == 1
    assert role_logs[0].access_decision == AccessDecision.DENIED_ROLE
    assert "ROLE_NOT_PERMITTED" in role_logs[0].reason_code


# 5. Missing / Invalid Metadata Safe Denial
def test_missing_metadata_safe_denial(rag_guard):
    req = RAGRequest(
        query="Unclassified Document Missing Metadata DOC-CORRUPT-001",
        user_context=RAGUserContext(user_id="USR-1001", user_role="RetailCustomer")
    )
    res = rag_guard.process_rag_request(req)
    assert "DOC-CORRUPT-001" not in res.sanitized_context_block
    meta_logs = [log for log in res.audit_trace if log.doc_id == "DOC-CORRUPT-001"]
    assert len(meta_logs) == 1
    assert meta_logs[0].access_decision == AccessDecision.DENIED_INVALID_METADATA
    assert "MISSING_OR_INVALID_METADATA" in meta_logs[0].reason_code


# 6. Malicious Document Text / Indirect Prompt Injection Blocked
def test_malicious_document_poisoning_blocked(rag_guard):
    req = RAGRequest(
        query="Promotional Advisory Indirect Injection DOC-POISON-001",
        user_context=RAGUserContext(user_id="USR-1001", user_role="RetailCustomer")
    )
    res = rag_guard.process_rag_request(req)
    assert "DOC-POISON-001" not in res.sanitized_context_block
    assert "SYSTEM OVERRIDE" not in res.sanitized_context_block
    poison_logs = [log for log in res.audit_trace if log.doc_id == "DOC-POISON-001"]
    assert len(poison_logs) == 1
    assert poison_logs[0].access_decision == AccessDecision.POISONING_BLOCKED
    assert "POISONING_BLOCKED" in poison_logs[0].reason_code


# 7. Zero Confidential Content in Audit Trace
def test_zero_confidential_data_in_audit_trace(rag_guard):
    req = RAGRequest(
        query="Alice Smith Wealth Portfolio Summary DOC-CUST-1001-A",
        user_context=RAGUserContext(user_id="USR-1001", user_role="RetailCustomer")
    )
    res = rag_guard.process_rag_request(req)
    for audit_log in res.audit_trace:
        log_dict = audit_log.model_dump()
        # Verify no raw body text or sensitive numbers logged in audit object
        assert "content" not in log_dict
        assert "equities allocation" not in str(log_dict)


# 8. FastAPI RAG Retrieve Endpoint Integration Test
def test_fastapi_rag_retrieve_endpoint():
    client = TestClient(app)
    payload = {
        "query": "savings account interest rate",
        "user_context": {
            "user_id": "USR-1001",
            "user_role": "RetailCustomer"
        },
        "top_k": 5
    }
    response = client.post("/api/v1/rag/retrieve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["authorized_count"] >= 1
    assert "<retrieved_reference_documents>" in data["sanitized_context_block"]
    assert len(data["audit_trace"]) > 0
