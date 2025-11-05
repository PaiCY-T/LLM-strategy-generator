"""
YAML Interpreter Usage Examples
================================

Demonstrates how to use the YAMLInterpreter to convert declarative YAML
configurations into executable Strategy objects.

Architecture: Structural Mutation Phase 2 - Phase D.2
Task: D.2 - YAML → Factor Interpreter

Examples:
---------
1. Basic usage: Load YAML → Strategy
2. Validation before interpretation
3. Custom factor parameters
4. Error handling patterns
5. Integration with evolution loop
6. Strategy execution with backtest data
"""

import pandas as pd
from pathlib import Path

from src.tier1 import YAMLInterpreter, YAMLValidator, InterpretationError
from src.factor_library import FactorRegistry


# ============================================================================
# Example 1: Basic Usage - Load YAML → Strategy
# ============================================================================

def example_basic_usage():
    """
    Basic usage: Load YAML file and create Strategy.
    """
    print("=" * 70)
    print("Example 1: Basic Usage - Load YAML → Strategy")
    print("=" * 70)

    # Create interpreter
    interpreter = YAMLInterpreter()

    # Load YAML configuration
    yaml_path = "examples/yaml_strategies/momentum_basic.yaml"

    try:
        strategy = interpreter.from_file(yaml_path)

        print(f"✓ Successfully loaded strategy: {strategy.id}")
        print(f"  - Factors: {len(strategy.factors)}")
        print(f"  - Factor IDs: {list(strategy.factors.keys())}")
        print(f"  - Generation: {strategy.generation}")

        # Validate strategy
        strategy.validate()
        print("✓ Strategy validation passed")

    except FileNotFoundError:
        print(f"✗ Example file not found: {yaml_path}")
    except InterpretationError as e:
        print(f"✗ Interpretation error: {e}")
        print(f"  Context: {e.context}")

    print()


# ============================================================================
# Example 2: Validation Before Interpretation
# ============================================================================

def example_validation_first():
    """
    Validate YAML before interpretation (best practice).
    """
    print("=" * 70)
    print("Example 2: Validation Before Interpretation")
    print("=" * 70)

    # Create validator and interpreter
    validator = YAMLValidator()
    interpreter = YAMLInterpreter()

    yaml_path = "examples/yaml_strategies/turtle_exit_combo.yaml"

    try:
        # Step 1: Validate configuration
        print(f"Validating {yaml_path}...")
        result = validator.validate_file(yaml_path)

        if result.is_valid:
            print("✓ Configuration is valid")
            if result.warnings:
                print(f"  Warnings: {len(result.warnings)}")
                for warning in result.warnings:
                    print(f"    - {warning}")

            # Step 2: Interpret validated configuration
            print("Interpreting configuration...")
            strategy = interpreter.from_file(yaml_path)

            print(f"✓ Successfully created strategy: {strategy.id}")
            print(f"  - Factors: {len(strategy.factors)}")

            # Step 3: Validate strategy structure
            strategy.validate()
            print("✓ Strategy validation passed")

        else:
            print("✗ Configuration is invalid")
            for error in result.errors:
                print(f"  - {error}")

    except FileNotFoundError:
        print(f"✗ Example file not found: {yaml_path}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()


# ============================================================================
# Example 3: Custom Factor Parameters
# ============================================================================

def example_custom_parameters():
    """
    Create strategy from dictionary with custom parameters.
    """
    print("=" * 70)
    print("Example 3: Custom Factor Parameters")
    print("=" * 70)

    interpreter = YAMLInterpreter()

    # Define custom configuration
    config = {
        "strategy_id": "custom-momentum-strategy",
        "description": "Custom momentum strategy with adjusted parameters",
        "factors": [
            {
                "id": "momentum_30",
                "type": "momentum_factor",
                "parameters": {"momentum_period": 30},  # Custom period
                "depends_on": [],
                "enabled": True
            },
            {
                "id": "ma_filter_120",
                "type": "ma_filter_factor",
                "parameters": {"ma_periods": 120},  # Custom period
                "depends_on": [],
                "enabled": True
            },
            {
                "id": "trailing_stop_15",
                "type": "trailing_stop_factor",
                "parameters": {
                    "trail_percent": 0.15,  # 15% trailing stop
                    "activation_profit": 0.08  # 8% activation
                },
                "depends_on": ["momentum_30", "ma_filter_120"],
                "enabled": True
            }
        ]
    }

    try:
        # Interpret configuration
        strategy = interpreter.from_dict(config)

        print(f"✓ Created custom strategy: {strategy.id}")
        print(f"  - Factors: {len(strategy.factors)}")

        # Check factor parameters
        for factor_id, factor in strategy.factors.items():
            print(f"  - {factor_id}: {factor.parameters}")

        # Validate strategy
        strategy.validate()
        print("✓ Strategy validation passed")

    except InterpretationError as e:
        print(f"✗ Interpretation error: {e}")

    print()


# ============================================================================
# Example 4: Error Handling Patterns
# ============================================================================

def example_error_handling():
    """
    Demonstrate comprehensive error handling.
    """
    print("=" * 70)
    print("Example 4: Error Handling Patterns")
    print("=" * 70)

    interpreter = YAMLInterpreter()

    # Test various error conditions
    error_configs = [
        # Error 1: Unknown factor type
        {
            "strategy_id": "error-test-1",
            "factors": [
                {
                    "id": "unknown",
                    "type": "unknown_factor_type",
                    "parameters": {},
                    "depends_on": []
                }
            ]
        },
        # Error 2: Invalid parameters (out of range)
        {
            "strategy_id": "error-test-2",
            "factors": [
                {
                    "id": "momentum",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 1},  # Too small (min=5)
                    "depends_on": []
                }
            ]
        },
        # Error 3: Missing dependency
        {
            "strategy_id": "error-test-3",
            "factors": [
                {
                    "id": "factor_a",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20},
                    "depends_on": ["nonexistent_factor"]  # Missing
                }
            ]
        }
    ]

    for i, config in enumerate(error_configs, 1):
        print(f"\nError Test {i}: {config['strategy_id']}")
        try:
            strategy = interpreter.from_dict(config)
            print("  ✗ Expected error but succeeded")
        except InterpretationError as e:
            print(f"  ✓ Caught expected error: {e.message}")
            if e.context:
                print(f"    Context: {e.context}")

    print()


