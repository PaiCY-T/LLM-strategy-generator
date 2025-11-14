"""TDD Test Suite for StrategyMetrics Dict Interface Compatibility.

This test suite follows Test-Driven Development principles:
1. All tests written BEFORE implementation
2. Tests define the desired behavior of dict-like methods
3. Implementation should make these tests pass

Tests cover backward compatibility with legacy code that expects
Dict[str, float] interface while preserving dataclass type safety.
"""

import pytest
import numpy as np
from src.backtest.metrics import StrategyMetrics
from src.constants import METRIC_SHARPE, METRIC_DRAWDOWN, METRIC_WIN_RATE


# ============================================================================
# CATEGORY A: .get() Method Tests (10 tests)
# ============================================================================

class TestGetMethod:
    """TDD tests for .get() dict-like method."""

    def test_get_existing_attribute_returns_value(self):
        """RED: .get() should return attribute value when it exists."""
        metrics = StrategyMetrics(sharpe_ratio=1.5, total_return=0.25)

        assert metrics.get('sharpe_ratio') == 1.5
        assert metrics.get('total_return') == 0.25

    def test_get_none_attribute_returns_default(self):
        """RED: .get() returns default for None values.

        For dataclass with optional fields, None represents "no value".
        This aligns with real usage where None metrics need numeric defaults.
        Champion_tracker.py:635 expects: metrics.get(METRIC_SHARPE, 0) → 0
        """
        metrics = StrategyMetrics(sharpe_ratio=None)

        # Practical behavior: treat None as "no value", return default
        assert metrics.get('sharpe_ratio', 0) == 0

    def test_get_nonexistent_attribute_returns_default(self):
        """RED: .get() should return default for missing attributes."""
        metrics = StrategyMetrics()

        assert metrics.get('nonexistent', 0.0) == 0.0
        assert metrics.get('invalid_key', -1) == -1

    def test_get_with_numeric_default_zero(self):
        """RED: Common pattern - .get() with default=0."""
        metrics = StrategyMetrics()

        # Empty metrics, all should return 0
        assert metrics.get('sharpe_ratio', 0) == 0
        assert metrics.get('total_return', 0) == 0
        assert metrics.get('max_drawdown', 0) == 0

    def test_get_all_five_metric_attributes(self):
        """RED: .get() works for all 5 standard metrics."""
        metrics = StrategyMetrics(
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=-0.15,
            win_rate=0.65,
            execution_success=True
        )

        assert metrics.get('sharpe_ratio') == 1.5
        assert metrics.get('total_return') == 0.25
        assert metrics.get('max_drawdown') == -0.15
        assert metrics.get('win_rate') == 0.65
        assert metrics.get('execution_success') is True

    def test_get_boolean_attribute(self):
        """RED: .get() handles boolean execution_success correctly."""
        metrics_true = StrategyMetrics(execution_success=True)
        metrics_false = StrategyMetrics(execution_success=False)

        assert metrics_true.get('execution_success') is True
        assert metrics_false.get('execution_success') is False

    def test_get_with_constant_based_access(self):
        """RED: champion_tracker.py pattern - .get() with constants."""
        metrics = StrategyMetrics(sharpe_ratio=1.5, max_drawdown=-0.12)

        # Simulate champion_tracker.py line 635
        champion_sharpe = metrics.get(METRIC_SHARPE, 0)
        champion_dd = metrics.get(METRIC_DRAWDOWN, 1.0)

        assert champion_sharpe == 1.5
        assert champion_dd == -0.12

    def test_get_empty_metrics_with_defaults(self):
        """RED: All .get() calls on empty metrics return defaults."""
        metrics = StrategyMetrics()

        assert metrics.get('sharpe_ratio', 0) == 0
        assert metrics.get('total_return', 0.0) == 0.0
        assert metrics.get('max_drawdown', 1.0) == 1.0
        assert metrics.get('win_rate', 0.5) == 0.5

    def test_get_explicit_none_default(self):
        """RED: .get() with default=None explicitly."""
        metrics = StrategyMetrics()

        result = metrics.get('sharpe_ratio', None)
        assert result is None

    def test_get_chain_multiple_attributes(self):
        """RED: Multiple .get() calls in sequence."""
        metrics = StrategyMetrics(sharpe_ratio=0.95, win_rate=0.65)

        # Simulate prompt_builder.py lines 176-186
        sharpe = metrics.get('sharpe_ratio', 0)
        mdd = metrics.get('max_drawdown', 1.0)
        win_rate = metrics.get('win_rate', 0)

        assert sharpe == 0.95
        assert mdd == 1.0  # Not set, returns default
        assert win_rate == 0.65


