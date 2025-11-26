"""
TDD RED Phase: Bollinger %B Factor Tests
Task 1.1 - Comprehensive failing tests for Bollinger %B factor

Test Coverage:
- Class 1: TestBollingerPercentBCalculation (5 tests)
- Class 2: TestBollingerPercentBSignalGeneration (5 tests)
- Class 3: TestBollingerPercentBParameters (3 tests)
- Class 4: TestBollingerPercentBDataFrameHandling (4 tests)
- Class 5: TestBollingerPercentBIntegration (3 tests)
Total: 20 tests
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any

# This import will FAIL - function doesn't exist yet (RED phase)
from src.factor_library.mean_reversion_factors import bollinger_percent_b


class TestBollingerPercentBCalculation:
    """Test mathematical correctness of Bollinger %B calculation."""

    def test_percent_b_at_middle_band_is_0_5(self):
        """When price equals SMA (middle band), %B should be 0.5."""
        # Create constant price series (no volatility)
        # With constant price, SMA = price, bands collapse
        close = pd.DataFrame({
            'stock': [100.0] * 30
        })
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        percent_b = result['metadata']['percent_b']

        # Last valid value should be ~0.5 (or NaN if no volatility)
        # For constant price, we expect special handling
        assert percent_b.iloc[-1, 0] == 0.5 or pd.isna(percent_b.iloc[-1, 0])

    def test_percent_b_at_upper_band_is_1_0(self):
        """When price equals upper band (+2σ), %B should be 1.0."""
        # Create price series that touches upper band
        # Price = SMA + 2*std_dev
        prices = list(range(90, 110)) + [110 + 2 * np.std(range(90, 110))] * 10
        close = pd.DataFrame({'stock': prices})
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        percent_b = result['metadata']['percent_b']
        upper_band = result['metadata']['upper_band']

        # Last value should be at upper band → %B = 1.0
        assert abs(percent_b.iloc[-1, 0] - 1.0) < 0.01

    def test_percent_b_at_lower_band_is_0_0(self):
        """When price equals lower band (-2σ), %B should be 0.0."""
        # Create price series that touches lower band
        # Price = SMA - 2*std_dev
        prices = list(range(90, 110)) + [90 - 2 * np.std(range(90, 110))] * 10
        close = pd.DataFrame({'stock': prices})
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        percent_b = result['metadata']['percent_b']
        lower_band = result['metadata']['lower_band']

        # Last value should be at lower band → %B = 0.0
        assert abs(percent_b.iloc[-1, 0] - 0.0) < 0.01

    def test_percent_b_above_upper_band(self):
        """When price exceeds upper band, %B should be > 1.0."""
        # Create price series with breakout above upper band
        prices = list(range(90, 110))
        std_dev = np.std(prices)
        breakout_price = 110 + 3 * std_dev  # 3σ above
        prices.extend([breakout_price] * 10)

        close = pd.DataFrame({'stock': prices})
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        percent_b = result['metadata']['percent_b']

        # %B should exceed 1.0 for breakout
        assert percent_b.iloc[-1, 0] > 1.0

    def test_percent_b_below_lower_band(self):
        """When price falls below lower band, %B should be < 0.0."""
        # Create price series with breakdown below lower band
        prices = list(range(90, 110))
        std_dev = np.std(prices)
        breakdown_price = 90 - 3 * std_dev  # 3σ below
        prices.extend([breakdown_price] * 10)

        close = pd.DataFrame({'stock': prices})
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        percent_b = result['metadata']['percent_b']

        # %B should be negative for breakdown
        assert percent_b.iloc[-1, 0] < 0.0


class TestBollingerPercentBSignalGeneration:
    """Test signal generation logic from %B values."""

    def test_oversold_generates_buy_signal(self):
        """When %B ≤ 0.2 (oversold), signal should be 1.0 (strong buy)."""
        # Create deeply oversold condition
        prices = list(range(100, 80, -1))  # Declining prices
        close = pd.DataFrame({'stock': prices})
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        signal = result['signal']
        percent_b = result['metadata']['percent_b']

        # Find last valid oversold point
        last_idx = signal.last_valid_index()
        if percent_b.loc[last_idx, 'stock'] <= 0.2:
            assert signal.loc[last_idx, 'stock'] == 1.0

    def test_moderate_oversold_signal(self):
        """When %B ∈ (0.2, 0.4], signal should be 0.5 (moderate buy)."""
        # Create moderate oversold condition
        # Target %B around 0.3
        close = pd.DataFrame({'stock': [100] * 15 + [98] * 15})
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        signal = result['signal']
        percent_b = result['metadata']['percent_b']

        # Check for moderate buy signal when %B in range
        last_idx = signal.last_valid_index()
        pb_val = percent_b.loc[last_idx, 'stock']
        if 0.2 < pb_val <= 0.4:
            assert signal.loc[last_idx, 'stock'] == 0.5

    def test_neutral_zone_signal(self):
        """When %B ∈ (0.4, 0.6], signal should be 0.0 (neutral)."""
        # Create neutral condition (price near middle band)
        close = pd.DataFrame({'stock': [100] * 30})
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        signal = result['signal']
        percent_b = result['metadata']['percent_b']

        # Neutral zone should give zero signal
        last_idx = signal.last_valid_index()
        pb_val = percent_b.loc[last_idx, 'stock']
        if 0.4 < pb_val <= 0.6 or pd.isna(pb_val):
            assert signal.loc[last_idx, 'stock'] == 0.0 or pd.isna(signal.loc[last_idx, 'stock'])

    def test_moderate_overbought_signal(self):
        """When %B ∈ (0.6, 0.8], signal should be -0.5 (moderate sell)."""
        # Create moderate overbought condition
        close = pd.DataFrame({'stock': [100] * 15 + [102] * 15})
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        signal = result['signal']
        percent_b = result['metadata']['percent_b']

        # Check for moderate sell signal when %B in range
        last_idx = signal.last_valid_index()
        pb_val = percent_b.loc[last_idx, 'stock']
        if 0.6 < pb_val <= 0.8:
            assert signal.loc[last_idx, 'stock'] == -0.5

    def test_overbought_generates_sell_signal(self):
        """When %B > 0.8 (overbought), signal should be -1.0 (strong sell)."""
        # Create strongly overbought condition
        prices = list(range(80, 100, 1))  # Rising prices
        close = pd.DataFrame({'stock': prices})
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        signal = result['signal']
        percent_b = result['metadata']['percent_b']

        # Find last valid overbought point
        last_idx = signal.last_valid_index()
        if percent_b.loc[last_idx, 'stock'] > 0.8:
            assert signal.loc[last_idx, 'stock'] == -1.0


class TestBollingerPercentBParameters:
    """Test parameter handling and defaults."""

    def test_default_period_20(self):
        """Default Bollinger Band period should be 20."""
        close = pd.DataFrame({'stock': list(range(100, 130))})
        params = {}  # Empty params, should use defaults

        result = bollinger_percent_b(close, params)

        # Check that calculation used period=20
        # Middle band should be 20-period SMA
        middle_band = result['metadata']['middle_band']
        assert len(middle_band) == len(close)

        # First 19 values should be NaN (insufficient data)
        assert middle_band.iloc[:19].isna().all().all()

    def test_default_std_dev_2(self):
        """Default standard deviation multiplier should be 2.0."""
        close = pd.DataFrame({'stock': list(range(100, 130))})
        params = {}  # Empty params, should use defaults

        result = bollinger_percent_b(close, params)

        # Check band width is 2*std_dev
        upper = result['metadata']['upper_band']
        lower = result['metadata']['lower_band']
        middle = result['metadata']['middle_band']

        # Band width should be ~4*std_dev total (2σ above + 2σ below)
        last_idx = middle.last_valid_index()
        band_width = upper.loc[last_idx, 'stock'] - lower.loc[last_idx, 'stock']

        # Calculate expected width
        prices = close['stock'].iloc[-20:]  # Last 20 prices
        expected_width = 4 * prices.std()

        assert abs(band_width - expected_width) < 0.01

    def test_custom_parameters(self):
        """Should accept custom period and std_dev_multiplier."""
        close = pd.DataFrame({'stock': list(range(100, 150))})
        params = {'bb_period': 10, 'bb_std_dev': 3.0}

        result = bollinger_percent_b(close, params)
        middle_band = result['metadata']['middle_band']

        # First 9 values should be NaN (period=10 needs 10 values)
        assert middle_band.iloc[:9].isna().all().all()
        assert not middle_band.iloc[9:].isna().all().all()


class TestBollingerPercentBDataFrameHandling:
    """Test DataFrame input/output handling."""

    def test_single_stock_dataframe(self):
        """Should work with single-column DataFrame."""
        close = pd.DataFrame({'AAPL': list(range(100, 130))})
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        signal = result['signal']

        assert signal.shape[1] == 1
        assert 'AAPL' in signal.columns

    def test_multi_stock_dataframe(self):
        """Should work with multi-column DataFrame."""
        close = pd.DataFrame({
            'AAPL': list(range(100, 130)),
            'GOOGL': list(range(200, 230)),
            'MSFT': list(range(150, 180))
        })
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        signal = result['signal']

        assert signal.shape[1] == 3
        assert set(signal.columns) == {'AAPL', 'GOOGL', 'MSFT'}

    def test_returns_same_shape(self):
        """Output signal should have same shape as input DataFrame."""
        close = pd.DataFrame({
            'A': list(range(100, 150)),
            'B': list(range(200, 250)),
            'C': list(range(300, 350))
        })
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        signal = result['signal']

        assert signal.shape == close.shape
        assert list(signal.columns) == list(close.columns)
        assert list(signal.index) == list(close.index)

    def test_handles_nan_values(self):
        """Should handle NaN values for insufficient data."""
        close = pd.DataFrame({'stock': list(range(100, 115))})  # Only 15 values
        params = {'bb_period': 20, 'bb_std_dev': 2.0}  # Needs 20

        result = bollinger_percent_b(close, params)
        signal = result['signal']
        percent_b = result['metadata']['percent_b']

        # First 19 values should be NaN
        assert signal.iloc[:14].isna().all().all()
        assert percent_b.iloc[:14].isna().all().all()


class TestBollingerPercentBIntegration:
    """Test integration requirements and contract."""

    def test_factor_function_signature(self):
        """Function should accept (close: DataFrame, params: Dict) → Dict."""
        close = pd.DataFrame({'stock': list(range(100, 130))})
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)

        # Should return a dictionary
        assert isinstance(result, dict)

    def test_return_structure(self):
        """Should return dict with 'signal' and 'metadata' keys."""
        close = pd.DataFrame({'stock': list(range(100, 130))})
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)

        # Check required keys
        assert 'signal' in result
        assert 'metadata' in result

        # Check metadata structure
        metadata = result['metadata']
        assert 'percent_b' in metadata
        assert 'upper_band' in metadata
        assert 'middle_band' in metadata
        assert 'lower_band' in metadata

        # Check all are DataFrames
        assert isinstance(result['signal'], pd.DataFrame)
        assert isinstance(metadata['percent_b'], pd.DataFrame)
        assert isinstance(metadata['upper_band'], pd.DataFrame)
        assert isinstance(metadata['middle_band'], pd.DataFrame)
        assert isinstance(metadata['lower_band'], pd.DataFrame)

    def test_signal_range_bounded(self):
        """All signals should be in [-1, 1] range."""
        # Create diverse price movements
        prices = (
            list(range(100, 120)) +  # Uptrend
            list(range(120, 100, -1)) +  # Downtrend
            [100] * 10  # Consolidation
        )
        close = pd.DataFrame({'stock': prices})
        params = {'bb_period': 20, 'bb_std_dev': 2.0}

        result = bollinger_percent_b(close, params)
        signal = result['signal']

        # All valid signals should be in [-1, 1]
        valid_signals = signal.dropna()
        assert (valid_signals >= -1.0).all().all()
        assert (valid_signals <= 1.0).all().all()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
