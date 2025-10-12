#!/usr/bin/env python3
"""Demo: Market Liquidity Statistics Analyzer Usage Examples

This script demonstrates various use cases for the market liquidity analyzer,
including integration with strategy generation and portfolio construction.
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()


def example_1_basic_analysis():
    """Example 1: Run basic market liquidity analysis."""
    print("=" * 70)
    print("Example 1: Basic Market Liquidity Analysis")
    print("=" * 70)
    print()

    from analyze_market_liquidity import query_market_liquidity
    import finlab
    from finlab import data

    # Login to Finlab
    finlab.login(os.getenv('FINLAB_API_TOKEN'))

    # Query market liquidity
    df = query_market_liquidity(data, lookback_days=60, verbose=True)

    # Display summary statistics
    print("\n📊 Summary Statistics:")
    print(f"   Total stocks: {len(df):,}")
    print(f"   Avg trading value (median): {df['avg_trading_value_60d'].median()/1e6:.1f}M TWD")
    print(f"   Avg trading value (mean): {df['avg_trading_value_60d'].mean()/1e6:.1f}M TWD")
    print(f"   Min: {df['avg_trading_value_60d'].min()/1e6:.1f}M TWD")
    print(f"   Max: {df['avg_trading_value_60d'].max()/1e6:.1f}M TWD")
    print()

    return df


def example_2_threshold_analysis(df):
    """Example 2: Analyze different threshold levels."""
    print("=" * 70)
    print("Example 2: Threshold Analysis")
    print("=" * 70)
    print()

    from analyze_market_liquidity import categorize_by_threshold

    # Test multiple threshold levels
    thresholds = [50_000_000, 75_000_000, 100_000_000, 125_000_000,
                  150_000_000, 175_000_000, 200_000_000, 250_000_000]

    counts = categorize_by_threshold(df, thresholds=thresholds, verbose=False)

    print("📦 Threshold Analysis:")
    print(f"{'Threshold':>12} | {'Count':>6} | {'% of Market':>11} | Portfolio Size Recommendation")
    print("-" * 70)

    for threshold in sorted(thresholds):
        count = counts[threshold]
        pct = (count / len(df) * 100)

        # Recommend portfolio size based on universe size
        if count >= 500:
            rec = "15-20 positions"
        elif count >= 400:
            rec = "10-15 positions"
        elif count >= 300:
            rec = "8-12 positions"
        else:
            rec = "5-10 positions"

        print(f"{threshold/1e6:>10.0f}M | {count:>6,} | {pct:>10.1f}% | {rec}")

    print()


def example_3_market_cap_breakdown(df):
    """Example 3: Market cap breakdown analysis."""
    print("=" * 70)
    print("Example 3: Market Cap Breakdown")
    print("=" * 70)
    print()

    from analyze_market_liquidity import categorize_by_market_cap
    import finlab
    from finlab import data

    breakdown = categorize_by_market_cap(df, data, verbose=False)

    print("💰 Market Cap Distribution at 150M TWD Threshold:")
    print()

    categories = [
        ('Large Cap (>100B TWD)', 'large_cap'),
        ('Mid Cap (10B-100B TWD)', 'mid_cap'),
        ('Small Cap (<10B TWD)', 'small_cap')
    ]

    total_150m = sum(breakdown[cat][150_000_000] for _, cat in categories)

    for label, cat in categories:
        count = breakdown[cat][150_000_000]
        pct = (count / total_150m * 100) if total_150m > 0 else 0
        print(f"   {label:>25}: {count:>3} stocks ({pct:>5.1f}%)")

    print()


def example_4_filter_universe(df):
    """Example 4: Filter tradeable universe for strategy."""
    print("=" * 70)
    print("Example 4: Filter Tradeable Universe")
    print("=" * 70)
    print()

    # Define threshold
    threshold = 150_000_000

    # Filter stocks
    liquid_stocks = df[df['avg_trading_value_60d'] >= threshold]['stock_id'].tolist()

    print(f"🎯 Tradeable Universe at {threshold/1e6:.0f}M TWD threshold:")
    print(f"   Total stocks: {len(liquid_stocks):,}")
    print(f"   Sample stocks: {liquid_stocks[:20]}")
    print()

    # Show stocks just below threshold (borderline cases)
    borderline = df[
        (df['avg_trading_value_60d'] >= threshold * 0.9) &
        (df['avg_trading_value_60d'] < threshold)
    ].sort_values('avg_trading_value_60d', ascending=False)

    print(f"⚠️  Borderline stocks (90-100% of threshold):")
    print(f"   Count: {len(borderline)}")
    if len(borderline) > 0:
        print(f"   Top 5: {borderline['stock_id'].head().tolist()}")
        print(f"   Avg value: {borderline['avg_trading_value_60d'].mean()/1e6:.1f}M TWD")
    print()

    return liquid_stocks


def example_5_quality_filtering(df):
    """Example 5: Filter by data quality."""
    print("=" * 70)
    print("Example 5: Data Quality Filtering")
    print("=" * 70)
    print()

    # Filter by data quality (>1 year of data)
    high_quality = df[df['data_points'] >= 250]
    medium_quality = df[(df['data_points'] >= 100) & (df['data_points'] < 250)]
    low_quality = df[df['data_points'] < 100]

    print("📊 Data Quality Distribution:")
    print(f"   High quality (>1 year):   {len(high_quality):>4} stocks ({len(high_quality)/len(df)*100:>5.1f}%)")
    print(f"   Medium quality (3m-1y):   {len(medium_quality):>4} stocks ({len(medium_quality)/len(df)*100:>5.1f}%)")
    print(f"   Low quality (<3 months):  {len(low_quality):>4} stocks ({len(low_quality)/len(df)*100:>5.1f}%)")
    print()

    # Show impact on tradeable universe
    threshold = 150_000_000
    high_quality_liquid = high_quality[high_quality['avg_trading_value_60d'] >= threshold]

    print(f"💡 High Quality + Liquid (150M TWD) Universe:")
    print(f"   Total stocks: {len(high_quality_liquid):,}")
    print(f"   Percentage of all liquid: {len(high_quality_liquid)/len(df[df['avg_trading_value_60d'] >= threshold])*100:.1f}%")
    print()


def example_6_strategy_integration():
    """Example 6: Integration with strategy generation."""
    print("=" * 70)
    print("Example 6: Strategy Integration Example")
    print("=" * 70)
    print()

    print("📝 Sample code for strategy generation integration:")
    print()
    print("""