# ============================================================================
# CATEGORY B: __getitem__ Bracket Access Tests (4 tests)
# ============================================================================

class TestBracketAccess:
    """TDD tests for __getitem__ dict[key] syntax."""

    def test_bracket_existing_attribute_returns_value(self):
        """RED: metrics['key'] should return value for existing attributes."""
        metrics = StrategyMetrics(sharpe_ratio=1.5, total_return=0.25)

        assert metrics['sharpe_ratio'] == 1.5
        assert metrics['total_return'] == 0.25

    def test_bracket_none_value_returns_none(self):
        """RED: metrics['key'] returns None if attribute value is None."""
        metrics = StrategyMetrics(sharpe_ratio=None)

        assert metrics['sharpe_ratio'] is None

    def test_bracket_nonexistent_raises_keyerror(self):
        """RED: metrics['invalid'] should raise KeyError."""
        metrics = StrategyMetrics()

        with pytest.raises(KeyError):
            _ = metrics['nonexistent']

    def test_bracket_keyerror_message_format(self):
        """RED: KeyError should have informative message."""
        metrics = StrategyMetrics()

        with pytest.raises(KeyError, match="Metric 'invalid_key' not found"):
            _ = metrics['invalid_key']


# ============================================================================
# CATEGORY C: __contains__ Membership Tests (4 tests)
# ============================================================================

class TestContainsOperator:
    """TDD tests for 'in' operator support."""

    def test_contains_existing_attributes_return_true(self):
        """RED: 'attribute' in metrics should return True for all 5 metrics."""
        metrics = StrategyMetrics()

        assert 'sharpe_ratio' in metrics
        assert 'total_return' in metrics
        assert 'max_drawdown' in metrics
        assert 'win_rate' in metrics
        assert 'execution_success' in metrics

    def test_contains_all_five_standard_metrics(self):
        """RED: All 5 standard metrics should be contained."""
        metrics = StrategyMetrics(sharpe_ratio=1.5)

        # Even with only one value set, all attributes exist
        standard_keys = ['sharpe_ratio', 'total_return', 'max_drawdown',
                        'win_rate', 'execution_success']

        for key in standard_keys:
            assert key in metrics

    def test_contains_nonexistent_returns_false(self):
        """RED: 'invalid' in metrics should return False."""
        metrics = StrategyMetrics()

        assert 'nonexistent' not in metrics
        assert 'invalid_key' not in metrics
        assert 'random_attr' not in metrics

    def test_contains_independent_of_value(self):
        """RED: Membership testing checks attribute existence, not value."""
        metrics = StrategyMetrics(sharpe_ratio=None)

        # Attribute exists even though value is None
        assert 'sharpe_ratio' in metrics


# ============================================================================
# CATEGORY D: .keys() Method Tests (3 tests)
# ============================================================================

class TestKeysMethod:
    """TDD tests for .keys() dict-like method."""

    def test_keys_returns_list_of_five_metrics(self):
        """RED: .keys() should return list of all 5 metric attribute names."""
        metrics = StrategyMetrics()

        keys = metrics.keys()

        assert isinstance(keys, list)
        assert len(keys) == 5

    def test_keys_contains_all_standard_metrics(self):
        """RED: .keys() list contains exact metric names."""
        metrics = StrategyMetrics()

        keys = metrics.keys()

        assert 'sharpe_ratio' in keys
        assert 'total_return' in keys
        assert 'max_drawdown' in keys
        assert 'win_rate' in keys
        assert 'execution_success' in keys

    def test_keys_are_strings(self):
        """RED: All keys should be string type."""
        metrics = StrategyMetrics()

        keys = metrics.keys()

        assert all(isinstance(key, str) for key in keys)


