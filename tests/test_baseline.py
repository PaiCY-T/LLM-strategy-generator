"""
Comprehensive tests for Baseline Comparison Validation

Tests all 3 baseline strategies and validation logic:
1. Buy-and-Hold 0050
2. Equal-Weight Top 50
3. Risk Parity

Requirements: AC-2.5.1 to AC-2.5.5
"""

import pytest
import numpy as np
import pandas as pd
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.validation.baseline import (
    BaselineComparator,
    BaselineMetrics,
    BaselineComparison,
    compare_strategy_with_baselines
)


class MockData:
    """Mock FinLab data object for testing."""

    def __init__(self, n_stocks=100, n_days=1000, seed=42):
        """
        Create mock data with realistic structure.

        Args:
            n_stocks: Number of stocks in universe
            n_days: Number of trading days
            seed: Random seed for reproducibility
        """
        np.random.seed(seed)

        self.dates = pd.date_range('2018-01-01', periods=n_days, freq='D')
        self.n_stocks = n_stocks

        # Generate stock returns (random walk)
        returns = np.random.randn(n_days, n_stocks) * 0.02  # 2% daily volatility
        prices = (1 + returns).cumprod(axis=0) * 100

        self.close = pd.DataFrame(
            prices,
            index=self.dates,
            columns=[f'stock_{i}' for i in range(n_stocks)]
        )

        # Add 0050.TW (slightly better performance)
        etf_returns = np.random.randn(n_days) * 0.015 + 0.0003  # Positive drift
        etf_prices = (1 + etf_returns).cumprod() * 100
        self.close['0050.TW'] = etf_prices

        # Generate volume
        self.volume = pd.DataFrame(
            np.random.randint(1000000, 10000000, (n_days, n_stocks)),
            index=self.dates,
            columns=[f'stock_{i}' for i in range(n_stocks)]
        )

        # Generate market cap (larger for top stocks)
        base_mcap = np.random.exponential(5e9, n_stocks)  # Exponential distribution
        base_mcap.sort()
        base_mcap = base_mcap[::-1]  # Reverse to have largest first

        self.market_cap = pd.DataFrame(
            np.tile(base_mcap, (n_days, 1)),
            index=self.dates,
            columns=[f'stock_{i}' for i in range(n_stocks)]
        )

    def get(self, key: str):
        """Mock finlab.data.get() method."""
        if 'price:收盤價' in key:
            return self.close
        elif 'price:成交股數' in key:
            return self.volume
        elif 'fundamental_features:market_cap' in key:
            return self.market_cap
        else:
            raise ValueError(f"Unknown data key: {key}")


@pytest.fixture
def mock_data():
    """Fixture providing mock data."""
    return MockData(n_stocks=100, n_days=1000, seed=42)


@pytest.fixture
def comparator():
    """Fixture providing BaselineComparator instance."""
    return BaselineComparator(enable_cache=False)  # Disable cache for tests


@pytest.fixture
def comparator_with_cache(tmp_path):
    """Fixture providing BaselineComparator with cache enabled."""
    comparator = BaselineComparator(enable_cache=True)
    # Override cache directory to use temp path
    comparator.CACHE_DIR = tmp_path / '.cache/baseline_metrics'
    comparator.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return comparator


# ==============================================================================
# Test Suite 1: Baseline Strategy Calculations (AC-2.5.1)
# ==============================================================================

def test_buyhold_0050_calculation(comparator, mock_data):
    """Test Buy-and-Hold 0050 baseline calculation."""
    metrics = comparator._calculate_buyhold_0050(
        data=mock_data,
        start_date=None,
        end_date=None
    )

    # Verify metrics structure
    assert 'sharpe_ratio' in metrics
    assert 'annual_return' in metrics
    assert 'max_drawdown' in metrics
    assert 'total_trades' in metrics
    assert 'win_rate' in metrics

    # Verify metrics are reasonable
    assert isinstance(metrics['sharpe_ratio'], float)
    assert isinstance(metrics['annual_return'], float)
    assert isinstance(metrics['max_drawdown'], float)
    assert metrics['total_trades'] == 1  # Buy-and-hold = 1 trade
    assert 0 <= metrics['win_rate'] <= 1.0

    # Verify max_drawdown is negative or zero
    assert metrics['max_drawdown'] <= 0

    print(f"✅ Buy-and-Hold 0050: Sharpe={metrics['sharpe_ratio']:.4f}, "
          f"Return={metrics['annual_return']:.2%}, MDD={metrics['max_drawdown']:.2%}")


