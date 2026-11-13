from typing import Dict, Any, List, Optional
import copy
import uuid
from datetime import datetime, timezone


class SimulatedBankingService:
    """
    Isolated Simulated Core Banking Service.
    Operates strictly on synthetic in-memory mock account ledgers.
    Provides fake accounts with zero external money movement.
    """

    def __init__(self):
        # In-memory synthetic account database
        self._accounts: Dict[str, Dict[str, Any]] = {
            "ACC-1001": {
                "account_id": "ACC-1001",
                "owner_name": "Alice Smith",
                "owner_id": "USR-1001",
                "account_type": "Savings",
                "balance": 10000.00,
                "currency": "USD",
                "created_at": "2024-01-15T08:00:00Z"
            },
            "ACC-1002": {
                "account_id": "ACC-1002",
                "owner_name": "Bob Jones",
                "owner_id": "USR-1002",
                "account_type": "Checking",
                "balance": 5000.00,
                "currency": "USD",
                "created_at": "2024-02-10T10:30:00Z"
            },
            "ACC-1003": {
                "account_id": "ACC-1003",
                "owner_name": "Charlie Brown",
                "owner_id": "USR-1003",
                "account_type": "Savings",
                "balance": 2500.00,
                "currency": "USD",
                "created_at": "2024-03-01T14:15:00Z"
            }
        }

        # Transaction ledgers
        self._transactions: List[Dict[str, Any]] = [
            {
                "transaction_id": "TXN-9001",
                "account_id": "ACC-1001",
                "type": "CREDIT",
                "amount": 2500.00,
                "description": "Salary Direct Deposit",
                "timestamp": "2026-10-01T09:00:00Z",
                "balance_after": 10000.00
            },
            {
                "transaction_id": "TXN-9002",
                "account_id": "ACC-1002",
                "type": "DEBIT",
                "amount": 150.00,
                "description": "Utility Bill Payment",
                "timestamp": "2026-10-03T11:20:00Z",
                "balance_after": 5000.00
            }
        ]

    def reset(self):
        """Resets ledgers to initial state for test reproducibility."""
        self.__init__()

    def get_balance(self, account_id: str) -> Dict[str, Any]:
        """Returns account balance and metadata."""
        if account_id not in self._accounts:
            raise ValueError(f"Account ID '{account_id}' not found in core banking ledger.")
        acc = copy.deepcopy(self._accounts[account_id])
        return {
            "account_id": acc["account_id"],
            "owner_name": acc["owner_name"],
            "account_type": acc["account_type"],
            "balance": acc["balance"],
            "currency": acc["currency"],
            "as_of": datetime.now(timezone.utc).isoformat()
        }

    def get_statement(self, account_id: str, limit: int = 5) -> Dict[str, Any]:
        """Returns recent transactions for an account."""
        if account_id not in self._accounts:
            raise ValueError(f"Account ID '{account_id}' not found in core banking ledger.")

        acc_txns = [t for t in self._transactions if t["account_id"] == account_id]
        sorted_txns = sorted(acc_txns, key=lambda x: x["timestamp"], reverse=True)[:limit]

        return {
            "account_id": account_id,
            "owner_name": self._accounts[account_id]["owner_name"],
            "transaction_count": len(sorted_txns),
            "transactions": sorted_txns
        }

    def initiate_transfer(self, from_account_id: str, to_account_id: str, amount: float, memo: Optional[str] = None) -> Dict[str, Any]:
        """Executes simulated money transfer between synthetic accounts."""
        if from_account_id not in self._accounts:
            raise ValueError(f"Source account '{from_account_id}' does not exist.")
        if to_account_id not in self._accounts:
            raise ValueError(f"Destination account '{to_account_id}' does not exist.")
        if amount <= 0:
            raise ValueError("Transfer amount must be greater than 0.")

        src_acc = self._accounts[from_account_id]
        dest_acc = self._accounts[to_account_id]

        if src_acc["balance"] < amount:
            raise ValueError(f"Insufficient funds: Available balance ${src_acc['balance']:.2f}, requested ${amount:.2f}")

        # Debit source, Credit destination
        src_acc["balance"] -= amount
        dest_acc["balance"] += amount

        now_iso = datetime.now(timezone.utc).isoformat()
        txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"

        debit_entry = {
            "transaction_id": txn_id,
            "account_id": from_account_id,
            "type": "DEBIT",
            "amount": amount,
            "description": f"Transfer to {to_account_id}: {memo or 'N/A'}",
            "timestamp": now_iso,
            "balance_after": src_acc["balance"]
        }
        credit_entry = {
            "transaction_id": f"{txn_id}-CR",
            "account_id": to_account_id,
            "type": "CREDIT",
            "amount": amount,
            "description": f"Transfer from {from_account_id}: {memo or 'N/A'}",
            "timestamp": now_iso,
            "balance_after": dest_acc["balance"]
        }

        self._transactions.append(debit_entry)
        self._transactions.append(credit_entry)

        return {
            "status": "COMPLETED",
            "transaction_id": txn_id,
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "amount": amount,
            "currency": src_acc["currency"],
            "remaining_balance": src_acc["balance"],
            "memo": memo or "",
            "timestamp": now_iso
        }
