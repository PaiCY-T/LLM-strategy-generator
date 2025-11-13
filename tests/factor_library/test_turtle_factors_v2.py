"""
Test Suite for Turtle Factors (Phase 2.0 Matrix-Native)
=======================================================

Comprehensive tests for turtle strategy factors using FinLabDataFrame container.
Tests cover ATR, breakout, dual MA filter, and ATR stop loss logic functions.

Test Coverage:
--------------
1. Component Tests - Logic Function Calculations
   - atr_logic: True Range and ATR calculation
   - breakout_logic: N-day high/low breakout detection
   - dual_ma_filter_logic: Dual moving average filter
   - atr_stop_loss_logic: ATR-based adaptive stop loss

2. Matrix Operations Tests
   - Multi-symbol vectorization
   - Signal generation (1, -1, 0)
   - Boolean filter generation
   - Stop level calculations

Architecture: Phase 2.0 Matrix-Native Factor Graph System
"""

import pytest
import pandas as pd
import numpy as np

from src.factor_graph.finlab_dataframe import FinLabDataFrame
from src.factor_library.turtle_factors import (
    _atr_logic,
    _breakout_logic,
    _dual_ma_filter_logic,
    _atr_stop_loss_logic,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_ohlc_matrix():
    """Create sample OHLC Dates×Symbols matrix data."""
    dates = pd.date_range('2023-01-01', periods=25)
    symbols = ['2330', '2317', '2454']

    np.random.seed(42)

    # Create realistic OHLC data
    base_prices = np.array([100, 200, 150])
    close_data = []

    for i in range(25):
        day_change = np.random.randn(3) * 2
        close_data.append(base_prices + np.cumsum(day_change))

    close = pd.DataFrame(close_data, index=dates, columns=symbols)
    high = close * 1.02  # High is 2% above close
    low = close * 0.98   # Low is 2% below close

    return {'high': high, 'low': low, 'close': close}


@pytest.fixture
def sample_container_ohlc(sample_ohlc_matrix):
    """Create FinLabDataFrame container with OHLC data."""
    container = FinLabDataFrame()
    container.add_matrix('high', sample_ohlc_matrix['high'])
    container.add_matrix('low', sample_ohlc_matrix['low'])
    container.add_matrix('close', sample_ohlc_matrix['close'])
    return container


# ============================================================================
# Component Tests - ATR Logic
# ============================================================================

class TestATRLogic:
    """Test atr_logic function with matrix operations."""

    def test_atr_calculation_correctness(self, sample_container_ohlc):
        """Test ATR calculation matches expected formula."""
        parameters = {'atr_period': 14}

        # Execute logic
        _atr_logic(sample_container_ohlc, parameters)

        # Check output exists
        assert sample_container_ohlc.has_matrix('atr')

        # Get matrices
        atr = sample_container_ohlc.get_matrix('atr')
        high = sample_container_ohlc.get_matrix('high')
        low = sample_container_ohlc.get_matrix('low')
        close = sample_container_ohlc.get_matrix('close')

        # Verify shape
        assert atr.shape == close.shape

        # Manual calculation for verification (for first symbol)
        prev_close = close.iloc[:, 0].shift(1)
        high_low = high.iloc[:, 0] - low.iloc[:, 0]
        high_prev_close = np.abs(high.iloc[:, 0] - prev_close)
        low_prev_close = np.abs(low.iloc[:, 0] - prev_close)

        true_range = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
        expected_atr = true_range.rolling(window=14).mean()

        # Compare non-NaN values
        pd.testing.assert_series_equal(
            atr.iloc[14:, 0],
            expected_atr.iloc[14:],
            check_dtype=False,
            check_names=False
        )

    def test_atr_with_different_periods(self, sample_container_ohlc):
        """Test ATR with various period parameters."""
        test_periods = [10, 14, 20]

        for period in test_periods:
            container = FinLabDataFrame()
            container.add_matrix('high', sample_container_ohlc.get_matrix('high'))
            container.add_matrix('low', sample_container_ohlc.get_matrix('low'))
            container.add_matrix('close', sample_container_ohlc.get_matrix('close'))

            parameters = {'atr_period': period}
            _atr_logic(container, parameters)

            atr = container.get_matrix('atr')

            # Check that first (period) rows have NaN
            assert atr.iloc[:period].isna().any().any()

            # Check that later rows have values
            assert not atr.iloc[period:].isna().all().all()


# ============================================================================
# Component Tests - Breakout Logic
# ============================================================================

class TestBreakoutLogic:
    """Test breakout_logic function with matrix operations."""

    def test_breakout_signal_generation(self, sample_container_ohlc):
        """Test breakout signal generation (1, -1, 0)."""
        parameters = {'entry_window': 10}

        # Execute logic
        _breakout_logic(sample_container_ohlc, parameters)

        # Check output exists
        assert sample_container_ohlc.has_matrix('breakout_signal')

        # Get result
        breakout_signal = sample_container_ohlc.get_matrix('breakout_signal')
        close = sample_container_ohlc.get_matrix('close')

        # Verify shape
        assert breakout_signal.shape == close.shape

        # Check signal values are in {-1, 0, 1}
        unique_values = set(breakout_signal.values.flatten())
        assert unique_values.issubset({-1, 0, 1})

    def test_breakout_long_signal(self):
        """Test long breakout signal detection."""
        dates = pd.date_range('2023-01-01', periods=15)
        symbols = ['2330']

        # Create data with clear breakout
        high_data = [100, 101, 102, 101, 100, 99, 100, 101, 102, 103, 105, 107, 110, 108, 106]
        low_data = [98, 99, 100, 99, 98, 97, 98, 99, 100, 101, 103, 105, 108, 106, 104]
        close_data = [99, 100, 101, 100, 99, 98, 99, 100, 101, 102, 104, 106, 109, 107, 105]

        container = FinLabDataFrame()
        container.add_matrix('high', pd.DataFrame(high_data, index=dates, columns=symbols))
        container.add_matrix('low', pd.DataFrame(low_data, index=dates, columns=symbols))
        container.add_matrix('close', pd.DataFrame(close_data, index=dates, columns=symbols))

        parameters = {'entry_window': 5}
        _breakout_logic(container, parameters)

        breakout_signal = container.get_matrix('breakout_signal')

        # Check that we have some long signals (1)
        assert (breakout_signal == 1).any().any()

    def test_breakout_shape_preservation(self, sample_container_ohlc):
        """Test that breakout preserves matrix shape."""
        original_shape = sample_container_ohlc.get_matrix('close').shape

        parameters = {'entry_window': 20}
        _breakout_logic(sample_container_ohlc, parameters)

        breakout_signal = sample_container_ohlc.get_matrix('breakout_signal')
        assert breakout_signal.shape == original_shape


# ============================================================================
# Component Tests - Dual MA Filter Logic
# ============================================================================

class TestDualMAFilterLogic:
    """Test dual_ma_filter_logic function with matrix operations."""

    def test_dual_ma_filter_calculation(self, sample_container_ohlc):
        """Test dual MA filter calculation."""
        parameters = {'short_ma': 5, 'long_ma': 10}

        # Execute logic
        _dual_ma_filter_logic(sample_container_ohlc, parameters)

        # Check output exists
        assert sample_container_ohlc.has_matrix('dual_ma_filter')

        # Get result
        dual_ma_filter = sample_container_ohlc.get_matrix('dual_ma_filter')
        close = sample_container_ohlc.get_matrix('close')

        # Verify shape
        assert dual_ma_filter.shape == close.shape

        # Verify boolean output
        assert dual_ma_filter.dtypes.apply(lambda x: x == bool or x == 'bool').all()

    def test_dual_ma_filter_logic_correctness(self):
        """Test dual MA filter logic (price > both MAs)."""
        dates = pd.date_range('2023-01-01', periods=20)
        symbols = ['2330']

        # Strong uptrend - price should be above both MAs
        close = pd.DataFrame(
            np.arange(100, 120),
            index=dates,
            columns=symbols
        )

        container = FinLabDataFrame()
        container.add_matrix('close', close)

        parameters = {'short_ma': 3, 'long_ma': 5}
        _dual_ma_filter_logic(container, parameters)

        dual_ma_filter = container.get_matrix('dual_ma_filter')

        # Manual calculation
        ma_short = close.rolling(window=3).mean()
        ma_long = close.rolling(window=5).mean()
        expected_filter = (close > ma_short) & (close > ma_long)

        pd.testing.assert_frame_equal(
            dual_ma_filter,
            expected_filter,
            check_dtype=False
        )

        # In strong uptrend, later values should be True
        assert dual_ma_filter.iloc[10:].sum().values[0] > 5


# ============================================================================
# Component Tests - ATR Stop Loss Logic
# ============================================================================

class TestATRStopLossLogic:
    """Test atr_stop_loss_logic function with matrix operations."""

    def test_atr_stop_loss_calculation(self):
        """Test ATR stop loss level calculation."""
        dates = pd.date_range('2023-01-01', periods=20)
        symbols = ['2330', '2317']

        # Create data
        close = pd.DataFrame(
            [[100, 200], [102, 202], [101, 201], [103, 203], [105, 205]] * 4,
            index=dates,
            columns=symbols
        )
        atr = pd.DataFrame(
            [[2.0, 4.0]] * 20,
            index=dates,
            columns=symbols
        )
        positions = pd.DataFrame(
            [[1, 1], [1, -1], [0, 1], [1, 0], [1, 1]] * 4,
            index=dates,
            columns=symbols
        )

        container = FinLabDataFrame()
        container.add_matrix('close', close)
        container.add_matrix('atr', atr)
        container.add_matrix('positions', positions)

        parameters = {'atr_multiplier': 2.0}
        _atr_stop_loss_logic(container, parameters)

        # Check output
        assert container.has_matrix('stop_loss_level')
        stop_loss = container.get_matrix('stop_loss_level')

        # Verify shape
        assert stop_loss.shape == close.shape

        # Manual verification for long position (row 0, col 0)
        # Stop = close - (atr * multiplier) = 100 - (2.0 * 2.0) = 96
        expected_long_stop = 100 - (2.0 * 2.0)
        assert abs(stop_loss.iloc[0, 0] - expected_long_stop) < 0.01

        # Manual verification for short position (row 1, col 1)
        # Stop = close + (atr * multiplier) = 202 + (4.0 * 2.0) = 210
        expected_short_stop = 202 + (4.0 * 2.0)
        assert abs(stop_loss.iloc[1, 1] - expected_short_stop) < 0.01

        # No position should have NaN
        assert pd.isna(stop_loss.iloc[2, 0])  # No position
        assert pd.isna(stop_loss.iloc[3, 1])  # No position

    def test_atr_stop_loss_with_different_multipliers(self):
        """Test ATR stop loss with various multiplier values."""
        dates = pd.date_range('2023-01-01', periods=10)
        symbols = ['2330']

        close = pd.DataFrame([100] * 10, index=dates, columns=symbols)
        atr = pd.DataFrame([2.0] * 10, index=dates, columns=symbols)
        positions = pd.DataFrame([1] * 10, index=dates, columns=symbols)

        test_multipliers = [1.0, 1.5, 2.0, 3.0]

        for multiplier in test_multipliers:
            container = FinLabDataFrame()
            container.add_matrix('close', close)
            container.add_matrix('atr', atr)
            container.add_matrix('positions', positions)

            parameters = {'atr_multiplier': multiplier}
            _atr_stop_loss_logic(container, parameters)

            stop_loss = container.get_matrix('stop_loss_level')

            # Expected stop level = 100 - (2.0 * multiplier)
            expected_stop = 100 - (2.0 * multiplier)
            assert abs(stop_loss.iloc[0, 0] - expected_stop) < 0.01


# ============================================================================
# Integration Tests
# ============================================================================

class TestTurtleFactorsIntegration:
    """Test integration of multiple turtle factors."""

    def test_full_turtle_pipeline(self, sample_container_ohlc):
        """Test executing full turtle factor pipeline."""
        # Execute all turtle factors in sequence
        _atr_logic(sample_container_ohlc, {'atr_period': 14})
        _breakout_logic(sample_container_ohlc, {'entry_window': 20})
        _dual_ma_filter_logic(sample_container_ohlc, {'short_ma': 10, 'long_ma': 20})

        # Add positions for stop loss
        close = sample_container_ohlc.get_matrix('close')
        positions = pd.DataFrame(1, index=close.index, columns=close.columns)
        sample_container_ohlc.add_matrix('positions', positions)

        _atr_stop_loss_logic(sample_container_ohlc, {'atr_multiplier': 2.0})

        # Verify all outputs exist
        assert sample_container_ohlc.has_matrix('atr')
        assert sample_container_ohlc.has_matrix('breakout_signal')
        assert sample_container_ohlc.has_matrix('dual_ma_filter')
        assert sample_container_ohlc.has_matrix('stop_loss_level')

        # Verify all outputs have correct shape
        original_shape = close.shape
        assert sample_container_ohlc.get_matrix('atr').shape == original_shape
        assert sample_container_ohlc.get_matrix('breakout_signal').shape == original_shape
        assert sample_container_ohlc.get_matrix('dual_ma_filter').shape == original_shape
        assert sample_container_ohlc.get_matrix('stop_loss_level').shape == original_shape


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
