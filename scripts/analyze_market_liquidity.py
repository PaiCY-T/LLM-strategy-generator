#!/usr/bin/env python3
"""Market Liquidity Statistics Analyzer for Taiwan Stock Market.

This analyzer queries Finlab data to determine stock availability at different
liquidity thresholds, helping inform portfolio construction strategies.

Features:
- Query trading value data and calculate 60-day rolling averages
- Categorize stocks by liquidity threshold buckets (50M, 100M, 150M, 200M TWD)
- Break down by market capitalization (large, mid, small cap)
- Generate comprehensive markdown report with actionable insights

Architecture:
- Uses finlab.data.get() for real-time Taiwan stock data
- Supports both live data (via finlab) and preloaded data (via PreloadedData)
- Handles missing data gracefully with informative warnings
- Caches results to avoid repeated API calls

Performance:
- First run: 5-10 minutes (data download from Finlab API)
- Subsequent runs: < 1 minute (uses cached data)

Output:
- MARKET_LIQUIDITY_STATS.md: Comprehensive analysis report
- Console: Summary statistics with visual progress indicators
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from data_wrapper import PreloadedData

# Load environment variables
load_dotenv()


def query_market_liquidity(
    data_obj,
    lookback_days: int = 60,
    verbose: bool = True
) -> pd.DataFrame:
    """Query market liquidity data and calculate rolling averages.

    Args:
        data_obj: Finlab data object or PreloadedData wrapper
        lookback_days: Rolling window for average calculation (default: 60)
        verbose: Print progress messages (default: True)

    Returns:
        DataFrame with columns:
            - stock_id: Stock ticker symbol
            - avg_trading_value_60d: 60-day rolling mean of trading value
            - min_trading_value: Minimum trading value over lookback period
            - max_trading_value: Maximum trading value over lookback period
            - data_points: Number of valid data points (for quality assessment)

    Raises:
        KeyError: If required dataset not available
        Exception: If data loading fails
    """
    if verbose:
        print(f"📊 Querying market liquidity data...")
        print(f"   Lookback period: {lookback_days} days")

    # Query trading value data (成交金額 = trading value in TWD)
    try:
        trading_value = data_obj.get('price:成交金額')
        if verbose:
            print(f"   ✅ Loaded trading value data: {trading_value.shape[0]} rows × {trading_value.shape[1]} stocks")
    except KeyError as e:
        if isinstance(data_obj, PreloadedData):
            available = data_obj.list_available()
            raise KeyError(
                f"Dataset 'price:成交金額' not preloaded. "
                f"Available datasets: {available}"
            )
        raise

    # Calculate 60-day rolling average for each stock
    if verbose:
        print(f"   🔄 Calculating {lookback_days}-day rolling averages...")

    # Use the most recent data (last row of rolling mean)
    rolling_avg = trading_value.rolling(window=lookback_days, min_periods=lookback_days//2).mean()

    # Get most recent valid values for each stock
    results = []
    for stock_id in trading_value.columns:
        stock_data = trading_value[stock_id]
        stock_rolling = rolling_avg[stock_id]

        # Drop NaN values
        valid_data = stock_data.dropna()
        valid_rolling = stock_rolling.dropna()

        if len(valid_rolling) == 0:
            continue  # Skip stocks with no valid data

        # Get most recent rolling average
        latest_avg = valid_rolling.iloc[-1]

        # Calculate min/max over lookback period
        recent_data = valid_data.tail(lookback_days)
        min_val = recent_data.min() if len(recent_data) > 0 else np.nan
        max_val = recent_data.max() if len(recent_data) > 0 else np.nan

        results.append({
            'stock_id': stock_id,
            'avg_trading_value_60d': latest_avg,
            'min_trading_value': min_val,
            'max_trading_value': max_val,
            'data_points': len(valid_data)
        })

    df = pd.DataFrame(results)

    if verbose:
        print(f"   ✅ Analyzed {len(df)} stocks with valid data")
        print(f"   📈 Average trading value range: {df['avg_trading_value_60d'].min()/1e6:.1f}M - {df['avg_trading_value_60d'].max()/1e6:.1f}M TWD")

    return df


def categorize_by_threshold(
    df: pd.DataFrame,
    thresholds: List[int] = [50_000_000, 100_000_000, 150_000_000, 200_000_000],
    verbose: bool = True
) -> Dict[int, int]:
    """Categorize stocks by liquidity threshold buckets.

    Args:
        df: DataFrame from query_market_liquidity()
        thresholds: List of threshold values in TWD (default: 50M, 100M, 150M, 200M)
        verbose: Print progress messages (default: True)

    Returns:
        Dictionary mapping threshold to stock count
        {threshold: count of stocks meeting threshold}

    Example:
        >>> counts = categorize_by_threshold(df)
        >>> print(counts)
        {50000000: 1245, 100000000: 856, 150000000: 542, 200000000: 387}
    """
    if verbose:
        print(f"📦 Categorizing stocks by threshold...")

    results = {}

    for threshold in sorted(thresholds):
        count = (df['avg_trading_value_60d'] >= threshold).sum()
        results[threshold] = count

        if verbose:
            pct = (count / len(df) * 100) if len(df) > 0 else 0
            print(f"   {threshold/1e6:>6.0f}M TWD: {count:>4} stocks ({pct:>5.1f}%)")

    return results


def categorize_by_market_cap(
    df: pd.DataFrame,
    data_obj,
    thresholds: List[int] = [50_000_000, 100_000_000, 150_000_000, 200_000_000],
    verbose: bool = True
) -> Dict[str, Dict[int, int]]:
    """Categorize stocks by market cap and liquidity threshold.

    Args:
        df: DataFrame from query_market_liquidity()
        data_obj: Finlab data object or PreloadedData wrapper
        thresholds: List of threshold values in TWD
        verbose: Print progress messages (default: True)

    Returns:
        Nested dictionary:
        {
            'large_cap': {threshold: count},
            'mid_cap': {threshold: count},
            'small_cap': {threshold: count}
        }

    Market cap categories:
        - Large cap: > 100B TWD (>100億)
        - Mid cap: 10B - 100B TWD (10億-100億)
        - Small cap: < 10B TWD (<10億)
    """
    if verbose:
        print(f"💰 Querying market capitalization data...")

    # Query market cap data
    try:
        market_cap = data_obj.get('etl:market_value')
        if verbose:
            print(f"   ✅ Loaded market cap data: {market_cap.shape[0]} rows × {market_cap.shape[1]} stocks")
    except KeyError as e:
        if isinstance(data_obj, PreloadedData):
            available = data_obj.list_available()
            print(f"   ⚠️  Market cap data not available: {e}")
            print(f"   Available datasets: {available}")
            return {'large_cap': {}, 'mid_cap': {}, 'small_cap': {}}
        raise

    # Get most recent market cap for each stock
    latest_market_cap = market_cap.iloc[-1]

    # Merge with liquidity data
    df_merged = df.copy()
    df_merged['market_cap'] = df_merged['stock_id'].map(latest_market_cap)

    # Remove stocks without market cap data
    df_merged = df_merged.dropna(subset=['market_cap'])

    if verbose:
        print(f"   📊 Matched {len(df_merged)} stocks with market cap data")

    # Define market cap categories (in TWD)
    LARGE_CAP_THRESHOLD = 100_000_000_000  # 100 billion TWD
    MID_CAP_THRESHOLD = 10_000_000_000     # 10 billion TWD

    # Categorize by market cap
    df_merged['cap_category'] = pd.cut(
        df_merged['market_cap'],
        bins=[0, MID_CAP_THRESHOLD, LARGE_CAP_THRESHOLD, float('inf')],
        labels=['small_cap', 'mid_cap', 'large_cap']
    )

    # Count stocks in each category and threshold
    results = {
        'large_cap': {},
        'mid_cap': {},
        'small_cap': {}
    }

    if verbose:
        print(f"   🔄 Categorizing by market cap and threshold...")

    for category in ['large_cap', 'mid_cap', 'small_cap']:
        df_category = df_merged[df_merged['cap_category'] == category]

        for threshold in sorted(thresholds):
            count = (df_category['avg_trading_value_60d'] >= threshold).sum()
            results[category][threshold] = count

        if verbose:
            total = len(df_category)
            print(f"   {category:>12}: {total:>4} stocks")

    return results


def generate_market_report(
    threshold_counts: Dict[int, int],
    marketcap_breakdown: Dict[str, Dict[int, int]],
    total_stocks: int,
    lookback_days: int = 60,
    output_file: str = 'MARKET_LIQUIDITY_STATS.md',
    verbose: bool = True
) -> str:
    """Generate comprehensive markdown report.

    Args:
        threshold_counts: Output from categorize_by_threshold()
        marketcap_breakdown: Output from categorize_by_market_cap()
        total_stocks: Total number of stocks analyzed
        lookback_days: Rolling window used for analysis
        output_file: Output file path (default: MARKET_LIQUIDITY_STATS.md)
        verbose: Print progress messages (default: True)

    Returns:
        Path to generated report file
    """
    if verbose:
        print(f"📝 Generating market report...")

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Build report content
    lines = [
        "# Taiwan Stock Market Liquidity Statistics",
        "",
        f"**Generated**: {timestamp}",
        f"**Analysis Period**: {lookback_days}-day rolling average",
        f"**Total Stocks Analyzed**: {total_stocks:,}",
        "",
        "---",
        "",
        "## Overall Market Statistics",
        "",
        "Stock availability at different liquidity thresholds:",
        "",
        "| Threshold (TWD) | Stock Count | % of Market | Portfolio Impact |",
        "|----------------|-------------|-------------|------------------|"
    ]

    # Overall market table
    for threshold in sorted(threshold_counts.keys()):
        count = threshold_counts[threshold]
        pct = (count / total_stocks * 100) if total_stocks > 0 else 0

        # Portfolio impact assessment
        if pct >= 80:
            impact = "Very High - Wide selection available"
        elif pct >= 60:
            impact = "High - Good selection available"
        elif pct >= 40:
            impact = "Moderate - Limited selection"
        elif pct >= 20:
            impact = "Low - Very limited selection"
        else:
            impact = "Very Low - Severe constraints"

        lines.append(f"| {threshold/1e6:>6.0f}M | {count:>11,} | {pct:>10.1f}% | {impact} |")

    lines.extend([
        "",
        "---",
        "",
        "## Market Cap Breakdown",
        ""
    ])

    # Market cap definitions
    lines.extend([
        "### Market Cap Categories",
        "",
        "- **Large Cap**: Market value > 100 billion TWD (>100億)",
        "- **Mid Cap**: Market value 10-100 billion TWD (10億-100億)",
        "- **Small Cap**: Market value < 10 billion TWD (<10億)",
        "",
    ])

    # Large cap section
    lines.extend([
        "### Large Cap Stocks",
        "",
        "| Threshold (TWD) | Stock Count | % of Large Cap |",
        "|----------------|-------------|----------------|"
    ])

    large_cap_total = sum(marketcap_breakdown['large_cap'].values())
    if large_cap_total > 0:
        large_cap_total = max(marketcap_breakdown['large_cap'].values())  # Use max count as total

    for threshold in sorted(threshold_counts.keys()):
        count = marketcap_breakdown['large_cap'].get(threshold, 0)
        pct = (count / large_cap_total * 100) if large_cap_total > 0 else 0
        lines.append(f"| {threshold/1e6:>6.0f}M | {count:>11,} | {pct:>13.1f}% |")

    # Mid cap section
    lines.extend([
        "",
        "### Mid Cap Stocks",
        "",
        "| Threshold (TWD) | Stock Count | % of Mid Cap |",
        "|----------------|-------------|--------------|"
    ])

    mid_cap_total = sum(marketcap_breakdown['mid_cap'].values())
    if mid_cap_total > 0:
        mid_cap_total = max(marketcap_breakdown['mid_cap'].values())

    for threshold in sorted(threshold_counts.keys()):
        count = marketcap_breakdown['mid_cap'].get(threshold, 0)
        pct = (count / mid_cap_total * 100) if mid_cap_total > 0 else 0
        lines.append(f"| {threshold/1e6:>6.0f}M | {count:>11,} | {pct:>11.1f}% |")

    # Small cap section
    lines.extend([
        "",
        "### Small Cap Stocks",
        "",
        "| Threshold (TWD) | Stock Count | % of Small Cap |",
        "|----------------|-------------|----------------|"
    ])

    small_cap_total = sum(marketcap_breakdown['small_cap'].values())
    if small_cap_total > 0:
        small_cap_total = max(marketcap_breakdown['small_cap'].values())

    for threshold in sorted(threshold_counts.keys()):
        count = marketcap_breakdown['small_cap'].get(threshold, 0)
        pct = (count / small_cap_total * 100) if small_cap_total > 0 else 0
        lines.append(f"| {threshold/1e6:>6.0f}M | {count:>11,} | {pct:>13.1f}% |")

    # Implications section
    lines.extend([
        "",
        "---",
        "",
        "## Portfolio Construction Implications",
        "",
        "### Key Insights",
        "",
    ])

    # Generate insights based on data
    threshold_150m = threshold_counts.get(150_000_000, 0)
    pct_150m = (threshold_150m / total_stocks * 100) if total_stocks > 0 else 0

    lines.append(f"1. **150M TWD Threshold (Recommended)**:")
    lines.append(f"   - {threshold_150m:,} stocks available ({pct_150m:.1f}% of market)")

    if pct_150m >= 30:
        lines.append("   - ✅ Sufficient liquidity for diversified portfolio construction")
        lines.append("   - ✅ Can comfortably hold 10-20 positions with monthly rebalancing")
    elif pct_150m >= 20:
        lines.append("   - ⚠️  Moderate liquidity - diversification may be challenging")
        lines.append("   - ⚠️  Consider 10-15 positions maximum")
    else:
        lines.append("   - ❌ Low liquidity - severe portfolio constraints")
        lines.append("   - ❌ May need to lower threshold or reduce position count")

    lines.extend([
        "",
        "2. **Market Cap Distribution**:",
    ])

    # Analyze market cap distribution at 150M threshold
    large_150m = marketcap_breakdown['large_cap'].get(150_000_000, 0)
    mid_150m = marketcap_breakdown['mid_cap'].get(150_000_000, 0)
    small_150m = marketcap_breakdown['small_cap'].get(150_000_000, 0)

    total_150m = large_150m + mid_150m + small_150m

    if total_150m > 0:
        large_pct = (large_150m / total_150m * 100)
        mid_pct = (mid_150m / total_150m * 100)
        small_pct = (small_150m / total_150m * 100)

        lines.append(f"   - Large cap: {large_150m:,} stocks ({large_pct:.1f}%)")
        lines.append(f"   - Mid cap: {mid_150m:,} stocks ({mid_pct:.1f}%)")
        lines.append(f"   - Small cap: {small_150m:,} stocks ({small_pct:.1f}%)")

        if large_pct > 50:
            lines.append("   - 💡 Portfolio will naturally skew toward large-cap stocks")
        elif mid_pct > 50:
            lines.append("   - 💡 Good balance of mid-cap opportunities")
        else:
            lines.append("   - 💡 Diverse market cap distribution available")

    lines.extend([
        "",
        "3. **Threshold Selection Guidance**:",
        "",
    ])

    # Provide guidance for different threshold levels
    for threshold in sorted(threshold_counts.keys()):
        count = threshold_counts[threshold]
        pct = (count / total_stocks * 100) if total_stocks > 0 else 0

        if threshold == 50_000_000:
            lines.append(f"   - **50M TWD**: {count:,} stocks ({pct:.1f}%) - Very liquid, may include volatile small caps")
        elif threshold == 100_000_000:
            lines.append(f"   - **100M TWD**: {count:,} stocks ({pct:.1f}%) - Good balance of liquidity and quality")
        elif threshold == 150_000_000:
            lines.append(f"   - **150M TWD**: {count:,} stocks ({pct:.1f}%) - Recommended for monthly rebalancing")
        elif threshold == 200_000_000:
            lines.append(f"   - **200M TWD**: {count:,} stocks ({pct:.1f}%) - Very high quality, reduced selection")

    lines.extend([
        "",
        "### Recommendations",
        "",
        "- **For weekly rebalancing**: Use 200M TWD threshold (higher quality, lower impact)",
        "- **For monthly rebalancing**: Use 150M TWD threshold (balanced approach)",
        "- **For large portfolios (>20 stocks)**: Use 100M TWD threshold (wider selection)",
        "- **Market cap constraints**: Consider separate thresholds per cap category",
        "",
        "### Data Quality Notes",
        "",
        f"- Analysis based on {lookback_days}-day rolling average trading value",
        "- Market cap data from most recent available snapshot",
        "- Stocks with incomplete data excluded from analysis",
        "- Thresholds should be reviewed periodically as market conditions change",
        "",
    ])

    # Write report
    report_content = '\n'.join(lines)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    if verbose:
        print(f"   ✅ Report saved to: {output_file}")

    return output_file


def main():
    """Main execution function."""
    print("=" * 70)
    print("Taiwan Stock Market Liquidity Statistics Analyzer")
    print("=" * 70)
    print()

    # Check for API token
    api_token = os.getenv('FINLAB_API_TOKEN')
    if not api_token:
        print("❌ Error: FINLAB_API_TOKEN not found in environment")
        print("   Please set the token in .env file")
        return 1

    print("🔑 Finlab API token found")
    print()

    # Import finlab and login
    try:
        import finlab
        from finlab import data

        print("🔐 Logging in to Finlab...")
        finlab.login(api_token)
        print("   ✅ Login successful")
        print()
    except Exception as e:
        print(f"❌ Error logging in to Finlab: {e}")
        return 1

    # Define thresholds
    thresholds = [50_000_000, 100_000_000, 150_000_000, 200_000_000]

    # Query market liquidity
    try:
        df = query_market_liquidity(data, lookback_days=60, verbose=True)
        print()
    except Exception as e:
        print(f"❌ Error querying market liquidity: {e}")
        return 1

    # Categorize by threshold
    try:
        threshold_counts = categorize_by_threshold(df, thresholds=thresholds, verbose=True)
        print()
    except Exception as e:
        print(f"❌ Error categorizing by threshold: {e}")
        return 1

    # Categorize by market cap
    try:
        marketcap_breakdown = categorize_by_market_cap(
            df,
            data,
            thresholds=thresholds,
            verbose=True
        )
        print()
    except Exception as e:
        print(f"⚠️  Warning: Could not categorize by market cap: {e}")
        print("   Continuing with overall statistics only...")
        marketcap_breakdown = {
            'large_cap': {},
            'mid_cap': {},
            'small_cap': {}
        }
        print()

    # Generate report
    try:
        report_file = generate_market_report(
            threshold_counts,
            marketcap_breakdown,
            total_stocks=len(df),
            lookback_days=60,
            output_file='MARKET_LIQUIDITY_STATS.md',
            verbose=True
        )
        print()
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return 1

    # Print summary
    print("=" * 70)
    print("📊 Analysis Summary")
    print("=" * 70)
    print(f"Total stocks analyzed: {len(df):,}")
    print()
    print("Stock counts by threshold:")
    for threshold in sorted(threshold_counts.keys()):
        count = threshold_counts[threshold]
        pct = (count / len(df) * 100) if len(df) > 0 else 0
        print(f"  {threshold/1e6:>6.0f}M TWD: {count:>4,} stocks ({pct:>5.1f}%)")
    print()

    # Market cap distribution
    if any(marketcap_breakdown.values()):
        print("Market cap distribution at 150M TWD threshold:")
        large_150m = marketcap_breakdown['large_cap'].get(150_000_000, 0)
        mid_150m = marketcap_breakdown['mid_cap'].get(150_000_000, 0)
        small_150m = marketcap_breakdown['small_cap'].get(150_000_000, 0)

        print(f"  Large cap: {large_150m:>4,} stocks")
        print(f"  Mid cap:   {mid_150m:>4,} stocks")
        print(f"  Small cap: {small_150m:>4,} stocks")
        print()

    print(f"✅ Report generated: {report_file}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    exit(main())