# ============================================================================
# CATEGORY E: Backward Compatibility Integration Tests (6 tests)
# ============================================================================

class TestBackwardCompatibility:
    """TDD integration tests for real legacy code patterns."""

    def test_prompt_builder_extract_success_factors_pattern(self):
        """RED: prompt_builder.py lines 176-190 pattern."""
        # Simulate champion metrics in prompt building
        metrics = StrategyMetrics(
            sharpe_ratio=0.95,
            max_drawdown=-0.12,
            win_rate=0.65
        )

        # Extract pattern from prompt_builder.py
        sharpe = metrics.get('sharpe_ratio', 0)
        mdd = metrics.get('max_drawdown', 1.0)
        win_rate = metrics.get('win_rate', 0)
        calmar = metrics.get('calmar_ratio', 0)  # Doesn't exist

        # Assertions matching real usage
        assert sharpe > 0.8  # Line 177 condition
        assert mdd < 0.15  # Line 181 condition
        assert win_rate > 0.6  # Line 185 condition
        assert calmar == 0  # Not set, returns default

    def test_champion_tracker_comparison_pattern(self):
        """RED: champion_tracker.py line 635 pattern."""
        # Simulate champion metrics comparison
        champion_metrics = StrategyMetrics(sharpe_ratio=1.5)
        current_metrics = StrategyMetrics(sharpe_ratio=1.8)

        # Pattern from champion_tracker.py
        champion_sharpe = champion_metrics.get(METRIC_SHARPE, 0)
        current_sharpe = current_metrics.get(METRIC_SHARPE, 0)

        # Should enable comparison logic
        assert current_sharpe > champion_sharpe
        assert champion_sharpe == 1.5
        assert current_sharpe == 1.8

    def test_historical_jsonl_loading_chain(self):
        """RED: Load from JSONL dict -> .get() access pattern."""
        # Simulate historical JSONL data (dict format)
        historical_dict = {
            'sharpe_ratio': 1.5,
            'total_return': 0.25,
            'max_drawdown': -0.15,
            'win_rate': 0.65,
            'execution_success': True
        }

        # Convert to StrategyMetrics
        metrics = StrategyMetrics.from_dict(historical_dict)

        # Both access patterns should work
        assert metrics.get('sharpe_ratio', 0) == 1.5  # Dict-like
        assert metrics.sharpe_ratio == 1.5  # Attribute access
        assert metrics.get('total_return', 0) == 0.25

    def test_to_dict_and_get_equivalence(self):
        """RED: .to_dict() + .get() should be equivalent to dict access."""
        metrics = StrategyMetrics(sharpe_ratio=1.5, win_rate=0.65)

        dict_repr = metrics.to_dict()

        # .get() on metrics should match dict access
        assert metrics.get('sharpe_ratio') == dict_repr['sharpe_ratio']
        assert metrics.get('win_rate') == dict_repr['win_rate']
        assert metrics.get('nonexistent', 0) == dict_repr.get('nonexistent', 0)

    def test_mixed_access_patterns(self):
        """RED: Can mix attribute and dict-like access."""
        metrics = StrategyMetrics(sharpe_ratio=1.5, total_return=0.25)

        # Attribute access
        sharpe_attr = metrics.sharpe_ratio

        # Dict-like access
        sharpe_get = metrics.get('sharpe_ratio')
        sharpe_bracket = metrics['sharpe_ratio']

        # All should be equivalent
        assert sharpe_attr == sharpe_get == sharpe_bracket == 1.5

    def test_orchestrator_iteration_pattern(self):
        """RED: orchestrator.py line 377 membership pattern."""
        # Simulate iteration dict-like structure check
        metrics = StrategyMetrics(sharpe_ratio=1.5)

        # Pattern: if 'sharpe_ratio' in iteration
        if 'sharpe_ratio' in metrics:
            value = metrics.get('sharpe_ratio')
            assert value == 1.5


