"""
Unit tests for backtest metrics calculations.

Tests Sharpe ratio calculation with different data frequencies
to ensure correct annualization factors are used.
Also tests StrategyMetrics dataclass and MetricsExtractor class.
"""

import pytest
import pandas as pd
import numpy as np
from src.backtest.metrics import (
    _calculate_sharpe_ratio_fallback,
    MetricsExtractor,
    StrategyMetrics,
)


class TestSharpeRatioFallback:
    """Test Sharpe ratio fallback calculation with different frequencies."""

    def test_monthly_data_sharpe(self):
        """Test Sharpe calculation with monthly data (should use sqrt(12))."""
        # Create monthly equity curve
        dates = pd.date_range('2020-01-31', periods=24, freq='ME')  # 2 years monthly

        # Monthly returns: 1% mean, 5% std
        monthly_returns = np.random.RandomState(42).normal(0.01, 0.05, 24)
        equity_values = (1 + monthly_returns).cumprod()
        equity_curve = pd.Series(equity_values, index=dates, name='equity')

        # Calculate Sharpe
        sharpe = _calculate_sharpe_ratio_fallback(equity_curve)

        # Expected Sharpe using pct_change (same as function)
        returns = equity_curve.pct_change().dropna()
        expected_sharpe = (returns.mean() / returns.std()) * np.sqrt(12)

        # Should match expected calculation
        assert np.isclose(sharpe, expected_sharpe, rtol=0.001), \
            f"Sharpe {sharpe:.3f} != expected {expected_sharpe:.3f}"

        # Sharpe should be reasonable for monthly data (<5.0)
        assert sharpe < 5.0, f"Monthly Sharpe {sharpe:.3f} unreasonably high"

    def test_weekly_data_sharpe(self):
        """Test Sharpe calculation with weekly data (should use sqrt(52))."""
        # Create weekly equity curve
        dates = pd.date_range('2020-01-03', periods=104, freq='W-FRI')  # 2 years weekly

        # Weekly returns: 0.5% mean, 3% std
        weekly_returns = np.random.RandomState(42).normal(0.005, 0.03, 104)
        equity_values = (1 + weekly_returns).cumprod()
        equity_curve = pd.Series(equity_values, index=dates, name='equity')

        # Calculate Sharpe
        sharpe = _calculate_sharpe_ratio_fallback(equity_curve)

        # Expected Sharpe using pct_change
        returns = equity_curve.pct_change().dropna()
        expected_sharpe = (returns.mean() / returns.std()) * np.sqrt(52)

        # Should match expected calculation
        assert np.isclose(sharpe, expected_sharpe, rtol=0.001), \
            f"Sharpe {sharpe:.3f} != expected {expected_sharpe:.3f}"

        # Sharpe should be reasonable for weekly data (<5.0)
        assert sharpe < 5.0, f"Weekly Sharpe {sharpe:.3f} unreasonably high"

    def test_daily_data_sharpe(self):
        """Test Sharpe calculation with daily data (should use sqrt(252))."""
        # Create daily equity curve
        dates = pd.date_range('2020-01-01', periods=252, freq='B')  # 1 year business days

        # Daily returns: 0.05% mean, 1.5% std
        daily_returns = np.random.RandomState(42).normal(0.0005, 0.015, 252)
        equity_values = (1 + daily_returns).cumprod()
        equity_curve = pd.Series(equity_values, index=dates, name='equity')

        # Calculate Sharpe
        sharpe = _calculate_sharpe_ratio_fallback(equity_curve)

        # Expected Sharpe using pct_change
        returns = equity_curve.pct_change().dropna()
        expected_sharpe = (returns.mean() / returns.std()) * np.sqrt(252)

        # Should match expected calculation
        assert np.isclose(sharpe, expected_sharpe, rtol=0.001), \
            f"Sharpe {sharpe:.3f} != expected {expected_sharpe:.3f}"

    def test_monthly_vs_daily_sharpe_difference(self):
        """Test that monthly and daily data produce different Sharpe ratios."""
        # Same return stream, different frequencies
        returns = np.random.RandomState(42).normal(0.01, 0.05, 24)

        # Monthly interpretation
        dates_monthly = pd.date_range('2020-01-31', periods=24, freq='ME')
        equity_monthly = pd.Series((1 + returns).cumprod(), index=dates_monthly)
        sharpe_monthly = _calculate_sharpe_ratio_fallback(equity_monthly)

        # Daily interpretation (WRONG for monthly returns!)
        dates_daily = pd.date_range('2020-01-01', periods=24, freq='D')
        equity_daily = pd.Series((1 + returns).cumprod(), index=dates_daily)
        sharpe_daily = _calculate_sharpe_ratio_fallback(equity_daily)

        # Daily should be ~4.58x higher than monthly (sqrt(252)/sqrt(12))
        ratio = sharpe_daily / sharpe_monthly if sharpe_monthly != 0 else 0
        expected_ratio = np.sqrt(252) / np.sqrt(12)

        assert np.isclose(ratio, expected_ratio, rtol=0.05), \
            f"Ratio {ratio:.2f} != expected {expected_ratio:.2f}"

    def test_empty_equity_curve(self):
        """Test that empty equity curve returns 0.0."""
        equity_curve = pd.Series([], dtype=float, name='equity')
        sharpe = _calculate_sharpe_ratio_fallback(equity_curve)
        assert sharpe == 0.0

    def test_single_value_equity_curve(self):
        """Test that single-value equity curve returns 0.0."""
        equity_curve = pd.Series([100], name='equity')
        sharpe = _calculate_sharpe_ratio_fallback(equity_curve)
        assert sharpe == 0.0


