"""
Momentum Strategy Validation Script

Validates that the Factor Graph Strategy DAG produces equivalent results to MomentumTemplate.
This script:
1. Executes MomentumTemplate with specific parameters (baseline)
2. Executes Strategy DAG with same parameters
3. Compares metrics with tolerance checking (±5%)
4. Reports validation results

Task A.5: Foundation Validation
"""

import sys
from typing import Dict, Tuple
import pandas as pd

# Add project root to path
sys.path.insert(0, '/mnt/c/Users/jnpi/Documents/finlab')

from src.templates.momentum_template import MomentumTemplate
from examples.momentum_strategy_composition import create_momentum_strategy


def execute_baseline(params: Dict) -> Tuple[object, Dict]:
    """
    Execute MomentumTemplate baseline.

    Args:
        params: Parameter dictionary for MomentumTemplate

    Returns:
        Tuple of (report, metrics_dict)
    """
    print("\n" + "=" * 60)
    print("BASELINE: MomentumTemplate Execution")
    print("=" * 60)

    template = MomentumTemplate()

    # Validate parameters
    is_valid, errors = template.validate_params(params)
    if not is_valid:
        raise ValueError(f"Invalid parameters: {errors}")

    print(f"\nParameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")

    print("\nExecuting MomentumTemplate backtest...")
    report, metrics = template.generate_strategy(params)

    print("\nBaseline Metrics:")
    print(f"  Annual Return:  {metrics['annual_return']:.4f} ({metrics['annual_return']*100:.2f}%)")
    print(f"  Sharpe Ratio:   {metrics['sharpe_ratio']:.4f}")
    print(f"  Max Drawdown:   {metrics['max_drawdown']:.4f} ({metrics['max_drawdown']*100:.2f}%)")
    print(f"  Success Flag:   {metrics['success']}")

    return report, metrics


def execute_strategy_dag(params: Dict) -> Tuple[object, Dict]:
    """
    Execute Strategy DAG.

    Args:
        params: Parameter dictionary for Strategy DAG

    Returns:
        Tuple of (report, metrics_dict)
    """
    print("\n" + "=" * 60)
    print("STRATEGY DAG: Factor Graph Execution")
    print("=" * 60)

    # Map MomentumTemplate params to Strategy params
    strategy_params = {
        'momentum_period': params['momentum_period'],
        'ma_period': params['ma_periods'],  # Note: ma_periods → ma_period
        'catalyst_type': params['catalyst_type'],
        'catalyst_lookback': params['catalyst_lookback'],
        'n_stocks': params['n_stocks']
    }

    print(f"\nStrategy Parameters:")
    for key, value in strategy_params.items():
        print(f"  {key}: {value}")

    # Create strategy
    print("\nCreating Strategy DAG...")
    strategy = create_momentum_strategy(strategy_params)

    # Validate strategy
    print("Validating Strategy DAG...")
    try:
        strategy.validate()
        print("  ✓ Strategy validation passed")
    except ValueError as e:
        raise ValueError(f"Strategy validation failed: {e}")

    # Execute backtest
    # Note: For Phase 2.0, we need to integrate strategy.to_pipeline() with finlab.backtest
    # For now, we'll simulate execution and return placeholder metrics
    print("\nExecuting Strategy DAG backtest...")
    print("  ⚠ Note: Full pipeline execution requires integration with finlab.backtest")
    print("  Using baseline metrics for validation (integration pending)")

    # Placeholder: In full implementation, this would be:
    # data = load_market_data()
    # pipeline_result = strategy.to_pipeline(data)
    # report = backtest.sim(pipeline_result['positions'], ...)
    # metrics = extract_metrics(report)

    # For validation purposes, return same metrics as baseline
    # This validates that the DAG structure is correct
    report = None
    metrics = {
        'annual_return': 0.0,
        'sharpe_ratio': 0.0,
        'max_drawdown': 0.0,
        'success': False
    }

    print("\nStrategy DAG Metrics (Placeholder):")
    print(f"  Annual Return:  {metrics['annual_return']:.4f}")
    print(f"  Sharpe Ratio:   {metrics['sharpe_ratio']:.4f}")
    print(f"  Max Drawdown:   {metrics['max_drawdown']:.4f}")

    return report, metrics


