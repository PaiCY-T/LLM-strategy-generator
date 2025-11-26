"""Tests for Schema Validator

This module tests comprehensive schema validation for strategy YAML files.

Test Coverage:
- Valid schema passes validation
- Missing required keys rejected
- Invalid field names rejected with suggestions
- Invalid data types rejected
- Parameter validation
- Logic validation
- Constraint validation
"""

import pytest
from src.execution.schema_validator import (
    SchemaValidator,
    ValidationError,
    ValidationSeverity
)


class TestSchemaValidatorBasic:
    """Test basic schema validation functionality."""

    def test_valid_schema_passes(self):
        """Test that a valid schema passes validation."""
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test Strategy",
            "type": "factor_graph",
            "description": "Test description",
            "required_fields": ["close", "volume"],
            "parameters": [
                {
                    "name": "period",
                    "type": "int",
                    "value": 20,
                    "default": 14,
                    "range": [5, 100]
                }
            ],
            "logic": {
                "entry": "close > 100",
                "exit": "close < 90",
                "dependencies": ["close"]
            }
        }

        errors = validator.validate(yaml_dict)
        assert len(errors) == 0, f"Valid schema should pass, got errors: {errors}"

    def test_empty_dict_fails(self):
        """Test that empty dict fails validation."""
        validator = SchemaValidator()
        errors = validator.validate({})

        assert len(errors) > 0
        # Should have 5 errors for missing required keys
        error_messages = [e.message for e in errors]
        assert any("name" in msg for msg in error_messages)
        assert any("type" in msg for msg in error_messages)
        assert any("required_fields" in msg for msg in error_messages)
        assert any("parameters" in msg for msg in error_messages)
        assert any("logic" in msg for msg in error_messages)

    def test_non_dict_fails(self):
        """Test that non-dict input fails validation."""
        validator = SchemaValidator()
        errors = validator.validate("not a dict")

        assert len(errors) == 1
        assert "dictionary" in errors[0].message.lower()
        assert errors[0].severity == ValidationSeverity.ERROR


class TestSchemaStructureValidation:
    """Test YAML structure validation."""

    def test_missing_required_keys(self):
        """Test detection of missing required keys."""
        validator = SchemaValidator()

        # Missing all required keys
        yaml_dict = {"description": "Test"}
        errors = validator.validate_yaml_structure(yaml_dict)

        assert len(errors) == 5  # 5 required keys missing
        error_messages = [e.message for e in errors]
        assert any("name" in msg for msg in error_messages)
        assert any("type" in msg for msg in error_messages)
        assert any("required_fields" in msg for msg in error_messages)
        assert any("parameters" in msg for msg in error_messages)
        assert any("logic" in msg for msg in error_messages)

    def test_unknown_keys_warning(self):
        """Test warning for unknown keys."""
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": [],
            "parameters": [],
            "logic": {"entry": "", "exit": ""},
            "unknown_key": "value"
        }

        errors = validator.validate_yaml_structure(yaml_dict)
        assert len(errors) == 1
        assert errors[0].severity == ValidationSeverity.WARNING
        assert "unknown_key" in errors[0].message.lower()