class TestStrategyMetrics:
    """Test StrategyMetrics dataclass."""

    def test_create_with_valid_metrics(self):
        """Test creating StrategyMetrics with valid values."""
        metrics = StrategyMetrics(
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=-0.15,
            win_rate=0.55,
            execution_success=True
        )
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return == 0.25
        assert metrics.max_drawdown == -0.15
        assert metrics.win_rate == 0.55
        assert metrics.execution_success is True

    def test_create_with_none_values(self):
        """Test creating StrategyMetrics with None values."""
        metrics = StrategyMetrics(execution_success=False)
        assert metrics.sharpe_ratio is None
        assert metrics.total_return is None
        assert metrics.max_drawdown is None
        assert metrics.win_rate is None
        assert metrics.execution_success is False

    def test_nan_conversion_in_post_init(self):
        """Test that NaN values are converted to None in __post_init__."""
        metrics = StrategyMetrics(
            sharpe_ratio=float('nan'),
            total_return=0.25,
            max_drawdown=float('nan'),
            win_rate=0.55,
            execution_success=True
        )
        assert metrics.sharpe_ratio is None
        assert metrics.total_return == 0.25
        assert metrics.max_drawdown is None
        assert metrics.win_rate == 0.55

    def test_all_nan_values(self):
        """Test StrategyMetrics with all NaN values."""
        metrics = StrategyMetrics(
            sharpe_ratio=float('nan'),
            total_return=float('nan'),
            max_drawdown=float('nan'),
            win_rate=float('nan'),
            execution_success=False
        )
        assert metrics.sharpe_ratio is None
        assert metrics.total_return is None
        assert metrics.max_drawdown is None
        assert metrics.win_rate is None


class MockReport:
    """Mock finlab report for testing MetricsExtractor."""

    def __init__(self, **kwargs):
        """Initialize mock report with given attributes."""
        self.__dict__.update(kwargs)


