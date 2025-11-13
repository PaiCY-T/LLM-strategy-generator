"""
Demo: Bonferroni Multiple Comparison Correction

Demonstrates how to use the BonferroniValidator to prevent false discoveries
when testing multiple trading strategies.

Example Scenario:
    Testing 500 strategies at α=0.05 (5% significance)
    Expected false discoveries: 500 × 0.05 = 25 strategies

    With Bonferroni correction:
    Adjusted α = 0.05 / 500 = 0.0001
    Expected false discoveries: 500 × 0.0001 = 0.05 strategies
"""

import numpy as np
from src.validation.multiple_comparison import BonferroniValidator


def main():
    print("=" * 70)
    print("BONFERRONI MULTIPLE COMPARISON CORRECTION DEMO")
    print("=" * 70)
    print()

    # Initialize validator for 500 strategies
    print("Step 1: Initialize validator")
    print("-" * 70)
    validator = BonferroniValidator(n_strategies=500, alpha=0.05)
    print(f"Testing {validator.n_strategies} strategies")
    print(f"Original α: {validator.alpha}")
    print(f"Adjusted α (Bonferroni): {validator.adjusted_alpha:.6f}")
    print()

    # Calculate significance threshold
    print("Step 2: Calculate Sharpe ratio significance threshold")
    print("-" * 70)
    threshold = validator.calculate_significance_threshold(n_periods=252)
    print(f"Sharpe must be > {threshold:.4f} to be statistically significant")
    print()

    # Test individual strategies
    print("Step 3: Check individual strategies")
    print("-" * 70)
    test_sharpes = [0.3, 0.6, 1.5, 2.0]
    for sharpe in test_sharpes:
        is_sig = validator.is_significant(sharpe_ratio=sharpe)
        status = "SIGNIFICANT" if is_sig else "NOT significant"
        print(f"  Sharpe {sharpe:.1f}: {status}")
    print()

    # Validate strategy set
    print("Step 4: Validate strategy set")
    print("-" * 70)
    # Generate realistic strategy set
    np.random.seed(42)
    strategies = []
    for i in range(500):
        # Most strategies have modest Sharpe ratios
        sharpe = np.random.normal(0.5, 0.5)
        strategies.append({
            'name': f'Strategy_{i:03d}',
            'sharpe_ratio': sharpe
        })

    results = validator.validate_strategy_set(strategies)

    print(f"Total strategies tested: {results['total_strategies']}")
    print(f"Statistically significant: {results['significant_count']}")
    print(f"Significance threshold: {results['significance_threshold']:.4f}")
    print(f"Expected false discoveries: {results['expected_false_discoveries']:.2f}")
    print(f"Estimated FDR: {results['estimated_fdr']:.2%}")
    print()

    # Show sample significant strategies
    print("Sample significant strategies:")
    for i, strategy in enumerate(results['significant_strategies'][:5]):
        print(f"  {strategy['name']}: Sharpe = {strategy['sharpe_ratio']:.2f}")
    if len(results['significant_strategies']) > 5:
        print(f"  ... and {len(results['significant_strategies']) - 5} more")
    print()

    # Calculate FWER
    print("Step 5: Family-Wise Error Rate (FWER)")
    print("-" * 70)
    fwer = validator.calculate_family_wise_error_rate()
    print(f"Calculated FWER: {fwer:.4f}")
    print(f"Bonferroni guarantee: FWER ≤ {validator.alpha}")
    print()

    # Generate full report
    print("Step 6: Generate comprehensive report")
    print("-" * 70)
    report = validator.generate_report(results)
    print(report)

    # Practical interpretation
    print()
    print("=" * 70)
    print("PRACTICAL INTERPRETATION")
    print("=" * 70)
    print()
    print("Without correction:")
    print(f"  - Testing 500 strategies at α=0.05")
    print(f"  - Expected false positives: 25 strategies")
    print(f"  - Would incorrectly label 25 bad strategies as 'good'")
    print()
    print("With Bonferroni correction:")
    print(f"  - Adjusted α = 0.0001")
    print(f"  - Expected false positives: 0.05 strategies")
    print(f"  - Family-Wise Error Rate: {fwer:.1%} ≤ 5%")
    print()
    print("Result:")
    print(f"  - Out of 500 strategies, only {results['significant_count']} ")
    print(f"    meet the stricter threshold")
    print(f"  - These strategies have Sharpe > {threshold:.2f}")
    print(f"  - High confidence they are truly profitable")
    print()


if __name__ == '__main__':
    main()
