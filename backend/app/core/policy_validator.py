import os
import yaml
from pathlib import Path
from typing import Dict, Union
from pydantic import ValidationError
from app.schemas.policy import PolicyDefinition



class PolicyValidationError(Exception):
    """Raised when a policy YAML file fails structural or schema validation."""
    pass


class PolicyValidator:
    """
    Validates and loads YAML policy configuration files.
    Rejects malformed policies safely before execution.
    """

    @classmethod
    def load_from_yaml_string(cls, yaml_content: str) -> PolicyDefinition:
        """
        Parses YAML string content and validates against PolicyDefinition schema.
        Raises PolicyValidationError if invalid.
        """
        try:
            raw_data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise PolicyValidationError(f"YAML Syntax Error: {str(e)}")

        if not isinstance(raw_data, dict):
            raise PolicyValidationError("Malformed YAML policy: root structure must be a mapping/dict object.")

        # Support root object wrapping under 'policy' key or direct root mapping
        policy_data = raw_data.get("policy", raw_data)

        try:
            return PolicyDefinition(**policy_data)
        except ValidationError as e:
            errors = []
            for err in e.errors():
                loc = " -> ".join([str(x) for x in err["loc"]])
                errors.append(f"[{loc}]: {err['msg']}")
            raise PolicyValidationError(f"Policy Schema Validation Error(s): {'; '.join(errors)}")

    @classmethod
    def load_from_file(cls, file_path: Union[str, os.PathLike]) -> PolicyDefinition:
        """
        Reads YAML file from path and validates.
        """
        path = str(file_path)
        if not os.path.exists(path):
            # Try resolving relative to repository root
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            candidate = base_dir / path
            if candidate.exists():
                path = str(candidate)
            else:
                raise PolicyValidationError(f"Policy file not found at path: '{path}'")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return cls.load_from_yaml_string(content)
        except IOError as e:
            raise PolicyValidationError(f"Failed to read policy file '{path}': {str(e)}")
