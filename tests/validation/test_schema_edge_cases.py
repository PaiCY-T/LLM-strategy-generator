"""Comprehensive Edge Case Tests for Task 5.3 - SchemaValidator Edge Cases.

This test suite validates 100% of malformed YAML is caught before parsing by testing
20+ edge cases across all validation categories.

**TDD Phase**: RED → GREEN (SchemaValidator already implemented)

Test Categories:
1. Structure Errors (6 tests): Non-dict YAML, missing required keys, unknown keys
2. Type Errors (6 tests): Invalid types for name, type, required_fields, parameters, logic, constraints
3. required_fields Errors (3 tests): Invalid field types, missing canonical_name, invalid alias/usage
4. parameters Errors (5 tests): Invalid parameter structure, missing fields, type mismatches, range errors
5. logic Errors (3 tests): Missing entry/exit, invalid types, invalid dependencies
6. constraints Errors (3 tests): Invalid constraint structure, missing fields, invalid severity
7. Boundary Cases (4 tests): Empty lists, null values, nested errors, coverage_percentage range

Total: 30 Edge Case Tests

Requirements:
- AC3.3: 100% of malformed YAML caught before parsing
- NFR-Q4: 90%+ actionable error messages with suggestions
- Task 5.3: Comprehensive YAML error test suite
"""

import os
import pytest

from src.execution.schema_validator import SchemaValidator, ValidationError, ValidationSeverity
from src.config.feature_flags import FeatureFlagManager


