#!/usr/bin/env python3
"""Test script for liquidity compliance checker."""

from analyze_metrics import (
    extract_liquidity_threshold,
    check_liquidity_compliance,
    get_compliance_statistics
)


def test_extract_threshold():
    """Test threshold extraction from strategy code."""
    print("Testing threshold extraction...")

    # Test case 1: Simple pattern
    code1 = """
trading_value = data.get('price:成交金額')
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000
"""
    threshold1 = extract_liquidity_threshold(code1)
    print(f"  Test 1: {threshold1} == 100000000? {threshold1 == 100_000_000}")

    # Test case 2: Without shift
    code2 = """
avg_trading_value = trading_value.rolling(20).mean()
liquidity_filter = avg_trading_value > 50_000_000
"""
    threshold2 = extract_liquidity_threshold(code2)
    print(f"  Test 2: {threshold2} == 50000000? {threshold2 == 50_000_000}")

    # Test case 3: Complex pattern
    code3 = """
# Liquidity filter: Average daily trading value over the last 20 days must be above 50 million TWD.
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 150_000_000
"""
    threshold3 = extract_liquidity_threshold(code3)
    print(f"  Test 3: {threshold3} == 150000000? {threshold3 == 150_000_000}")

    # Test case 4: No threshold
    code4 = """
position = close.pct_change(20).is_largest(10)
"""
    threshold4 = extract_liquidity_threshold(code4)
    print(f"  Test 4: {threshold4} == None? {threshold4 is None}")

    print()


def test_check_compliance():
    """Test compliance checking on actual files."""
    print("Testing compliance checking on actual files...")

    test_files = [
        ('generated_strategy_loop_iter0.py', 0),
        ('generated_strategy_loop_iter15.py', 15),
        ('generated_strategy_loop_iter29.py', 29)
    ]

    for filename, iter_num in test_files:
        result = check_liquidity_compliance(iter_num, filename)
        print(f"  {filename}:")
        print(f"    Threshold: {result['threshold_found']}")
        print(f"    Compliant: {result['compliant']}")
        print(f"    Min required: {result['min_threshold']:,} TWD")

    print()


def test_statistics():
    """Test compliance statistics."""
    print("Testing compliance statistics...")

    stats = get_compliance_statistics()
    print(f"  Total checks: {stats['total_checks']}")
    print(f"  Compliant count: {stats['compliant_count']}")
    print(f"  Compliance rate: {stats['compliance_rate']:.1%}")

    if stats['average_threshold']:
        print(f"  Average threshold: {stats['average_threshold']:,.0f} TWD")

    if stats['non_compliant_iterations']:
        print(f"  Non-compliant iterations (first 10): {stats['non_compliant_iterations'][:10]}")

    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Liquidity Compliance Checker - Unit Tests")
    print("=" * 60)
    print()

    test_extract_threshold()
    test_check_compliance()
    test_statistics()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