def test_equal_weight_top50_calculation(comparator, mock_data):
    """Test Equal-Weight Top 50 baseline calculation."""
    metrics = comparator._calculate_equal_weight_top50(
        data=mock_data,
        start_date=None,
        end_date=None
    )

    # Verify metrics structure
    assert 'sharpe_ratio' in metrics
    assert 'annual_return' in metrics
    assert 'max_drawdown' in metrics
    assert 'total_trades' in metrics

    # Verify metrics are reasonable
    assert isinstance(metrics['sharpe_ratio'], float)
    assert metrics['total_trades'] > 0  # Should have rebalancing trades
    assert metrics['max_drawdown'] <= 0

    print(f"✅ Equal-Weight Top 50: Sharpe={metrics['sharpe_ratio']:.4f}, "
          f"Trades={metrics['total_trades']}")


def test_risk_parity_calculation(comparator, mock_data):
    """Test Risk Parity baseline calculation."""
    metrics = comparator._calculate_risk_parity(
        data=mock_data,
        start_date=None,
        end_date=None
    )

    # Verify metrics structure
    assert 'sharpe_ratio' in metrics
    assert 'annual_return' in metrics
    assert 'max_drawdown' in metrics
    assert 'total_trades' in metrics

    # Verify metrics are reasonable
    assert isinstance(metrics['sharpe_ratio'], float)
    assert metrics['total_trades'] > 0  # Should have rebalancing trades
    assert metrics['max_drawdown'] <= 0

    print(f"✅ Risk Parity: Sharpe={metrics['sharpe_ratio']:.4f}, "
          f"Trades={metrics['total_trades']}")


# ==============================================================================
# Test Suite 2: Metric Accuracy (AC-2.5.2)
# ==============================================================================

def test_sharpe_calculation_accuracy(comparator):
    """Test Sharpe ratio calculation accuracy."""
    # Test case 1: Known Sharpe ratio
    # Generate returns with known mean and std
    np.random.seed(42)
    mean_daily = 0.001  # 0.1% daily return
    std_daily = 0.02    # 2% daily volatility

    returns = pd.Series(np.random.normal(mean_daily, std_daily, 252))

    sharpe = comparator._calculate_sharpe(returns)

    # Expected Sharpe: (mean / std) * sqrt(252)
    expected_sharpe = (mean_daily / std_daily) * np.sqrt(252)

    # Allow 20% tolerance due to random sampling
    assert abs(sharpe - expected_sharpe) / abs(expected_sharpe) < 0.2

    print(f"✅ Sharpe calculation: actual={sharpe:.4f}, expected={expected_sharpe:.4f}")


def test_max_drawdown_calculation_accuracy(comparator):
    """Test maximum drawdown calculation accuracy."""
    # Test case: Known drawdown scenario
    # Price goes: 100 -> 120 -> 80 -> 100
    prices = pd.Series([100, 120, 80, 100], index=pd.date_range('2020-01-01', periods=4))
    returns = prices.pct_change().dropna()

    max_dd = comparator._calculate_max_drawdown(returns)

    # Expected max drawdown: (80 - 120) / 120 = -33.33%
    expected_dd = (80 - 120) / 120

    assert abs(max_dd - expected_dd) < 0.001  # Within 0.1%

    print(f"✅ Max drawdown: actual={max_dd:.4f}, expected={expected_dd:.4f}")


def test_annual_return_calculation(comparator, mock_data):
    """Test annual return calculation."""
    metrics = comparator._calculate_buyhold_0050(
        data=mock_data,
        start_date=None,
        end_date=None
    )

    annual_return = metrics['annual_return']

    # Verify reasonable range (-50% to +100% annual)
    assert -0.5 <= annual_return <= 1.0

    print(f"✅ Annual return: {annual_return:.2%}")


# ==============================================================================
# Test Suite 3: Sharpe Improvement Calculation (AC-2.5.3)
# ==============================================================================

