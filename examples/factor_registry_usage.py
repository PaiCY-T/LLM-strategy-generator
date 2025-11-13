"""
Factor Registry Usage Examples
===============================

Demonstrates factor discovery, creation, and validation using the Factor Registry.
Task: B.4 - Factor Registry Implementation

Examples:
1. Basic factor discovery and creation
2. Category-based discovery
3. Parameter validation
4. Creating factor pipelines
5. Mutation scenarios (replacing factors)

Architecture: Phase 2.0+ Factor Graph System
"""

import pandas as pd
from src.factor_library.registry import FactorRegistry
from src.factor_graph.factor_category import FactorCategory


def example_1_basic_discovery():
    """Example 1: Basic factor discovery and creation."""
    print("=" * 70)
    print("Example 1: Basic Factor Discovery and Creation")
    print("=" * 70)

    # Get registry instance
    registry = FactorRegistry.get_instance()

    # List all available factors
    all_factors = registry.list_factors()
    print(f"\nTotal factors available: {len(all_factors)}")
    print("Factors:", ", ".join(all_factors))

    # Get metadata for a specific factor
    print("\n--- Momentum Factor Metadata ---")
    metadata = registry.get_metadata("momentum_factor")
    print(f"Name: {metadata['name']}")
    print(f"Category: {metadata['category']}")
    print(f"Description: {metadata['description']}")
    print(f"Default Parameters: {metadata['parameters']}")
    print(f"Parameter Ranges: {metadata['parameter_ranges']}")

    # Create factor with default parameters
    print("\n--- Creating Factor with Defaults ---")
    momentum = registry.create_factor("momentum_factor")
    print(f"Created: {momentum.name}")
    print(f"Parameters: {momentum.parameters}")

    # Create factor with custom parameters
    print("\n--- Creating Factor with Custom Parameters ---")
    custom_momentum = registry.create_factor(
        "momentum_factor",
        parameters={"momentum_period": 30}
    )
    print(f"Created: {custom_momentum.name}")
    print(f"Parameters: {custom_momentum.parameters}")


def example_2_category_discovery():
    """Example 2: Category-based factor discovery."""
    print("\n" + "=" * 70)
    print("Example 2: Category-Based Factor Discovery")
    print("=" * 70)

    registry = FactorRegistry.get_instance()

    # Discover momentum factors
    print("\n--- Momentum Factors ---")
    momentum_factors = registry.get_momentum_factors()
    for name in momentum_factors:
        metadata = registry.get_metadata(name)
        print(f"  - {name}: {metadata['description']}")

    # Discover exit factors
    print("\n--- Exit Factors ---")
    exit_factors = registry.get_exit_factors()
    for name in exit_factors:
        metadata = registry.get_metadata(name)
        print(f"  - {name}: {metadata['description']}")

    # Discover entry factors
    print("\n--- Entry Factors ---")
    entry_factors = registry.get_entry_factors()
    for name in entry_factors:
        metadata = registry.get_metadata(name)
        print(f"  - {name}: {metadata['description']}")

    # Discover risk factors
    print("\n--- Risk Factors ---")
    risk_factors = registry.get_risk_factors()
    for name in risk_factors:
        metadata = registry.get_metadata(name)
        print(f"  - {name}: {metadata['description']}")

    # Use category-based filtering
    print("\n--- All Factors by Category ---")
    for category in FactorCategory:
        factors = registry.list_by_category(category)
        if factors:
            print(f"{category.value.upper()}: {len(factors)} factors")
            for name in factors:
                print(f"  - {name}")


