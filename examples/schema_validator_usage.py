"""Schema Validator Usage Examples

This example demonstrates how to use the SchemaValidator to validate
strategy YAML files with comprehensive error reporting.

Usage:
    python examples/schema_validator_usage.py
"""

from src.execution.schema_validator import SchemaValidator, ValidationSeverity


def example_valid_schema():
    """Example 1: Valid schema passes validation."""
    print("=" * 80)
    print("Example 1: Valid Schema")
    print("=" * 80)

    validator = SchemaValidator()

    yaml_dict = {
        "name": "Momentum Strategy",
        "type": "factor_graph",
        "description": "A momentum-based trading strategy",
        "required_fields": [
            "close",
            "volume",
            "high",
            "low"
        ],
        "parameters": [
            {
                "name": "momentum_period",
                "type": "int",
                "value": 20,
                "default": 14,
                "range": [5, 100]
            },
            {
                "name": "threshold",
                "type": "float",
                "value": 0.05,
                "default": 0.03,
                "range": [0.01, 0.20]
            }
        ],
        "logic": {
            "entry": "data.get('close') > data.get('high').shift(20)",
            "exit": "data.get('close') < data.get('low').shift(10)",
            "dependencies": ["close", "high", "low"]
        }
    }

    errors = validator.validate(yaml_dict)

    if not errors:
        print("✅ Schema validation PASSED")
        print(f"   Strategy: {yaml_dict['name']}")
        print(f"   Type: {yaml_dict['type']}")
        print(f"   Fields: {len(yaml_dict['required_fields'])}")
        print(f"   Parameters: {len(yaml_dict['parameters'])}")
    else:
        print("❌ Schema validation FAILED")
        for error in errors:
            print(f"\n{error}")

    print()


def example_missing_required_keys():
    """Example 2: Missing required keys."""
    print("=" * 80)
    print("Example 2: Missing Required Keys")
    print("=" * 80)

    validator = SchemaValidator()

    yaml_dict = {
        "name": "Incomplete Strategy",
        "description": "Missing required fields"
        # Missing: type, required_fields, parameters, logic
    }

    errors = validator.validate(yaml_dict)

    print(f"Found {len(errors)} error(s):\n")
    for error in errors:
        print(f"  • {error.message}")
        if error.suggestion:
            print(f"    💡 {error.suggestion}")

    print()


def example_invalid_data_types():
    """Example 3: Invalid data types."""
    print("=" * 80)
    print("Example 3: Invalid Data Types")
    print("=" * 80)

    validator = SchemaValidator()

    yaml_dict = {
        "name": 123,  # Should be string
        "type": "invalid_type",  # Invalid value
        "required_fields": "not_a_list",  # Should be list
        "parameters": {"not": "a list"},  # Should be list
        "logic": ["not", "a", "dict"]  # Should be dict
    }

    errors = validator.validate(yaml_dict)

    print(f"Found {len(errors)} error(s):\n")
    for error in errors:
        severity_icon = "🔴" if error.severity == ValidationSeverity.ERROR else "🟡"
        print(f"{severity_icon} {error.field_path}: {error.message}")
        if error.suggestion:
            print(f"   💡 {error.suggestion}")

    print()


def example_parameter_validation():
    """Example 4: Parameter validation."""
    print("=" * 80)
    print("Example 4: Parameter Validation")
    print("=" * 80)

    validator = SchemaValidator()

    yaml_dict = {
        "name": "Test Strategy",
        "type": "factor_graph",
        "required_fields": ["close"],
        "parameters": [
            {
                # Missing 'name'
                "type": "int",
                "value": 20
            },
            {
                "name": "period",
                "type": "invalid_type",  # Invalid type
                "value": 20
            },
            {
                "name": "threshold",
                "type": "int",
                "value": "not_an_int"  # Type mismatch
            },
            {
                "name": "window",
                "type": "int",
                "value": 200,  # Outside range
                "range": [5, 100]
            }
        ],
        "logic": {
            "entry": "close > 100",
            "exit": "close < 90"
        }
    }

    errors = validator.validate(yaml_dict)

    print(f"Found {len(errors)} parameter error(s):\n")
    param_errors = [e for e in errors if "parameters" in e.field_path]
    for error in param_errors:
        print(f"  🔴 {error.field_path}")
        print(f"     {error.message}")
        if error.suggestion:
            print(f"     💡 {error.suggestion}")

    print()


