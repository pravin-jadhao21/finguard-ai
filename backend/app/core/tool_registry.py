import re
from typing import Dict, Any, List, Optional, Tuple


class ToolRegistry:
    """
    Strict Tool Allowlist & Schema Registry for BFSI Gateway.
    Defines explicit JSON parameter schemas and sensitivity attributes.
    """

    ALLOWED_TOOLS: Dict[str, Dict[str, Any]] = {
        "get_demo_balance": {
            "name": "get_demo_balance",
            "description": "Fetch current balance and metadata for a simulated demo account",
            "is_sensitive": False,
            "allowed_roles": ["RetailCustomer", "WealthManager", "ComplianceOfficer", "Admin"],
            "parameters": {
                "type": "object",
                "required": ["account_id"],
                "properties": {
                    "account_id": {
                        "type": "string",
                        "pattern": r"^ACC-\d{4}$",
                        "description": "Simulated account identifier (e.g. ACC-1001)"
                    }
                }
            }
        },
        "get_demo_statement": {
            "name": "get_demo_statement",
            "description": "Fetch recent transaction history statement for a demo account",
            "is_sensitive": False,
            "allowed_roles": ["RetailCustomer", "WealthManager", "ComplianceOfficer", "Admin"],
            "parameters": {
                "type": "object",
                "required": ["account_id"],
                "properties": {
                    "account_id": {
                        "type": "string",
                        "pattern": r"^ACC-\d{4}$",
                        "description": "Simulated account identifier (e.g. ACC-1001)"
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 5,
                        "description": "Maximum number of recent transactions to retrieve"
                    }
                }
            }
        },
        "initiate_demo_transfer": {
            "name": "initiate_demo_transfer",
            "description": "Initiate a simulated money transfer between fake demo accounts",
            "is_sensitive": True,  # Requires step-up authorization or approval token
            "allowed_roles": ["RetailCustomer", "WealthManager", "Admin"],
            "parameters": {
                "type": "object",
                "required": ["from_account_id", "to_account_id", "amount"],
                "properties": {
                    "from_account_id": {
                        "type": "string",
                        "pattern": r"^ACC-\d{4}$",
                        "description": "Source account ID"
                    },
                    "to_account_id": {
                        "type": "string",
                        "pattern": r"^ACC-\d{4}$",
                        "description": "Destination account ID"
                    },
                    "amount": {
                        "type": "number",
                        "minimum": 0.01,
                        "description": "Transfer amount in USD"
                    },
                    "currency": {
                        "type": "string",
                        "default": "USD",
                        "enum": ["USD", "EUR", "GBP", "INR"]
                    },
                    "memo": {
                        "type": "string",
                        "maxLength": 100,
                        "description": "Optional transfer description or memo"
                    }
                }
            }
        }
    }

    @classmethod
    def is_tool_allowed(cls, tool_name: str) -> bool:
        """Returns True if tool_name is in strict allowlist."""
        return tool_name in cls.ALLOWED_TOOLS

    @classmethod
    def get_tool_schema(cls, tool_name: str) -> Optional[Dict[str, Any]]:
        """Returns tool schema definition or None."""
        return cls.ALLOWED_TOOLS.get(tool_name)

    @classmethod
    def validate_arguments(cls, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validates argument types, required parameters, and constraints against schema.
        Returns (is_valid, error_message).
        """
        schema = cls.get_tool_schema(tool_name)
        if not schema:
            return False, f"Tool '{tool_name}' is not in the allowlist."

        params = schema["parameters"]
        required = params.get("required", [])

        # Check required fields
        for field in required:
            if field not in args:
                return False, f"Missing required parameter '{field}' for tool '{tool_name}'."
            if args[field] is None or args[field] == "":
                return False, f"Required parameter '{field}' cannot be empty."

        props = params.get("properties", {})
        for arg_key, arg_val in args.items():
            if arg_key not in props:
                return False, f"Unexpected argument '{arg_key}' passed to tool '{tool_name}'."

            spec = props[arg_key]
            expected_type = spec.get("type")

            # Validate types
            if expected_type == "string":
                if not isinstance(arg_val, str):
                    return False, f"Parameter '{arg_key}' must be a string."
                pattern = spec.get("pattern")
                if pattern and not re.match(pattern, arg_val):
                    return False, f"Parameter '{arg_key}' value '{arg_val}' does not match pattern '{pattern}'."

            elif expected_type in ("number", "integer"):
                if not isinstance(arg_val, (int, float)) or isinstance(arg_val, bool):
                    return False, f"Parameter '{arg_key}' must be a numeric value."
                min_val = spec.get("minimum")
                if min_val is not None and arg_val < min_val:
                    return False, f"Parameter '{arg_key}' value {arg_val} is below minimum allowed {min_val}."
                max_val = spec.get("maximum")
                if max_val is not None and arg_val > max_val:
                    return False, f"Parameter '{arg_key}' value {arg_val} exceeds maximum allowed {max_val}."

        return True, None
