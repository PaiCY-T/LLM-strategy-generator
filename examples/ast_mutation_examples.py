"""
AST Mutation Examples - Demonstrating Tier 3 capabilities.

This module provides practical examples of AST-based factor mutations,
signal combinations, and adaptive parameters.

Usage:
    python examples/ast_mutation_examples.py
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.mutation.tier3 import (
    ASTFactorMutator,
    SignalCombiner,
    AdaptiveParameterMutator,
    ASTValidator,
)


# ============================================================================
# Helper Functions
# ============================================================================

def create_sample_data(periods: int = 252) -> pd.DataFrame:
    """
    Create sample OHLCV data for examples.

    Args:
        periods: Number of days

    Returns:
        DataFrame with OHLCV data
    """
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=periods, freq='D')

    # Generate synthetic price data with trend and noise
    trend = np.linspace(100, 120, periods)
    noise = np.random.normal(0, 2, periods)
    close = trend + noise

    data = pd.DataFrame({
        'open': close + np.random.uniform(-1, 1, periods),
        'high': close + np.random.uniform(0, 2, periods),
        'low': close - np.random.uniform(0, 2, periods),
        'close': close,
        'volume': np.random.uniform(1e6, 5e6, periods),
    }, index=dates)

    return data


def create_rsi_factor() -> Factor:
    """Create RSI momentum factor."""
    def rsi_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        period = params.get('period', 14)
        overbought = params.get('overbought', 70)
        oversold = params.get('oversold', 30)

        # Calculate RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))

        data['rsi'] = rsi
        data['rsi_signal'] = ((rsi > overbought).astype(int) -
                             (rsi < oversold).astype(int))

        return data

    return Factor(
        id='rsi_14',
        name='RSI Momentum',
        category=FactorCategory.MOMENTUM,
        inputs=['close'],
        outputs=['rsi', 'rsi_signal'],
        logic=rsi_logic,
        parameters={'period': 14, 'overbought': 70, 'oversold': 30},
        description='RSI momentum indicator with overbought/oversold signals'
    )


def create_macd_factor() -> Factor:
    """Create MACD momentum factor."""
    def macd_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)

        # Calculate MACD
        ema_fast = data['close'].ewm(span=fast).mean()
        ema_slow = data['close'].ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()

        data['macd'] = macd_line
        data['macd_signal_line'] = signal_line
        data['macd_signal'] = (macd_line > signal_line).astype(int)

        return data

    return Factor(
        id='macd_12_26_9',
        name='MACD Momentum',
        category=FactorCategory.MOMENTUM,
        inputs=['close'],
        outputs=['macd', 'macd_signal_line', 'macd_signal'],
        logic=macd_logic,
        parameters={'fast': 12, 'slow': 26, 'signal': 9},
        description='MACD momentum indicator'
    )


# ============================================================================
# Example 1: Basic AST Mutations
# ============================================================================

def example_1_basic_ast_mutation():
    """
    Example 1: Basic AST Mutation

    Demonstrates operator mutation, threshold adjustment, and
    expression modification.
    """
    print("=" * 70)
    print("Example 1: Basic AST Mutation")
    print("=" * 70)

    # Create sample data and factor
    data = create_sample_data()
    rsi_factor = create_rsi_factor()

    # Initialize mutator
    mutator = ASTFactorMutator()

    # 1. Operator Mutation
    print("\n1. Operator Mutation (< to <=, > to >=)")
    print("-" * 50)

    operator_config = {
        'mutation_type': 'operator_mutation',
        'seed': 42
    }

    mutated_operator = mutator.mutate(rsi_factor, operator_config)
    print(f"Original: {rsi_factor.name}")
    print(f"Mutated: {mutated_operator.description}")

    # Execute and compare
    original_result = rsi_factor.execute(data.copy())
    mutated_result = mutated_operator.execute(data.copy())

    print(f"Original signals: {original_result['rsi_signal'].sum()}")
    print(f"Mutated signals: {mutated_result['rsi_signal'].sum()}")

    # 2. Threshold Adjustment
    print("\n2. Threshold Adjustment (multiply by 1.1)")
    print("-" * 50)

    threshold_config = {
        'mutation_type': 'threshold_adjustment',
        'adjustment_factor': 1.1
    }

    mutated_threshold = mutator.mutate(rsi_factor, threshold_config)
    print(f"Mutated: {mutated_threshold.description}")

    # 3. Expression Modification
    print("\n3. Expression Modification (change operators)")
    print("-" * 50)

    expression_config = {
        'mutation_type': 'expression_modification'
    }

    mutated_expression = mutator.mutate(rsi_factor, expression_config)
    print(f"Mutated: {mutated_expression.description}")

    print("\n✓ Example 1 completed successfully\n")


# ============================================================================
# Example 2: Signal Combination
# ============================================================================

def example_2_signal_combination():
    """
    Example 2: Signal Combination

    Demonstrates AND, OR, and weighted combinations of signals.
    """
    print("=" * 70)
    print("Example 2: Signal Combination")
    print("=" * 70)

    # Create sample data and factors
    data = create_sample_data()
    rsi_factor = create_rsi_factor()
    macd_factor = create_macd_factor()

    # Initialize combiner
    combiner = SignalCombiner()

    # 1. AND Combination
    print("\n1. AND Combination (RSI AND MACD)")
    print("-" * 50)

    and_composite = combiner.combine_and(rsi_factor, macd_factor)
    print(f"Composite: {and_composite.name}")
    print(f"ID: {and_composite.id}")

    and_result = and_composite.execute(data.copy())
    and_signal_col = [col for col in and_result.columns if '_and_' in col][0]
    print(f"AND signals: {and_result[and_signal_col].sum()}")

    # 2. OR Combination
    print("\n2. OR Combination (RSI OR MACD)")
    print("-" * 50)

    or_composite = combiner.combine_or(rsi_factor, macd_factor)
    print(f"Composite: {or_composite.name}")

    or_result = or_composite.execute(data.copy())
    or_signal_col = [col for col in or_result.columns if '_or_' in col][0]
    print(f"OR signals: {or_result[or_signal_col].sum()}")

    # 3. Weighted Combination
    print("\n3. Weighted Combination (60% RSI + 40% MACD)")
    print("-" * 50)

    weighted_composite = combiner.combine_weighted(
        [rsi_factor, macd_factor],
        [0.6, 0.4]
    )
    print(f"Composite: {weighted_composite.name}")

    weighted_result = weighted_composite.execute(data.copy())
    weighted_signal_col = [col for col in weighted_result.columns if '_weighted_' in col][0]
    print(f"Weighted signal mean: {weighted_result[weighted_signal_col].mean():.2f}")

    print("\n✓ Example 2 completed successfully\n")


# ============================================================================
# Example 3: Adaptive Parameters
# ============================================================================

def example_3_adaptive_parameters():
    """
    Example 3: Adaptive Parameters

    Demonstrates volatility-adaptive and regime-adaptive parameters.
    """
    print("=" * 70)
    print("Example 3: Adaptive Parameters")
    print("=" * 70)

    # Create sample data and factor
    data = create_sample_data()
    rsi_factor = create_rsi_factor()

    # Initialize mutator
    mutator = AdaptiveParameterMutator()

    # 1. Volatility-Adaptive
    print("\n1. Volatility-Adaptive Parameters")
    print("-" * 50)

    vol_adaptive = mutator.create_volatility_adaptive(
        base_factor=rsi_factor,
        param_name='overbought',
        volatility_period=20,
        scale_factor=1.0
    )

    print(f"Adaptive Factor: {vol_adaptive.name}")
    vol_result = vol_adaptive.execute(data.copy())

    print(f"Base overbought: {rsi_factor.parameters['overbought']}")
    print(f"Adaptive overbought (mean): {vol_result['overbought_adaptive'].mean():.2f}")
    print(f"Adaptive overbought (min): {vol_result['overbought_adaptive'].min():.2f}")
    print(f"Adaptive overbought (max): {vol_result['overbought_adaptive'].max():.2f}")

    # 2. Regime-Adaptive
    print("\n2. Regime-Adaptive Parameters")
    print("-" * 50)

    regime_adaptive = mutator.create_regime_adaptive(
        base_factor=rsi_factor,
        param_name='period',
        bull_value=10,
        bear_value=20,
        regime_period=50
    )

    print(f"Adaptive Factor: {regime_adaptive.name}")
    regime_result = regime_adaptive.execute(data.copy())

    print(f"Base period: {rsi_factor.parameters['period']}")
    print(f"Bull market periods: {(regime_result['regime'] == 'bull').sum()}")
    print(f"Bear market periods: {(regime_result['regime'] == 'bear').sum()}")
    print(f"Sideways periods: {(regime_result['regime'] == 'sideways').sum()}")

    # 3. Bounded-Adaptive
    print("\n3. Bounded-Adaptive Parameters")
    print("-" * 50)

    bounded_adaptive = mutator.create_bounded_adaptive(
        base_factor=rsi_factor,
        param_name='period',
        min_value=10,
        max_value=20,
        adaptation_rate=0.1
    )

    print(f"Adaptive Factor: {bounded_adaptive.name}")
    bounded_result = bounded_adaptive.execute(data.copy())

    print(f"Adaptive period (min): {bounded_result['period_adaptive'].min():.2f}")
    print(f"Adaptive period (max): {bounded_result['period_adaptive'].max():.2f}")
    print(f"All values in bounds: {(bounded_result['period_adaptive'] >= 10).all() and (bounded_result['period_adaptive'] <= 20).all()}")

    print("\n✓ Example 3 completed successfully\n")


# ============================================================================
# Example 4: Validation and Safety
# ============================================================================

def example_4_validation_and_safety():
    """
    Example 4: Validation and Safety

    Demonstrates AST validation for security and correctness.
    """
    print("=" * 70)
    print("Example 4: Validation and Safety")
    print("=" * 70)

    validator = ASTValidator()

    # 1. Valid Code
    print("\n1. Valid Code")
    print("-" * 50)

    valid_code = """