def test_sharpe_improvement_calculation(comparator, mock_data):
    """Test Sharpe improvement calculation."""
    strategy_sharpe = 2.5

    comparison = comparator.compare_with_baselines(
        strategy_code="",
        strategy_sharpe=strategy_sharpe,
        data=mock_data,
        iteration_num=1
    )

    # Verify improvements calculated for all baselines
    assert len(comparison.sharpe_improvements) == 3
    assert 'Buy-and-Hold 0050' in comparison.sharpe_improvements
    assert 'Equal-Weight Top 50' in comparison.sharpe_improvements
    assert 'Risk Parity' in comparison.sharpe_improvements

    # Verify improvement = strategy_sharpe - baseline_sharpe
    for baseline_name, baseline_metrics in comparison.baselines.items():
        improvement = comparison.sharpe_improvements[baseline_name]
        expected_improvement = strategy_sharpe - baseline_metrics.sharpe_ratio

        assert abs(improvement - expected_improvement) < 1e-6

    print(f"✅ Sharpe improvements calculated correctly")
    for name, imp in comparison.sharpe_improvements.items():
        print(f"  {name}: {imp:+.4f}")


# ==============================================================================
# Test Suite 4: Validation Criteria (AC-2.5.4)
# ==============================================================================

def test_validation_pass_criteria(comparator, mock_data):
    """Test validation passes when criteria met."""
    # High Sharpe strategy should beat baselines
    strategy_sharpe = 3.0

    comparison = comparator.compare_with_baselines(
        strategy_code="",
        strategy_sharpe=strategy_sharpe,
        data=mock_data,
        iteration_num=1
    )

    # Should pass validation
    assert comparison.validation_passed
    assert "Beats baseline" in comparison.validation_reason

    print(f"✅ Validation PASS: {comparison.validation_reason}")


def test_validation_fail_low_improvement(comparator, mock_data):
    """Test validation fails when improvement too small."""
    # Low Sharpe strategy (beats baselines but not by enough)
    strategy_sharpe = 0.3

    comparison = comparator.compare_with_baselines(
        strategy_code="",
        strategy_sharpe=strategy_sharpe,
        data=mock_data,
        iteration_num=1
    )

    # Should fail validation
    assert not comparison.validation_passed
    assert "Best improvement" in comparison.validation_reason

    print(f"✅ Validation FAIL (expected): {comparison.validation_reason}")


def test_validation_fail_catastrophic_underperformance(comparator, mock_data):
    """Test validation fails on catastrophic underperformance."""
    # Very low Sharpe (catastrophic underperformance)
    strategy_sharpe = -2.0

    comparison = comparator.compare_with_baselines(
        strategy_code="",
        strategy_sharpe=strategy_sharpe,
        data=mock_data,
        iteration_num=1
    )

    # Should fail validation
    assert not comparison.validation_passed
    assert "catastrophic" in comparison.validation_reason.lower()

    print(f"✅ Validation FAIL (catastrophic): {comparison.validation_reason}")


def test_validation_threshold_boundaries(comparator):
    """Test validation criteria at threshold boundaries."""
    # Test MIN_SHARPE_IMPROVEMENT threshold
    assert comparator.MIN_SHARPE_IMPROVEMENT == 0.5

    # Test MAX_UNDERPERFORMANCE threshold
    assert comparator.MAX_UNDERPERFORMANCE == -1.0

    # Test exact boundary case: max improvement exactly at threshold (should fail)
    sharpe_improvements_at_threshold = {
        'Baseline1': 0.5,    # Exactly at threshold (should fail: <= not <)
        'Baseline2': 0.3,
        'Baseline3': 0.2
    }

    passed, reason = comparator._check_validation_criteria(sharpe_improvements_at_threshold)
    assert not passed  # Should fail because max = 0.5 (not > 0.5)
    assert "Best improvement" in reason

    # Test barely passing case: max improvement just above threshold
    sharpe_improvements_barely_pass = {
        'Baseline1': 0.51,   # Just above threshold (should pass)
        'Baseline2': 0.3,
        'Baseline3': 0.2
    }

    passed, reason = comparator._check_validation_criteria(sharpe_improvements_barely_pass)
    assert passed  # Should pass because max = 0.51 > 0.5

    # Test catastrophic case: even with one good improvement
    sharpe_improvements_catastrophic = {
        'Baseline1': 2.0,    # Great improvement
        'Baseline2': 0.5,
        'Baseline3': -1.1    # Catastrophic (worse than -1.0)
    }

    passed, reason = comparator._check_validation_criteria(sharpe_improvements_catastrophic)
    assert not passed  # Should fail due to catastrophic underperformance
    assert "catastrophic" in reason.lower()

    print(f"✅ Validation thresholds: MIN_IMPROVEMENT={comparator.MIN_SHARPE_IMPROVEMENT}, "
          f"MAX_UNDERPERFORMANCE={comparator.MAX_UNDERPERFORMANCE}")


