#!/usr/bin/env python3
"""
Usage examples for the liquidity_calculator module.

This script demonstrates how to use the dynamic liquidity calculator
to determine appropriate liquidity thresholds for trading strategies.
"""

from src.liquidity_calculator import (
    calculate_min_liquidity,
    recommend_threshold,
    validate_liquidity_threshold,
)


def example_basic_calculation() -> None:
    """Example 1: Basic liquidity calculation."""
    print("=" * 70)
    print("Example 1: Basic Liquidity Calculation")
    print("=" * 70)
    print("Calculate minimum liquidity for 20M TWD portfolio with 8 stocks\n")

    result = calculate_min_liquidity(
        portfolio_value=20_000_000, stock_count=8, safety_multiplier=50.0, safety_margin=0.1
    )

    print(f"Portfolio Value: {result['portfolio_value']:,.0f} TWD")
    print(f"Stock Count: {result['stock_count']}")
    print(f"Position Size per Stock: {result['position_size']:,.0f} TWD")
    print(f"Theoretical Minimum: {result['theoretical_min']:,.0f} TWD")
    print(f"Recommended Threshold: {result['recommended_threshold']:,.0f} TWD")
    print(f"Market Impact: {result['market_impact_pct']:.2f}%")
    print(f"Safety Multiplier: {result['safety_multiplier']}x")
    print(f"Safety Margin: {result['safety_margin'] * 100:.0f}%")
    print()


def example_stock_count_comparison() -> None:
    """Example 2: Compare liquidity needs across different stock counts."""
    print("=" * 70)
    print("Example 2: Stock Count Comparison")
    print("=" * 70)
    print("How does liquidity requirement change with stock count?\n")

    portfolio_value = 20_000_000

    for stock_count in [6, 8, 10, 12]:
        result = calculate_min_liquidity(portfolio_value, stock_count=stock_count)
        print(
            f"{stock_count:2d} stocks: Position={result['position_size']:>11,.0f} TWD  "
            f"Threshold={result['recommended_threshold']:>12,.0f} TWD  "
            f"Impact={result['market_impact_pct']:.2f}%"
        )
    print()


def example_validate_threshold() -> None:
    """Example 3: Validate different threshold values."""
    print("=" * 70)
    print("Example 3: Threshold Validation")
    print("=" * 70)
    print("Validate different liquidity thresholds\n")

    portfolio_value = 20_000_000
    thresholds = [100_000_000, 150_000_000, 200_000_000]

    for threshold in thresholds:
        result = validate_liquidity_threshold(
            threshold=threshold, portfolio_value=portfolio_value, stock_count_range=(6, 12)
        )

        status = "✓ VALID" if result["is_valid"] else "✗ INVALID"
        worst = result["worst_case"]

        print(f"{threshold:>12,} TWD: {status}")
        print(
            f"  Worst case: {worst['stock_count']} stocks "
            f"→ {worst['market_impact_pct']:.2f}% impact"
        )
    print()


def example_recommend_threshold() -> None:
    """Example 4: Get threshold recommendations."""
    print("=" * 70)
    print("Example 4: Threshold Recommendations")
    print("=" * 70)
    print("What threshold should we use for different scenarios?\n")

    scenarios = [
        (20_000_000, 6, 2.0, "Conservative: 6 stocks, 2% max impact"),
        (20_000_000, 8, 2.0, "Standard: 8 stocks, 2% max impact"),
        (20_000_000, 6, 1.5, "Strict: 6 stocks, 1.5% max impact"),
        (30_000_000, 8, 2.0, "Large portfolio: 30M TWD, 8 stocks"),
    ]

    for portfolio, stocks, max_impact, description in scenarios:
        result = recommend_threshold(portfolio, stocks, max_impact)

        print(f"Scenario: {description}")
        print(f"  Recommended: {result['recommended_threshold']:,.0f} TWD")
        print(f"  Safety Multiplier: {result['safety_multiplier']:.1f}x")
        print()


def example_edge_cases() -> None:
    """Example 5: Handle edge cases."""
    print("=" * 70)
    print("Example 5: Edge Cases")
    print("=" * 70)
    print("Special scenarios and configurations\n")

    # Small portfolio
    small = calculate_min_liquidity(portfolio_value=5_000_000, stock_count=5)
    print(f"Small Portfolio (5M TWD, 5 stocks):")
    print(f"  Recommended Threshold: {small['recommended_threshold']:,.0f} TWD")
    print()

    # Large portfolio
    large = calculate_min_liquidity(portfolio_value=100_000_000, stock_count=10)
    print(f"Large Portfolio (100M TWD, 10 stocks):")
    print(f"  Recommended Threshold: {large['recommended_threshold']:,.0f} TWD")
    print()

    # Zero safety margin (theoretical minimum only)
    no_margin = calculate_min_liquidity(
        portfolio_value=20_000_000, stock_count=8, safety_margin=0.0
    )
    print(f"Zero Safety Margin (8 stocks):")
    print(f"  Theoretical Min = Recommended: {no_margin['recommended_threshold']:,.0f} TWD")
    print(f"  Market Impact: {no_margin['market_impact_pct']:.2f}%")
    print()

    # Very conservative (100x safety multiplier = 1% impact)
    conservative = calculate_min_liquidity(
        portfolio_value=20_000_000, stock_count=8, safety_multiplier=100.0
    )
    print(f"Conservative (100x multiplier):")
    print(f"  Recommended Threshold: {conservative['recommended_threshold']:,.0f} TWD")
    print(f"  Market Impact: {conservative['market_impact_pct']:.2f}%")
    print()


def main() -> None:
    """Run all examples."""
    example_basic_calculation()
    example_stock_count_comparison()
    example_validate_threshold()
    example_recommend_threshold()
    example_edge_cases()

    print("=" * 70)
    print("Key Insights from Examples")
    print("=" * 70)
    print("1. Position size = Portfolio / Stock Count")
    print("2. Lower stock count → Larger positions → Higher liquidity needed")
    print("3. Safety multiplier of 50x → 2% market impact")
    print("4. Safety margin adds buffer (10% margin → 1.11x multiplier)")
    print("5. 150M TWD threshold is too low for 6 stocks (2.22% impact)")
    print("6. 200M TWD threshold works well for 6-12 stock range")
    print("=" * 70)


if __name__ == "__main__":
    main()