class TestFieldTypeValidation:
    """Test data type validation."""

    def test_name_must_be_string(self):
        """Test that 'name' must be a string."""
        validator = SchemaValidator()

        yaml_dict = {"name": 123}
        errors = validator.validate_field_types(yaml_dict)

        assert len(errors) == 1
        assert "name" in errors[0].field_path
        assert "string" in errors[0].message

    def test_type_must_be_valid_value(self):
        """Test that 'type' must be a valid strategy type."""
        validator = SchemaValidator()

        yaml_dict = {"type": "invalid_type"}
        errors = validator.validate_field_types(yaml_dict)

        assert len(errors) == 1
        assert "type" in errors[0].field_path
        assert "invalid_type" in errors[0].message
        assert errors[0].suggestion is not None

    def test_required_fields_must_be_list(self):
        """Test that 'required_fields' must be a list."""
        validator = SchemaValidator()

        yaml_dict = {"required_fields": "not_a_list"}
        errors = validator.validate_field_types(yaml_dict)

        assert len(errors) == 1
        assert "required_fields" in errors[0].field_path
        assert "list" in errors[0].message

    def test_parameters_must_be_list(self):
        """Test that 'parameters' must be a list."""
        validator = SchemaValidator()

        yaml_dict = {"parameters": {"not": "a list"}}
        errors = validator.validate_field_types(yaml_dict)

        assert len(errors) == 1
        assert "parameters" in errors[0].field_path
        assert "list" in errors[0].message

    def test_logic_must_be_dict(self):
        """Test that 'logic' must be a dictionary."""
        validator = SchemaValidator()

        yaml_dict = {"logic": ["not", "a", "dict"]}
        errors = validator.validate_field_types(yaml_dict)

        assert len(errors) == 1
        assert "logic" in errors[0].field_path
        assert "dictionary" in errors[0].message

    def test_coverage_percentage_validation(self):
        """Test coverage_percentage range validation."""
        validator = SchemaValidator()

        # Test invalid type
        yaml_dict = {"coverage_percentage": "not_a_number"}
        errors = validator.validate_field_types(yaml_dict)
        assert len(errors) == 1
        assert "coverage_percentage" in errors[0].field_path

        # Test out of range (negative)
        yaml_dict = {"coverage_percentage": -10}
        errors = validator.validate_field_types(yaml_dict)
        assert len(errors) == 1
        assert "between 0 and 100" in errors[0].message

        # Test out of range (>100)
        yaml_dict = {"coverage_percentage": 150}
        errors = validator.validate_field_types(yaml_dict)
        assert len(errors) == 1
        assert "between 0 and 100" in errors[0].message

        # Test valid value
        yaml_dict = {"coverage_percentage": 75}
        errors = validator.validate_field_types(yaml_dict)
        assert len(errors) == 0


class TestRequiredFieldsValidation:
    """Test required_fields section validation."""

    def test_string_fields(self):
        """Test validation of string field names."""
        validator = SchemaValidator()

        fields = ["close", "volume", "high"]
        errors = validator.validate_required_fields(fields)

        # Without manifest, no field validation errors
        assert len(errors) == 0

    def test_dict_fields(self):
        """Test validation of dict field definitions."""
        validator = SchemaValidator()

        fields = [
            {
                "canonical_name": "price:收盤價",
                "alias": "close",
                "usage": "entry_exit"
            }
        ]
        errors = validator.validate_required_fields(fields)

        assert len(errors) == 0

    def test_missing_canonical_name(self):
        """Test error when dict field missing canonical_name."""
        validator = SchemaValidator()

        fields = [{"alias": "close", "usage": "entry"}]
        errors = validator.validate_required_fields(fields)

        assert len(errors) == 1
        assert "canonical_name" in errors[0].message

    def test_invalid_field_type(self):
        """Test error for invalid field type."""
        validator = SchemaValidator()

        fields = [123, "close"]  # 123 is invalid
        errors = validator.validate_required_fields(fields)

        assert len(errors) == 1
        assert "must be string or dict" in errors[0].message

    def test_invalid_alias_type(self):
        """Test error for invalid alias type."""
        validator = SchemaValidator()

        fields = [{
            "canonical_name": "close",
            "alias": 123  # Should be string
        }]
        errors = validator.validate_required_fields(fields)

        assert len(errors) == 1
        assert "alias" in errors[0].field_path