class TestMetricsExtractor:
    """Test MetricsExtractor class.

    Comprehensive tests for MetricsExtractor covering:
    - Various report formats and attribute names
    - NaN and infinite value handling
    - Edge cases (boundaries, zero values, type conversions)
    - Callable vs property attributes
    - Partial metric extraction
    - Error handling and validation
    """

    def test_extract_metrics_with_valid_report(self):
        """Test extracting metrics from a valid report."""
        report = MockReport(
            sharpe_ratio=1.5,
            total_return=25.0,  # Percentage form
            max_drawdown=-15.0,  # Percentage form
            win_rate=55.0  # Percentage form
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return == 0.25  # Should be converted to decimal
        assert metrics.max_drawdown == -0.15  # Should be converted to decimal
        assert metrics.win_rate == 0.55  # Should be converted to decimal

    def test_extract_metrics_with_decimal_format(self):
        """Test extracting metrics already in decimal format."""
        report = MockReport(
            sharpe_ratio=1.5,
            total_return=0.25,  # Decimal form
            max_drawdown=-0.15,  # Decimal form
            win_rate=0.55  # Decimal form
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return == 0.25
        assert metrics.max_drawdown == -0.15
        assert metrics.win_rate == 0.55

    def test_extract_metrics_with_none_report(self):
        """Test extracting metrics from None report."""
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(None)

        assert metrics.execution_success is False
        assert metrics.sharpe_ratio is None
        assert metrics.total_return is None
        assert metrics.max_drawdown is None
        assert metrics.win_rate is None

    def test_extract_metrics_partial_attributes(self):
        """Test extracting metrics when only some attributes exist."""
        report = MockReport(
            sharpe_ratio=1.5,
            total_return=25.0
            # max_drawdown and win_rate missing
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return == 0.25
        assert metrics.max_drawdown is None
        assert metrics.win_rate is None

    def test_extract_metrics_with_callable_attributes(self):
        """Test extracting metrics from callable attributes."""
        report = MockReport()
        report.sharpe_ratio = lambda: 1.5
        report.total_return = lambda: 25.0
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return == 0.25

    def test_extract_metrics_with_nan_values(self):
        """Test extracting metrics with NaN values."""
        report = MockReport(
            sharpe_ratio=float('nan'),
            total_return=25.0,
            max_drawdown=float('nan'),
            win_rate=0.55
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio is None  # NaN converted to None
        assert metrics.total_return == 0.25
        assert metrics.max_drawdown is None  # NaN converted to None
        assert metrics.win_rate == 0.55

    def test_extract_metrics_with_alternative_names(self):
        """Test extracting metrics using alternative attribute names."""
        report = MockReport(
            sharpe=1.5,  # Alternative name
            cumulative_return=0.25,  # Alternative name
            drawdown=-0.15,  # Alternative name
            winning_rate=55.0  # Alternative name
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return == 0.25
        assert metrics.max_drawdown == -0.15
        assert metrics.win_rate == 0.55

    def test_extract_metrics_invalid_win_rate(self):
        """Test that invalid win_rate (>1 or <0) is rejected."""
        report = MockReport(
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=-0.15,
            win_rate=155.0  # 155% is invalid after conversion
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.win_rate is None  # Invalid value (1.55) rejected

    def test_extract_metrics_no_metrics_found(self):
        """Test when no metrics can be extracted."""
        report = MockReport(some_attr=42)  # No metric attributes
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is False
        assert metrics.sharpe_ratio is None
        assert metrics.total_return is None
        assert metrics.max_drawdown is None
        assert metrics.win_rate is None

    def test_extract_attribute_with_none_object(self):
        """Test _extract_attribute with None object."""
        extractor = MetricsExtractor()
        result = extractor._extract_attribute(None, ['any_attr'])
        assert result is None

    def test_extract_attribute_with_missing_attribute(self):
        """Test _extract_attribute when attribute doesn't exist."""
        obj = MockReport()
        extractor = MetricsExtractor()
        result = extractor._extract_attribute(obj, ['nonexistent_attr'])
        assert result is None

    def test_extract_attribute_with_non_numeric_value(self):
        """Test _extract_attribute with non-numeric value returns None."""
        obj = MockReport(attr="not a number")
        extractor = MetricsExtractor()
        result = extractor._extract_attribute(obj, ['attr'])
        assert result is None  # Non-numeric values are skipped

    def test_extract_attribute_with_infinite_value(self):
        """Test _extract_attribute rejects infinite values."""
        obj = MockReport(attr=float('inf'))
        extractor = MetricsExtractor()
        result = extractor._extract_attribute(obj, ['attr'])
        assert result is None

    def test_extract_metrics_negative_return_preserved(self):
        """Test that negative returns are preserved correctly."""
        report = MockReport(
            sharpe_ratio=0.5,
            total_return=-0.10,  # -10% return
            max_drawdown=-0.25,
            win_rate=0.40
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.total_return == -0.10
        assert metrics.max_drawdown == -0.25

    def test_extract_metrics_with_zero_values(self):
        """Test extracting metrics when all values are zero."""
        report = MockReport(
            sharpe_ratio=0.0,
            total_return=0.0,
            max_drawdown=0.0,
            win_rate=0.0
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 0.0
        assert metrics.total_return == 0.0
        assert metrics.max_drawdown == 0.0
        assert metrics.win_rate == 0.0

    def test_extract_metrics_mixed_callable_and_properties(self):
        """Test extracting metrics with mix of callable methods and properties."""
        report = MockReport()
        report.sharpe_ratio = lambda: 1.5  # Callable
        report.total_return = 25.0  # Property
        report.max_drawdown = lambda: -15.0  # Callable
        report.win_rate = 0.55  # Property

        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return == 0.25
        assert metrics.max_drawdown == -0.15
        assert metrics.win_rate == 0.55

    def test_extract_metrics_with_negative_infinity(self):
        """Test that negative infinity values are rejected."""
        report = MockReport(
            sharpe_ratio=float('-inf'),
            total_return=0.25,
            max_drawdown=-0.15,
            win_rate=0.55
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio is None  # -inf rejected
        assert metrics.total_return == 0.25

    def test_extract_metrics_with_positive_infinity(self):
        """Test that positive infinity values are rejected."""
        report = MockReport(
            sharpe_ratio=1.5,
            total_return=float('inf'),
            max_drawdown=-0.15,
            win_rate=0.55
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return is None  # inf rejected

    def test_extract_metrics_with_very_large_percentage(self):
        """Test extracting very large percentage values (>10000%)."""
        report = MockReport(
            sharpe_ratio=1.5,
            total_return=50000.0,  # 50000% return
            max_drawdown=-15.0,
            win_rate=0.55
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return == 500.0  # Converted: 50000 / 100
        assert metrics.max_drawdown == -0.15

    def test_extract_metrics_with_very_small_decimal(self):
        """Test extracting very small decimal values."""
        report = MockReport(
            sharpe_ratio=0.001,
            total_return=0.00001,  # 0.001% return
            max_drawdown=-0.00001,
            win_rate=0.001
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 0.001
        assert metrics.total_return == 0.00001
        assert metrics.max_drawdown == -0.00001
        assert metrics.win_rate == 0.001

    def test_extract_metrics_win_rate_boundary_zero(self):
        """Test win_rate at lower boundary (0.0)."""
        report = MockReport(
            sharpe_ratio=0.5,
            total_return=0.10,
            max_drawdown=-0.10,
            win_rate=0.0  # Exactly 0%
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.win_rate == 0.0

    def test_extract_metrics_win_rate_boundary_one(self):
        """Test win_rate at upper boundary (1.0)."""
        report = MockReport(
            sharpe_ratio=0.5,
            total_return=0.10,
            max_drawdown=-0.10,
            win_rate=1.0  # Exactly 100%
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.win_rate == 1.0

    def test_extract_metrics_win_rate_just_above_boundary(self):
        """Test that win_rate value that becomes valid after normalization."""
        report = MockReport(
            sharpe_ratio=0.5,
            total_return=0.10,
            max_drawdown=-0.10,
            win_rate=1.001  # >1, so divides by 100 = 0.01001 (valid)
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        # After normalization: 1.001 / 100 = 0.01001 (valid)
        assert np.isclose(metrics.win_rate, 0.01001, rtol=1e-5)

    def test_extract_metrics_win_rate_just_below_zero(self):
        """Test that win_rate slightly below 0.0 is rejected."""
        report = MockReport(
            sharpe_ratio=0.5,
            total_return=0.10,
            max_drawdown=-0.10,
            win_rate=-0.001  # Negative
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.win_rate is None  # Rejected as <0.0

    def test_extract_metrics_win_rate_truly_invalid_too_large(self):
        """Test that very large win_rate percentage is rejected."""
        report = MockReport(
            sharpe_ratio=0.5,
            total_return=0.10,
            max_drawdown=-0.10,
            win_rate=200.0  # 200% (>1.0 even after division)
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.win_rate is None  # 200/100 = 2.0, rejected as >1.0

    def test_extract_metrics_negative_percentage_win_rate(self):
        """Test negative percentage win_rate is rejected."""
        report = MockReport(
            sharpe_ratio=0.5,
            total_return=0.10,
            max_drawdown=-0.10,
            win_rate=-50.0  # -50%
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.win_rate is None  # Rejected after conversion to -0.5

    def test_extract_attribute_with_exception_in_callable(self):
        """Test that exceptions in callable attributes are handled gracefully."""
        report = MockReport()
        report.sharpe_ratio = lambda: 1.5
        report.total_return = lambda: 1/0  # Will raise ZeroDivisionError

        extractor = MetricsExtractor()
        # Should not raise, should return None for total_return
        result = extractor._extract_attribute(report, ['total_return'])
        assert result is None

    def test_extract_attribute_with_callable_returning_none(self):
        """Test that callable returning None is handled."""
        report = MockReport()
        report.sharpe_ratio = lambda: None

        extractor = MetricsExtractor()
        result = extractor._extract_attribute(report, ['sharpe_ratio'])
        assert result is None

    def test_extract_metrics_string_numeric_values(self):
        """Test that numeric strings are converted properly."""
        report = MockReport(
            sharpe_ratio="1.5",
            total_return="25.0",
            max_drawdown="-15.0",
            win_rate="55.0"
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return == 0.25
        assert metrics.max_drawdown == -0.15
        assert metrics.win_rate == 0.55

    def test_extract_metrics_all_nan_pandas(self):
        """Test that pd.NA and pandas NaN are both handled."""
        report = MockReport(
            sharpe_ratio=pd.NA,
            total_return=float('nan'),
            max_drawdown=np.nan,
            win_rate=pd.NaT  # pandas NaT
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is False  # No valid metrics extracted
        assert metrics.sharpe_ratio is None
        assert metrics.total_return is None
        assert metrics.max_drawdown is None
        assert metrics.win_rate is None

    def test_extract_metrics_alternative_sharpe_names(self):
        """Test all alternative sharpe attribute names."""
        for attr_name in ['sharpe_ratio', 'sharpe', '_sharpe', 'sharp_ratio']:
            report = MockReport()
            setattr(report, attr_name, 1.5)
            extractor = MetricsExtractor()
            metrics = extractor.extract_metrics(report)

            assert metrics.sharpe_ratio == 1.5, f"Failed for {attr_name}"
            assert metrics.execution_success is True

    def test_extract_metrics_alternative_return_names(self):
        """Test all alternative return attribute names."""
        for attr_name in ['total_return', 'return', 'cumulative_return', 'cum_return', 'returns']:
            report = MockReport()
            setattr(report, attr_name, 25.0)
            extractor = MetricsExtractor()
            metrics = extractor.extract_metrics(report)

            assert metrics.total_return == 0.25, f"Failed for {attr_name}"
            assert metrics.execution_success is True

    def test_extract_metrics_alternative_drawdown_names(self):
        """Test all alternative drawdown attribute names."""
        for attr_name in ['max_drawdown', 'drawdown', 'maximum_drawdown', 'maxdrawdown']:
            report = MockReport()
            setattr(report, attr_name, -15.0)
            extractor = MetricsExtractor()
            metrics = extractor.extract_metrics(report)

            assert metrics.max_drawdown == -0.15, f"Failed for {attr_name}"
            assert metrics.execution_success is True

    def test_extract_metrics_alternative_win_rate_names(self):
        """Test all alternative win_rate attribute names."""
        for attr_name in ['win_rate', 'winning_rate', 'win_pct', 'winrate', 'win_percentage']:
            report = MockReport()
            setattr(report, attr_name, 55.0)
            extractor = MetricsExtractor()
            metrics = extractor.extract_metrics(report)

            assert metrics.win_rate == 0.55, f"Failed for {attr_name}"
            assert metrics.execution_success is True

    def test_extract_metrics_with_none_values_in_callable(self):
        """Test report with some attributes as None."""
        report = MockReport(
            sharpe_ratio=1.5,
            total_return=None,  # Explicitly None
            max_drawdown=-0.15,
            win_rate=None  # Explicitly None
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return is None
        assert metrics.max_drawdown == -0.15
        assert metrics.win_rate is None

    def test_extract_metrics_with_only_sharpe(self):
        """Test extracting when only sharpe_ratio exists."""
        report = MockReport(sharpe_ratio=1.5)
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return is None
        assert metrics.max_drawdown is None
        assert metrics.win_rate is None

    def test_extract_metrics_with_only_return(self):
        """Test extracting when only return exists."""
        report = MockReport(total_return=25.0)
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio is None
        assert metrics.total_return == 0.25
        assert metrics.max_drawdown is None
        assert metrics.win_rate is None

    def test_extract_attribute_with_list_value(self):
        """Test that list values are rejected."""
        obj = MockReport(attr=[1, 2, 3])
        extractor = MetricsExtractor()
        result = extractor._extract_attribute(obj, ['attr'])
        assert result is None

    def test_extract_attribute_with_dict_value(self):
        """Test that dict values are rejected."""
        obj = MockReport(attr={'key': 'value'})
        extractor = MetricsExtractor()
        result = extractor._extract_attribute(obj, ['attr'])
        assert result is None

    def test_extract_attribute_with_series_value(self):
        """Test that pandas Series values are rejected."""
        obj = MockReport(attr=pd.Series([1, 2, 3]))
        extractor = MetricsExtractor()
        result = extractor._extract_attribute(obj, ['attr'])
        assert result is None

    def test_extract_metrics_max_drawdown_positive_percentage(self):
        """Test that positive max_drawdown is converted to negative decimal."""
        report = MockReport(
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=15.0,  # Positive 15% (should be normalized)
            win_rate=0.55
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        # 15.0 > 0, so it divides by 100 = 0.15
        assert metrics.max_drawdown == 0.15

    def test_extract_metrics_max_drawdown_negative_large_percentage(self):
        """Test negative large percentage max_drawdown."""
        report = MockReport(
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=-150.0,  # -150% (large drawdown)
            win_rate=0.55
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        # -150.0 < -1, so divides by 100 = -1.5
        assert metrics.max_drawdown == -1.5

    def test_extract_metrics_negative_return_percentage(self):
        """Test negative return percentage."""
        report = MockReport(
            sharpe_ratio=0.5,
            total_return=-50.0,  # -50% return (percentage form)
            max_drawdown=-0.25,
            win_rate=0.40
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        # |-50| > 1, so divides by 100 = -0.5
        assert metrics.total_return == -0.5

    def test_extract_metrics_sharpe_very_negative(self):
        """Test very negative sharpe ratio."""
        report = MockReport(
            sharpe_ratio=-10.5,
            total_return=0.25,
            max_drawdown=-0.15,
            win_rate=0.55
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == -10.5

    def test_extract_metrics_decimal_already_normalized_return(self):
        """Test return already in normalized form (between -1 and 1)."""
        report = MockReport(
            sharpe_ratio=1.5,
            total_return=0.5,  # 50% already in decimal
            max_drawdown=-0.15,
            win_rate=0.55
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        # abs(0.5) <= 1, so no division, stays 0.5
        assert metrics.total_return == 0.5

    def test_extract_metrics_decimal_already_normalized_drawdown(self):
        """Test drawdown already in normalized form."""
        report = MockReport(
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=-0.5,  # Already in decimal form
            win_rate=0.55
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        # -1 < -0.5 < 0, so no division, stays -0.5
        assert metrics.max_drawdown == -0.5

    def test_extract_metrics_with_empty_report_object(self):
        """Test with report object that has no metrics attributes."""
        report = MockReport()  # Empty report
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is False
        assert metrics.sharpe_ratio is None
        assert metrics.total_return is None
        assert metrics.max_drawdown is None
        assert metrics.win_rate is None

    def test_extract_attribute_multiple_names_first_match(self):
        """Test that first matching attribute is returned."""
        report = MockReport()
        report.sharpe = 2.0  # Second name
        report.sharpe_ratio = 1.5  # First name (preferred)

        extractor = MetricsExtractor()
        result = extractor._extract_attribute(report, ['sharpe_ratio', 'sharpe'])
        # Should return sharpe_ratio value (first match)
        assert result == 1.5

    def test_extract_attribute_multiple_names_second_match(self):
        """Test fallback to second name if first doesn't exist."""
        report = MockReport()
        report.sharpe = 2.0  # Second name only

        extractor = MetricsExtractor()
        result = extractor._extract_attribute(report, ['sharpe_ratio', 'sharpe'])
        # Should return sharpe value (second match)
        assert result == 2.0

    def test_extract_attribute_multiple_names_no_match(self):
        """Test None returned when no names match."""
        report = MockReport()

        extractor = MetricsExtractor()
        result = extractor._extract_attribute(report, ['sharpe_ratio', 'sharpe', '_sharpe'])
        # Should return None
        assert result is None

    def test_extract_metrics_with_numpy_types(self):
        """Test extracting metrics with numpy numeric types."""
        report = MockReport(
            sharpe_ratio=np.float64(1.5),
            total_return=np.float32(25.0),
            max_drawdown=np.float64(-15.0),
            win_rate=np.float32(55.0)
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return == 0.25
        assert metrics.max_drawdown == -0.15
        assert metrics.win_rate == 0.55

    def test_extract_metrics_with_int_values(self):
        """Test extracting metrics with integer values."""
        report = MockReport(
            sharpe_ratio=2,  # Integer
            total_return=25,  # Integer percentage
            max_drawdown=-15,  # Integer percentage
            win_rate=55  # Integer percentage
        )
        extractor = MetricsExtractor()
        metrics = extractor.extract_metrics(report)

        assert metrics.execution_success is True
        assert metrics.sharpe_ratio == 2.0
        assert metrics.total_return == 0.25
        assert metrics.max_drawdown == -0.15
        assert metrics.win_rate == 0.55


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