# ============================================================================
# Example 5: Integration with Evolution Loop
# ============================================================================

def example_evolution_integration():
    """
    Show how to use YAML interpreter in evolution loop.
    """
    print("=" * 70)
    print("Example 5: Integration with Evolution Loop")
    print("=" * 70)

    interpreter = YAMLInterpreter()
    registry = interpreter.get_registry()

    print(f"Available factor types: {len(registry.list_factors())}")

    # Simulate creating strategies from YAML templates
    template_files = [
        "examples/yaml_strategies/momentum_basic.yaml",
        "examples/yaml_strategies/turtle_exit_combo.yaml",
        "examples/yaml_strategies/multi_factor_complex.yaml"
    ]

    strategies = []
    for template_path in template_files:
        try:
            strategy = interpreter.from_file(template_path)
            strategies.append(strategy)
            print(f"✓ Loaded template: {strategy.id}")
        except FileNotFoundError:
            print(f"  Skipping missing template: {template_path}")
        except Exception as e:
            print(f"  Error loading {template_path}: {e}")

    print(f"\nTotal strategies loaded: {len(strategies)}")

    # Show strategy details
    for strategy in strategies:
        print(f"\n{strategy.id}:")
        print(f"  - Factors: {len(strategy.factors)}")
        print(f"  - Factor IDs: {list(strategy.factors.keys())}")

        # Get factors in execution order
        factors = strategy.get_factors()
        print(f"  - Execution order: {[f.id for f in factors]}")

    print()


# ============================================================================
# Example 6: Strategy Execution with Backtest Data
# ============================================================================

def example_strategy_execution():
    """
    Execute strategy pipeline with sample data.
    """
    print("=" * 70)
    print("Example 6: Strategy Execution with Backtest Data")
    print("=" * 70)

    interpreter = YAMLInterpreter()

    # Load strategy
    yaml_path = "examples/yaml_strategies/momentum_basic.yaml"

    try:
        strategy = interpreter.from_file(yaml_path)
        print(f"✓ Loaded strategy: {strategy.id}")

        # Create sample OHLCV data
        print("\nCreating sample OHLCV data...")
        data = pd.DataFrame({
            'open': [100, 102, 101, 103, 105, 104, 106, 108],
            'high': [101, 103, 102, 104, 106, 105, 107, 109],
            'low': [99, 101, 100, 102, 104, 103, 105, 107],
            'close': [100.5, 102.5, 101.5, 103.5, 105.5, 104.5, 106.5, 108.5],
            'volume': [1000, 1100, 1050, 1150, 1200, 1080, 1250, 1300]
        })

        print(f"  - Data shape: {data.shape}")
        print(f"  - Columns: {list(data.columns)}")

        # Execute strategy pipeline
        print("\nExecuting strategy pipeline...")
        result = strategy.to_pipeline(data)

        print(f"✓ Pipeline executed successfully")
        print(f"  - Result shape: {result.shape}")
        print(f"  - Result columns: {list(result.columns)}")

        # Show factor outputs
        print("\nFactor outputs:")
        for factor in strategy.get_factors():
            for output in factor.outputs:
                if output in result.columns:
                    print(f"  - {output} (from {factor.id})")

    except FileNotFoundError:
        print(f"✗ Example file not found: {yaml_path}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("YAML Interpreter Usage Examples")
    print("=" * 70 + "\n")

    # Run examples
    example_basic_usage()
    example_validation_first()
    example_custom_parameters()
    example_error_handling()
    example_evolution_integration()
    example_strategy_execution()

    print("=" * 70)
    print("All examples completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