class TestParametersValidation:
    """Test parameters section validation."""

    def test_valid_parameter(self):
        """Test validation of valid parameter."""
        validator = SchemaValidator()

        params = [{
            "name": "period",
            "type": "int",
            "value": 20,
            "default": 14,
            "range": [5, 100]
        }]
        errors = validator.validate_parameters(params)

        assert len(errors) == 0

    def test_missing_required_fields(self):
        """Test error for missing required parameter fields."""
        validator = SchemaValidator()

        # Missing 'name'
        params = [{"type": "int", "value": 20}]
        errors = validator.validate_parameters(params)
        assert any("name" in e.message for e in errors)

        # Missing 'type'
        params = [{"name": "period", "value": 20}]
        errors = validator.validate_parameters(params)
        assert any("type" in e.message for e in errors)

        # Missing 'value'
        params = [{"name": "period", "type": "int"}]
        errors = validator.validate_parameters(params)
        assert any("value" in e.message for e in errors)

    def test_invalid_parameter_type(self):
        """Test error for invalid parameter type."""
        validator = SchemaValidator()

        params = [{
            "name": "period",
            "type": "invalid_type",
            "value": 20
        }]
        errors = validator.validate_parameters(params)

        assert len(errors) == 1
        assert "Invalid parameter type" in errors[0].message
        assert errors[0].suggestion is not None

    def test_type_mismatch(self):
        """Test error when value type doesn't match declared type."""
        validator = SchemaValidator()

        # Declare int, provide string
        params = [{
            "name": "period",
            "type": "int",
            "value": "not_an_int"
        }]
        errors = validator.validate_parameters(params)

        assert len(errors) == 1
        assert "type mismatch" in errors[0].message

    def test_range_validation(self):
        """Test parameter range validation."""
        validator = SchemaValidator()

        # Valid range
        params = [{
            "name": "period",
            "type": "int",
            "value": 20,
            "range": [5, 100]
        }]
        errors = validator.validate_parameters(params)
        assert len(errors) == 0

        # Invalid range format
        params = [{
            "name": "period",
            "type": "int",
            "value": 20,
            "range": [5]  # Should be [min, max]
        }]
        errors = validator.validate_parameters(params)
        assert any("list/tuple of [min, max]" in e.message for e in errors)

        # Min >= Max
        params = [{
            "name": "period",
            "type": "int",
            "value": 20,
            "range": [100, 5]
        }]
        errors = validator.validate_parameters(params)
        assert any("min must be less than max" in e.message for e in errors)

        # Value outside range
        params = [{
            "name": "period",
            "type": "int",
            "value": 200,
            "range": [5, 100]
        }]
        errors = validator.validate_parameters(params)
        assert any("outside range" in e.message for e in errors)

    def test_range_on_non_numeric_type(self):
        """Test warning when range specified for non-numeric type."""
        validator = SchemaValidator()

        params = [{
            "name": "name",
            "type": "str",
            "value": "test",
            "range": [0, 10]  # Range doesn't make sense for string
        }]
        errors = validator.validate_parameters(params)

        assert len(errors) == 1
        assert errors[0].severity == ValidationSeverity.WARNING
        assert "int/float" in errors[0].message


class TestLogicValidation:
    """Test logic section validation."""

    def test_valid_logic(self):
        """Test validation of valid logic section."""
        validator = SchemaValidator()

        logic = {
            "entry": "close > 100",
            "exit": "close < 90",
            "dependencies": ["close"]
        }
        errors = validator.validate_logic(logic)

        assert len(errors) == 0

    def test_missing_entry(self):
        """Test error when logic missing 'entry'."""
        validator = SchemaValidator()

        logic = {"exit": "close < 90"}
        errors = validator.validate_logic(logic)

        assert len(errors) == 1
        assert "entry" in errors[0].message

    def test_missing_exit(self):
        """Test error when logic missing 'exit'."""
        validator = SchemaValidator()

        logic = {"entry": "close > 100"}
        errors = validator.validate_logic(logic)

        assert len(errors) == 1
        assert "exit" in errors[0].message

    def test_invalid_entry_type(self):
        """Test error when entry is not a string."""
        validator = SchemaValidator()

        logic = {"entry": 123, "exit": "close < 90"}
        errors = validator.validate_logic(logic)

        assert len(errors) == 1
        assert "entry" in errors[0].field_path
        assert "string" in errors[0].message

    def test_invalid_dependencies_type(self):
        """Test error when dependencies is not a list."""
        validator = SchemaValidator()

        logic = {
            "entry": "close > 100",
            "exit": "close < 90",
            "dependencies": "not_a_list"
        }
        errors = validator.validate_logic(logic)

        assert len(errors) == 1
        assert "dependencies" in errors[0].field_path
        assert "list" in errors[0].message

    def test_invalid_dependency_item_type(self):
        """Test error when dependency item is not a string."""
        validator = SchemaValidator()

        logic = {
            "entry": "close > 100",
            "exit": "close < 90",
            "dependencies": ["close", 123]  # 123 is invalid
        }
        errors = validator.validate_logic(logic)

        assert len(errors) == 1
        assert "dependencies[1]" in errors[0].field_path


