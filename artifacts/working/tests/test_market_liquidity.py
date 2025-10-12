#!/usr/bin/env python3
"""Unit tests for analyze_market_liquidity.py"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_market_liquidity import (
    query_market_liquidity,
    categorize_by_threshold,
    categorize_by_market_cap,
    generate_market_report
)

load_dotenv()


def test_query_market_liquidity():
    """Test market liquidity query function."""
    print("=" * 60)
    print("Test 1: query_market_liquidity()")
    print("=" * 60)

    import finlab
    from finlab import data

    finlab.login(os.getenv('FINLAB_API_TOKEN'))

    df = query_market_liquidity(data, lookback_days=60, verbose=True)

    # Validate results
    assert isinstance(df, pd.DataFrame), "Should return DataFrame"
    assert len(df) > 0, "Should have data"
    assert 'stock_id' in df.columns, "Should have stock_id column"
    assert 'avg_trading_value_60d' in df.columns, "Should have avg_trading_value_60d column"

    print(f"\n✅ Test 1 passed: {len(df)} stocks analyzed")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Sample data:\n{df.head(3)}")
    print()

    return df


def test_categorize_by_threshold(df):
    """Test threshold categorization."""
    print("=" * 60)
    print("Test 2: categorize_by_threshold()")
    print("=" * 60)

    thresholds = [50_000_000, 100_000_000, 150_000_000, 200_000_000]
    counts = categorize_by_threshold(df, thresholds=thresholds, verbose=True)

    # Validate results
    assert isinstance(counts, dict), "Should return dict"
    assert len(counts) == len(thresholds), "Should have all thresholds"

    # Check decreasing counts (higher threshold = fewer stocks)
    prev_count = float('inf')
    for threshold in sorted(thresholds):
        count = counts[threshold]
        assert count <= prev_count, f"Counts should decrease: {threshold}"
        prev_count = count

    print(f"\n✅ Test 2 passed: Threshold categorization correct")
    print()

    return counts


def test_categorize_by_market_cap(df):
    """Test market cap categorization."""
    print("=" * 60)
    print("Test 3: categorize_by_market_cap()")
    print("=" * 60)

    import finlab
    from finlab import data

    thresholds = [50_000_000, 100_000_000, 150_000_000, 200_000_000]
    breakdown = categorize_by_market_cap(
        df, data, thresholds=thresholds, verbose=True
    )

    # Validate results
    assert isinstance(breakdown, dict), "Should return dict"
    assert 'large_cap' in breakdown, "Should have large_cap category"
    assert 'mid_cap' in breakdown, "Should have mid_cap category"
    assert 'small_cap' in breakdown, "Should have small_cap category"

    print(f"\n✅ Test 3 passed: Market cap categorization correct")
    print()

    return breakdown


def test_generate_report(threshold_counts, marketcap_breakdown, total_stocks):
    """Test report generation."""
    print("=" * 60)
    print("Test 4: generate_market_report()")
    print("=" * 60)

    output_file = 'TEST_MARKET_LIQUIDITY_STATS.md'

    report_path = generate_market_report(
        threshold_counts,
        marketcap_breakdown,
        total_stocks=total_stocks,
        lookback_days=60,
        output_file=output_file,
        verbose=True
    )

    # Validate results
    assert os.path.exists(report_path), "Report file should exist"

    with open(report_path, 'r') as f:
        content = f.read()

    assert len(content) > 0, "Report should have content"
    assert 'Taiwan Stock Market Liquidity Statistics' in content, "Should have title"
    assert '150M TWD' in content, "Should mention 150M threshold"

    print(f"\n✅ Test 4 passed: Report generated successfully")
    print(f"   File: {report_path}")
    print(f"   Size: {len(content)} characters")
    print()

    # Clean up test file
    os.remove(report_path)
    print("   🗑️  Cleaned up test file")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Market Liquidity Analyzer - Unit Tests")
    print("=" * 60)
    print()

    try:
        # Test 1: Query market liquidity
        df = test_query_market_liquidity()

        # Test 2: Categorize by threshold
        threshold_counts = test_categorize_by_threshold(df)

        # Test 3: Categorize by market cap
        marketcap_breakdown = test_categorize_by_market_cap(df)

        # Test 4: Generate report
        test_generate_report(threshold_counts, marketcap_breakdown, len(df))

        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print()

        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
