"""
Unit tests for pattern extraction (Task 20).

Tests extract_success_patterns() and _prioritize_patterns() functions
to ensure correct pattern identification and prioritization.
"""

import pytest
from typing import Dict, Any

from performance_attributor import extract_success_patterns, _prioritize_patterns


# Test Fixtures

@pytest.fixture
def sample_strategy_code() -> str:
    """Sample strategy code with multiple patterns."""
    return """
# Trading Strategy with ROE and Liquidity

data = data.get('price:收盤價')
roe = data.get('fundamental_features:ROE綜合損益')
revenue = data.get('fundamental_features:營收成長率')
trading_value = data.get('price:成交金額')

# Strict liquidity filter (critical)
liquidity_filter = trading_value > 150_000_000

# ROE smoothing with 4-quarter window (critical)
roe_smoothed = roe.rolling(window=4).mean()

# Forward-fill revenue data (moderate)
revenue_filled = revenue.ffill()

# Value factor using inverse P/E (moderate)
pe = data.get('fundamental_features:本益比')
value_factor = 1 / pe

# Combine signals
signal = (roe_smoothed * 0.6 + value_factor * 0.4)[liquidity_filter]
"""


@pytest.fixture
def parameters_with_all_patterns() -> Dict[str, Any]:
    """Parameters dict with all extractable patterns."""
    return {
        'roe_type': 'smoothed',
        'roe_smoothing_window': 4,
        'liquidity_threshold': 150_000_000,
        'revenue_handling': 'forward_filled',
        'value_factor': 'inverse_pe',
        'price_filter': 10.0,
        'volume_filter': 1000,
        'market_cap_filter': None
    }


@pytest.fixture
def parameters_roe_only() -> Dict[str, Any]:
    """Parameters with only ROE smoothing pattern."""
    return {
        'roe_type': 'smoothed',
        'roe_smoothing_window': 6,
        'liquidity_threshold': None,
        'revenue_handling': None,
        'value_factor': None,
        'price_filter': None,
        'volume_filter': None,
        'market_cap_filter': None
    }


@pytest.fixture
def parameters_liquidity_only() -> Dict[str, Any]:
    """Parameters with only liquidity pattern."""
    return {
        'roe_type': 'raw',
        'roe_smoothing_window': 1,
        'liquidity_threshold': 100_000_000,
        'revenue_handling': None,
        'value_factor': None,
        'price_filter': None,
        'volume_filter': None,
        'market_cap_filter': None
    }


# Core Tests (Task 20 Specification)

def test_extracts_roe_smoothing_pattern(sample_strategy_code, parameters_roe_only):
    """Test 1: Verify ROE smoothing pattern is extracted correctly."""

    patterns = extract_success_patterns(sample_strategy_code, parameters_roe_only)

    # Should extract ROE pattern
    assert len(patterns) > 0, "No patterns extracted"

    # Find ROE pattern
    roe_pattern = next((p for p in patterns if 'roe.rolling' in p.lower()), None)
    assert roe_pattern is not None, "ROE smoothing pattern not found"

    # Verify pattern content
    assert '6-quarter' in roe_pattern, "Window size not in pattern"
    assert 'noise' in roe_pattern.lower(), "Noise reduction not mentioned"


def test_extracts_liquidity_pattern(sample_strategy_code, parameters_liquidity_only):
    """Test 2: Verify liquidity filter pattern is extracted correctly."""

    patterns = extract_success_patterns(sample_strategy_code, parameters_liquidity_only)

    # Should extract liquidity pattern
    assert len(patterns) > 0, "No patterns extracted"

    # Find liquidity pattern
    liquidity_pattern = next((p for p in patterns if 'liquidity' in p.lower()), None)
    assert liquidity_pattern is not None, "Liquidity pattern not found"

    # Verify pattern content
    assert '100,000,000' in liquidity_pattern or '100000000' in liquidity_pattern, "Threshold not formatted"
    assert 'stable' in liquidity_pattern.lower() or 'volume' in liquidity_pattern.lower(), "Purpose not explained"