class TestSchemaEdgeCases:
    """Comprehensive edge case test suite for SchemaValidator."""

    def setup_method(self):
        """Reset FeatureFlagManager singleton before each test."""
        FeatureFlagManager._instance = None
        if hasattr(FeatureFlagManager, '_initialized'):
            delattr(FeatureFlagManager, '_initialized')

    def teardown_method(self):
        """Clean up after each test."""
        FeatureFlagManager._instance = None

    # ==================== Category 1: Structure Errors (6 tests) ====================

    def test_edge_case_01_yaml_not_dictionary(self):
        """
        Edge Case 1: YAML is a list instead of dictionary.

        Given: YAML input is ["item1", "item2"] (list, not dict)
        When: SchemaValidator validates the YAML
        Then: Should return error: "YAML must be a dictionary/object"
        """
        validator = SchemaValidator()

        # Invalid: YAML is a list
        yaml_list = ["item1", "item2", "item3"]

        errors = validator.validate(yaml_list)

        assert len(errors) == 1, "Should have exactly 1 error"
        assert errors[0].severity == ValidationSeverity.ERROR
        assert "dictionary" in errors[0].message.lower()
        assert errors[0].field_path == "<root>"

    def test_edge_case_02_yaml_is_string(self):
        """
        Edge Case 2: YAML is a string instead of dictionary.

        Given: YAML input is "some string" (string, not dict)
        When: SchemaValidator validates the YAML
        Then: Should return error: "YAML must be a dictionary/object"
        """
        validator = SchemaValidator()

        # Invalid: YAML is a string
        yaml_string = "This is not a dictionary"

        errors = validator.validate(yaml_string)

        assert len(errors) == 1
        assert "dictionary" in errors[0].message.lower()

    def test_edge_case_03_missing_all_required_keys(self):
        """
        Edge Case 3: YAML dict is empty (missing all 5 required keys).

        Given: YAML dict is {}
        When: SchemaValidator validates the YAML
        Then: Should return 5 errors for missing: name, type, required_fields, parameters, logic
        """
        validator = SchemaValidator()

        # Invalid: Empty dictionary missing all required keys
        yaml_dict = {}

        errors = validator.validate(yaml_dict)

        # Should have 5 errors for missing required keys
        assert len(errors) == 5, f"Expected 5 errors, got {len(errors)}"

        # Verify all required keys are reported as missing
        error_messages = [e.message for e in errors]
        required_keys = ["name", "type", "required_fields", "parameters", "logic"]

        for key in required_keys:
            assert any(key in msg for msg in error_messages), \
                f"Missing error for required key: {key}"

    def test_edge_case_04_missing_partial_required_keys(self):
        """
        Edge Case 4: YAML dict missing 3 out of 5 required keys.

        Given: YAML dict with only name and type
        When: SchemaValidator validates the YAML
        Then: Should return 3 errors for missing: required_fields, parameters, logic
        """
        validator = SchemaValidator()

        # Invalid: Missing required_fields, parameters, logic
        yaml_dict = {
            "name": "Partial Strategy",
            "type": "factor_graph"
        }

        errors = validator.validate(yaml_dict)

        # Should have 3 errors for missing keys
        assert len(errors) == 3

        error_messages = [e.message for e in errors]
        assert any("required_fields" in msg for msg in error_messages)
        assert any("parameters" in msg for msg in error_messages)
        assert any("logic" in msg for msg in error_messages)

    def test_edge_case_05_unknown_top_level_keys(self):
        """
        Edge Case 5: YAML has unknown/invalid top-level keys.

        Given: YAML dict with invalid keys "invalid_key" and "random_field"
        When: SchemaValidator validates the YAML
        Then: Should return warnings for unknown keys with suggestions

        Requirements: NFR-Q4 (90%+ actionable error messages)
        """
        validator = SchemaValidator()

        # Valid structure but with unknown keys
        yaml_dict = {
            "name": "Test Strategy",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "true", "exit": "false"},
            "invalid_key": "should warn",
            "random_field": 123
        }

        errors = validator.validate(yaml_dict)

        # Should have 2 warnings for unknown keys
        warnings = [e for e in errors if e.severity == ValidationSeverity.WARNING]
        assert len(warnings) == 2, f"Expected 2 warnings, got {len(warnings)}"

        # Verify warnings have suggestions
        for warning in warnings:
            assert warning.suggestion is not None
            assert "Valid keys are:" in warning.suggestion

    def test_edge_case_06_multiple_structure_errors_combined(self):
        """
        Edge Case 6: Multiple structure errors in single YAML.

        Given: YAML with missing keys AND unknown keys
        When: SchemaValidator validates the YAML
        Then: Should return all errors (missing + warnings)
        """
        validator = SchemaValidator()

        # Missing 'logic' + unknown 'bad_key'
        yaml_dict = {
            "name": "Multi-Error Strategy",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "bad_key": "unknown"
        }

        errors = validator.validate(yaml_dict)

        # 1 error for missing 'logic' + 1 warning for 'bad_key'
        assert len(errors) == 2

        error_count = len([e for e in errors if e.severity == ValidationSeverity.ERROR])
        warning_count = len([e for e in errors if e.severity == ValidationSeverity.WARNING])

        assert error_count == 1  # Missing 'logic'
        assert warning_count == 1  # Unknown 'bad_key'

    # ==================== Category 2: Type Errors (6 tests) ====================

    def test_edge_case_07_name_wrong_type(self):
        """
        Edge Case 7: 'name' field is integer instead of string.

        Given: name = 123 (int instead of string)
        When: SchemaValidator validates the YAML
        Then: Should return error: "Field 'name' must be a string"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": 123,  # Invalid: should be string
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        assert len(errors) > 0
        name_errors = [e for e in errors if "name" in e.field_path]
        assert len(name_errors) == 1
        assert "string" in name_errors[0].message.lower()
        assert "int" in name_errors[0].message.lower()

    def test_edge_case_08_type_invalid_value(self):
        """
        Edge Case 8: 'type' field has invalid value (not in VALID_TYPES).

        Given: type = "invalid_type" (not in ["factor_graph", "llm_generated", "hybrid"])
        When: SchemaValidator validates the YAML
        Then: Should return error with suggestion of valid types

        Requirements: NFR-Q4 (actionable error messages)
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "invalid_type",  # Invalid: not in VALID_TYPES
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        type_errors = [e for e in errors if e.field_path == "type"]
        assert len(type_errors) == 1
        assert "Invalid strategy type" in type_errors[0].message
        assert type_errors[0].suggestion is not None
        assert "factor_graph" in type_errors[0].suggestion

    def test_edge_case_09_required_fields_not_list(self):
        """
        Edge Case 9: 'required_fields' is dictionary instead of list.

        Given: required_fields = {"field": "close"} (dict instead of list)
        When: SchemaValidator validates the YAML
        Then: Should return error: "Field 'required_fields' must be a list"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": {"field": "close"},  # Invalid: should be list
            "parameters": [],
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        required_fields_errors = [e for e in errors if "required_fields" in e.field_path]
        assert len(required_fields_errors) > 0
        assert "list" in required_fields_errors[0].message.lower()

    def test_edge_case_10_parameters_not_list(self):
        """
        Edge Case 10: 'parameters' is string instead of list.

        Given: parameters = "param1" (string instead of list)
        When: SchemaValidator validates the YAML
        Then: Should return error: "Field 'parameters' must be a list"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": "not a list",  # Invalid: should be list
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        param_errors = [e for e in errors if e.field_path == "parameters"]
        assert len(param_errors) == 1
        assert "list" in param_errors[0].message.lower()

    def test_edge_case_11_logic_not_dict(self):
        """
        Edge Case 11: 'logic' is list instead of dictionary.

        Given: logic = ["entry", "exit"] (list instead of dict)
        When: SchemaValidator validates the YAML
        Then: Should return error: "Field 'logic' must be a dictionary"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": ["entry", "exit"]  # Invalid: should be dict
        }

        errors = validator.validate(yaml_dict)

        logic_errors = [e for e in errors if e.field_path == "logic"]
        assert len(logic_errors) == 1
        assert "dictionary" in logic_errors[0].message.lower()

    def test_edge_case_12_constraints_not_list(self):
        """
        Edge Case 12: 'constraints' (optional) is integer instead of list.

        Given: constraints = 42 (int instead of list)
        When: SchemaValidator validates the YAML
        Then: Should return error: "Field 'constraints' must be a list"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "true", "exit": "false"},
            "constraints": 42  # Invalid: should be list
        }

        errors = validator.validate(yaml_dict)

        constraint_errors = [e for e in errors if e.field_path == "constraints"]
        assert len(constraint_errors) == 1
        assert "list" in constraint_errors[0].message.lower()

    # ==================== Category 3: required_fields Errors (3 tests) ====================

    def test_edge_case_13_required_fields_invalid_item_type(self):
        """
        Edge Case 13: required_fields contains integer instead of string/dict.

        Given: required_fields = ["close", 123, "volume"] (contains int)
        When: SchemaValidator validates the YAML
        Then: Should return error for item at index 1
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close", 123, "volume"],  # Invalid: 123 is int
            "parameters": [],
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        field_errors = [e for e in errors if "required_fields[1]" in e.field_path]
        assert len(field_errors) == 1
        assert "string or dict" in field_errors[0].message.lower()

    def test_edge_case_14_required_fields_dict_missing_canonical_name(self):
        """
        Edge Case 14: required_fields dict missing 'canonical_name' key.

        Given: required_fields = [{"alias": "price"}] (missing canonical_name)
        When: SchemaValidator validates the YAML
        Then: Should return error: "missing 'canonical_name'"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": [
                {"alias": "price", "usage": "entry"}  # Missing canonical_name
            ],
            "parameters": [],
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        canonical_errors = [e for e in errors if "canonical_name" in e.message]
        assert len(canonical_errors) == 1

    def test_edge_case_15_required_fields_invalid_alias_type(self):
        """
        Edge Case 15: required_fields dict has non-string 'alias'.

        Given: required_fields = [{"canonical_name": "close", "alias": 123}]
        When: SchemaValidator validates the YAML
        Then: Should return error: "'alias' must be a string"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": [
                {"canonical_name": "close", "alias": 123}  # alias should be string
            ],
            "parameters": [],
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        alias_errors = [e for e in errors if "alias" in e.field_path]
        assert len(alias_errors) == 1
        assert "string" in alias_errors[0].message.lower()

    # ==================== Category 4: parameters Errors (5 tests) ====================

    def test_edge_case_16_parameters_item_not_dict(self):
        """
        Edge Case 16: parameters list contains string instead of dict.

        Given: parameters = ["param1", "param2"] (strings instead of dicts)
        When: SchemaValidator validates the YAML
        Then: Should return errors for each non-dict item
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": ["param1", "param2"],  # Invalid: should be dicts
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        param_errors = [e for e in errors if "parameters[" in e.field_path and "dictionary" in e.message.lower()]
        assert len(param_errors) == 2  # Both parameters are invalid

    def test_edge_case_17_parameter_missing_required_fields(self):
        """
        Edge Case 17: parameter dict missing required fields (name, type, value).

        Given: parameters = [{"description": "A parameter"}] (missing name, type, value)
        When: SchemaValidator validates the YAML
        Then: Should return 3 errors for missing required fields
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [
                {"description": "Missing required fields"}  # Missing name, type, value
            ],
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        param_errors = [e for e in errors if "parameters[0]" in e.field_path]
        assert len(param_errors) >= 3  # At least 3 errors for missing fields

    def test_edge_case_18_parameter_invalid_type_value(self):
        """
        Edge Case 18: parameter 'type' is invalid (not in VALID_PARAM_TYPES).

        Given: parameters = [{"name": "x", "type": "invalid_type", "value": 1}]
        When: SchemaValidator validates the YAML
        Then: Should return error with suggestion of valid types
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [
                {"name": "x", "type": "invalid_type", "value": 1}
            ],
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        type_errors = [e for e in errors if "Invalid parameter type" in e.message]
        assert len(type_errors) == 1
        assert type_errors[0].suggestion is not None
        assert "int" in type_errors[0].suggestion

    def test_edge_case_19_parameter_value_type_mismatch(self):
        """
        Edge Case 19: parameter 'value' type doesn't match declared 'type'.

        Given: parameters = [{"name": "x", "type": "int", "value": "not_an_int"}]
        When: SchemaValidator validates the YAML
        Then: Should return error: "value type mismatch"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [
                {"name": "x", "type": "int", "value": "not_an_int"}  # Type mismatch
            ],
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        mismatch_errors = [e for e in errors if "type mismatch" in e.message.lower()]
        assert len(mismatch_errors) == 1

    def test_edge_case_20_parameter_range_invalid_structure(self):
        """
        Edge Case 20: parameter 'range' is not a list of 2 elements.

        Given: parameters = [{"name": "x", "type": "int", "value": 5, "range": [1, 2, 3]}]
        When: SchemaValidator validates the YAML
        Then: Should return error: "range must be a list/tuple of [min, max]"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [
                {"name": "x", "type": "int", "value": 5, "range": [1, 2, 3]}  # Invalid: 3 elements
            ],
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        range_errors = [e for e in errors if "range" in e.field_path and "[min, max]" in e.message]
        assert len(range_errors) == 1

    # ==================== Category 5: logic Errors (3 tests) ====================

    def test_edge_case_21_logic_missing_entry(self):
        """
        Edge Case 21: logic dict missing required 'entry' key.

        Given: logic = {"exit": "close < 90"} (missing 'entry')
        When: SchemaValidator validates the YAML
        Then: Should return error: "Logic section missing 'entry'"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"exit": "close < 90"}  # Missing 'entry'
        }

        errors = validator.validate(yaml_dict)

        entry_errors = [e for e in errors if "entry" in e.message.lower() and "missing" in e.message.lower()]
        assert len(entry_errors) == 1

    def test_edge_case_22_logic_entry_not_string(self):
        """
        Edge Case 22: logic 'entry' is integer instead of string.

        Given: logic = {"entry": 123, "exit": "close < 90"}
        When: SchemaValidator validates the YAML
        Then: Should return error: "'entry' must be a string"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": 123, "exit": "close < 90"}  # entry should be string
        }

        errors = validator.validate(yaml_dict)

        entry_type_errors = [e for e in errors if "logic.entry" in e.field_path and "string" in e.message.lower()]
        assert len(entry_type_errors) == 1

    def test_edge_case_23_logic_dependencies_invalid_item(self):
        """
        Edge Case 23: logic 'dependencies' list contains non-string item.

        Given: logic = {..., "dependencies": ["close", 123, "volume"]}
        When: SchemaValidator validates the YAML
        Then: Should return error for non-string dependency at index 1
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {
                "entry": "close > 100",
                "exit": "close < 90",
                "dependencies": ["close", 123, "volume"]  # 123 is invalid
            }
        }

        errors = validator.validate(yaml_dict)

        dep_errors = [e for e in errors if "dependencies[1]" in e.field_path]
        assert len(dep_errors) == 1
        assert "string" in dep_errors[0].message.lower()

    # ==================== Category 6: constraints Errors (3 tests) ====================

    def test_edge_case_24_constraints_item_not_dict(self):
        """
        Edge Case 24: constraints list contains string instead of dict.

        Given: constraints = ["constraint1"] (string instead of dict)
        When: SchemaValidator validates the YAML
        Then: Should return error: "Constraint at index 0 must be a dictionary"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "true", "exit": "false"},
            "constraints": ["constraint1"]  # Invalid: should be dict
        }

        errors = validator.validate(yaml_dict)

        constraint_errors = [e for e in errors if "constraints[0]" in e.field_path and "dictionary" in e.message.lower()]
        assert len(constraint_errors) == 1

    def test_edge_case_25_constraint_missing_all_required_fields(self):
        """
        Edge Case 25: constraint dict missing all required fields.

        Given: constraints = [{"description": "A constraint"}] (missing type, condition, severity, message)
        When: SchemaValidator validates the YAML
        Then: Should return 4 errors for missing required fields
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "true", "exit": "false"},
            "constraints": [
                {"description": "Missing required fields"}
            ]
        }

        errors = validator.validate(yaml_dict)

        constraint_errors = [e for e in errors if "constraints[0]" in e.field_path and "missing" in e.message.lower()]
        assert len(constraint_errors) >= 4  # type, condition, severity, message

    def test_edge_case_26_constraint_invalid_severity(self):
        """
        Edge Case 26: constraint 'severity' is invalid value.

        Given: constraints = [{..., "severity": "invalid_severity"}]
        When: SchemaValidator validates the YAML
        Then: Should return error with suggestion of valid severities
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "true", "exit": "false"},
            "constraints": [
                {
                    "type": "field_check",
                    "condition": "close > 0",
                    "severity": "invalid_severity",  # Invalid
                    "message": "Test"
                }
            ]
        }

        errors = validator.validate(yaml_dict)

        severity_errors = [e for e in errors if "Invalid constraint severity" in e.message]
        assert len(severity_errors) == 1
        assert severity_errors[0].suggestion is not None
        assert "critical" in severity_errors[0].suggestion

    # ==================== Category 7: Boundary Cases (4 tests) ====================

    def test_edge_case_27_empty_required_fields_list(self):
        """
        Edge Case 27: required_fields is empty list (valid but unusual).

        Given: required_fields = []
        When: SchemaValidator validates the YAML
        Then: Should validate successfully (empty list is valid)
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": [],  # Empty but valid
            "parameters": [],
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        # Should have no errors (empty lists are valid)
        assert len(errors) == 0

    def test_edge_case_28_coverage_percentage_out_of_range(self):
        """
        Edge Case 28: coverage_percentage outside valid range 0-100.

        Given: coverage_percentage = 150 (>100)
        When: SchemaValidator validates the YAML
        Then: Should return error: "must be between 0 and 100"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "true", "exit": "false"},
            "coverage_percentage": 150  # Invalid: >100
        }

        errors = validator.validate(yaml_dict)

        coverage_errors = [e for e in errors if "coverage_percentage" in e.field_path]
        assert len(coverage_errors) == 1
        assert "0 and 100" in coverage_errors[0].message

    def test_edge_case_29_parameter_value_outside_range(self):
        """
        Edge Case 29: parameter value outside specified range.

        Given: parameters = [{"name": "x", "type": "int", "value": 200, "range": [1, 100]}]
        When: SchemaValidator validates the YAML
        Then: Should return error: "value 200 outside range [1, 100]"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [
                {
                    "name": "x",
                    "type": "int",
                    "value": 200,  # Outside range
                    "range": [1, 100]
                }
            ],
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        range_errors = [e for e in errors if "outside range" in e.message.lower()]
        assert len(range_errors) == 1

    def test_edge_case_30_parameter_range_min_greater_than_max(self):
        """
        Edge Case 30: parameter range has min >= max (invalid).

        Given: parameters = [{..., "range": [100, 50]}] (min > max)
        When: SchemaValidator validates the YAML
        Then: Should return error: "min must be less than max"
        """
        validator = SchemaValidator()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [
                {
                    "name": "x",
                    "type": "int",
                    "value": 75,
                    "range": [100, 50]  # Invalid: min > max
                }
            ],
            "logic": {"entry": "true", "exit": "false"}
        }

        errors = validator.validate(yaml_dict)

        min_max_errors = [e for e in errors if "min must be less than max" in e.message.lower()]
        assert len(min_max_errors) == 1


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])