# ============================================================================
# CATEGORY F: Edge Cases & Robustness Tests (3 tests)
# ============================================================================

class TestEdgeCases:
    """TDD tests for edge cases and robustness."""

    def test_empty_metrics_all_get_calls(self):
        """RED: Empty StrategyMetrics with all possible .get() calls."""
        metrics = StrategyMetrics()

        # All should return defaults without errors
        assert metrics.get('sharpe_ratio', 0) == 0
        assert metrics.get('total_return', 0) == 0
        assert metrics.get('max_drawdown', 0) == 0
        assert metrics.get('win_rate', 0) == 0
        assert metrics.get('execution_success', False) is False

    def test_nan_values_converted_then_get(self):
        """RED: NaN values converted by __post_init__, then .get() works."""
        # StrategyMetrics converts NaN to None in __post_init__
        metrics = StrategyMetrics(
            sharpe_ratio=np.nan,
            total_return=np.nan
        )

        # After __post_init__, values are None
        assert metrics.sharpe_ratio is None
        assert metrics.total_return is None

        # .get() should return defaults (None treated as "no value")
        assert metrics.get('sharpe_ratio', 0) == 0
        assert metrics.get('total_return', 0) == 0

    def test_performance_repeated_get_calls(self):
        """RED: Repeated .get() calls should be performant."""
        metrics = StrategyMetrics(sharpe_ratio=1.5)

        # Should handle many repeated calls efficiently
        for _ in range(1000):
            value = metrics.get('sharpe_ratio', 0)
            assert value == 1.5


# =============================================================================
# Category G: Missing Dict Methods - values(), items(), __len__() (P0.1)
# =============================================================================

class TestValuesMethod:
    """RED: Test suite for .values() method - dict-like interface."""

    def test_values_returns_all_metric_values(self):
        """RED: values() should return all 5 metric values."""
        metrics = StrategyMetrics(
            sharpe_ratio=2.5,
            total_return=0.45,
            max_drawdown=0.15,
            win_rate=0.65,
            execution_success=True
        )
        values = list(metrics.values())

        assert len(values) == 5
        assert 2.5 in values  # sharpe_ratio
        assert 0.45 in values  # total_return
        assert 0.15 in values  # max_drawdown
        assert 0.65 in values  # win_rate
        assert True in values  # execution_success

    def test_values_with_none_metrics(self):
        """RED: values() should handle None values correctly."""
        metrics = StrategyMetrics()  # All None except execution_success=False
        values = list(metrics.values())

        assert len(values) == 5
        assert values.count(None) == 4  # 4 None values
        assert False in values  # execution_success defaults to False

    def test_values_with_partial_metrics(self):
        """RED: values() should return mix of values and None."""
        metrics = StrategyMetrics(
            sharpe_ratio=1.8,
            total_return=0.32,
            execution_success=True
        )
        values = list(metrics.values())

        assert len(values) == 5
        assert 1.8 in values  # sharpe_ratio
        assert 0.32 in values  # total_return
        assert None in values  # max_drawdown is None
        assert None in values  # win_rate is None
        assert True in values  # execution_success

    def test_values_returns_iterator(self):
        """RED: values() should return an iterable/iterator."""
        metrics = StrategyMetrics(sharpe_ratio=2.5, total_return=0.45)
        values = metrics.values()

        # Should be iterable (can be converted to list)
        values_list = list(values)
        assert len(values_list) == 5

    def test_values_order_matches_keys(self):
        """RED: values() order should match keys() order."""
        metrics = StrategyMetrics(sharpe_ratio=2.5, total_return=0.45, max_drawdown=0.15)
        keys = list(metrics.keys())
        values = list(metrics.values())

        # Verify each key-value pair matches
        for key, value in zip(keys, values):
            assert metrics[key] == value


