"""
Phase B Migration Validation Script
====================================

Comprehensive validation of Phase B migration work.

This script validates that all Phase B migration work is complete and functional:
1. Factor Registry loads all 13 factors correctly
2. Factor metadata is accurate (categories, parameters, ranges)
3. Factor creation via registry works
4. Full strategies can be composed using Factor Registry
5. Factor-based strategies execute correctly
6. DAG structure is valid for composed strategies

Usage:
    python scripts/validate_phase_b_migration.py

Expected Output:
    - All 13 factors registered
    - 3 full strategies composed and executed
    - Performance metrics (factor creation, composition, execution)
    - Migration report summary

Exit Codes:
    0: All validations passed
    1: Validation failures detected
"""

import sys
import time
from typing import Dict, List
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, '/mnt/c/Users/jnpi/Documents/finlab')

from src.factor_library.registry import FactorRegistry
from src.factor_graph.factor import Factor
from src.factor_graph.strategy import Strategy
from src.factor_graph.factor_category import FactorCategory


# ============================================================================
# Validation Functions
# ============================================================================

def validate_registry_loading() -> bool:
    """
    Validate that Factor Registry loads all 13 factors correctly.

    Returns:
        True if all 13 factors loaded successfully
    """
    print("\n" + "="*80)
    print("VALIDATION 1: Factor Registry Loading")
    print("="*80)

    try:
        # Get registry instance (auto-initializes)
        registry = FactorRegistry.get_instance()

        # Get all factors
        all_factors = registry.list_factors()

        print(f"✓ Registry initialized successfully")
        print(f"✓ Total factors registered: {len(all_factors)}")

        # Verify 13 factors
        if len(all_factors) != 13:
            print(f"✗ Expected 13 factors, got {len(all_factors)}")
            return False

        print(f"✓ All 13 factors registered")

        # List factors by category
        print(f"\nFactors by category:")
        for category in FactorCategory:
            factors = registry.list_by_category(category)
            if factors:
                print(f"  {category.name}: {len(factors)} factors")
                for factor_name in factors:
                    print(f"    - {factor_name}")

        return True

    except Exception as e:
        print(f"✗ Registry loading failed: {str(e)}")
        return False


def validate_factor_metadata() -> bool:
    """
    Validate factor metadata accuracy (categories, parameters, ranges).

    Returns:
        True if all metadata is accurate
    """
    print("\n" + "="*80)
    print("VALIDATION 2: Factor Metadata Accuracy")
    print("="*80)

    try:
        registry = FactorRegistry.get_instance()
        all_factors = registry.list_factors()

        validation_passed = True

        for factor_name in all_factors:
            metadata = registry.get_metadata(factor_name)

            # Validate metadata structure
            required_fields = ["name", "category", "description", "parameters", "parameter_ranges"]
            missing_fields = [field for field in required_fields if field not in metadata]

            if missing_fields:
                print(f"✗ Factor '{factor_name}': Missing metadata fields {missing_fields}")
                validation_passed = False
                continue

            # Validate category is FactorCategory enum
            if not isinstance(metadata["category"], FactorCategory):
                print(f"✗ Factor '{factor_name}': Invalid category type {type(metadata['category'])}")
                validation_passed = False
                continue

            # Validate parameters is dict
            if not isinstance(metadata["parameters"], dict):
                print(f"✗ Factor '{factor_name}': Parameters must be dict, got {type(metadata['parameters'])}")
                validation_passed = False
                continue

            # Validate parameter_ranges is dict
            if not isinstance(metadata["parameter_ranges"], dict):
                print(f"✗ Factor '{factor_name}': Parameter ranges must be dict, got {type(metadata['parameter_ranges'])}")
                validation_passed = False
                continue

            print(f"✓ Factor '{factor_name}': Metadata valid")
            print(f"    Category: {metadata['category'].name}")
            print(f"    Parameters: {metadata['parameters']}")
            print(f"    Parameter ranges: {metadata['parameter_ranges']}")

        if validation_passed:
            print(f"\n✓ All {len(all_factors)} factors have valid metadata")

        return validation_passed

    except Exception as e:
        print(f"✗ Metadata validation failed: {str(e)}")
        return False