# In your strategy generation code:

from analyze_market_liquidity import query_market_liquidity
import finlab
from finlab import data

# Get liquidity data
finlab.login(api_token)
liquidity_df = query_market_liquidity(data, lookback_days=60, verbose=False)

# Define your threshold
LIQUIDITY_THRESHOLD = 150_000_000  # 150M TWD

# Filter tradeable universe
tradeable_stocks = liquidity_df[
    liquidity_df['avg_trading_value_60d'] >= LIQUIDITY_THRESHOLD
]['stock_id'].tolist()

# Use in strategy
def my_strategy():
    close = data.get('price:收盤價')

    # Your strategy logic here
    signal = close.pct_change(20).is_largest(10)

    # Filter by liquidity
    signal = signal[tradeable_stocks]

    return signal

# Verify compliance
strategy_universe = my_strategy()
compliant_stocks = set(strategy_universe.columns) & set(tradeable_stocks)
print(f"Strategy universe: {len(strategy_universe.columns)} stocks")
print(f"Liquidity compliant: {len(compliant_stocks)} stocks")
    """)
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Market Liquidity Statistics Analyzer - Usage Examples")
    print("=" * 70)
    print()

    try:
        # Example 1: Basic analysis
        df = example_1_basic_analysis()

        # Example 2: Threshold analysis
        example_2_threshold_analysis(df)

        # Example 3: Market cap breakdown
        example_3_market_cap_breakdown(df)

        # Example 4: Filter universe
        liquid_stocks = example_4_filter_universe(df)

        # Example 5: Quality filtering
        example_5_quality_filtering(df)

        # Example 6: Strategy integration
        example_6_strategy_integration()

        print("=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70)
        print()

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