class TestItemsMethod:
    """RED: Test suite for .items() method - dict-like interface."""

    def test_items_returns_key_value_tuples(self):
        """RED: items() should return (key, value) tuples."""
        metrics = StrategyMetrics(sharpe_ratio=2.5, total_return=0.45)
        items = list(metrics.items())

        assert len(items) == 5

        # Verify each item is a tuple
        for item in items:
            assert isinstance(item, tuple)
            assert len(item) == 2
            key, value = item
            assert isinstance(key, str)

    def test_items_contains_all_metrics(self):
        """RED: items() should contain all 5 metric pairs."""
        metrics = StrategyMetrics(
            sharpe_ratio=2.5,
            total_return=0.45,
            max_drawdown=0.15,
            win_rate=0.65,
            execution_success=True
        )
        items = dict(metrics.items())

        assert items['sharpe_ratio'] == 2.5
        assert items['total_return'] == 0.45
        assert items['max_drawdown'] == 0.15
        assert items['win_rate'] == 0.65
        assert items['execution_success'] is True

    def test_items_with_none_values(self):
        """RED: items() should handle None values correctly."""
        metrics = StrategyMetrics()  # All None except execution_success=False
        items = dict(metrics.items())

        assert len(items) == 5
        assert items['sharpe_ratio'] is None
        assert items['total_return'] is None
        assert items['max_drawdown'] is None
        assert items['win_rate'] is None
        assert items['execution_success'] is False

    def test_items_can_reconstruct_dict(self):
        """RED: items() should allow dict reconstruction."""
        metrics = StrategyMetrics(sharpe_ratio=2.5, total_return=0.45, max_drawdown=0.15)
        items = metrics.items()
        reconstructed = dict(items)

        # Verify reconstructed dict matches original
        assert reconstructed['sharpe_ratio'] == metrics.sharpe_ratio
        assert reconstructed['total_return'] == metrics.total_return
        assert reconstructed['max_drawdown'] == metrics.max_drawdown
        assert reconstructed['win_rate'] == metrics.win_rate
        assert reconstructed['execution_success'] == metrics.execution_success

    def test_items_iteration_pattern(self):
        """RED: items() should support dict-like iteration."""
        metrics = StrategyMetrics(sharpe_ratio=1.8, total_return=0.32, execution_success=True)

        # Common pattern: for key, value in obj.items()
        result = {}
        for key, value in metrics.items():
            result[key] = value

        assert len(result) == 5
        assert result['sharpe_ratio'] == 1.8
        assert result['total_return'] == 0.32


class TestLenMethod:
    """RED: Test suite for __len__() method - dict-like interface."""

    def test_len_returns_field_count(self):
        """RED: len() should return 5 for all metrics."""
        metrics = StrategyMetrics(sharpe_ratio=2.5, total_return=0.45)
        assert len(metrics) == 5

    def test_len_with_empty_metrics(self):
        """RED: len() should return 5 even when values are None."""
        metrics = StrategyMetrics()  # All None except execution_success
        assert len(metrics) == 5

    def test_len_with_partial_metrics(self):
        """RED: len() should return 5 regardless of None values."""
        metrics = StrategyMetrics(sharpe_ratio=1.8, total_return=0.32)
        assert len(metrics) == 5

    def test_len_consistency_with_keys(self):
        """RED: len() should match len(keys())."""
        metrics = StrategyMetrics(sharpe_ratio=2.5)
        assert len(metrics) == len(metrics.keys())

    def test_len_enables_bool_check(self):
        """RED: len() enables truthiness checks via __bool__."""
        full_metrics = StrategyMetrics(sharpe_ratio=2.5, total_return=0.45)
        empty_metrics = StrategyMetrics()

        # Both should be truthy since they have fields
        # (Python uses __len__ for __bool__ if __bool__ not defined)
        assert len(full_metrics) > 0
        assert len(empty_metrics) > 0
