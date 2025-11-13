"""
YAML Schema Validator Usage Examples

Demonstrates how to use the YAMLSchemaValidator to validate
trading strategy specifications.
"""

from pathlib import Path
from src.generators.yaml_schema_validator import YAMLSchemaValidator


def main():
    """Demonstrate validator usage."""

    # Initialize validator
    print("=" * 70)
    print("YAML Schema Validator - Usage Examples")
    print("=" * 70)
    print()

    validator = YAMLSchemaValidator()
    print(f"✓ Validator initialized with schema version {validator.schema_version}")
    print()

    # Example 1: Validate from file
    print("Example 1: Validate from YAML file")
    print("-" * 70)

    yaml_file = "examples/yaml_strategies/test_valid_momentum.yaml"
    is_valid, errors = validator.load_and_validate(yaml_file)

    print(f"File: {yaml_file}")
    print(f"Valid: {is_valid}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ No validation errors")
    print()

    # Example 2: Validate in-memory spec
    print("Example 2: Validate in-memory specification")
    print("-" * 70)

    spec = {
        "metadata": {
            "name": "Example Strategy",
            "description": "A test strategy for demonstration",
            "strategy_type": "momentum",
            "rebalancing_frequency": "M",
            "version": "1.0.0"
        },
        "indicators": {
            "technical_indicators": [
                {
                    "name": "rsi_14",
                    "type": "RSI",
                    "period": 14,
                    "source": "data.get('RSI_14')"
                }
            ]
        },
        "entry_conditions": {
            "threshold_rules": [
                {
                    "condition": "rsi_14 > 50",
                    "description": "RSI shows upward momentum"
                }
            ]
        }
    }

    is_valid, errors = validator.validate(spec)
    print(f"Valid: {is_valid}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ No validation errors")
    print()

    # Example 3: Detect missing required fields
    print("Example 3: Detect missing required fields")
    print("-" * 70)

    incomplete_spec = {
        "metadata": {
            "name": "Incomplete Strategy"
            # Missing: strategy_type and rebalancing_frequency
        },
        "indicators": {
            "technical_indicators": []
        },
        "entry_conditions": {
            "threshold_rules": []
        }
    }

    is_valid, errors = validator.validate(incomplete_spec)
    print(f"Valid: {is_valid}")
    print("Errors:")
    for error in errors:
        print(f"  - {error}")
    print()

    # Example 4: Detect invalid field values
    print("Example 4: Detect invalid field values")
    print("-" * 70)

    invalid_spec = {
        "metadata": {
            "name": "Invalid Strategy",
            "strategy_type": "bad_type",  # Invalid enum value
            "rebalancing_frequency": "DAILY"  # Invalid enum value
        },
        "indicators": {
            "technical_indicators": [
                {
                    "name": "invalid-name!",  # Invalid pattern
                    "type": "INVALID_TYPE",  # Invalid enum value
                    "period": 500  # Out of range
                }
            ]
        },
        "entry_conditions": {
            "threshold_rules": []
        }
    }

    is_valid, errors = validator.validate(invalid_spec)
    print(f"Valid: {is_valid}")
    print(f"Total errors found: {len(errors)}")
    print("First 3 errors:")
    for error in errors[:3]:
        print(f"  - {error}")
    print()

    # Example 5: Validate indicator references
    print("Example 5: Validate indicator references (cross-field validation)")
    print("-" * 70)

    spec_with_refs = {
        "metadata": {
            "name": "Factor Strategy",
            "strategy_type": "factor_combination",
            "rebalancing_frequency": "M"
        },
        "indicators": {
            "fundamental_factors": [
                {
                    "name": "roe",
                    "field": "ROE",
                    "source": "data.get('ROE')"
                }
            ]
        },
        "entry_conditions": {
            "ranking_rules": [
                {
                    "field": "nonexistent_field",  # This field doesn't exist!
                    "method": "top_percent",
                    "value": 20
                }
            ]
        }
    }

    # First validate schema
    is_valid, schema_errors = validator.validate(spec_with_refs)
    print(f"Schema valid: {is_valid}")

    # Then validate indicator references
    ref_valid, ref_errors = validator.validate_indicator_references(spec_with_refs)
    print(f"References valid: {ref_valid}")
    if ref_errors:
        print("Reference errors:")
        for error in ref_errors:
            print(f"  - {error}")
    print()

    # Example 6: Batch validate multiple files
    print("Example 6: Batch validate all example files")
    print("-" * 70)

    examples_dir = Path("examples/yaml_strategies")
    yaml_files = list(examples_dir.glob("*.yaml"))

    valid_count = 0
    invalid_count = 0

    for yaml_file in yaml_files:
        is_valid, errors = validator.load_and_validate(str(yaml_file))
        if is_valid:
            valid_count += 1
            status = "✓"
        else:
            invalid_count += 1
            status = "✗"

        print(f"{status} {yaml_file.name}: {is_valid} ({len(errors)} errors)")

    print()
    print(f"Summary: {valid_count} valid, {invalid_count} invalid")
    print()

    print("=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
