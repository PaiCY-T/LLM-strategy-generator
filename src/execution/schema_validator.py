"""Schema Validator for Strategy YAML Files

This module implements comprehensive schema validation for strategy YAML files,
integrating with Layer 1 (DataFieldManifest) and Layer 2 (FieldValidator) validation.

Key Features:
- Validates YAML structure matches expected schema
- Checks required keys exist (name, type, required_fields, parameters, logic)
- Validates data types for each section
- Integrates with DataFieldManifest for field validation
- Returns structured validation errors with line numbers and suggestions

Architecture:
- Layer 1 Integration: Uses DataFieldManifest for field name validation
- Layer 2 Integration: Uses FieldValidator for code validation
- Structured Error Reporting: Returns detailed errors with line numbers and suggestions

Usage:
    from src.execution.schema_validator import SchemaValidator

    validator = SchemaValidator()
    errors = validator.validate(yaml_dict)
    if errors:
        for error in errors:
            print(f"{error.severity}: {error.message}")

Example:
    >>> validator = SchemaValidator()
    >>> yaml_dict = {
    ...     "name": "Test Strategy",
    ...     "type": "factor_graph",
    ...     "required_fields": ["close", "volume"],
    ...     "parameters": [{"name": "period", "type": "int", "value": 20}],
    ...     "logic": {"entry": "close > 100", "exit": "close < 90"}
    ... }
    >>> errors = validator.validate(yaml_dict)
    >>> assert len(errors) == 0  # Valid schema
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation errors."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """Structured validation error with context."""
    severity: ValidationSeverity
    message: str
    field_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """Format error message for display."""
        parts = [f"{self.severity.value.upper()}: {self.message}"]
        if self.field_path:
            parts.append(f"  Field: {self.field_path}")
        if self.line_number:
            parts.append(f"  Line: {self.line_number}")
        if self.suggestion:
            parts.append(f"  Suggestion: {self.suggestion}")
        return "\n".join(parts)


class SchemaValidator:
    """
    Comprehensive schema validator for strategy YAML files.

    Validates YAML structure, data types, and field references using
    integration with Layer 1 (DataFieldManifest) and Layer 2 (FieldValidator).

    Attributes:
        manifest: Optional DataFieldManifest for field validation
        field_validator: Optional FieldValidator for code validation

    Example:
        >>> from src.config.data_fields import DataFieldManifest
        >>> manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
        >>> validator = SchemaValidator(manifest=manifest)
        >>>
        >>> yaml_dict = {"name": "Test", "type": "factor_graph"}
        >>> errors = validator.validate(yaml_dict)
        >>> assert len(errors) > 0  # Missing required fields
    """

    # Required top-level keys
    REQUIRED_KEYS = ["name", "type", "required_fields", "parameters", "logic"]

    # Optional top-level keys
    OPTIONAL_KEYS = ["description", "constraints", "optional_fields", "coverage_percentage"]

    # Valid strategy types
    VALID_TYPES = ["factor_graph", "llm_generated", "hybrid"]

    # Valid parameter types
    VALID_PARAM_TYPES = ["int", "float", "bool", "str", "list"]

    # Valid constraint severities
    VALID_SEVERITIES = ["critical", "high", "medium", "low"]

    def __init__(
        self,
        manifest: Optional[Any] = None,
        field_validator: Optional[Any] = None
    ):
        """
        Initialize schema validator.

        Args:
            manifest: Optional DataFieldManifest for field validation
            field_validator: Optional FieldValidator for code validation
        """
        self.manifest = manifest
        self.field_validator = field_validator

    def validate(self, yaml_dict: Dict[str, Any]) -> List[ValidationError]:
        """
        Validate YAML dictionary against schema.

        Performs comprehensive validation including:
        - Required keys validation
        - Data type validation
        - Field reference validation
        - Parameter validation
        - Logic validation
        - Constraint validation

        Args:
            yaml_dict: Parsed YAML dictionary to validate

        Returns:
            List of ValidationError objects (empty if valid)

        Example:
            >>> validator = SchemaValidator()
            >>> errors = validator.validate({"name": "Test"})
            >>> assert len(errors) > 0  # Missing required keys
        """
        errors = []

        # Validate YAML is a dictionary
        if not isinstance(yaml_dict, dict):
            errors.append(ValidationError(
                severity=ValidationSeverity.ERROR,
                message="YAML must be a dictionary/object",
                field_path="<root>"
            ))
            return errors

        # Validate required keys
        errors.extend(self.validate_yaml_structure(yaml_dict))

        # Validate data types (only if structure is valid)
        if not errors:
            errors.extend(self.validate_field_types(yaml_dict))

        # Validate required_fields section
        if "required_fields" in yaml_dict:
            errors.extend(self.validate_required_fields(yaml_dict["required_fields"]))

        # Validate parameters section
        if "parameters" in yaml_dict:
            errors.extend(self.validate_parameters(yaml_dict["parameters"]))

        # Validate logic section (only if it's a dict)
        if "logic" in yaml_dict and isinstance(yaml_dict["logic"], dict):
            errors.extend(self.validate_logic(yaml_dict["logic"]))

        # Validate constraints section (only if it's a list)
        if "constraints" in yaml_dict and isinstance(yaml_dict["constraints"], list):
            errors.extend(self.validate_constraints(yaml_dict["constraints"]))

        return errors

    def validate_yaml_structure(self, yaml_dict: Dict[str, Any]) -> List[ValidationError]:
        """
        Validate YAML has all required top-level keys.

        Args:
            yaml_dict: Parsed YAML dictionary

        Returns:
            List of validation errors for missing required keys

        Example:
            >>> validator = SchemaValidator()
            >>> errors = validator.validate_yaml_structure({"name": "Test"})
            >>> assert len(errors) == 4  # Missing type, required_fields, parameters, logic
        """
        errors = []

        # Check for required keys
        for key in self.REQUIRED_KEYS:
            if key not in yaml_dict:
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Missing required key: '{key}'",
                    field_path="<root>",
                    suggestion=f"Add '{key}' to the top level of your YAML"
                ))

        # Check for unknown keys
        all_valid_keys = set(self.REQUIRED_KEYS + self.OPTIONAL_KEYS)
        for key in yaml_dict.keys():
            if key not in all_valid_keys:
                errors.append(ValidationError(
                    severity=ValidationSeverity.WARNING,
                    message=f"Unknown key: '{key}'",
                    field_path="<root>",
                    suggestion=f"Valid keys are: {', '.join(sorted(all_valid_keys))}"
                ))

        return errors

    def validate_field_types(self, yaml_dict: Dict[str, Any]) -> List[ValidationError]:
        """
        Validate data types for each section.

        Args:
            yaml_dict: Parsed YAML dictionary

        Returns:
            List of validation errors for invalid data types

        Example:
            >>> validator = SchemaValidator()
            >>> yaml_dict = {"name": 123, "type": "factor_graph"}
            >>> errors = validator.validate_field_types(yaml_dict)
            >>> assert any("name" in e.message for e in errors)
        """
        errors = []

        # Validate 'name' is string
        if "name" in yaml_dict and not isinstance(yaml_dict["name"], str):
            errors.append(ValidationError(
                severity=ValidationSeverity.ERROR,
                message=f"Field 'name' must be a string, got {type(yaml_dict['name']).__name__}",
                field_path="name"
            ))

        # Validate 'type' is string and valid value
        if "type" in yaml_dict:
            if not isinstance(yaml_dict["type"], str):
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Field 'type' must be a string, got {type(yaml_dict['type']).__name__}",
                    field_path="type"
                ))
            elif yaml_dict["type"] not in self.VALID_TYPES:
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid strategy type: '{yaml_dict['type']}'",
                    field_path="type",
                    suggestion=f"Valid types are: {', '.join(self.VALID_TYPES)}"
                ))

        # Validate 'description' is string (optional)
        if "description" in yaml_dict and not isinstance(yaml_dict["description"], str):
            errors.append(ValidationError(
                severity=ValidationSeverity.ERROR,
                message=f"Field 'description' must be a string, got {type(yaml_dict['description']).__name__}",
                field_path="description"
            ))

        # Validate 'required_fields' is list
        if "required_fields" in yaml_dict and not isinstance(yaml_dict["required_fields"], list):
            errors.append(ValidationError(
                severity=ValidationSeverity.ERROR,
                message=f"Field 'required_fields' must be a list, got {type(yaml_dict['required_fields']).__name__}",
                field_path="required_fields"
            ))

        # Validate 'parameters' is list
        if "parameters" in yaml_dict and not isinstance(yaml_dict["parameters"], list):
            errors.append(ValidationError(
                severity=ValidationSeverity.ERROR,
                message=f"Field 'parameters' must be a list, got {type(yaml_dict['parameters']).__name__}",
                field_path="parameters"
            ))

        # Validate 'logic' is dict
        if "logic" in yaml_dict and not isinstance(yaml_dict["logic"], dict):
            errors.append(ValidationError(
                severity=ValidationSeverity.ERROR,
                message=f"Field 'logic' must be a dictionary, got {type(yaml_dict['logic']).__name__}",
                field_path="logic"
            ))

        # Validate 'constraints' is list (optional)
        if "constraints" in yaml_dict and not isinstance(yaml_dict["constraints"], list):
            errors.append(ValidationError(
                severity=ValidationSeverity.ERROR,
                message=f"Field 'constraints' must be a list, got {type(yaml_dict['constraints']).__name__}",
                field_path="constraints"
            ))

        # Validate 'coverage_percentage' is number (optional)
        if "coverage_percentage" in yaml_dict:
            if not isinstance(yaml_dict["coverage_percentage"], (int, float)):
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Field 'coverage_percentage' must be a number, got {type(yaml_dict['coverage_percentage']).__name__}",
                    field_path="coverage_percentage"
                ))
            elif not (0 <= yaml_dict["coverage_percentage"] <= 100):
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Field 'coverage_percentage' must be between 0 and 100, got {yaml_dict['coverage_percentage']}",
                    field_path="coverage_percentage"
                ))

        return errors

    def validate_required_fields(self, required_fields: List[Any]) -> List[ValidationError]:
        """
        Validate required_fields section using Layer 1 DataFieldManifest.

        Args:
            required_fields: List of required field names

        Returns:
            List of validation errors for invalid fields

        Example:
            >>> from src.config.data_fields import DataFieldManifest
            >>> manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
            >>> validator = SchemaValidator(manifest=manifest)
            >>> errors = validator.validate_required_fields(["close", "invalid_field"])
            >>> assert any("invalid_field" in e.message for e in errors)
        """
        errors = []

        # Validate each field is a string or dict
        for i, field in enumerate(required_fields):
            if isinstance(field, str):
                field_name = field
            elif isinstance(field, dict):
                if "canonical_name" not in field:
                    errors.append(ValidationError(
                        severity=ValidationSeverity.ERROR,
                        message=f"Field dict at index {i} missing 'canonical_name'",
                        field_path=f"required_fields[{i}]"
                    ))
                    continue
                field_name = field["canonical_name"]

                # Validate field structure
                if "alias" in field and not isinstance(field["alias"], str):
                    errors.append(ValidationError(
                        severity=ValidationSeverity.ERROR,
                        message=f"Field 'alias' must be a string",
                        field_path=f"required_fields[{i}].alias"
                    ))

                if "usage" in field and not isinstance(field["usage"], str):
                    errors.append(ValidationError(
                        severity=ValidationSeverity.ERROR,
                        message=f"Field 'usage' must be a string",
                        field_path=f"required_fields[{i}].usage"
                    ))
            else:
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Field at index {i} must be string or dict, got {type(field).__name__}",
                    field_path=f"required_fields[{i}]"
                ))
                continue

            # Validate field name using DataFieldManifest if available
            if self.manifest is not None:
                is_valid, suggestion = self.manifest.validate_field_with_suggestion(field_name)
                if not is_valid:
                    errors.append(ValidationError(
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid field name: '{field_name}'",
                        field_path=f"required_fields[{i}]",
                        suggestion=suggestion
                    ))

        return errors

    def validate_parameters(self, parameters: List[Any]) -> List[ValidationError]:
        """
        Validate parameters section.

        Each parameter must have:
        - name (str)
        - type (str, one of VALID_PARAM_TYPES)
        - value (matching type)
        - default (optional, matching type)
        - range (optional, for numeric types: tuple of (min, max))

        Args:
            parameters: List of parameter dictionaries

        Returns:
            List of validation errors

        Example:
            >>> validator = SchemaValidator()
            >>> params = [{"name": "period", "type": "int", "value": 20, "range": [5, 100]}]
            >>> errors = validator.validate_parameters(params)
            >>> assert len(errors) == 0
        """
        errors = []

        for i, param in enumerate(parameters):
            if not isinstance(param, dict):
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Parameter at index {i} must be a dictionary, got {type(param).__name__}",
                    field_path=f"parameters[{i}]"
                ))
                continue

            # Check required fields
            if "name" not in param:
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Parameter at index {i} missing 'name'",
                    field_path=f"parameters[{i}]"
                ))
            elif not isinstance(param["name"], str):
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Parameter 'name' must be a string",
                    field_path=f"parameters[{i}].name"
                ))

            if "type" not in param:
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Parameter at index {i} missing 'type'",
                    field_path=f"parameters[{i}]"
                ))
            elif param["type"] not in self.VALID_PARAM_TYPES:
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid parameter type: '{param['type']}'",
                    field_path=f"parameters[{i}].type",
                    suggestion=f"Valid types are: {', '.join(self.VALID_PARAM_TYPES)}"
                ))

            if "value" not in param:
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Parameter at index {i} missing 'value'",
                    field_path=f"parameters[{i}]"
                ))

            # Validate value type matches declared type
            if "type" in param and "value" in param:
                expected_type = param["type"]
                value = param["value"]

                type_map = {
                    "int": int,
                    "float": (int, float),  # Allow int for float
                    "bool": bool,
                    "str": str,
                    "list": list
                }

                if expected_type in type_map:
                    expected_python_type = type_map[expected_type]
                    if not isinstance(value, expected_python_type):
                        errors.append(ValidationError(
                            severity=ValidationSeverity.ERROR,
                            message=f"Parameter value type mismatch: expected {expected_type}, got {type(value).__name__}",
                            field_path=f"parameters[{i}].value"
                        ))

            # Validate range for numeric types
            if "range" in param:
                if "type" not in param or param["type"] not in ["int", "float"]:
                    errors.append(ValidationError(
                        severity=ValidationSeverity.WARNING,
                        message=f"Parameter 'range' only valid for int/float types",
                        field_path=f"parameters[{i}].range"
                    ))
                elif not isinstance(param["range"], (list, tuple)) or len(param["range"]) != 2:
                    errors.append(ValidationError(
                        severity=ValidationSeverity.ERROR,
                        message=f"Parameter 'range' must be a list/tuple of [min, max]",
                        field_path=f"parameters[{i}].range"
                    ))
                else:
                    min_val, max_val = param["range"]
                    if not isinstance(min_val, (int, float)) or not isinstance(max_val, (int, float)):
                        errors.append(ValidationError(
                            severity=ValidationSeverity.ERROR,
                            message=f"Parameter 'range' values must be numeric",
                            field_path=f"parameters[{i}].range"
                        ))
                    elif min_val >= max_val:
                        errors.append(ValidationError(
                            severity=ValidationSeverity.ERROR,
                            message=f"Parameter 'range' min must be less than max",
                            field_path=f"parameters[{i}].range"
                        ))

                    # Check if value is within range
                    if "value" in param and isinstance(param["value"], (int, float)):
                        if not (min_val <= param["value"] <= max_val):
                            errors.append(ValidationError(
                                severity=ValidationSeverity.ERROR,
                                message=f"Parameter value {param['value']} outside range [{min_val}, {max_val}]",
                                field_path=f"parameters[{i}].value"
                            ))

        return errors

    def validate_logic(self, logic: Dict[str, Any]) -> List[ValidationError]:
        """
        Validate logic section.

        Logic must have:
        - entry (str): Entry condition code
        - exit (str): Exit condition code
        - dependencies (list, optional): List of dependency field names

        Args:
            logic: Logic dictionary

        Returns:
            List of validation errors

        Example:
            >>> validator = SchemaValidator()
            >>> logic = {"entry": "close > 100", "exit": "close < 90"}
            >>> errors = validator.validate_logic(logic)
            >>> assert len(errors) == 0
        """
        errors = []

        # Check required fields
        if "entry" not in logic:
            errors.append(ValidationError(
                severity=ValidationSeverity.ERROR,
                message="Logic section missing 'entry'",
                field_path="logic"
            ))
        elif not isinstance(logic["entry"], str):
            errors.append(ValidationError(
                severity=ValidationSeverity.ERROR,
                message=f"Logic 'entry' must be a string, got {type(logic['entry']).__name__}",
                field_path="logic.entry"
            ))

        if "exit" not in logic:
            errors.append(ValidationError(
                severity=ValidationSeverity.ERROR,
                message="Logic section missing 'exit'",
                field_path="logic"
            ))
        elif not isinstance(logic["exit"], str):
            errors.append(ValidationError(
                severity=ValidationSeverity.ERROR,
                message=f"Logic 'exit' must be a string, got {type(logic['exit']).__name__}",
                field_path="logic.exit"
            ))

        # Validate dependencies (optional)
        if "dependencies" in logic:
            if not isinstance(logic["dependencies"], list):
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Logic 'dependencies' must be a list, got {type(logic['dependencies']).__name__}",
                    field_path="logic.dependencies"
                ))
            else:
                for i, dep in enumerate(logic["dependencies"]):
                    if not isinstance(dep, str):
                        errors.append(ValidationError(
                            severity=ValidationSeverity.ERROR,
                            message=f"Dependency at index {i} must be a string",
                            field_path=f"logic.dependencies[{i}]"
                        ))

        # Validate entry/exit code using FieldValidator if available
        if self.field_validator is not None:
            if "entry" in logic and isinstance(logic["entry"], str):
                result = self.field_validator.validate(logic["entry"])
                for error in result.errors:
                    errors.append(ValidationError(
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid field in entry logic: {error.message}",
                        field_path="logic.entry",
                        line_number=error.line,
                        suggestion=error.suggestion
                    ))

            if "exit" in logic and isinstance(logic["exit"], str):
                result = self.field_validator.validate(logic["exit"])
                for error in result.errors:
                    errors.append(ValidationError(
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid field in exit logic: {error.message}",
                        field_path="logic.exit",
                        line_number=error.line,
                        suggestion=error.suggestion
                    ))

        return errors

    def validate_constraints(self, constraints: List[Any]) -> List[ValidationError]:
        """
        Validate constraints section.

        Each constraint must have:
        - type (str): Constraint type
        - condition (str): Condition expression
        - severity (str): One of VALID_SEVERITIES
        - message (str): Error message

        Args:
            constraints: List of constraint dictionaries

        Returns:
            List of validation errors

        Example:
            >>> validator = SchemaValidator()
            >>> constraints = [{
            ...     "type": "field_dependency",
            ...     "condition": "close > volume",
            ...     "severity": "critical",
            ...     "message": "Price must be greater than volume"
            ... }]
            >>> errors = validator.validate_constraints(constraints)
            >>> assert len(errors) == 0
        """
        errors = []

        for i, constraint in enumerate(constraints):
            if not isinstance(constraint, dict):
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Constraint at index {i} must be a dictionary",
                    field_path=f"constraints[{i}]"
                ))
                continue

            # Check required fields
            if "type" not in constraint:
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Constraint at index {i} missing 'type'",
                    field_path=f"constraints[{i}]"
                ))
            elif not isinstance(constraint["type"], str):
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Constraint 'type' must be a string",
                    field_path=f"constraints[{i}].type"
                ))

            if "condition" not in constraint:
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Constraint at index {i} missing 'condition'",
                    field_path=f"constraints[{i}]"
                ))
            elif not isinstance(constraint["condition"], str):
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Constraint 'condition' must be a string",
                    field_path=f"constraints[{i}].condition"
                ))

            if "severity" not in constraint:
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Constraint at index {i} missing 'severity'",
                    field_path=f"constraints[{i}]"
                ))
            elif constraint["severity"] not in self.VALID_SEVERITIES:
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid constraint severity: '{constraint['severity']}'",
                    field_path=f"constraints[{i}].severity",
                    suggestion=f"Valid severities are: {', '.join(self.VALID_SEVERITIES)}"
                ))

            if "message" not in constraint:
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Constraint at index {i} missing 'message'",
                    field_path=f"constraints[{i}]"
                ))
            elif not isinstance(constraint["message"], str):
                errors.append(ValidationError(
                    severity=ValidationSeverity.ERROR,
                    message=f"Constraint 'message' must be a string",
                    field_path=f"constraints[{i}].message"
                ))

        return errors