def example_logic_validation():
    """Example 5: Logic validation."""
    print("=" * 80)
    print("Example 5: Logic Validation")
    print("=" * 80)

    validator = SchemaValidator()

    yaml_dict = {
        "name": "Test Strategy",
        "type": "factor_graph",
        "required_fields": ["close"],
        "parameters": [],
        "logic": {
            # Missing 'exit'
            "entry": "close > 100",
            "dependencies": "not_a_list"  # Should be list
        }
    }

    errors = validator.validate(yaml_dict)

    print(f"Found {len(errors)} logic error(s):\n")
    logic_errors = [e for e in errors if "logic" in e.field_path]
    for error in logic_errors:
        print(f"  🔴 {error.message}")
        print(f"     Field: {error.field_path}")

    print()


def example_constraint_validation():
    """Example 6: Constraint validation."""
    print("=" * 80)
    print("Example 6: Constraint Validation")
    print("=" * 80)

    validator = SchemaValidator()

    yaml_dict = {
        "name": "Test Strategy",
        "type": "factor_graph",
        "required_fields": ["close"],
        "parameters": [],
        "logic": {
            "entry": "close > 100",
            "exit": "close < 90"
        },
        "constraints": [
            {
                "type": "field_dependency",
                "condition": "close > volume",
                "severity": "critical",
                "message": "Price must be greater than volume"
            },
            {
                # Missing 'type'
                "condition": "close > 0",
                "severity": "invalid_severity",  # Invalid severity
                "message": "Test"
            }
        ]
    }

    errors = validator.validate(yaml_dict)

    print(f"Found {len(errors)} constraint error(s):\n")
    constraint_errors = [e for e in errors if "constraints" in e.field_path]
    for error in constraint_errors:
        print(f"  🔴 {error.field_path}")
        print(f"     {error.message}")
        if error.suggestion:
            print(f"     💡 {error.suggestion}")

    print()


def example_with_manifest_integration():
    """Example 7: Integration with DataFieldManifest."""
    print("=" * 80)
    print("Example 7: Integration with DataFieldManifest")
    print("=" * 80)

    # Create mock manifest for demonstration
    class MockManifest:
        def validate_field_with_suggestion(self, field_name):
            valid_fields = {"close", "volume", "high", "low", "open"}
            if field_name in valid_fields:
                return True, None
            # Provide suggestion for common mistakes
            if field_name == "price":
                return False, "Did you mean 'close'?"
            if field_name == "vol":
                return False, "Did you mean 'volume'?"
            return False, f"Unknown field. Valid fields: {', '.join(valid_fields)}"

    validator = SchemaValidator(manifest=MockManifest())

    yaml_dict = {
        "name": "Test Strategy",
        "type": "factor_graph",
        "required_fields": [
            "close",
            "price",  # Invalid - should be 'close'
            "vol"     # Invalid - should be 'volume'
        ],
        "parameters": [],
        "logic": {
            "entry": "close > 100",
            "exit": "close < 90"
        }
    }

    errors = validator.validate(yaml_dict)

    print(f"Found {len(errors)} field error(s):\n")
    field_errors = [e for e in errors if "required_fields" in e.field_path]
    for error in field_errors:
        print(f"  🔴 {error.message}")
        if error.suggestion:
            print(f"     💡 Suggestion: {error.suggestion}")

    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Schema Validator Usage Examples" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    example_valid_schema()
    example_missing_required_keys()
    example_invalid_data_types()
    example_parameter_validation()
    example_logic_validation()
    example_constraint_validation()
    example_with_manifest_integration()

    print("=" * 80)
    print("All examples completed!")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
