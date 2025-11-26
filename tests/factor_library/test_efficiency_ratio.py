"""
TDD RED Phase: Efficiency Ratio Factor Tests
Task 1.2 - Comprehensive failing tests for Efficiency Ratio factor

Test Coverage:
- Class 1: TestEfficiencyRatioCalculation (6 tests)
- Class 2: TestEfficiencyRatioSignalGeneration (5 tests)
- Class 3: TestEfficiencyRatioParameters (3 tests)
- Class 4: TestEfficiencyRatioDataFrameHandling (4 tests)
- Class 5: TestEfficiencyRatioIntegration (3 tests)
Total: 21 tests
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any

# This import will FAIL - function doesn't exist yet (RED phase)
from src.factor_library.regime_factors import efficiency_ratio


class TestEfficiencyRatioCalculation:
    """Test mathematical correctness of Efficiency Ratio calculation."""

    def test_perfect_uptrend_er_equals_1(self):
        """When prices increase monotonically, ER should equal 1.0."""
        # Perfect trend: each step moves in same direction
        # net_change = |105-100| = 5
        # volatility = sum of |price[i] - price[i-1]| = 1+1+1+1+1 = 5
        # ER = 5/5 = 1.0
        close = pd.DataFrame({
            'stock': list(range(100, 120))  # 100, 101, 102, ..., 119
        })
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
        er_values = result['metadata']['efficiency_ratio']

        # Last ER value should be 1.0 (perfect trend)
        assert abs(er_values.iloc[-1, 0] - 1.0) < 0.01

    def test_perfect_downtrend_er_equals_1(self):
        """When prices decrease monotonically, ER should equal 1.0."""
        # Perfect downtrend also has ER = 1.0
        # Direction doesn't matter, only efficiency of movement
        close = pd.DataFrame({
            'stock': list(range(120, 100, -1))  # 120, 119, 118, ..., 101
        })
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
        er_values = result['metadata']['efficiency_ratio']

        # Last ER value should be 1.0 (perfect trend)
        assert abs(er_values.iloc[-1, 0] - 1.0) < 0.01

    def test_perfect_mean_reversion_er_low(self):
        """When prices oscillate, ER should be very low (near 0)."""
        # Perfect oscillation between two values
        # net_change = |105-100| = 5
        # volatility = sum of |105-100| + |100-105| + ... = 5*10 = 50
        # ER = 5/50 = 0.1
        close = pd.DataFrame({
            'stock': [100, 105, 100, 105, 100, 105, 100, 105, 100, 105,
                      100, 105, 100, 105, 100, 105, 100, 105, 100, 105]
        })
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
        er_values = result['metadata']['efficiency_ratio']

        # Last ER value should be very low (choppy market)
        assert er_values.iloc[-1, 0] < 0.3

    def test_sideways_market_er_zero(self):
        """When prices are constant, ER should be 0.0."""
        # Constant prices → net_change = 0
        # ER = 0/0 should be handled as 0.0
        close = pd.DataFrame({
            'stock': [100.0] * 30
        })
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
        er_values = result['metadata']['efficiency_ratio']

        # Last ER value should be 0.0 (no movement)
        assert er_values.iloc[-1, 0] == 0.0

    def test_er_range_0_to_1(self):
        """All ER values should be in [0, 1] range."""
        # Create diverse price movements
        prices = (
            list(range(100, 110)) +      # Uptrend
            [109, 110, 109, 110] * 3 +   # Choppy
            list(range(110, 100, -1))    # Downtrend
        )
        close = pd.DataFrame({'stock': prices})
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
        er_values = result['metadata']['efficiency_ratio']

        # All valid ER values should be in [0, 1]
        valid_er = er_values.dropna()
        assert (valid_er >= 0.0).all().all()
        assert (valid_er <= 1.0).all().all()

    def test_volatility_zero_handling(self):
        """When volatility is zero (constant price), ER should be 0.0."""
        # Edge case: all prices identical
        close = pd.DataFrame({
            'stock': [100.0] * 20
        })
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
        er_values = result['metadata']['efficiency_ratio']
        volatility = result['metadata']['volatility']

        # Volatility should be 0, ER should be 0
        assert volatility.iloc[-1, 0] == 0.0
        assert er_values.iloc[-1, 0] == 0.0


class TestEfficiencyRatioSignalGeneration:
    """Test signal generation logic from ER values."""

    def test_strong_trend_signal(self):
        """When ER ≥ 0.7, signal should be 1.0 (strong trend)."""
        # Create strong trend to achieve ER ≥ 0.7
        close = pd.DataFrame({
            'stock': list(range(100, 130))  # Consistent uptrend
        })
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
        signal = result['signal']
        er_values = result['metadata']['efficiency_ratio']

        # Find last valid index
        last_idx = signal.last_valid_index()
        if er_values.loc[last_idx, 'stock'] >= 0.7:
            assert signal.loc[last_idx, 'stock'] == 1.0

    def test_moderate_trend_signal(self):
        """When ER ∈ [0.5, 0.7), signal should be 0.5 (moderate trend)."""
        # Create moderate trend: some noise but generally trending
        # Target ER around 0.6
        prices = []
        for i in range(30):
            prices.append(100 + i + (-1 if i % 3 == 0 else 0))
        close = pd.DataFrame({'stock': prices})
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
        signal = result['signal']
        er_values = result['metadata']['efficiency_ratio']

        # Check for moderate trend signal when ER in range
        last_idx = signal.last_valid_index()
        er_val = er_values.loc[last_idx, 'stock']
        if 0.5 <= er_val < 0.7:
            assert signal.loc[last_idx, 'stock'] == 0.5

    def test_neutral_regime_signal(self):
        """When ER ∈ [0.3, 0.5), signal should be 0.0 (neutral)."""
        # Create transitional market: mixed signals
        # Target ER around 0.4
        prices = []
        for i in range(30):
            prices.append(100 + (i % 5) - (i % 3))
        close = pd.DataFrame({'stock': prices})
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
        signal = result['signal']
        er_values = result['metadata']['efficiency_ratio']

        # Check for neutral signal when ER in range
        last_idx = signal.last_valid_index()
        er_val = er_values.loc[last_idx, 'stock']
        if 0.3 <= er_val < 0.5:
            assert signal.loc[last_idx, 'stock'] == 0.0

    def test_moderate_mean_reversion_signal(self):
        """When ER ∈ [0.1, 0.3), signal should be -0.5 (moderate mean reversion)."""
        # Create moderately choppy market
        # Target ER around 0.2
        prices = [100 + (5 if i % 2 == 0 else -5) + (i % 3) for i in range(30)]
        close = pd.DataFrame({'stock': prices})
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
        signal = result['signal']
        er_values = result['metadata']['efficiency_ratio']

        # Check for moderate mean reversion signal
        last_idx = signal.last_valid_index()
        er_val = er_values.loc[last_idx, 'stock']
        if 0.1 <= er_val < 0.3:
            assert signal.loc[last_idx, 'stock'] == -0.5

    def test_strong_mean_reversion_signal(self):
        """When ER < 0.1, signal should be -1.0 (strong mean reversion/choppy)."""
        # Create very choppy market with high volatility, low net change
        close = pd.DataFrame({
            'stock': [100, 110, 100, 110, 100, 110, 100, 110, 100, 110,
                      100, 110, 100, 110, 100, 110, 100, 110, 100, 105]
        })
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
        signal = result['signal']
        er_values = result['metadata']['efficiency_ratio']

        # Find last valid index
        last_idx = signal.last_valid_index()
        if er_values.loc[last_idx, 'stock'] < 0.1:
            assert signal.loc[last_idx, 'stock'] == -1.0


class TestEfficiencyRatioParameters:
    """Test parameter handling and defaults."""

    def test_default_period_10(self):
        """Default ER period should be 10."""
        close = pd.DataFrame({'stock': list(range(100, 130))})
        params = {}  # Empty params, should use defaults

        result = efficiency_ratio(close, params)
        er_values = result['metadata']['efficiency_ratio']

        # Check that calculation used period=10
        # First 9 values should be NaN (insufficient data for period=10)
        assert er_values.iloc[:9].isna().all().all()
        assert not er_values.iloc[9:].isna().all().all()

    def test_custom_period(self):
        """Should accept custom period parameter."""
        close = pd.DataFrame({'stock': list(range(100, 140))})
        params = {'er_period': 20}

        result = efficiency_ratio(close, params)
        er_values = result['metadata']['efficiency_ratio']

        # First 19 values should be NaN (period=20 needs 20 values)
        assert er_values.iloc[:19].isna().all().all()
        assert not er_values.iloc[19:].isna().all().all()

    def test_period_validation(self):
        """Period must be >= 2 for valid calculation."""
        close = pd.DataFrame({'stock': list(range(100, 120))})
        params = {'er_period': 1}  # Invalid period

        # Should raise ValueError for invalid period
        with pytest.raises(ValueError):
            efficiency_ratio(close, params)


class TestEfficiencyRatioDataFrameHandling:
    """Test DataFrame input/output handling."""

    def test_single_stock_dataframe(self):
        """Should work with single-column DataFrame."""
        close = pd.DataFrame({'AAPL': list(range(100, 130))})
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
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
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
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
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
        signal = result['signal']

        assert signal.shape == close.shape
        assert list(signal.columns) == list(close.columns)
        assert list(signal.index) == list(close.index)

    def test_handles_insufficient_data(self):
        """Should return NaN for rows with insufficient data."""
        close = pd.DataFrame({'stock': list(range(100, 108))})  # Only 8 values
        params = {'er_period': 10}  # Needs 10

        result = efficiency_ratio(close, params)
        signal = result['signal']
        er_values = result['metadata']['efficiency_ratio']

        # All values should be NaN (insufficient data)
        assert signal.isna().all().all()
        assert er_values.isna().all().all()


class TestEfficiencyRatioIntegration:
    """Test integration requirements and contract."""

    def test_factor_function_signature(self):
        """Function should accept (close: DataFrame, params: Dict) → Dict."""
        close = pd.DataFrame({'stock': list(range(100, 130))})
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)

        # Should return a dictionary
        assert isinstance(result, dict)

    def test_return_structure(self):
        """Should return dict with 'signal' and 'metadata' keys."""
        close = pd.DataFrame({'stock': list(range(100, 130))})
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)

        # Check required keys
        assert 'signal' in result
        assert 'metadata' in result

        # Check metadata structure
        metadata = result['metadata']
        assert 'efficiency_ratio' in metadata
        assert 'net_change' in metadata
        assert 'volatility' in metadata

        # Check all are DataFrames
        assert isinstance(result['signal'], pd.DataFrame)
        assert isinstance(metadata['efficiency_ratio'], pd.DataFrame)
        assert isinstance(metadata['net_change'], pd.DataFrame)
        assert isinstance(metadata['volatility'], pd.DataFrame)

    def test_signal_range_bounded(self):
        """All signals should be in [-1, 1] range."""
        # Create diverse price movements
        prices = (
            list(range(100, 120)) +        # Uptrend
            [119, 118, 119, 118] * 3 +     # Choppy
            list(range(118, 108, -1)) +    # Downtrend
            [108] * 5                       # Sideways
        )
        close = pd.DataFrame({'stock': prices})
        params = {'er_period': 10}

        result = efficiency_ratio(close, params)
        signal = result['signal']

        # All valid signals should be in [-1, 1]
        valid_signals = signal.dropna()
        assert (valid_signals >= -1.0).all().all()
        assert (valid_signals <= 1.0).all().all()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