def calculate(data, params):
    period = params.get('period', 14)
    data['sma'] = data['close'].rolling(window=period).mean()
    return data
"""

    result = validator.validate(valid_code)
    print(f"Valid code validation: {'✓ PASSED' if result.success else '✗ FAILED'}")
    if result.warnings:
        print(f"Warnings: {result.warnings}")

    # 2. Import Forbidden
    print("\n2. Import Forbidden (Security)")
    print("-" * 50)

    unsafe_import = """
import os
def calculate(data, params):
    os.system('rm -rf /')  # DANGEROUS!
    return data
"""

    result = validator.validate(unsafe_import)
    print(f"Unsafe code validation: {'✓ PASSED' if result.success else '✗ FAILED (as expected)'}")
    if result.errors:
        print(f"Errors: {result.errors[0]}")

    # 3. File Access Forbidden
    print("\n3. File Access Forbidden (Security)")
    print("-" * 50)

    unsafe_file = """
def calculate(data, params):
    with open('/etc/passwd', 'r') as f:
        passwords = f.read()
    return data
"""

    result = validator.validate(unsafe_file)
    print(f"File access validation: {'✓ PASSED' if result.success else '✗ FAILED (as expected)'}")
    if result.errors:
        print(f"Errors: {result.errors[0]}")

    # 4. Syntax Error
    print("\n4. Syntax Error Detection")
    print("-" * 50)

    syntax_error = """
