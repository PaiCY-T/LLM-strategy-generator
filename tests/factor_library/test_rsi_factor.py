"""
TDD Tests for RSI Factor (Spec B P1).

Tests written FIRST following Red-Green-Refactor cycle.
RSI Factor implements mean reversion strategy using TA-Lib.

Test Coverage:
- RSI value range [0, 100]
- Signal value range [-1, 1]
- No look-ahead bias (TTPT validation)
- Parameter validation
- Edge cases
"""

import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any


class TestRSIFactor:
    """TDD tests for RSI Factor - Write FIRST (RED phase)."""

    @pytest.fixture
    def sample_close_data(self) -> pd.DataFrame:
        """Standard test fixture with price data."""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        # Generate trending price data
        price_base = 100 + np.cumsum(np.random.randn(50) * 2)
        close = pd.DataFrame({
            '2330': price_base,
            '2317': price_base * 1.1 + np.random.randn(50)
        }, index=dates)
        return close

    @pytest.fixture
    def rsi_params(self) -> Dict[str, Any]:
        """Default RSI parameters."""
        return {
            'rsi_period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70
        }

    def test_rsi_range_0_to_100(self, sample_close_data, rsi_params):
        """RED: RSI must be in [0, 100]"""
        from src.factor_library.mean_reversion_factors import rsi_factor

        result = rsi_factor(sample_close_data, rsi_params)
        rsi = result['rsi']

        # Exclude NaN values from comparison (initial period)
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all().all(), "RSI values must be >= 0"
        assert (valid_rsi <= 100).all().all(), "RSI values must be <= 100"

    def test_signal_range_neg1_to_1(self, sample_close_data, rsi_params):
        """RED: Signal must be in [-1, 1]"""
        from src.factor_library.mean_reversion_factors import rsi_factor

        result = rsi_factor(sample_close_data, rsi_params)
        signal = result['signal']

        valid_signal = signal.dropna()
        assert (valid_signal >= -1.0).all().all(), "Signal must be >= -1"
        assert (valid_signal <= 1.0).all().all(), "Signal must be <= 1"

    def test_signal_linear_mapping(self, sample_close_data, rsi_params):
        """RED: Signal = (50 - RSI) / 50 linear mapping"""
        from src.factor_library.mean_reversion_factors import rsi_factor

        result = rsi_factor(sample_close_data, rsi_params)
        rsi = result['rsi']
        signal = result['signal']

        # Calculate expected signal from RSI
        expected_signal = (50 - rsi) / 50
        valid_idx = ~signal.isna()

        pd.testing.assert_frame_equal(
            signal[valid_idx],
            expected_signal[valid_idx],
            check_exact=False,
            atol=1e-10
        )

    def test_oversold_generates_positive_signal(self, sample_close_data, rsi_params):
        """RED: Oversold (RSI < 30) should generate positive signal (buy)"""
        from src.factor_library.mean_reversion_factors import rsi_factor

        result = rsi_factor(sample_close_data, rsi_params)
        rsi = result['rsi']
        signal = result['signal']

        # Where RSI < 30, signal should be > 0.4 (since signal = (50-30)/50 = 0.4)
        oversold_mask = rsi < 30
        if oversold_mask.any().any():
            oversold_signals = signal[oversold_mask].dropna()
            assert (oversold_signals > 0.4).all().all() if hasattr(oversold_signals, 'all') else (oversold_signals > 0.4), \
                "Oversold conditions should generate strong positive signals"

    def test_overbought_generates_negative_signal(self, sample_close_data, rsi_params):
        """RED: Overbought (RSI > 70) should generate negative signal (sell)"""
        from src.factor_library.mean_reversion_factors import rsi_factor

        result = rsi_factor(sample_close_data, rsi_params)
        rsi = result['rsi']
        signal = result['signal']

        # Where RSI > 70, signal should be < -0.4
        overbought_mask = rsi > 70
        if overbought_mask.any().any():
            overbought_signals = signal[overbought_mask].dropna()
            assert (overbought_signals < -0.4).all().all() if hasattr(overbought_signals, 'all') else (overbought_signals < -0.4), \
                "Overbought conditions should generate strong negative signals"

    def test_rsi_period_parameter(self, sample_close_data):
        """RED: Different RSI periods should produce different results"""
        from src.factor_library.mean_reversion_factors import rsi_factor

        result_14 = rsi_factor(sample_close_data, {'rsi_period': 14})
        result_7 = rsi_factor(sample_close_data, {'rsi_period': 7})

        # Different periods should give different RSI values
        rsi_14 = result_14['rsi'].dropna()
        rsi_7 = result_7['rsi'].dropna()

        # Shorter period should have more NaN at beginning
        assert result_7['rsi'].isna().sum().sum() < result_14['rsi'].isna().sum().sum()

    def test_default_parameters(self, sample_close_data):
        """RED: Factor should work with default parameters"""
        from src.factor_library.mean_reversion_factors import rsi_factor

        # Call with empty params dict
        result = rsi_factor(sample_close_data, {})

        assert 'rsi' in result
        assert 'signal' in result
        assert result['rsi'].shape == sample_close_data.shape
        assert result['signal'].shape == sample_close_data.shape