def example_3_parameter_validation():
    """Example 3: Parameter validation before creation."""
    print("\n" + "=" * 70)
    print("Example 3: Parameter Validation")
    print("=" * 70)

    registry = FactorRegistry.get_instance()

    # Valid parameters
    print("\n--- Valid Parameters ---")
    params = {"momentum_period": 20}
    is_valid, msg = registry.validate_parameters("momentum_factor", params)
    print(f"Parameters: {params}")
    print(f"Valid: {is_valid}")
    if is_valid:
        factor = registry.create_factor("momentum_factor", params)
        print(f"✓ Successfully created: {factor.name}")

    # Invalid parameters (out of range)
    print("\n--- Invalid Parameters (Out of Range) ---")
    params = {"momentum_period": 1}  # Below minimum of 5
    is_valid, msg = registry.validate_parameters("momentum_factor", params)
    print(f"Parameters: {params}")
    print(f"Valid: {is_valid}")
    if not is_valid:
        print(f"✗ Error: {msg}")

    # Invalid parameters (above maximum)
    print("\n--- Invalid Parameters (Above Maximum) ---")
    params = {"momentum_period": 200}  # Above maximum of 100
    is_valid, msg = registry.validate_parameters("momentum_factor", params)
    print(f"Parameters: {params}")
    print(f"Valid: {is_valid}")
    if not is_valid:
        print(f"✗ Error: {msg}")

    # Unknown parameters
    print("\n--- Invalid Parameters (Unknown Parameter) ---")
    params = {"unknown_param": 10}
    is_valid, msg = registry.validate_parameters("momentum_factor", params)
    print(f"Parameters: {params}")
    print(f"Valid: {is_valid}")
    if not is_valid:
        print(f"✗ Error: {msg}")

    # Valid float parameters
    print("\n--- Valid Float Parameters ---")
    params = {"atr_multiplier": 2.5}
    is_valid, msg = registry.validate_parameters("atr_stop_loss_factor", params)
    print(f"Parameters: {params}")
    print(f"Valid: {is_valid}")
    if is_valid:
        factor = registry.create_factor("atr_stop_loss_factor", params)
        print(f"✓ Successfully created: {factor.name}")


def example_4_factor_pipeline():
    """Example 4: Creating and executing a factor pipeline."""
    print("\n" + "=" * 70)
    print("Example 4: Creating Factor Pipeline")
    print("=" * 70)

    registry = FactorRegistry.get_instance()

    # Create momentum pipeline
    print("\n--- Momentum + MA Filter Pipeline ---")
    momentum = registry.create_factor(
        "momentum_factor",
        parameters={"momentum_period": 10}
    )
    ma_filter = registry.create_factor(
        "ma_filter_factor",
        parameters={"ma_periods": 30}
    )

    print(f"Created pipeline:")
    print(f"  1. {momentum.name} (period={momentum.parameters['momentum_period']})")
    print(f"  2. {ma_filter.name} (periods={ma_filter.parameters['ma_periods']})")

    # Create test data
    data = pd.DataFrame({
        "close": [100, 102, 104, 103, 105, 107, 106, 108, 110, 112, 111, 113, 115]
    })

    print(f"\nTest data: {len(data)} rows")

    # Execute pipeline
    result = momentum.execute(data)
    result = ma_filter.execute(result)

    print(f"\nPipeline outputs:")
    print(f"  - momentum: {result['momentum'].notna().sum()} non-NaN values")
    print(f"  - ma_filter: {result['ma_filter'].sum()} True values")

    # Create exit pipeline
    print("\n--- Multi-Exit Strategy Pipeline ---")
    trailing_stop = registry.create_factor(
        "trailing_stop_factor",
        parameters={"trail_percent": 0.10, "activation_profit": 0.05}
    )
    profit_target = registry.create_factor(
        "profit_target_factor",
        parameters={"target_percent": 0.20}
    )
    composite_exit = registry.create_factor(
        "composite_exit_factor",
        parameters={
            "exit_signals": ["trailing_stop_signal", "profit_target_signal"]
        }
    )

    print(f"Created exit pipeline:")
    print(f"  1. {trailing_stop.name}")
    print(f"  2. {profit_target.name}")
    print(f"  3. {composite_exit.name}")

    # Create test data with positions
    exit_data = pd.DataFrame({
        "close": [100, 105, 110, 108, 115, 120, 118, 122, 125],
        "positions": [True] * 9,
        "entry_price": [100] * 9,
    })

    # Execute exit pipeline
    exit_result = trailing_stop.execute(exit_data)
    exit_result = profit_target.execute(exit_result)
    exit_result = composite_exit.execute(exit_result)

    print(f"\nExit pipeline outputs:")
    print(f"  - trailing_stop_signal: {exit_result['trailing_stop_signal'].sum()} triggers")
    print(f"  - profit_target_signal: {exit_result['profit_target_signal'].sum()} triggers")
    print(f"  - final_exit_signal: {exit_result['final_exit_signal'].sum()} total exits")