# ==============================================================================
# Test Suite 5: Caching Performance (AC-2.5.5)
# ==============================================================================

def test_cache_save_and_load(comparator_with_cache, mock_data):
    """Test caching mechanism saves and loads correctly."""
    baseline_name = 'Buy-and-Hold 0050'

    # First call: calculate and cache
    start_time = time.time()
    metrics1 = comparator_with_cache._calculate_baseline(
        baseline_name=baseline_name,
        data=mock_data,
        start_date=None,
        end_date=None
    )
    first_call_time = time.time() - start_time

    # Second call: should load from cache (much faster)
    start_time = time.time()
    metrics2 = comparator_with_cache._calculate_baseline(
        baseline_name=baseline_name,
        data=mock_data,
        start_date=None,
        end_date=None
    )
    second_call_time = time.time() - start_time

    # Verify metrics are identical
    assert metrics1.sharpe_ratio == metrics2.sharpe_ratio
    assert metrics1.annual_return == metrics2.annual_return
    assert metrics1.max_drawdown == metrics2.max_drawdown

    # Verify second call is faster (should be <0.01s from cache)
    assert second_call_time < 0.1  # Very fast from cache
    assert second_call_time < first_call_time  # Faster than calculation

    print(f"✅ Cache working: first={first_call_time:.3f}s, second={second_call_time:.3f}s (cached)")


def test_cache_key_generation(comparator_with_cache):
    """Test cache key generation is unique and consistent."""
    # Same parameters should generate same key
    key1 = comparator_with_cache._get_cache_key('Buy-and-Hold 0050', '2020-01-01', '2024-12-31')
    key2 = comparator_with_cache._get_cache_key('Buy-and-Hold 0050', '2020-01-01', '2024-12-31')
    assert key1 == key2

    # Different parameters should generate different keys
    key3 = comparator_with_cache._get_cache_key('Risk Parity', '2020-01-01', '2024-12-31')
    assert key1 != key3

    key4 = comparator_with_cache._get_cache_key('Buy-and-Hold 0050', '2021-01-01', '2024-12-31')
    assert key1 != key4

    print(f"✅ Cache key generation: key1={key1[:16]}..., key3={key3[:16]}... (different)")


def test_performance_with_caching(comparator_with_cache, mock_data):
    """Test performance target < 5s with caching."""
    strategy_sharpe = 2.5

    # First run: calculate all baselines (should take longer)
    start_time = time.time()
    comparison1 = comparator_with_cache.compare_with_baselines(
        strategy_code="",
        strategy_sharpe=strategy_sharpe,
        data=mock_data,
        iteration_num=1
    )
    first_run_time = time.time() - start_time

    # Second run: load from cache (should be very fast)
    start_time = time.time()
    comparison2 = comparator_with_cache.compare_with_baselines(
        strategy_code="",
        strategy_sharpe=strategy_sharpe,
        data=mock_data,
        iteration_num=2
    )
    second_run_time = time.time() - start_time

    # Verify second run meets performance target
    assert second_run_time < 5.0  # AC-2.5.5: < 5 seconds with caching
    assert second_run_time < first_run_time  # Should be faster

    print(f"✅ Performance target met: first_run={first_run_time:.2f}s, "
          f"second_run={second_run_time:.2f}s (< 5s target)")