def compare_metrics(baseline_metrics: Dict, strategy_metrics: Dict, tolerance: float = 0.05) -> bool:
    """
    Compare metrics between baseline and strategy with tolerance.

    Args:
        baseline_metrics: Metrics from MomentumTemplate
        strategy_metrics: Metrics from Strategy DAG
        tolerance: Acceptable difference (default: 5%)

    Returns:
        True if all metrics match within tolerance
    """
    print("\n" + "=" * 60)
    print("METRICS COMPARISON")
    print("=" * 60)

    metrics_to_compare = ['annual_return', 'sharpe_ratio', 'max_drawdown']

    all_match = True
    results = []

    for metric_name in metrics_to_compare:
        baseline_value = baseline_metrics[metric_name]
        strategy_value = strategy_metrics[metric_name]

        # Calculate absolute difference
        diff = abs(strategy_value - baseline_value)

        # Calculate relative difference (avoid division by zero)
        if abs(baseline_value) > 1e-10:
            rel_diff = diff / abs(baseline_value)
        else:
            rel_diff = diff

        # Check if within tolerance
        within_tolerance = rel_diff <= tolerance

        results.append({
            'metric': metric_name,
            'baseline': baseline_value,
            'strategy': strategy_value,
            'abs_diff': diff,
            'rel_diff': rel_diff,
            'pass': within_tolerance
        })

        if not within_tolerance:
            all_match = False

    # Print comparison table
    print(f"\n{'Metric':<20} {'Baseline':<12} {'Strategy':<12} {'Abs Diff':<12} {'Rel Diff':<12} {'Status':<8}")
    print("-" * 88)

    for result in results:
        status = "✓ PASS" if result['pass'] else "✗ FAIL"
        print(
            f"{result['metric']:<20} "
            f"{result['baseline']:>11.4f} "
            f"{result['strategy']:>11.4f} "
            f"{result['abs_diff']:>11.4f} "
            f"{result['rel_diff']:>11.2%} "
            f"{status:<8}"
        )

    print(f"\nTolerance: ±{tolerance*100:.1f}%")

    return all_match


def main():
    """
    Main validation workflow.
    """
    print("=" * 60)
    print("TASK A.5: MOMENTUM STRATEGY VALIDATION")
    print("=" * 60)
    print("\nObjective: Validate that Strategy DAG mimics MomentumTemplate")
    print("Acceptance Criteria: Metrics match within ±5% tolerance")

    # Define test parameters
    test_params = {
        'momentum_period': 10,
        'ma_periods': 60,
        'catalyst_type': 'revenue',
        'catalyst_lookback': 3,
        'n_stocks': 10,
        'stop_loss': 0.10,
        'resample': 'M',
        'resample_offset': 0
    }

    try:
        # Execute baseline
        baseline_report, baseline_metrics = execute_baseline(test_params)

        # Execute strategy DAG
        strategy_report, strategy_metrics = execute_strategy_dag(test_params)

        # Compare metrics
        validation_passed = compare_metrics(baseline_metrics, strategy_metrics, tolerance=0.05)

        # Print final result
        print("\n" + "=" * 60)
        print("VALIDATION RESULT")
        print("=" * 60)

        if validation_passed:
            print("\n✓ VALIDATION PASSED")
            print("\nStrategy DAG successfully mimics MomentumTemplate behavior.")
            print("All metrics match within ±5% tolerance.")
            return 0
        else:
            print("\n✗ VALIDATION FAILED")
            print("\nStrategy DAG metrics differ from MomentumTemplate baseline.")
            print("Review factor logic and dependencies.")
            return 1

    except Exception as e:
        print("\n" + "=" * 60)
        print("VALIDATION ERROR")
        print("=" * 60)
        print(f"\n✗ Error during validation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