def calculate(data, params)  # Missing colon
    return data
"""

    result = validator.validate(syntax_error)
    print(f"Syntax error validation: {'✓ PASSED' if result.success else '✗ FAILED (as expected)'}")
    if result.errors:
        print(f"Errors: {result.errors[0][:50]}...")

    print("\n✓ Example 4 completed successfully\n")


# ============================================================================
# Example 5: Full Workflow
# ============================================================================

def example_5_full_workflow():
    """
    Example 5: Full Workflow

    Demonstrates complete workflow: create -> validate -> mutate -> combine -> execute
    """
    print("=" * 70)
    print("Example 5: Full Workflow")
    print("=" * 70)

    # Setup
    data = create_sample_data()
    rsi_factor = create_rsi_factor()
    macd_factor = create_macd_factor()

    # Step 1: Validate original factors
    print("\nStep 1: Validate Original Factors")
    print("-" * 50)

    validator = ASTValidator()
    ast_mutator = ASTFactorMutator()

    rsi_source = ast_mutator.get_source(rsi_factor)
    rsi_validation = validator.validate(rsi_source)
    print(f"RSI validation: {'✓ PASSED' if rsi_validation.success else '✗ FAILED'}")

    # Step 2: Mutate RSI factor
    print("\nStep 2: Mutate RSI Factor")
    print("-" * 50)

    mutated_rsi = ast_mutator.mutate(
        rsi_factor,
        {'mutation_type': 'threshold_adjustment', 'adjustment_factor': 1.15}
    )
    print(f"Mutated: {mutated_rsi.description}")

    # Step 3: Make MACD adaptive
    print("\nStep 3: Make MACD Adaptive")
    print("-" * 50)

    param_mutator = AdaptiveParameterMutator()
    adaptive_macd = param_mutator.create_volatility_adaptive(
        base_factor=macd_factor,
        param_name='fast',
        volatility_period=20
    )
    print(f"Adaptive: {adaptive_macd.name}")

    # Step 4: Combine factors
    print("\nStep 4: Combine Mutated and Adaptive Factors")
    print("-" * 50)

    combiner = SignalCombiner()
    # Note: Can't combine mutated_rsi with adaptive_macd directly due to closure complexity
    # Instead, combine original mutated_rsi with original macd_factor
    composite = combiner.combine_weighted(
        [mutated_rsi, macd_factor],
        [0.6, 0.4]
    )
    print(f"Composite: {composite.name}")

    # Step 5: Execute composite strategy
    print("\nStep 5: Execute Composite Strategy")
    print("-" * 50)

    result = composite.execute(data.copy())
    print(f"Execution successful: ✓")
    print(f"Output columns: {len(result.columns)}")
    print(f"Data rows: {len(result)}")

    # Step 6: Analyze results
    print("\nStep 6: Analyze Results")
    print("-" * 50)

    # Find weighted signal column
    weighted_cols = [col for col in result.columns if 'weighted' in col]
    if weighted_cols:
        signal_col = weighted_cols[0]
        print(f"Signal column: {signal_col}")
        print(f"Signal mean: {result[signal_col].mean():.3f}")
        print(f"Signal std: {result[signal_col].std():.3f}")

    print("\n✓ Example 5 completed successfully\n")


# ============================================================================
# Main Function
# ============================================================================

def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 10 + "AST Mutation Framework - Examples" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    try:
        example_1_basic_ast_mutation()
        example_2_signal_combination()
        example_3_adaptive_parameters()
        example_4_validation_and_safety()
        example_5_full_workflow()

        print("=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)
        print()

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