def test_cache_disabled(comparator, mock_data):
    """Test operation with caching disabled."""
    baseline_name = 'Buy-and-Hold 0050'

    # Two calls with cache disabled should both calculate
    start_time = time.time()
    metrics1 = comparator._calculate_baseline(
        baseline_name=baseline_name,
        data=mock_data,
        start_date=None,
        end_date=None
    )
    time1 = time.time() - start_time

    start_time = time.time()
    metrics2 = comparator._calculate_baseline(
        baseline_name=baseline_name,
        data=mock_data,
        start_date=None,
        end_date=None
    )
    time2 = time.time() - start_time

    # Both should take similar time (no caching benefit)
    assert abs(time1 - time2) < time1 * 0.5  # Within 50% of each other

    print(f"✅ Cache disabled: time1={time1:.3f}s, time2={time2:.3f}s (similar)")


# ==============================================================================
# Test Suite 6: Comparison Report Generation
# ==============================================================================

def test_comparison_report_structure(comparator, mock_data):
    """Test comparison report has all required fields."""
    strategy_sharpe = 2.5

    comparison = comparator.compare_with_baselines(
        strategy_code="",
        strategy_sharpe=strategy_sharpe,
        data=mock_data,
        iteration_num=1
    )

    # Verify BaselineComparison structure
    assert hasattr(comparison, 'strategy_sharpe')
    assert hasattr(comparison, 'baselines')
    assert hasattr(comparison, 'sharpe_improvements')
    assert hasattr(comparison, 'best_baseline_matchup')
    assert hasattr(comparison, 'worst_baseline_matchup')
    assert hasattr(comparison, 'validation_passed')
    assert hasattr(comparison, 'validation_reason')
    assert hasattr(comparison, 'total_computation_time')

    # Verify baselines dict has all 3 baselines
    assert len(comparison.baselines) == 3

    print(f"✅ Comparison report structure complete")


def test_comparison_to_dict(comparator, mock_data):
    """Test comparison can be serialized to dict."""
    strategy_sharpe = 2.5

    comparison = comparator.compare_with_baselines(
        strategy_code="",
        strategy_sharpe=strategy_sharpe,
        data=mock_data,
        iteration_num=1
    )

    # Convert to dict
    result_dict = comparison.to_dict()

    # Verify dict structure
    assert 'strategy_sharpe' in result_dict
    assert 'baselines' in result_dict
    assert 'sharpe_improvements' in result_dict
    assert 'validation_passed' in result_dict

    # Verify baselines are properly serialized
    for baseline_name, baseline_dict in result_dict['baselines'].items():
        assert 'sharpe_ratio' in baseline_dict
        assert 'annual_return' in baseline_dict
        assert 'max_drawdown' in baseline_dict

    # Verify can be JSON serialized
    json_str = json.dumps(result_dict)
    assert len(json_str) > 0

    print(f"✅ Comparison serialization successful: {len(json_str)} chars")


def test_best_worst_matchup_identification(comparator, mock_data):
    """Test best/worst baseline matchup identification."""
    strategy_sharpe = 2.0

    comparison = comparator.compare_with_baselines(
        strategy_code="",
        strategy_sharpe=strategy_sharpe,
        data=mock_data,
        iteration_num=1
    )

    # Verify best/worst matchups are identified
    assert comparison.best_baseline_matchup != "N/A"
    assert comparison.worst_baseline_matchup != "N/A"
    assert comparison.best_baseline_matchup != comparison.worst_baseline_matchup

    # Verify format includes improvement value
    assert "(" in comparison.best_baseline_matchup
    assert ")" in comparison.best_baseline_matchup

    print(f"✅ Best matchup: {comparison.best_baseline_matchup}")
    print(f"✅ Worst matchup: {comparison.worst_baseline_matchup}")


# ==============================================================================
# Test Suite 7: Convenience Function
# ==============================================================================

def test_convenience_function(mock_data):
    """Test convenience wrapper function."""
    results = compare_strategy_with_baselines(
        strategy_sharpe=2.5,
        data=mock_data,
        iteration_num=1,
        enable_cache=False
    )

    # Verify returns dict
    assert isinstance(results, dict)
    assert 'strategy_sharpe' in results
    assert 'validation_passed' in results
    assert 'baselines' in results

    print(f"✅ Convenience function: validation_passed={results['validation_passed']}")


# ==============================================================================
# Test Suite 8: Error Handling
# ==============================================================================

