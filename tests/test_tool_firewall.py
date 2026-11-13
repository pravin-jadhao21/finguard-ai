import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.tool_firewall import ToolActionFirewall
from app.services.simulated_banking import SimulatedBankingService
from app.schemas.tool_firewall import (
    ToolValidationRequest,
    ToolValidationAction,
    UserAuthContext
)
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def banking_service():
    service = SimulatedBankingService()
    service.reset()
    return service


@pytest.fixture
def firewall(banking_service):
    return ToolActionFirewall(banking_service=banking_service)


@pytest.fixture
def valid_auth_context():
    return UserAuthContext(
        user_id="USR-1001",
        user_role="RetailCustomer",
        step_up_authenticated=True
    )


# 1. Valid Demo Balance Request Test
def test_valid_demo_balance_request(firewall, valid_auth_context):
    req = ToolValidationRequest(
        tool_name="get_demo_balance",
        arguments={"account_id": "ACC-1001"},
        user_prompt="What is my account balance for ACC-1001?",
        user_context=valid_auth_context
    )
    res = firewall.validate_and_execute(req)
    assert res.action_decision == ToolValidationAction.ALLOW
    assert res.reason_code == "TOOL_VALIDATION_PASSED"
    assert res.execution_success is True
    assert res.result["balance"] == 10000.00
    assert res.result["account_id"] == "ACC-1001"


# 2. Valid Demo Statement Request Test
def test_valid_demo_statement_request(firewall, valid_auth_context):
    req = ToolValidationRequest(
        tool_name="get_demo_statement",
        arguments={"account_id": "ACC-1001", "limit": 5},
        user_prompt="Show me recent transactions for ACC-1001",
        user_context=valid_auth_context
    )
    res = firewall.validate_and_execute(req)
    assert res.action_decision == ToolValidationAction.ALLOW
    assert res.execution_success is True
    assert "transactions" in res.result


# 3. Valid Demo Transfer with Step-Up Approval Test
def test_valid_demo_transfer_with_approval(firewall, valid_auth_context):
    req = ToolValidationRequest(
        tool_name="initiate_demo_transfer",
        arguments={
            "from_account_id": "ACC-1001",
            "to_account_id": "ACC-1002",
            "amount": 500.0,
            "memo": "Rent contribution"
        },
        user_prompt="Transfer $500 to ACC-1002 for Rent contribution",
        user_context=valid_auth_context
    )
    res = firewall.validate_and_execute(req)
    assert res.action_decision == ToolValidationAction.ALLOW
    assert res.execution_success is True
    assert res.result["amount"] == 500.0
    assert res.result["remaining_balance"] == 9500.00


# 4. Amount Mismatch Test (Blocked)
def test_amount_mismatch_blocked(firewall, valid_auth_context):
    req = ToolValidationRequest(
        tool_name="initiate_demo_transfer",
        arguments={
            "from_account_id": "ACC-1001",
            "to_account_id": "ACC-1002",
            "amount": 5000.0,  # Tool tries 5000.0, prompt asked for 50.0
        },
        user_prompt="Transfer $50 to ACC-1002",
        user_context=valid_auth_context
    )
    res = firewall.validate_and_execute(req)
    assert res.action_decision == ToolValidationAction.BLOCK
    assert "TOOL_PARAMETER_AMOUNT_MISMATCH_BLOCKED" in res.reason_code
    assert res.execution_success is False


# 5. Recipient Mismatch Test (Blocked)
def test_recipient_mismatch_blocked(firewall, valid_auth_context):
    req = ToolValidationRequest(
        tool_name="initiate_demo_transfer",
        arguments={
            "from_account_id": "ACC-1001",
            "to_account_id": "ACC-1003",  # Tool tries ACC-1003, prompt asked ACC-1002
            "amount": 100.0
        },
        user_prompt="Transfer $100 to ACC-1002",
        user_context=valid_auth_context
    )
    res = firewall.validate_and_execute(req)
    assert res.action_decision == ToolValidationAction.BLOCK
    assert "TOOL_PARAMETER_RECIPIENT_MISMATCH_BLOCKED" in res.reason_code
    assert res.execution_success is False


# 6. Unauthorized / Unknown Tool Test (Blocked)
def test_unauthorized_unknown_tool_blocked(firewall, valid_auth_context):
    req = ToolValidationRequest(
        tool_name="execute_sql_query",
        arguments={"sql": "SELECT * FROM users"},
        user_prompt="Show all users",
        user_context=valid_auth_context
    )
    res = firewall.validate_and_execute(req)
    assert res.action_decision == ToolValidationAction.BLOCK
    assert res.reason_code == "TOOL_UNAUTHORIZED_NAME_BLOCKED"
    assert res.execution_success is False


# 7. Invalid Arguments / Schema Validation Test (Blocked)
def test_invalid_arguments_blocked(firewall, valid_auth_context):
    req = ToolValidationRequest(
        tool_name="initiate_demo_transfer",
        arguments={
            "from_account_id": "ACC-1001",
            "to_account_id": "ACC-1002",
            "amount": -50.0  # Invalid negative amount
        },
        user_prompt="Transfer -$50 to ACC-1002",
        user_context=valid_auth_context
    )
    res = firewall.validate_and_execute(req)
    assert res.action_decision == ToolValidationAction.BLOCK
    assert "TOOL_SCHEMA_VALIDATION_FAILED" in res.reason_code
    assert res.execution_success is False


# 8. Missing Step-Up Approval Test (Escalated)
def test_missing_approval_escalated(firewall):
    unapproved_context = UserAuthContext(
        user_id="USR-1001",
        user_role="RetailCustomer",
        step_up_authenticated=False,
        approval_token=None
    )
    req = ToolValidationRequest(
        tool_name="initiate_demo_transfer",
        arguments={
            "from_account_id": "ACC-1001",
            "to_account_id": "ACC-1002",
            "amount": 200.0
        },
        user_prompt="Transfer $200 to ACC-1002",
        user_context=unapproved_context
    )
    res = firewall.validate_and_execute(req)
    assert res.action_decision == ToolValidationAction.ESCALATE
    assert "TOOL_APPROVAL_REQUIRED_ESCALATED" in res.reason_code
    assert res.execution_success is False


# 9. Missing Auth Context Test (Blocked)
def test_missing_auth_context_blocked(firewall):
    req = ToolValidationRequest(
        tool_name="get_demo_balance",
        arguments={"account_id": "ACC-1001"},
        user_prompt="Check balance",
        user_context=None
    )
    res = firewall.validate_and_execute(req)
    assert res.action_decision == ToolValidationAction.BLOCK
    assert res.reason_code == "TOOL_AUTH_CONTEXT_MISSING_BLOCKED"


# 10. FastAPI Tool Execution Endpoint Integration Test
def test_fastapi_tool_execute_endpoint():
    client = TestClient(app)
    payload = {
        "tool_name": "get_demo_balance",
        "arguments": {"account_id": "ACC-1001"},
        "user_prompt": "What is my balance for ACC-1001?",
        "user_context": {
            "user_id": "USR-1001",
            "user_role": "RetailCustomer",
            "step_up_authenticated": True
        }
    }
    response = client.post("/api/v1/tool/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["action_decision"] == "ALLOW"
    assert data["execution_success"] is True
    assert isinstance(data["result"]["balance"], float)
    assert data["result"]["balance"] > 0