def test_extracts_revenue_pattern(sample_strategy_code):
    """Test 3: Verify revenue handling pattern is extracted correctly."""

    parameters = {
        'roe_type': 'raw',
        'roe_smoothing_window': 1,
        'liquidity_threshold': None,
        'revenue_handling': 'forward_filled',
        'value_factor': None,
        'price_filter': None,
        'volume_filter': None,
        'market_cap_filter': None
    }

    patterns = extract_success_patterns(sample_strategy_code, parameters)

    # Find revenue pattern
    revenue_pattern = next((p for p in patterns if 'revenue' in p.lower() or 'ffill' in p.lower()), None)
    assert revenue_pattern is not None, "Revenue pattern not found"

    # Verify pattern content
    assert 'ffill' in revenue_pattern.lower() or 'forward' in revenue_pattern.lower(), "Forward-fill not mentioned"
    assert 'missing' in revenue_pattern.lower() or 'values' in revenue_pattern.lower(), "Purpose not explained"


def test_patterns_prioritized_correctly(sample_strategy_code, parameters_with_all_patterns):
    """Test 4: Verify critical patterns appear before moderate patterns."""

    patterns = extract_success_patterns(sample_strategy_code, parameters_with_all_patterns)

    assert len(patterns) >= 4, f"Expected at least 4 patterns, got {len(patterns)}"

    # Find indices of critical and moderate patterns
    critical_indices = []
    moderate_indices = []

    for i, pattern in enumerate(patterns):
        pattern_lower = pattern.lower()
        if 'rolling' in pattern_lower or 'liquidity' in pattern_lower or 'smoothing' in pattern_lower:
            critical_indices.append(i)
        elif 'ffill' in pattern_lower or 'forward' in pattern_lower or 'inverse' in pattern_lower or 'value' in pattern_lower:
            moderate_indices.append(i)

    # All critical patterns should come before all moderate patterns
    if critical_indices and moderate_indices:
        max_critical_index = max(critical_indices)
        min_moderate_index = min(moderate_indices)
        assert max_critical_index < min_moderate_index, \
            f"Critical patterns not prioritized: critical indices {critical_indices}, moderate indices {moderate_indices}"


def test_empty_parameters_returns_empty_list(sample_strategy_code):
    """Test 5: Verify graceful handling of empty parameters."""

    empty_params = {
        'roe_type': 'raw',
        'roe_smoothing_window': 1,
        'liquidity_threshold': None,
        'revenue_handling': None,
        'value_factor': None,
        'price_filter': None,
        'volume_filter': None,
        'market_cap_filter': None
    }

    patterns = extract_success_patterns(sample_strategy_code, empty_params)

    # Should return empty list or minimal patterns
    assert isinstance(patterns, list), "Should return list"
    # Empty params = no patterns (or very few low-priority ones)
    assert len(patterns) <= 2, f"Expected <= 2 patterns for empty params, got {len(patterns)}"


# Edge Case Tests

def test_prioritize_patterns_empty_list():
    """Test edge case: _prioritize_patterns with empty list."""

    result = _prioritize_patterns([])

    assert result == [], "Empty list should return empty list"


def test_prioritize_patterns_single_pattern():
    """Test edge case: _prioritize_patterns with single pattern."""

    patterns = ["roe.rolling(window=4).mean() - 4-quarter smoothing"]

    result = _prioritize_patterns(patterns)

    assert len(result) == 1, "Should return single pattern"
    assert result[0] == patterns[0], "Pattern should be unchanged"