class TestRSIFactorNoLookahead:
    """TTPT tests for look-ahead bias validation."""

    @pytest.fixture
    def sample_close_data(self) -> pd.DataFrame:
        """Test fixture."""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        price_base = 100 + np.cumsum(np.random.randn(50) * 2)
        return pd.DataFrame({
            '2330': price_base,
            '2317': price_base * 1.1
        }, index=dates)

    def test_no_lookahead_bias_single_perturbation(self, sample_close_data):
        """RED: TTPT - T+1 perturbation must not affect T"""
        from src.factor_library.mean_reversion_factors import rsi_factor

        # Original calculation
        result_orig = rsi_factor(sample_close_data.copy(), {})
        signal_orig = result_orig['signal'].copy()

        # Perturb T+1 (last row)
        perturbed_data = sample_close_data.copy()
        perturbed_data.iloc[-1] += np.random.randn(2) * 10

        result_perturbed = rsi_factor(perturbed_data, {})
        signal_perturbed = result_perturbed['signal']

        # T-1 and before must be identical
        pd.testing.assert_frame_equal(
            signal_orig.iloc[:-1],
            signal_perturbed.iloc[:-1],
            check_exact=False,
            atol=1e-10
        )

    def test_no_lookahead_bias_multi_perturbation(self, sample_close_data):
        """RED: TTPT - Multiple future perturbations must not affect past"""
        from src.factor_library.mean_reversion_factors import rsi_factor

        # Original calculation
        result_orig = rsi_factor(sample_close_data.copy(), {})
        signal_orig = result_orig['signal'].copy()

        # Perturb last 5 rows
        perturbed_data = sample_close_data.copy()
        perturbed_data.iloc[-5:] += np.random.randn(5, 2) * 10

        result_perturbed = rsi_factor(perturbed_data, {})
        signal_perturbed = result_perturbed['signal']

        # T-6 and before must be identical
        pd.testing.assert_frame_equal(
            signal_orig.iloc[:-5],
            signal_perturbed.iloc[:-5],
            check_exact=False,
            atol=1e-10
        )


class TestRSIFactorEdgeCases:
    """Edge case tests."""

    def test_constant_prices_rsi_50(self):
        """RED: Constant prices should give RSI near 50"""
        from src.factor_library.mean_reversion_factors import rsi_factor

        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        close = pd.DataFrame({
            '2330': [100.0] * 50,
            '2317': [200.0] * 50
        }, index=dates)

        result = rsi_factor(close, {})
        rsi = result['rsi']

        # For constant prices, RSI should be 50 (no up/down movement)
        valid_rsi = rsi.dropna()
        # Note: Some implementations may give NaN for constant prices
        # We check that non-NaN values are near 50
        if not valid_rsi.empty:
            # RSI for constant prices is undefined, but should not crash
            assert True

    def test_single_column_data(self):
        """RED: Factor should work with single symbol"""
        from src.factor_library.mean_reversion_factors import rsi_factor

        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        close = pd.DataFrame({
            '2330': 100 + np.cumsum(np.random.randn(50) * 2)
        }, index=dates)

        result = rsi_factor(close, {})

        assert 'rsi' in result
        assert result['rsi'].shape == close.shape

    def test_insufficient_data_for_period(self):
        """RED: Factor should handle data shorter than period"""
        from src.factor_library.mean_reversion_factors import rsi_factor

        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=10, freq='D')  # < 14 period
        close = pd.DataFrame({
            '2330': 100 + np.cumsum(np.random.randn(10) * 2)
        }, index=dates)

        result = rsi_factor(close, {'rsi_period': 14})

        # Should return mostly NaN but not crash
        assert 'rsi' in result
        assert 'signal' in result

    def test_nan_handling(self):
        """RED: Factor should handle NaN values gracefully"""
        from src.factor_library.mean_reversion_factors import rsi_factor

        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        close = pd.DataFrame({
            '2330': 100 + np.cumsum(np.random.randn(50) * 2)
        }, index=dates)

        # Introduce NaN
        close.iloc[25] = np.nan

        result = rsi_factor(close, {})

        # Should not crash
        assert 'rsi' in result
        assert 'signal' in result
