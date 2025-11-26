"""
TDD Tests for RVOL (Relative Volume) Factor (Spec B P1).

Tests written FIRST following Red-Green-Refactor cycle.
RVOL Factor measures relative volume compared to moving average.

Test Coverage:
- RVOL calculation correctness
- Signal value range
- High/low volume detection
- No look-ahead bias (TTPT validation)
- Edge cases
"""

import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any


class TestRVOLFactor:
    """TDD tests for RVOL Factor - Write FIRST (RED phase)."""

    @pytest.fixture
    def sample_volume_data(self) -> pd.DataFrame:
        """Standard test fixture with volume data."""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        # Generate volume data with some spikes
        base_volume = 1_000_000
        volume = pd.DataFrame({
            '2330': base_volume + np.random.randn(50) * 200_000,
            '2317': base_volume * 0.5 + np.random.randn(50) * 100_000
        }, index=dates)
        volume = volume.clip(lower=0)  # Volume can't be negative
        return volume

    @pytest.fixture
    def rvol_params(self) -> Dict[str, Any]:
        """Default RVOL parameters."""
        return {
            'rvol_period': 20,
            'high_rvol_threshold': 2.0,
            'low_rvol_threshold': 0.5
        }

    def test_rvol_positive_values(self, sample_volume_data, rvol_params):
        """RED: RVOL must be positive (ratio of volume to MA)"""
        from src.factor_library.mean_reversion_factors import rvol_factor

        result = rvol_factor(sample_volume_data, rvol_params)
        rvol = result['rvol']

        valid_rvol = rvol.dropna()
        assert (valid_rvol >= 0).all().all(), "RVOL must be non-negative"

    def test_rvol_average_near_1(self, sample_volume_data, rvol_params):
        """RED: Average RVOL should be approximately 1.0"""
        from src.factor_library.mean_reversion_factors import rvol_factor

        result = rvol_factor(sample_volume_data, rvol_params)
        rvol = result['rvol']

        # After initial warmup, RVOL should average near 1.0
        valid_rvol = rvol.iloc[rvol_params['rvol_period']:].dropna()
        mean_rvol = valid_rvol.mean().mean()

        # Allow 50% deviation due to random data
        assert 0.5 < mean_rvol < 1.5, \
            f"Average RVOL should be near 1.0, got {mean_rvol}"

    def test_signal_range_neg1_to_1(self, sample_volume_data, rvol_params):
        """RED: Signal must be in [-1, 1]"""
        from src.factor_library.mean_reversion_factors import rvol_factor

        result = rvol_factor(sample_volume_data, rvol_params)
        signal = result['signal']

        valid_signal = signal.dropna()
        assert (valid_signal >= -1.0).all().all(), "Signal must be >= -1"
        assert (valid_signal <= 1.0).all().all(), "Signal must be <= 1"

    def test_high_volume_generates_positive_signal(self, rvol_params):
        """RED: High volume (RVOL > 2.0) should generate positive signal"""
        from src.factor_library.mean_reversion_factors import rvol_factor

        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')

        # Create data with consistent volume, then a spike
        volume = pd.DataFrame({
            '2330': [1_000_000] * 49 + [3_000_000]  # 3x spike at end
        }, index=dates)

        result = rvol_factor(volume, rvol_params)
        signal = result['signal']

        # Last value should have positive signal (high volume)
        assert signal.iloc[-1, 0] > 0, \
            "High volume should generate positive signal"

    def test_low_volume_generates_negative_signal(self, rvol_params):
        """RED: Low volume (RVOL < 0.5) should generate negative signal"""
        from src.factor_library.mean_reversion_factors import rvol_factor

        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')

        # Create data with consistent volume, then a drop
        volume = pd.DataFrame({
            '2330': [1_000_000] * 49 + [200_000]  # 0.2x drop at end
        }, index=dates)

        result = rvol_factor(volume, rvol_params)
        signal = result['signal']

        # Last value should have negative signal (low volume)
        assert signal.iloc[-1, 0] < 0, \
            "Low volume should generate negative signal"

    def test_default_parameters(self, sample_volume_data):
        """RED: Factor should work with default parameters"""
        from src.factor_library.mean_reversion_factors import rvol_factor

        # Call with empty params dict
        result = rvol_factor(sample_volume_data, {})

        assert 'rvol' in result
        assert 'signal' in result
        assert result['rvol'].shape == sample_volume_data.shape
        assert result['signal'].shape == sample_volume_data.shape

    def test_rvol_period_parameter(self, sample_volume_data):
        """RED: Different RVOL periods should produce different results"""
        from src.factor_library.mean_reversion_factors import rvol_factor

        result_20 = rvol_factor(sample_volume_data, {'rvol_period': 20})
        result_5 = rvol_factor(sample_volume_data, {'rvol_period': 5})

        # Different periods should give different RVOL values
        # Shorter period is more responsive to recent changes
        assert not result_20['rvol'].equals(result_5['rvol'])