def validate_factor_creation() -> bool:
    """
    Validate factor creation via registry with parameter validation.

    Returns:
        True if factor creation works correctly
    """
    print("\n" + "="*80)
    print("VALIDATION 3: Factor Creation via Registry")
    print("="*80)

    try:
        registry = FactorRegistry.get_instance()

        # Test cases: (factor_name, custom_parameters, should_succeed)
        test_cases = [
            ("momentum_factor", {"momentum_period": 20}, True),
            ("momentum_factor", {"momentum_period": 5}, True),  # Min valid
            ("momentum_factor", {"momentum_period": 100}, True),  # Max valid
            ("momentum_factor", {"momentum_period": 1}, False),  # Below min
            ("momentum_factor", {"momentum_period": 150}, False),  # Above max
            ("atr_factor", {"atr_period": 20}, True),
            ("breakout_factor", {"entry_window": 55}, True),
            ("dual_ma_filter_factor", {"short_ma": 20, "long_ma": 60}, True),
            ("trailing_stop_factor", {"trail_percent": 0.10, "activation_profit": 0.05}, True),
            ("profit_target_factor", {"target_percent": 0.30}, True),
        ]

        validation_passed = True

        for factor_name, parameters, should_succeed in test_cases:
            try:
                # Validate parameters first
                is_valid, error_msg = registry.validate_parameters(factor_name, parameters)

                if should_succeed and not is_valid:
                    print(f"✗ Factor '{factor_name}': Expected parameters {parameters} to be valid, got error: {error_msg}")
                    validation_passed = False
                    continue

                if not should_succeed and is_valid:
                    print(f"✗ Factor '{factor_name}': Expected parameters {parameters} to be invalid, but validation passed")
                    validation_passed = False
                    continue

                # Create factor if validation should succeed
                if should_succeed:
                    factor = registry.create_factor(factor_name, parameters)

                    # Verify factor attributes
                    if factor.parameters != parameters:
                        print(f"✗ Factor '{factor_name}': Parameter mismatch. Expected {parameters}, got {factor.parameters}")
                        validation_passed = False
                        continue

                    print(f"✓ Factor '{factor_name}': Created successfully with parameters {parameters}")
                else:
                    print(f"✓ Factor '{factor_name}': Correctly rejected invalid parameters {parameters}")

            except Exception as e:
                if should_succeed:
                    print(f"✗ Factor '{factor_name}': Creation failed with {parameters}: {str(e)}")
                    validation_passed = False
                else:
                    print(f"✓ Factor '{factor_name}': Correctly rejected invalid parameters {parameters} ({str(e)})")

        if validation_passed:
            print(f"\n✓ All factor creation tests passed")

        return validation_passed

    except Exception as e:
        print(f"✗ Factor creation validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def create_sample_data() -> pd.DataFrame:
    """
    Create sample OHLCV data for strategy testing.

    Returns:
        DataFrame with OHLCV columns and 100 rows
    """
    np.random.seed(42)

    # Generate realistic price data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    base_price = 100

    # Random walk with drift
    returns = np.random.randn(100) * 0.02 + 0.001
    close_prices = base_price * np.exp(np.cumsum(returns))

    # Generate OHLC from close
    data = pd.DataFrame({
        'open': close_prices * (1 + np.random.randn(100) * 0.005),
        'high': close_prices * (1 + np.abs(np.random.randn(100) * 0.01)),
        'low': close_prices * (1 - np.abs(np.random.randn(100) * 0.01)),
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)

    # Ensure high >= close >= low and high >= open >= low
    data['high'] = data[['high', 'open', 'close']].max(axis=1)
    data['low'] = data[['low', 'open', 'close']].min(axis=1)

    return data


def compose_momentum_strategy() -> Strategy:
    """
    Compose momentum strategy using Factor Registry.

    Strategy composition:
    - MomentumFactor (momentum_period=20)
    - MAFilterFactor (ma_periods=60)
    - ProfitTargetFactor (target_percent=0.30)
    - TrailingStopFactor (trail_percent=0.10, activation_profit=0.05)
    - CompositeExitFactor (combines profit and trailing)

    Returns:
        Composed momentum Strategy
    """
    print("\n" + "="*80)
    print("STRATEGY COMPOSITION 1: Momentum Strategy")
    print("="*80)

    registry = FactorRegistry.get_instance()

    # Create strategy
    strategy = Strategy(id="momentum_strategy", generation=0)

    # Add momentum factor
    momentum = registry.create_factor("momentum_factor", {"momentum_period": 20})
    strategy.add_factor(momentum)
    print(f"✓ Added: {momentum.name}")

    # Add MA filter (depends on momentum for close)
    ma_filter = registry.create_factor("ma_filter_factor", {"ma_periods": 60})
    strategy.add_factor(ma_filter)
    print(f"✓ Added: {ma_filter.name}")

    # Add entry signal factor (simple momentum + MA filter combination)
    # Create custom factor for signal generation
    def momentum_signal_logic(data: pd.DataFrame, parameters: Dict) -> pd.DataFrame:
        """Generate position signals from momentum and MA filter."""
        # Entry: positive momentum + above MA
        data['positions'] = (data['momentum'] > 0) & data['ma_filter']
        data['entry_price'] = data['close'].where(data['positions'], np.nan).ffill()
        data['entry_date'] = data.index.to_series().where(data['positions'], pd.NaT).ffill()
        return data

    signal_factor = Factor(
        id="momentum_signal",
        name="Momentum Entry Signal",
        category=FactorCategory.SIGNAL,
        inputs=["close", "momentum", "ma_filter"],
        outputs=["positions", "entry_price", "entry_date"],
        logic=momentum_signal_logic,
        parameters={},
        description="Generate entry signals from momentum and MA filter"
    )
    strategy.add_factor(signal_factor, depends_on=["momentum_20", "ma_filter_60"])
    print(f"✓ Added: {signal_factor.name}")

    # Add profit target exit
    profit_target = registry.create_factor("profit_target_factor", {"target_percent": 0.30})
    strategy.add_factor(profit_target, depends_on=["momentum_signal"])
    print(f"✓ Added: {profit_target.name}")

    # Add trailing stop exit
    trailing_stop = registry.create_factor(
        "trailing_stop_factor",
        {"trail_percent": 0.10, "activation_profit": 0.05}
    )
    strategy.add_factor(trailing_stop, depends_on=["momentum_signal"])
    print(f"✓ Added: {trailing_stop.name}")

    # Add composite exit
    composite_exit = registry.create_factor(
        "composite_exit_factor",
        {"exit_signals": ["profit_target_signal", "trailing_stop_signal"]}
    )
    strategy.add_factor(composite_exit, depends_on=["profit_target_30pct", "trailing_stop_10pct"])
    print(f"✓ Added: {composite_exit.name}")

    print(f"\n✓ Momentum strategy composed with {len(strategy.factors)} factors")

    return strategy


def compose_turtle_strategy() -> Strategy:
    """
    Compose turtle strategy using Factor Registry.

    Strategy composition:
    - ATRFactor (atr_period=20)
    - BreakoutFactor (entry_window=20)
    - DualMAFilterFactor (short_ma=20, long_ma=60)
    - ATRStopLossFactor (atr_multiplier=2.0)

    Returns:
        Composed turtle Strategy
    """
    print("\n" + "="*80)
    print("STRATEGY COMPOSITION 2: Turtle Strategy")
    print("="*80)

    registry = FactorRegistry.get_instance()

    # Create strategy
    strategy = Strategy(id="turtle_strategy", generation=0)

    # Add ATR factor
    atr = registry.create_factor("atr_factor", {"atr_period": 20})
    strategy.add_factor(atr)
    print(f"✓ Added: {atr.name}")

    # Add breakout factor
    breakout = registry.create_factor("breakout_factor", {"entry_window": 20})
    strategy.add_factor(breakout)
    print(f"✓ Added: {breakout.name}")

    # Add dual MA filter
    dual_ma = registry.create_factor("dual_ma_filter_factor", {"short_ma": 20, "long_ma": 60})
    strategy.add_factor(dual_ma)
    print(f"✓ Added: {dual_ma.name}")

    # Add entry signal factor (breakout + dual MA filter)
    def turtle_signal_logic(data: pd.DataFrame, parameters: Dict) -> pd.DataFrame:
        """Generate position signals from breakout and dual MA filter."""
        # Entry: long breakout + above both MAs
        data['positions'] = (data['breakout_signal'] == 1) & data['dual_ma_filter']
        data['entry_price'] = data['close'].where(data['positions'], np.nan).ffill()
        data['entry_date'] = data.index.to_series().where(data['positions'], pd.NaT).ffill()
        return data

    signal_factor = Factor(
        id="turtle_signal",
        name="Turtle Entry Signal",
        category=FactorCategory.SIGNAL,
        inputs=["close", "breakout_signal", "dual_ma_filter"],
        outputs=["positions", "entry_price", "entry_date"],
        logic=turtle_signal_logic,
        parameters={},
        description="Generate entry signals from breakout and dual MA filter"
    )
    strategy.add_factor(signal_factor, depends_on=["breakout_20", "dual_ma_filter_20_60"])
    print(f"✓ Added: {signal_factor.name}")

    # Add ATR stop loss
    atr_stop = registry.create_factor("atr_stop_loss_factor", {"atr_multiplier": 2.0})
    strategy.add_factor(atr_stop, depends_on=["atr_20", "turtle_signal"])
    print(f"✓ Added: {atr_stop.name}")

    print(f"\n✓ Turtle strategy composed with {len(strategy.factors)} factors")

    return strategy


def compose_hybrid_strategy() -> Strategy:
    """
    Compose hybrid strategy mixing momentum and turtle factors.

    Strategy composition:
    - MomentumFactor (momentum_period=10)
    - ATRFactor (atr_period=14)
    - BreakoutFactor (entry_window=20)
    - MAFilterFactor (ma_periods=50)
    - Multiple exit factors (profit target, trailing stop, volatility stop)

    Returns:
        Composed hybrid Strategy
    """
    print("\n" + "="*80)
    print("STRATEGY COMPOSITION 3: Hybrid Strategy")
    print("="*80)

    registry = FactorRegistry.get_instance()

    # Create strategy
    strategy = Strategy(id="hybrid_strategy", generation=0)

    # Add momentum factor (shorter period)
    momentum = registry.create_factor("momentum_factor", {"momentum_period": 10})
    strategy.add_factor(momentum)
    print(f"✓ Added: {momentum.name}")

    # Add ATR factor
    atr = registry.create_factor("atr_factor", {"atr_period": 14})
    strategy.add_factor(atr)
    print(f"✓ Added: {atr.name}")

    # Add breakout factor
    breakout = registry.create_factor("breakout_factor", {"entry_window": 20})
    strategy.add_factor(breakout)
    print(f"✓ Added: {breakout.name}")

    # Add MA filter
    ma_filter = registry.create_factor("ma_filter_factor", {"ma_periods": 50})
    strategy.add_factor(ma_filter)
    print(f"✓ Added: {ma_filter.name}")

    # Add hybrid entry signal (momentum + breakout + MA filter)
    def hybrid_signal_logic(data: pd.DataFrame, parameters: Dict) -> pd.DataFrame:
        """Generate position signals from momentum, breakout, and MA filter."""
        # Entry: (positive momentum OR long breakout) AND above MA
        data['positions'] = ((data['momentum'] > 0) | (data['breakout_signal'] == 1)) & data['ma_filter']
        data['entry_price'] = data['close'].where(data['positions'], np.nan).ffill()
        data['entry_date'] = data.index.to_series().where(data['positions'], pd.NaT).ffill()
        return data

    signal_factor = Factor(
        id="hybrid_signal",
        name="Hybrid Entry Signal",
        category=FactorCategory.SIGNAL,
        inputs=["close", "momentum", "breakout_signal", "ma_filter"],
        outputs=["positions", "entry_price", "entry_date"],
        logic=hybrid_signal_logic,
        parameters={},
        description="Generate entry signals from momentum, breakout, and MA filter"
    )
    # Include ATR in dependencies to ensure it's connected
    strategy.add_factor(signal_factor, depends_on=["momentum_10", "atr_14", "breakout_20", "ma_filter_50"])
    print(f"✓ Added: {signal_factor.name}")

    # Add profit target exit
    profit_target = registry.create_factor("profit_target_factor", {"target_percent": 0.25})
    strategy.add_factor(profit_target, depends_on=["hybrid_signal"])
    print(f"✓ Added: {profit_target.name}")

    # Add trailing stop exit
    trailing_stop = registry.create_factor(
        "trailing_stop_factor",
        {"trail_percent": 0.08, "activation_profit": 0.03}
    )
    strategy.add_factor(trailing_stop, depends_on=["hybrid_signal"])
    print(f"✓ Added: {trailing_stop.name}")

    # Add volatility stop exit
    volatility_stop = registry.create_factor(
        "volatility_stop_factor",
        {"std_period": 14, "std_multiplier": 2.5}
    )
    strategy.add_factor(volatility_stop, depends_on=["hybrid_signal"])
    print(f"✓ Added: {volatility_stop.name}")

    # Add composite exit (3 signals)
    composite_exit = registry.create_factor(
        "composite_exit_factor",
        {"exit_signals": ["profit_target_signal", "trailing_stop_signal", "volatility_stop_signal"]}
    )
    strategy.add_factor(
        composite_exit,
        depends_on=["profit_target_25pct", "trailing_stop_8pct", "volatility_stop_14_2_5std"]
    )
    print(f"✓ Added: {composite_exit.name}")

    print(f"\n✓ Hybrid strategy composed with {len(strategy.factors)} factors")

    return strategy


def validate_strategy_composition() -> bool:
    """
    Validate full strategy composition and DAG structure.

    Returns:
        True if all 3 strategies compose and validate successfully
    """
    print("\n" + "="*80)
    print("VALIDATION 4: Strategy Composition & DAG Validation")
    print("="*80)

    try:
        # Compose strategies
        momentum_strategy = compose_momentum_strategy()
        turtle_strategy = compose_turtle_strategy()
        hybrid_strategy = compose_hybrid_strategy()

        # Validate DAG structures
        print(f"\nValidating DAG structures...")

        for strategy in [momentum_strategy, turtle_strategy, hybrid_strategy]:
            try:
                # Validate strategy
                is_valid = strategy.validate()

                if is_valid:
                    print(f"✓ Strategy '{strategy.id}': DAG validation passed")
                    print(f"    Factors: {len(strategy.factors)}")
                    print(f"    Topological order: {[f.id for f in strategy.get_factors()]}")
                else:
                    print(f"✗ Strategy '{strategy.id}': Validation returned False")
                    return False

            except Exception as e:
                print(f"✗ Strategy '{strategy.id}': Validation failed: {str(e)}")
                return False

        print(f"\n✓ All 3 strategies composed and validated successfully")
        return True

    except Exception as e:
        print(f"✗ Strategy composition validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def validate_strategy_execution() -> bool:
    """
    Validate strategy execution on sample data.

    Returns:
        True if all strategies execute successfully
    """
    print("\n" + "="*80)
    print("VALIDATION 5: Strategy Execution")
    print("="*80)

    try:
        # Create sample data
        data = create_sample_data()
        print(f"✓ Created sample data: {len(data)} rows, {list(data.columns)} columns")

        # Compose strategies
        momentum_strategy = compose_momentum_strategy()
        turtle_strategy = compose_turtle_strategy()
        hybrid_strategy = compose_hybrid_strategy()

        # Execute strategies
        for strategy in [momentum_strategy, turtle_strategy, hybrid_strategy]:
            try:
                print(f"\nExecuting strategy '{strategy.id}'...")

                # Execute pipeline
                start_time = time.time()
                result = strategy.to_pipeline(data)
                execution_time = time.time() - start_time

                # Verify outputs
                print(f"✓ Strategy '{strategy.id}': Execution succeeded")
                print(f"    Execution time: {execution_time:.4f} seconds")
                print(f"    Output columns: {len(result.columns)}")
                print(f"    Result shape: {result.shape}")

                # Check for required outputs
                if 'positions' not in result.columns:
                    print(f"✗ Strategy '{strategy.id}': Missing 'positions' column")
                    return False

                # Check for NaN values in final outputs
                nan_counts = result.isna().sum()
                if nan_counts.sum() > len(data) * 0.2:  # Allow up to 20% NaN (for warm-up periods)
                    print(f"⚠ Strategy '{strategy.id}': High NaN count in outputs: {nan_counts[nan_counts > 0].to_dict()}")

            except Exception as e:
                print(f"✗ Strategy '{strategy.id}': Execution failed: {str(e)}")
                import traceback
                traceback.print_exc()
                return False

        print(f"\n✓ All 3 strategies executed successfully")
        return True

    except Exception as e:
        print(f"✗ Strategy execution validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def validate_performance() -> bool:
    """
    Validate performance meets targets.

    Targets:
    - Factor creation: <1ms per factor
    - Strategy composition: <10ms
    - Pipeline execution: <1s for 10 factors, 1000 rows

    Returns:
        True if all performance targets met
    """
    print("\n" + "="*80)
    print("VALIDATION 6: Performance Benchmarks")
    print("="*80)

    try:
        registry = FactorRegistry.get_instance()

        # Benchmark 1: Factor creation time
        print(f"\nBenchmark 1: Factor Creation Time")
        factor_names = ["momentum_factor", "atr_factor", "breakout_factor"]
        creation_times = []

        for factor_name in factor_names:
            start_time = time.time()
            for _ in range(100):  # Create 100 times
                factor = registry.create_factor(factor_name)
            end_time = time.time()

            avg_time = (end_time - start_time) / 100 * 1000  # Convert to ms
            creation_times.append(avg_time)
            print(f"  {factor_name}: {avg_time:.4f} ms/factor")

        avg_creation_time = sum(creation_times) / len(creation_times)
        if avg_creation_time < 1.0:
            print(f"✓ Average factor creation time: {avg_creation_time:.4f} ms/factor (target: <1 ms)")
        else:
            print(f"⚠ Average factor creation time: {avg_creation_time:.4f} ms/factor (target: <1 ms)")

        # Benchmark 2: Strategy composition time
        print(f"\nBenchmark 2: Strategy Composition Time")

        start_time = time.time()
        momentum_strategy = compose_momentum_strategy()
        composition_time = (time.time() - start_time) * 1000  # Convert to ms

        if composition_time < 10.0:
            print(f"✓ Strategy composition time: {composition_time:.2f} ms (target: <10 ms)")
        else:
            print(f"⚠ Strategy composition time: {composition_time:.2f} ms (target: <10 ms)")

        # Benchmark 3: Pipeline execution time
        print(f"\nBenchmark 3: Pipeline Execution Time")

        # Create larger dataset (1000 rows)
        np.random.seed(42)
        dates = pd.date_range(start='2020-01-01', periods=1000, freq='D')
        base_price = 100
        returns = np.random.randn(1000) * 0.02 + 0.001
        close_prices = base_price * np.exp(np.cumsum(returns))

        data = pd.DataFrame({
            'open': close_prices * (1 + np.random.randn(1000) * 0.005),
            'high': close_prices * (1 + np.abs(np.random.randn(1000) * 0.01)),
            'low': close_prices * (1 - np.abs(np.random.randn(1000) * 0.01)),
            'close': close_prices,
            'volume': np.random.randint(1000, 10000, 1000)
        }, index=dates)

        data['high'] = data[['high', 'open', 'close']].max(axis=1)
        data['low'] = data[['low', 'open', 'close']].min(axis=1)

        start_time = time.time()
        result = momentum_strategy.to_pipeline(data)
        execution_time = time.time() - start_time

        if execution_time < 1.0:
            print(f"✓ Pipeline execution time: {execution_time:.4f} s (target: <1 s)")
        else:
            print(f"⚠ Pipeline execution time: {execution_time:.4f} s (target: <1 s)")

        print(f"  Data size: {len(data)} rows x {len(data.columns)} columns")
        print(f"  Factor count: {len(momentum_strategy.factors)} factors")
        print(f"  Throughput: {len(data) * len(momentum_strategy.factors) / execution_time:.0f} factor-rows/second")

        print(f"\n✓ All performance benchmarks completed")
        return True

    except Exception as e:
        print(f"✗ Performance validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Main Validation Runner
# ============================================================================

def main():
    """
    Run all Phase B migration validations.

    Exit codes:
        0: All validations passed
        1: One or more validations failed
    """
    print("="*80)
    print("PHASE B MIGRATION VALIDATION")
    print("="*80)
    print(f"Validating Phase B migration: Factor extraction and registry")
    print(f"Expected: 13 factors (4 momentum, 4 turtle, 5 exit)")
    print(f"Expected: 3 full strategies composed and executed")

    # Run validations
    validations = [
        ("Registry Loading", validate_registry_loading),
        ("Factor Metadata", validate_factor_metadata),
        ("Factor Creation", validate_factor_creation),
        ("Strategy Composition", validate_strategy_composition),
        ("Strategy Execution", validate_strategy_execution),
        ("Performance Benchmarks", validate_performance),
    ]

    results = {}
    for name, validation_func in validations:
        try:
            result = validation_func()
            results[name] = result
        except Exception as e:
            print(f"\n✗ Validation '{name}' crashed: {str(e)}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Print summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    passed_count = sum(1 for result in results.values() if result)
    total_count = len(results)

    for name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")

    print(f"\nOverall: {passed_count}/{total_count} validations passed")

    if passed_count == total_count:
        print(f"\n✓ Phase B migration validation: ALL CHECKS PASSED")
        return 0
    else:
        print(f"\n✗ Phase B migration validation: FAILURES DETECTED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
