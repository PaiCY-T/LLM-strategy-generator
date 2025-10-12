#!/usr/bin/env python3
"""
Diagnostic test to understand FinLab backtest.sim() report structure.

Run this FIRST before implementing M2 fix to confirm report format.
"""

import pandas as pd
import numpy as np
from finlab import backtest, data

def test_finlab_report_structure():
    """Diagnose what finlab.backtest.sim() actually returns."""
    print("=" * 80)
    print("FINLAB REPORT STRUCTURE DIAGNOSTIC")
    print("=" * 80)

    # Get Taiwan stock data (簡單範例)
    try:
        print("\n1. Loading Taiwan stock data...")
        stock_data = data.get('price:收盤價')
        print(f"   ✅ Successfully loaded stock data: {stock_data.shape}")
        print(f"   Date range: {stock_data.index[0]} to {stock_data.index[-1]}")
    except Exception as e:
        print(f"   ❌ Failed to load stock data: {e}")
        print("\n   Trying alternative data source...")
        try:
            # Alternative: use simple synthetic data with valid Taiwan stock IDs
            dates = pd.date_range('2018-01-01', '2024-12-31', freq='D')
            # Use real Taiwan stock IDs (numbers as strings, then convert to int)
            stock_ids = ['2330', '2317', '2454', '2412', '2308', '1301', '1303', '2881', '2882', '2886']
            stock_data = pd.DataFrame(
                np.random.randn(len(dates), 10).cumsum(axis=0) + 100,
                index=dates,
                columns=stock_ids  # Use string stock IDs (FinLab format)
            )
            print(f"   ✅ Using synthetic data: {stock_data.shape}")
            print(f"   Stock IDs: {list(stock_data.columns)}")
        except Exception as e2:
            print(f"   ❌ Failed to create synthetic data: {e2}")
            return None

    # Simple momentum strategy
    print("\n2. Creating simple momentum strategy...")
    try:
        position = stock_data > stock_data.shift(1)
        print(f"   ✅ Strategy created: {position.shape}")
    except Exception as e:
        print(f"   ❌ Failed to create strategy: {e}")
        return None

    # Run backtest
    print("\n3. Running backtest...")
    try:
        report = backtest.sim(position, resample='D')
        print(f"   ✅ Successfully ran backtest")
    except Exception as e:
        print(f"   ❌ Failed to run backtest: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

    # Diagnose report structure
    print("\n" + "=" * 80)
    print("REPORT STRUCTURE ANALYSIS")
    print("=" * 80)

    print(f"\n4. Report type:")
    print(f"   Type: {type(report)}")
    print(f"   Full type path: {type(report).__module__}.{type(report).__name__}")

    print(f"\n5. Date filtering capabilities:")
    print(f"   Has filter_dates method: {hasattr(report, 'filter_dates')}")

    print(f"\n6. DataFrame analysis:")
    print(f"   Is DataFrame: {isinstance(report, pd.DataFrame)}")
    if isinstance(report, pd.DataFrame):
        print(f"   - Shape: {report.shape}")
        print(f"   - Index type: {type(report.index)}")
        print(f"   - Is DatetimeIndex: {isinstance(report.index, pd.DatetimeIndex)}")
        if isinstance(report.index, pd.DatetimeIndex):
            print(f"   - Date range: {report.index[0]} to {report.index[-1]}")
        print(f"   - Columns (first 10): {list(report.columns)[:10]}")

    print(f"\n7. Report attributes:")
    attrs = [attr for attr in dir(report) if not attr.startswith('_')]
    print(f"   Total attributes: {len(attrs)}")
    print(f"   First 20 attributes:")
    for i, attr in enumerate(attrs[:20], 1):
        attr_type = type(getattr(report, attr, None)).__name__
        print(f"      {i:2d}. {attr:30s} ({attr_type})")
    if len(attrs) > 20:
        print(f"   ... and {len(attrs) - 20} more attributes")

    print(f"\n8. Common report methods:")
    common_methods = ['filter_dates', 'get_stats', 'plot', 'to_dict', 'to_json', 'stats']
    for method in common_methods:
        has_method = hasattr(report, method)
        marker = '✅' if has_method else '❌'
        print(f"   {marker} {method}")

    # Try to extract Sharpe ratio
    print(f"\n9. Sharpe ratio extraction:")
    sharpe_found = False
    try:
        # Method 1: Direct attribute
        if hasattr(report, 'sharpe'):
            sharpe_value = report.sharpe
            print(f"   ✅ Method 1: report.sharpe = {sharpe_value}")
            sharpe_found = True
    except Exception as e:
        print(f"   ❌ Method 1 failed: {e}")

    try:
        # Method 2: get_stats()
        if hasattr(report, 'get_stats'):
            stats = report.get_stats()
            print(f"   ✅ Method 2: report.get_stats() returned {type(stats)}")
            if hasattr(stats, 'sharpe'):
                print(f"      - stats.sharpe = {stats.sharpe}")
                sharpe_found = True
            elif isinstance(stats, dict) and 'sharpe' in stats:
                print(f"      - stats['sharpe'] = {stats['sharpe']}")
                sharpe_found = True
    except Exception as e:
        print(f"   ❌ Method 2 failed: {e}")

    try:
        # Method 3: stats attribute
        if hasattr(report, 'stats'):
            stats = report.stats
            print(f"   ✅ Method 3: report.stats exists ({type(stats)})")
            if hasattr(stats, 'sharpe'):
                print(f"      - stats.sharpe = {stats.sharpe}")
                sharpe_found = True
            elif isinstance(stats, dict) and 'sharpe' in stats:
                print(f"      - stats['sharpe'] = {stats['sharpe']}")
                sharpe_found = True
    except Exception as e:
        print(f"   ❌ Method 3 failed: {e}")

    try:
        # Method 4: DataFrame column
        if isinstance(report, pd.DataFrame) and 'sharpe' in report.columns:
            print(f"   ✅ Method 4: report['sharpe'] found in DataFrame")
            sharpe_found = True
    except Exception as e:
        print(f"   ❌ Method 4 failed: {e}")

    if not sharpe_found:
        print(f"   ⚠️  Could not find Sharpe ratio using standard methods")

    # Test date filtering
    print(f"\n10. Date filtering capability test:")
    test_start = '2020-01-01'
    test_end = '2020-12-31'

    filtering_works = False

    # Test Method 1: filter_dates()
    if hasattr(report, 'filter_dates'):
        try:
            filtered = report.filter_dates(test_start, test_end)
            print(f"   ✅ Method 1: report.filter_dates() works!")
            print(f"      - Filtered type: {type(filtered)}")
            if isinstance(filtered, pd.DataFrame):
                print(f"      - Original shape: {report.shape}")
                print(f"      - Filtered shape: {filtered.shape}")
            filtering_works = True
        except Exception as e:
            print(f"   ⚠️  Method 1: report.filter_dates() exists but failed: {e}")

    # Test Method 2: DataFrame.loc[]
    if isinstance(report, pd.DataFrame) and isinstance(report.index, pd.DatetimeIndex):
        try:
            filtered = report.loc[test_start:test_end]
            print(f"   ✅ Method 2: DataFrame.loc[] date filtering works!")
            print(f"      - Original shape: {report.shape}")
            print(f"      - Filtered shape: {filtered.shape}")
            print(f"      - Date range: {filtered.index[0]} to {filtered.index[-1]}")
            filtering_works = True
        except Exception as e:
            print(f"   ⚠️  Method 2: DataFrame filtering failed: {e}")

    if not filtering_works:
        print(f"   ❌ No date filtering method available - M2 fix CRITICAL!")

    # Summary
    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)

    print(f"\n✅ Report Type: {type(report).__name__}")
    print(f"✅ Has filter_dates: {hasattr(report, 'filter_dates')}")
    print(f"✅ Is DataFrame: {isinstance(report, pd.DataFrame)}")
    print(f"✅ Has DatetimeIndex: {isinstance(report, pd.DataFrame) and isinstance(report.index, pd.DatetimeIndex)}")
    print(f"✅ Date filtering works: {filtering_works}")
    print(f"✅ Sharpe extraction works: {sharpe_found}")

    print("\n" + "=" * 80)
    print("RECOMMENDATION FOR M2 FIX:")
    print("=" * 80)

    if filtering_works:
        if hasattr(report, 'filter_dates'):
            print("\n✅ GOOD NEWS: Report has filter_dates() method")
            print("   → Option A (strict raise error) has LOW RISK")
            print("   → Can safely enforce strict_filtering=True in future")
        elif isinstance(report, pd.DataFrame) and isinstance(report.index, pd.DatetimeIndex):
            print("\n✅ GOOD NEWS: Report is DataFrame with DatetimeIndex")
            print("   → Option A (strict raise error) has LOW RISK")
            print("   → DataFrame.loc[] filtering works perfectly")
        else:
            print("\n⚠️  WARNING: Filtering works but mechanism unclear")
            print("   → Need to investigate further")
    else:
        print("\n❌ CRITICAL: No date filtering capability found!")
        print("   → Option A (strict raise error) will BREAK existing code")
        print("   → MUST use version parameter control (strict_filtering=False default)")
        print("   → Consider implementing custom filter wrapper for FinLab")

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

    return report

if __name__ == '__main__':
    try:
        report = test_finlab_report_structure()
        if report is None:
            print("\n⚠️  Diagnostic completed with errors - review output above")
        else:
            print("\n✅ Diagnostic completed successfully")
    except Exception as e:
        print(f"\n❌ Diagnostic failed with exception: {e}")
        import traceback
        traceback.print_exc()
