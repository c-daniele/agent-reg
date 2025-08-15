#!/usr/bin/env python3

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Union, List, Any, Tuple, Optional
from jsonschema import validate, ValidationError, SchemaError, Draft7Validator

class AgentCardValidator:
    """Validator for Agent Card JSON against the A2A schema specification."""
    
    def __init__(self, schema_path: Union[str, Path]):
        """Initialize with the path to the schema file.
        
        Args:
            schema_path: Path to the JSON schema file
        """
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load the JSON schema from file.
        
        Returns:
            The loaded schema as a dictionary
            
        Raises:
            FileNotFoundError: If schema file doesn't exist
            json.JSONDecodeError: If schema isn't valid JSON
        """
        try:
            with open(self.schema_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in schema file: {e.msg}", e.doc, e.pos)
    
    def validate_file(self, agent_card_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
        """Validate an agent card JSON file against the schema.
        
        Args:
            agent_card_path: Path to the agent card JSON file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(agent_card_path, 'r') as f:
                agent_card = json.load(f)
            return self.validate_dict(agent_card)
        except FileNotFoundError:
            return False, f"Agent card file not found: {agent_card_path}"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in agent card file: {e.msg}"
    
    def validate_string(self, agent_card_json: str) -> Tuple[bool, Optional[str]]:
        """Validate an agent card JSON string against the schema.
        
        Args:
            agent_card_json: JSON string containing the agent card
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            agent_card = json.loads(agent_card_json)
            return self.validate_dict(agent_card)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON string: {e.msg}"
    
    def validate_dict(self, agent_card: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate an agent card dictionary against the schema.
        
        Args:
            agent_card: Dictionary containing the agent card
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Create a schema specifically for the AgentCard
            agent_card_schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "$ref": "#/definitions/AgentCard",
                "definitions": self.schema["definitions"]
            }
            
            # Use Draft7Validator for more detailed validation
            validator = Draft7Validator(agent_card_schema)
            errors = list(validator.iter_errors(agent_card))
            
            if not errors:
                return True, None
                
            # Format all validation errors
            error_messages = []
            for error in errors:
                error_messages.append(self._format_validation_error(error))
            
            return False, "\n".join(error_messages)
            
        except SchemaError as e:
            return False, f"Schema error: {str(e)}"
    
    def _format_validation_error(self, error: ValidationError) -> str:
        """Format a validation error for better readability.
        
        Args:
            error: The ValidationError object
            
        Returns:
            Formatted error message
        """
        # Create a readable path to the error
        path = " → ".join([str(p) for p in error.path]) if error.path else "root"
        
        # Handle different types of validation errors more specifically
        if error.validator == 'required':
            missing_props = error.validator_value
            return f"Validation error at {path}: Missing required properties: {', '.join(missing_props)}"
        elif error.validator == 'additionalProperties':
            extra_props = list(error.instance.keys() - set(error.schema.get('properties', {}).keys()))
            return f"Validation error at {path}: Additional properties not allowed: {', '.join(extra_props)}"
        else:
            return f"Validation error at {path}: {error.message}"

    def check_only_required_fields(self, agent_card: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate that only the required fields are present in the agent card.
        
        Args:
            agent_card: Dictionary containing the agent card
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Get the AgentCard schema
            agent_card_schema = self.schema["definitions"]["AgentCard"]
            required_fields = set(agent_card_schema.get("required", []))
            
            # Check if all required fields are present
            missing_fields = [field for field in required_fields if field not in agent_card]
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            return True, None
        except Exception as e:
            return False, f"Error checking required fields: {str(e)}"

def simple_validate(schemaFilePath: str, agentCardFilePath: str) -> Tuple[bool, Optional[str]]:
    validator = AgentCardValidator(schemaFilePath)
    return validator.validate_file(agentCardFilePath)

# def main():
#     parser = argparse.ArgumentParser(description="Validate an A2A Agent Card against the schema")
#     parser.add_argument("--schema", default="a2a_agent_card_schema.json", 
#                         help="Path to the schema file")
    
#     group = parser.add_mutually_exclusive_group(required=True)
#     group.add_argument("--file", help="Path to agent card JSON file")
#     group.add_argument("--json", help="Agent card JSON string")
    
#     parser.add_argument("--strict", action="store_true", 
#                         help="Strictly validate all fields (not just required ones)")
    
#     args = parser.parse_args()
    
#     try:
#         validator = AgentCardValidator(args.schema)
        
#         if args.file:
#             is_valid, error = validator.validate_file(args.file)
#         else:
#             is_valid, error = validator.validate_string(args.json)
        
#         # If using non-strict mode and validation failed, try checking only required fields
#         if not is_valid and not args.strict:
#             agent_card = json.loads(args.json) if args.json else json.load(open(args.file))
#             req_valid, req_error = validator.check_only_required_fields(agent_card)
#             if req_valid:
#                 is_valid = True
#                 error = None
#                 print("⚠️ Note: Agent card is valid for required fields only, but has other schema issues.")
            
#         if is_valid:
#             print("✅ Agent card is valid!")
#             return 0
#         else:
#             print(f"❌ Agent card is invalid: {error}")
#             return 1
            
#     except Exception as e:
#         print(f"Error: {str(e)}")
#         return 2