class TestConstraintsValidation:
    """Test constraints section validation."""

    def test_valid_constraint(self):
        """Test validation of valid constraint."""
        validator = SchemaValidator()

        constraints = [{
            "type": "field_dependency",
            "condition": "close > volume",
            "severity": "critical",
            "message": "Price must be greater than volume"
        }]
        errors = validator.validate_constraints(constraints)

        assert len(errors) == 0

    def test_missing_required_fields(self):
        """Test error for missing required constraint fields."""
        validator = SchemaValidator()

        # Missing 'type'
        constraints = [{
            "condition": "close > 0",
            "severity": "critical",
            "message": "Test"
        }]
        errors = validator.validate_constraints(constraints)
        assert any("type" in e.message for e in errors)

        # Missing 'condition'
        constraints = [{
            "type": "field_dependency",
            "severity": "critical",
            "message": "Test"
        }]
        errors = validator.validate_constraints(constraints)
        assert any("condition" in e.message for e in errors)

        # Missing 'severity'
        constraints = [{
            "type": "field_dependency",
            "condition": "close > 0",
            "message": "Test"
        }]
        errors = validator.validate_constraints(constraints)
        assert any("severity" in e.message for e in errors)

        # Missing 'message'
        constraints = [{
            "type": "field_dependency",
            "condition": "close > 0",
            "severity": "critical"
        }]
        errors = validator.validate_constraints(constraints)
        assert any("message" in e.message for e in errors)

    def test_invalid_severity(self):
        """Test error for invalid severity level."""
        validator = SchemaValidator()

        constraints = [{
            "type": "field_dependency",
            "condition": "close > 0",
            "severity": "invalid_severity",
            "message": "Test"
        }]
        errors = validator.validate_constraints(constraints)

        assert len(errors) == 1
        assert "Invalid constraint severity" in errors[0].message
        assert errors[0].suggestion is not None

    def test_invalid_constraint_type(self):
        """Test error when constraint is not a dict."""
        validator = SchemaValidator()

        constraints = ["not_a_dict"]
        errors = validator.validate_constraints(constraints)

        assert len(errors) == 1
        assert "must be a dictionary" in errors[0].message


class TestIntegration:
    """Test integration with Layer 1 and Layer 2 validation."""

    def test_integration_with_manifest(self):
        """Test integration with DataFieldManifest for field validation."""
        # Create mock manifest
        class MockManifest:
            def validate_field_with_suggestion(self, field_name):
                if field_name == "invalid_field":
                    return False, "Did you mean 'close'?"
                return True, None

        validator = SchemaValidator(manifest=MockManifest())

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close", "invalid_field"],
            "parameters": [],
            "logic": {"entry": "close > 100", "exit": "close < 90"}
        }

        errors = validator.validate(yaml_dict)

        # Should have error for invalid_field with suggestion
        field_errors = [e for e in errors if "invalid_field" in e.message]
        assert len(field_errors) == 1
        assert field_errors[0].suggestion == "Did you mean 'close'?"

    def test_integration_with_field_validator(self):
        """Test integration with FieldValidator for code validation."""
        # Create mock field validator
        class MockFieldError:
            def __init__(self, line, message, suggestion=None):
                self.line = line
                self.message = message
                self.suggestion = suggestion

        class MockValidationResult:
            def __init__(self, errors):
                self.errors = errors

        class MockFieldValidator:
            def validate(self, code):
                if "invalid_field" in code:
                    return MockValidationResult([
                        MockFieldError(1, "Invalid field: invalid_field", "Did you mean 'close'?")
                    ])
                return MockValidationResult([])

        validator = SchemaValidator(field_validator=MockFieldValidator())

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": [],
            "parameters": [],
            "logic": {
                "entry": "invalid_field > 100",
                "exit": "close < 90"
            }
        }

        errors = validator.validate(yaml_dict)

        # Should have error from field validator
        logic_errors = [e for e in errors if "Invalid field in entry logic" in e.message]
        assert len(logic_errors) == 1
        assert logic_errors[0].line_number == 1
        assert logic_errors[0].suggestion == "Did you mean 'close'?"


class TestErrorReporting:
    """Test error reporting and formatting."""

    def test_error_formatting(self):
        """Test ValidationError string formatting."""
        error = ValidationError(
            severity=ValidationSeverity.ERROR,
            message="Test error message",
            field_path="parameters[0].name",
            line_number=42,
            suggestion="Try using 'correct_name' instead"
        )

        error_str = str(error)
        assert "ERROR:" in error_str
        assert "Test error message" in error_str
        assert "Field: parameters[0].name" in error_str
        assert "Line: 42" in error_str
        assert "Suggestion: Try using 'correct_name' instead" in error_str

    def test_error_without_optional_fields(self):
        """Test ValidationError formatting without optional fields."""
        error = ValidationError(
            severity=ValidationSeverity.WARNING,
            message="Warning message",
            field_path="<root>"
        )

        error_str = str(error)
        assert "WARNING:" in error_str
        assert "Warning message" in error_str
        assert "Field: <root>" in error_str
        assert "Line:" not in error_str  # No line number
        assert "Suggestion:" not in error_str  # No suggestion


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
