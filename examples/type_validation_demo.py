"""Demonstration of Type Validation Integration (Task 7.2).

This example shows how to use the new type validation methods in ValidationGateway
to prevent Phase 7 type regressions and ensure correct data types.

Run with:
    python3 examples/type_validation_demo.py
"""

import os
from typing import Dict, Any

# Enable validation layers
os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'

from src.validation.gateway import ValidationGateway
from src.backtest.metrics import StrategyMetrics


def demo_yaml_structure_validation():
    """Demonstrate YAML structure type validation."""
    print("=" * 70)
    print("1. YAML Structure Type Validation")
    print("=" * 70)

    gateway = ValidationGateway()

    # Valid YAML
    print("\n✓ Valid YAML structure:")
    valid_yaml: Dict[str, Any] = {
        "name": "Momentum Strategy",
        "type": "factor_graph",
        "required_fields": ["close", "volume"],
        "parameters": [
            {"name": "period", "type": "int", "value": 20}
        ],
        "logic": {
            "entry": "close > sma(close, 20)",
            "exit": "close < sma(close, 20)"
        }
    }

    result = gateway.validate_yaml_structure_types(valid_yaml)
    print(f"   Valid: {result.is_valid}")
    print(f"   Errors: {len(result.errors)}")

    # Invalid YAML - string instead of dict
    print("\n✗ Invalid YAML (string instead of dict):")
    invalid_yaml = "this is a string, not a dictionary"
    result = gateway.validate_yaml_structure_types(invalid_yaml)
    print(f"   Valid: {result.is_valid}")
    print(f"   Errors: {len(result.errors)}")
    if result.errors:
        for error in result.errors:
            print(f"   - {error.error_type}: {error.message}")
            if error.suggestion:
                print(f"     Suggestion: {error.suggestion}")

    # Invalid YAML - wrong field type
    print("\n✗ Invalid YAML (logic is list instead of dict):")
    invalid_yaml_2 = {
        "name": "Test",
        "type": "factor_graph",
        "required_fields": ["close"],
        "parameters": [],
        "logic": ["entry", "exit"]  # Should be dict!
    }
    result = gateway.validate_yaml_structure_types(invalid_yaml_2)
    print(f"   Valid: {result.is_valid}")
    if result.errors:
        for error in result.errors:
            print(f"   - {error.field_name}: {error.message}")


def demo_strategy_metrics_validation():
    """Demonstrate StrategyMetrics type validation."""
    print("\n" + "=" * 70)
    print("2. StrategyMetrics Type Validation")
    print("=" * 70)

    gateway = ValidationGateway()

    # Valid StrategyMetrics instance
    print("\n✓ Valid StrategyMetrics instance:")
    valid_metrics = StrategyMetrics(
        sharpe_ratio=1.5,
        total_return=0.25,
        max_drawdown=-0.15,
        win_rate=0.60,
        execution_success=True
    )

    result = gateway.validate_strategy_metrics_type(valid_metrics)
    print(f"   Valid: {result.is_valid}")
    print(f"   Type: {type(valid_metrics).__name__}")

    # Invalid - dict instead of StrategyMetrics
    print("\n✗ Invalid (dict instead of StrategyMetrics):")
    invalid_metrics = {
        'sharpe_ratio': 1.5,
        'total_return': 0.25,
        'max_drawdown': -0.15,
        'win_rate': 0.60,
        'execution_success': True
    }

    result = gateway.validate_strategy_metrics_type(invalid_metrics)
    print(f"   Valid: {result.is_valid}")
    print(f"   Type: {type(invalid_metrics).__name__}")
    if result.errors:
        for error in result.errors:
            print(f"   - {error.message}")
            if error.suggestion:
                print(f"     Suggestion: {error.suggestion}")

    # Show correct conversion
    print("\n✓ Correct way to convert dict to StrategyMetrics:")
    converted_metrics = StrategyMetrics.from_dict(invalid_metrics)
    result = gateway.validate_strategy_metrics_type(converted_metrics)
    print(f"   Valid: {result.is_valid}")
    print(f"   Type: {type(converted_metrics).__name__}")