def test_prioritize_patterns_all_critical():
    """Test edge case: All patterns are critical."""

    patterns = [
        "roe.rolling(window=4).mean() - smoothing",
        "liquidity_filter > 100,000,000 TWD - strict filter"
    ]

    result = _prioritize_patterns(patterns)

    assert len(result) == 2, "Should return both patterns"
    # Order should be preserved (all critical)
    assert result == patterns, "Order should be preserved for same priority"


def test_prioritize_patterns_mixed_order():
    """Test prioritization with mixed pattern types."""

    patterns = [
        "sector filter - low priority",                           # low
        "revenue_yoy.ffill() - forward fill",                     # moderate
        "liquidity_filter > 150M TWD - strict",                   # critical
        "1 / pe_ratio - value factor",                            # moderate
        "roe.rolling(window=4).mean() - smoothing"                # critical
    ]

    result = _prioritize_patterns(patterns)

    # First patterns should be critical
    assert 'liquidity' in result[0].lower() or 'rolling' in result[0].lower(), \
        f"First pattern should be critical, got: {result[0]}"
    assert 'liquidity' in result[1].lower() or 'rolling' in result[1].lower(), \
        f"Second pattern should be critical, got: {result[1]}"

    # Middle patterns should be moderate
    assert 'ffill' in result[2].lower() or 'value' in result[2].lower() or 'inverse' in result[2].lower(), \
        f"Third pattern should be moderate, got: {result[2]}"

    # Last pattern should be low
    assert 'sector' in result[-1].lower(), f"Last pattern should be low priority, got: {result[-1]}"


def test_extract_patterns_with_value_factor(sample_strategy_code):
    """Test extraction of value factor pattern."""

    parameters = {
        'roe_type': 'raw',
        'roe_smoothing_window': 1,
        'liquidity_threshold': None,
        'revenue_handling': None,
        'value_factor': 'inverse_pe',
        'price_filter': None,
        'volume_filter': None,
        'market_cap_filter': None
    }

    patterns = extract_success_patterns(sample_strategy_code, parameters)

    # Find value factor pattern
    value_pattern = next((p for p in patterns if 'value' in p.lower() or 'pe' in p.lower()), None)
    assert value_pattern is not None, "Value factor pattern not found"

    # Verify pattern content
    assert '1 / pe' in value_pattern.lower() or 'inverse' in value_pattern.lower(), "Inverse P/E not mentioned"


def test_extract_patterns_with_filters(sample_strategy_code):
    """Test extraction of price and volume filter patterns."""

    parameters = {
        'roe_type': 'raw',
        'roe_smoothing_window': 1,
        'liquidity_threshold': None,
        'revenue_handling': None,
        'value_factor': None,
        'price_filter': 15.0,
        'volume_filter': 5000,
        'market_cap_filter': None
    }

    patterns = extract_success_patterns(sample_strategy_code, parameters)

    # Should have at least 2 patterns (price + volume)
    assert len(patterns) >= 2, f"Expected at least 2 filter patterns, got {len(patterns)}"

    # Find filter patterns
    price_pattern = next((p for p in patterns if 'price' in p.lower()), None)
    volume_pattern = next((p for p in patterns if 'volume' in p.lower() and 'liquidity' not in p.lower()), None)

    # At least one filter should be present
    assert price_pattern is not None or volume_pattern is not None, "No filter patterns found"


def test_pattern_format_consistency(sample_strategy_code, parameters_with_all_patterns):
    """Test that all patterns follow consistent format."""

    patterns = extract_success_patterns(sample_strategy_code, parameters_with_all_patterns)

    for pattern in patterns:
        # Each pattern should have a description (contain " - ")
        assert ' - ' in pattern, f"Pattern missing separator: {pattern}"

        # Pattern should be non-empty on both sides
        parts = pattern.split(' - ')
        assert len(parts) >= 2, f"Pattern not properly formatted: {pattern}"
        assert len(parts[0].strip()) > 0, f"Pattern code part empty: {pattern}"
        assert len(parts[1].strip()) > 0, f"Pattern description part empty: {pattern}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