def example_5_mutation_scenario():
    """Example 5: Factor mutation - replacing one factor with another."""
    print("\n" + "=" * 70)
    print("Example 5: Factor Mutation Scenario")
    print("=" * 70)

    registry = FactorRegistry.get_instance()

    # Original strategy uses simple momentum
    print("\n--- Original Strategy ---")
    original_factor = registry.create_factor(
        "momentum_factor",
        parameters={"momentum_period": 20}
    )
    print(f"Using: {original_factor.name}")
    print(f"Category: {original_factor.category}")
    print(f"Parameters: {original_factor.parameters}")

    # Discover alternative momentum factors
    print("\n--- Discovering Alternatives (Same Category) ---")
    alternatives = registry.get_momentum_factors()
    print(f"Found {len(alternatives)} momentum factors:")
    for name in alternatives:
        metadata = registry.get_metadata(name)
        print(f"  - {name}: {metadata['description']}")

    # Replace with MA filter (same category)
    print("\n--- Mutation: Replace with MA Filter ---")
    replacement_factor = registry.create_factor(
        "ma_filter_factor",
        parameters={"ma_periods": 60}
    )
    print(f"Replaced with: {replacement_factor.name}")
    print(f"Category: {replacement_factor.category}")
    print(f"Parameters: {replacement_factor.parameters}")
    print(f"✓ Category match: {original_factor.category == replacement_factor.category}")

    # Test both factors
    data = pd.DataFrame({
        "close": [100, 102, 104, 103, 105, 107, 106, 108, 110, 112]
    })

    print("\n--- Execution Comparison ---")
    result_original = original_factor.execute(data.copy())
    result_replacement = replacement_factor.execute(data.copy())

    print(f"Original output: 'momentum' -> {result_original['momentum'].notna().sum()} values")
    print(f"Replacement output: 'ma_filter' -> {result_replacement['ma_filter'].sum()} True values")


def example_6_advanced_usage():
    """Example 6: Advanced usage patterns."""
    print("\n" + "=" * 70)
    print("Example 6: Advanced Usage Patterns")
    print("=" * 70)

    registry = FactorRegistry.get_instance()

    # Pattern 1: Parameter sweeping
    print("\n--- Pattern 1: Parameter Sweeping ---")
    periods = [10, 20, 30, 40, 50]
    print(f"Testing momentum with periods: {periods}")

    for period in periods:
        # Validate before creating
        is_valid, msg = registry.validate_parameters(
            "momentum_factor",
            {"momentum_period": period}
        )
        if is_valid:
            factor = registry.create_factor(
                "momentum_factor",
                parameters={"momentum_period": period}
            )
            print(f"  ✓ Created momentum factor with period={period}")
        else:
            print(f"  ✗ Invalid period={period}: {msg}")

    # Pattern 2: Building strategy configurations
    print("\n--- Pattern 2: Strategy Configuration ---")
    strategy_config = {
        "entry": {
            "factor": "breakout_factor",
            "params": {"entry_window": 20}
        },
        "filters": [
            {
                "factor": "ma_filter_factor",
                "params": {"ma_periods": 60}
            }
        ],
        "exits": [
            {
                "factor": "trailing_stop_factor",
                "params": {"trail_percent": 0.10, "activation_profit": 0.05}
            },
            {
                "factor": "profit_target_factor",
                "params": {"target_percent": 0.30}
            }
        ]
    }

    print("Strategy configuration:")
    print(f"  Entry: {strategy_config['entry']['factor']}")
    print(f"  Filters: {len(strategy_config['filters'])} filters")
    print(f"  Exits: {len(strategy_config['exits'])} exit conditions")

    # Create factors from configuration
    print("\nCreating factors from config:")
    entry_factor = registry.create_factor(
        strategy_config["entry"]["factor"],
        parameters=strategy_config["entry"]["params"]
    )
    print(f"  ✓ Created entry: {entry_factor.name}")

    filter_factors = []
    for filter_cfg in strategy_config["filters"]:
        factor = registry.create_factor(
            filter_cfg["factor"],
            parameters=filter_cfg["params"]
        )
        filter_factors.append(factor)
        print(f"  ✓ Created filter: {factor.name}")

    exit_factors = []
    for exit_cfg in strategy_config["exits"]:
        factor = registry.create_factor(
            exit_cfg["factor"],
            parameters=exit_cfg["params"]
        )
        exit_factors.append(factor)
        print(f"  ✓ Created exit: {factor.name}")

    print(f"\nTotal factors created: {1 + len(filter_factors) + len(exit_factors)}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("FACTOR REGISTRY USAGE EXAMPLES")
    print("=" * 70)

    example_1_basic_discovery()
    example_2_category_discovery()
    example_3_parameter_validation()
    example_4_factor_pipeline()
    example_5_mutation_scenario()
    example_6_advanced_usage()

    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