def test_error_handling_invalid_baseline(comparator, mock_data):
    """Test error handling for invalid baseline name."""
    with pytest.raises(ValueError, match="Unknown baseline"):
        comparator._calculate_baseline(
            baseline_name='Invalid Baseline',
            data=mock_data,
            start_date=None,
            end_date=None
        )

    print(f"✅ Invalid baseline error handling works")


def test_error_handling_missing_data(comparator):
    """Test error handling when data is missing."""
    # Mock data that raises error
    bad_data = Mock()
    bad_data.get = Mock(side_effect=Exception("Data not found"))

    # Should not crash, should return default metrics
    metrics = comparator._calculate_buyhold_0050(
        data=bad_data,
        start_date=None,
        end_date=None
    )

    # Should return default metrics
    assert metrics['sharpe_ratio'] == 0.0
    assert metrics['annual_return'] == 0.0

    print(f"✅ Missing data error handling works")


def test_error_handling_cache_corruption(comparator_with_cache, mock_data):
    """Test error handling when cache file is corrupted."""
    baseline_name = 'Buy-and-Hold 0050'

    # Create corrupted cache file
    cache_key = comparator_with_cache._get_cache_key(baseline_name, None, None)
    cache_file = comparator_with_cache.CACHE_DIR / f"{cache_key}.json"

    cache_file.write_text("corrupted json {{{")

    # Should not crash, should recalculate
    metrics = comparator_with_cache._calculate_baseline(
        baseline_name=baseline_name,
        data=mock_data,
        start_date=None,
        end_date=None
    )

    # Should return valid metrics
    assert isinstance(metrics.sharpe_ratio, float)

    print(f"✅ Cache corruption error handling works")


# ==============================================================================
# Test Suite 9: Integration Tests
# ==============================================================================

def test_end_to_end_validation_pass(comparator, mock_data):
    """Test end-to-end validation flow (passing case)."""
    strategy_sharpe = 3.0

    comparison = comparator.compare_with_baselines(
        strategy_code="",
        strategy_sharpe=strategy_sharpe,
        data=mock_data,
        iteration_num=1
    )

    # Verify complete flow
    assert len(comparison.baselines) == 3
    assert len(comparison.sharpe_improvements) == 3
    assert comparison.validation_passed
    assert comparison.total_computation_time > 0

    print(f"✅ End-to-end validation PASS: {comparison.validation_reason}")


def test_end_to_end_validation_fail(comparator, mock_data):
    """Test end-to-end validation flow (failing case)."""
    strategy_sharpe = 0.2

    comparison = comparator.compare_with_baselines(
        strategy_code="",
        strategy_sharpe=strategy_sharpe,
        data=mock_data,
        iteration_num=1
    )

    # Verify complete flow
    assert len(comparison.baselines) == 3
    assert len(comparison.sharpe_improvements) == 3
    assert not comparison.validation_passed
    assert comparison.total_computation_time > 0

    print(f"✅ End-to-end validation FAIL: {comparison.validation_reason}")


# ==============================================================================
# Test Suite 10: Performance Tests
# ==============================================================================

def test_baseline_calculation_performance(comparator, mock_data):
    """Test individual baseline calculation performance."""
    for baseline_name in ['Buy-and-Hold 0050', 'Equal-Weight Top 50', 'Risk Parity']:
        start_time = time.time()

        metrics = comparator._calculate_baseline(
            baseline_name=baseline_name,
            data=mock_data,
            start_date=None,
            end_date=None
        )

        elapsed = time.time() - start_time

        # Each baseline should complete in reasonable time (<10s)
        assert elapsed < 10.0

        print(f"✅ {baseline_name} performance: {elapsed:.2f}s")


def test_full_comparison_performance(comparator, mock_data):
    """Test full comparison performance without cache."""
    start_time = time.time()

    comparison = comparator.compare_with_baselines(
        strategy_code="",
        strategy_sharpe=2.5,
        data=mock_data,
        iteration_num=1
    )

    elapsed = time.time() - start_time

    # Full comparison should complete in reasonable time (<30s without cache)
    assert elapsed < 30.0

    print(f"✅ Full comparison performance: {elapsed:.2f}s (without cache)")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