def demo_parameter_validation():
    """Demonstrate parameter type validation."""
    print("\n" + "=" * 70)
    print("3. Parameter Type Validation")
    print("=" * 70)

    gateway = ValidationGateway()

    # Valid parameters
    print("\n✓ Valid parameters:")
    valid_params = [
        {"name": "period", "type": "int", "value": 20},
        {"name": "threshold", "type": "float", "value": 0.5},
        {"name": "enabled", "type": "bool", "value": True}
    ]

    result = gateway.validate_parameter_types(valid_params)
    print(f"   Valid: {result.is_valid}")
    for param in valid_params:
        print(f"   - {param['name']}: {param['type']} = {param['value']}")

    # Invalid parameters - type mismatch
    print("\n✗ Invalid parameters (type mismatch):")
    invalid_params = [
        {"name": "period", "type": "int", "value": "20"},  # String instead of int!
        {"name": "threshold", "type": "float", "value": "0.5"}  # String instead of float!
    ]

    result = gateway.validate_parameter_types(invalid_params)
    print(f"   Valid: {result.is_valid}")
    if result.errors:
        for error in result.errors:
            print(f"   - {error.field_name}: {error.message}")
            if error.suggestion:
                print(f"     Suggestion: {error.suggestion}")


def demo_required_fields_validation():
    """Demonstrate required_fields type validation."""
    print("\n" + "=" * 70)
    print("4. Required Fields Type Validation")
    print("=" * 70)

    gateway = ValidationGateway()

    # Valid required_fields
    print("\n✓ Valid required_fields (list of strings):")
    valid_yaml = {
        "required_fields": ["close", "volume", "open", "high", "low"]
    }

    result = gateway.validate_required_field_types(valid_yaml)
    print(f"   Valid: {result.is_valid}")
    print(f"   Fields: {valid_yaml['required_fields']}")

    # Invalid required_fields - not a list
    print("\n✗ Invalid required_fields (string instead of list):")
    invalid_yaml = {
        "required_fields": "close, volume"  # Should be a list!
    }

    result = gateway.validate_required_field_types(invalid_yaml)
    print(f"   Valid: {result.is_valid}")
    if result.errors:
        for error in result.errors:
            print(f"   - {error.field_name}: {error.message}")

    # Invalid required_fields - contains non-string
    print("\n✗ Invalid required_fields (contains non-string):")
    invalid_yaml_2 = {
        "required_fields": ["close", 123, "volume"]  # 123 is not a string!
    }

    result = gateway.validate_required_field_types(invalid_yaml_2)
    print(f"   Valid: {result.is_valid}")
    if result.errors:
        for error in result.errors:
            print(f"   - {error.field_name}: {error.message}")


def demo_comprehensive_validation():
    """Demonstrate comprehensive validation workflow."""
    print("\n" + "=" * 70)
    print("5. Comprehensive Validation Workflow")
    print("=" * 70)

    gateway = ValidationGateway()

    print("\nValidating a complete strategy YAML...")

    strategy_yaml = {
        "name": "Momentum Breakout",
        "type": "factor_graph",
        "required_fields": ["close", "volume", "high", "low"],
        "parameters": [
            {"name": "ma_period", "type": "int", "value": 20},
            {"name": "volume_threshold", "type": "float", "value": 1.5},
            {"name": "use_stops", "type": "bool", "value": True}
        ],
        "logic": {
            "entry": "close > sma(close, ma_period) and volume > volume_threshold * avg_volume",
            "exit": "close < sma(close, ma_period) or not use_stops"
        }
    }

    # Validate YAML structure
    print("\n   Step 1: Validate YAML structure types...")
    result1 = gateway.validate_yaml_structure_types(strategy_yaml)
    print(f"   ✓ YAML structure: {result1.is_valid}")

    # Validate required fields
    print("\n   Step 2: Validate required_fields types...")
    result2 = gateway.validate_required_field_types(strategy_yaml)
    print(f"   ✓ Required fields: {result2.is_valid}")

    # Validate parameters
    print("\n   Step 3: Validate parameter types...")
    result3 = gateway.validate_parameter_types(strategy_yaml['parameters'])
    print(f"   ✓ Parameters: {result3.is_valid}")

    # Check final status
    all_valid = result1.is_valid and result2.is_valid and result3.is_valid
    print(f"\n   Final status: {'✓ ALL VALID' if all_valid else '✗ ERRORS FOUND'}")

    if not all_valid:
        print("\n   Errors:")
        for result in [result1, result2, result3]:
            for error in result.errors:
                print(f"   - {error.field_name}: {error.message}")


def main():
    """Run all type validation demonstrations."""
    print("\nType Validation Integration Demo (Task 7.2)")
    print("=" * 70)
    print("Preventing Phase 7 type regressions with comprehensive validation")
    print()

    demo_yaml_structure_validation()
    demo_strategy_metrics_validation()
    demo_parameter_validation()
    demo_required_fields_validation()
    demo_comprehensive_validation()

    print("\n" + "=" * 70)
    print("Demo complete! All type validation methods demonstrated.")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