class TestRVOLFactorNoLookahead:
    """TTPT tests for look-ahead bias validation."""

    @pytest.fixture
    def sample_volume_data(self) -> pd.DataFrame:
        """Test fixture."""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        volume = pd.DataFrame({
            '2330': 1_000_000 + np.random.randn(50) * 200_000,
            '2317': 500_000 + np.random.randn(50) * 100_000
        }, index=dates)
        return volume.clip(lower=0)

    def test_no_lookahead_bias_single_perturbation(self, sample_volume_data):
        """RED: TTPT - T+1 perturbation must not affect T"""
        from src.factor_library.mean_reversion_factors import rvol_factor

        # Original calculation
        result_orig = rvol_factor(sample_volume_data.copy(), {})
        signal_orig = result_orig['signal'].copy()

        # Perturb T+1 (last row)
        perturbed_data = sample_volume_data.copy()
        perturbed_data.iloc[-1] *= 3  # Triple the volume

        result_perturbed = rvol_factor(perturbed_data, {})
        signal_perturbed = result_perturbed['signal']

        # T-1 and before must be identical
        pd.testing.assert_frame_equal(
            signal_orig.iloc[:-1],
            signal_perturbed.iloc[:-1],
            check_exact=False,
            atol=1e-10
        )

    def test_no_lookahead_bias_multi_perturbation(self, sample_volume_data):
        """RED: TTPT - Multiple future perturbations must not affect past"""
        from src.factor_library.mean_reversion_factors import rvol_factor

        # Original calculation
        result_orig = rvol_factor(sample_volume_data.copy(), {})
        signal_orig = result_orig['signal'].copy()

        # Perturb last 5 rows
        perturbed_data = sample_volume_data.copy()
        perturbed_data.iloc[-5:] *= 2

        result_perturbed = rvol_factor(perturbed_data, {})
        signal_perturbed = result_perturbed['signal']

        # T-6 and before must be identical
        pd.testing.assert_frame_equal(
            signal_orig.iloc[:-5],
            signal_perturbed.iloc[:-5],
            check_exact=False,
            atol=1e-10
        )


class TestRVOLFactorEdgeCases:
    """Edge case tests."""

    def test_constant_volume_rvol_1(self):
        """RED: Constant volume should give RVOL = 1"""
        from src.factor_library.mean_reversion_factors import rvol_factor

        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        volume = pd.DataFrame({
            '2330': [1_000_000] * 50,
            '2317': [500_000] * 50
        }, index=dates)

        result = rvol_factor(volume, {})
        rvol = result['rvol']

        # For constant volume, RVOL should be exactly 1.0
        valid_rvol = rvol.dropna()
        assert np.allclose(valid_rvol, 1.0), \
            "Constant volume should give RVOL = 1.0"

    def test_single_column_data(self):
        """RED: Factor should work with single symbol"""
        from src.factor_library.mean_reversion_factors import rvol_factor

        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        volume = pd.DataFrame({
            '2330': 1_000_000 + np.random.randn(50) * 200_000
        }, index=dates)
        volume = volume.clip(lower=0)

        result = rvol_factor(volume, {})

        assert 'rvol' in result
        assert result['rvol'].shape == volume.shape

    def test_zero_volume_handling(self):
        """RED: Factor should handle zero volume gracefully"""
        from src.factor_library.mean_reversion_factors import rvol_factor

        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        volume = pd.DataFrame({
            '2330': [1_000_000] * 25 + [0] * 25  # Zero volume in second half
        }, index=dates)

        result = rvol_factor(volume, {})

        # Should not crash
        assert 'rvol' in result
        assert 'signal' in result

    def test_nan_handling(self):
        """RED: Factor should handle NaN values gracefully"""
        from src.factor_library.mean_reversion_factors import rvol_factor

        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        volume = pd.DataFrame({
            '2330': 1_000_000 + np.random.randn(50) * 200_000
        }, index=dates)

        # Introduce NaN
        volume.iloc[25] = np.nan

        result = rvol_factor(volume, {})

        # Should not crash
        assert 'rvol' in result
        assert 'signal' in result
