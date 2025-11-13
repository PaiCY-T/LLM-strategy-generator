"""
Unit tests for Turtle Factors
==============================

Tests for turtle strategy factors extracted from TurtleTemplate.
Validates ATR calculation, breakout detection, dual MA filtering, and ATR-based stop loss.

Architecture: Phase 2.0+ Factor Graph System
Test Coverage: All 4 turtle factors + factory functions
"""

import pytest
import pandas as pd
import numpy as np

from src.factor_library.turtle_factors import (
    ATRFactor,
    BreakoutFactor,
    DualMAFilterFactor,
    ATRStopLossFactor,
    create_atr_factor,
    create_breakout_factor,
    create_dual_ma_filter_factor,
    create_atr_stop_loss_factor,
)
from src.factor_graph.factor_category import FactorCategory


# ============================================================================
# ATRFactor Tests
# ============================================================================

class TestATRFactor:
    """Test suite for ATRFactor."""

    def test_atr_factor_initialization(self):
        """Test ATRFactor initializes with correct properties."""
        atr = ATRFactor(atr_period=20)

        assert atr.id == "atr_20"
        assert atr.name == "ATR (20d)"
        assert atr.category == FactorCategory.RISK
        assert atr.inputs == ["high", "low", "close"]
        assert atr.outputs == ["atr"]
        assert atr.parameters == {"atr_period": 20}
        assert "Average True Range" in atr.description

    def test_atr_calculation_simple(self):
        """Test ATR calculation with simple data."""
        atr = ATRFactor(atr_period=3)

        # Create test data with known true ranges
        data = pd.DataFrame({
            "high": [102, 104, 106, 105, 107],
            "low": [98, 100, 102, 101, 103],
            "close": [100, 102, 104, 103, 105]
        })

        result = atr.execute(data)

        # Verify ATR column exists
        assert "atr" in result.columns

        # Verify ATR values are reasonable (non-negative)
        atr_values = result["atr"].dropna()
        assert len(atr_values) > 0
        assert all(atr_values >= 0)

    def test_atr_calculation_expanding_range(self):
        """Test ATR with expanding true range (increasing volatility)."""
        atr = ATRFactor(atr_period=3)

        # Create data with expanding ranges: 4, 6, 8, 10, 12
        data = pd.DataFrame({
            "high": [102, 105, 109, 114, 120],
            "low": [98, 99, 101, 104, 108],
            "close": [100, 103, 107, 112, 118]
        })

        result = atr.execute(data)

        # ATR should increase with expanding ranges
        atr_values = result["atr"].dropna()
        assert len(atr_values) >= 2
        # Last ATR should be larger than first due to expanding volatility
        assert atr_values.iloc[-1] > atr_values.iloc[0]

    def test_atr_calculation_gaps(self):
        """Test ATR calculation with price gaps (tests abs(high - prev_close))."""
        atr = ATRFactor(atr_period=3)

        # Create data with overnight gap up
        data = pd.DataFrame({
            "high": [102, 110, 112, 114, 116],  # Gap up from 100 to 110
            "low": [98, 108, 110, 112, 114],
            "close": [100, 109, 111, 113, 115]
        })

        result = atr.execute(data)

        # Verify ATR captures the gap
        atr_values = result["atr"].dropna()
        assert len(atr_values) > 0
        # ATR should be substantial due to gap
        assert atr_values.iloc[0] > 2.0  # Gap creates large true range

    def test_atr_different_periods(self):
        """Test ATR with different lookback periods."""
        data = pd.DataFrame({
            "high": [102, 104, 106, 105, 107, 109, 108, 110],
            "low": [98, 100, 102, 101, 103, 105, 104, 106],
            "close": [100, 102, 104, 103, 105, 107, 106, 108]
        })

        atr_short = ATRFactor(atr_period=3)
        atr_long = ATRFactor(atr_period=5)

        result_short = atr_short.execute(data.copy())
        result_long = atr_long.execute(data.copy())

        # Both should produce ATR values
        assert "atr" in result_short.columns
        assert "atr" in result_long.columns

        # Longer period has more NaN at start
        assert result_short["atr"].notna().sum() > result_long["atr"].notna().sum()

    def test_atr_factory_function(self):
        """Test create_atr_factor factory function."""
        atr = create_atr_factor(atr_period=14)

        assert isinstance(atr, ATRFactor)
        assert atr.parameters == {"atr_period": 14}
        assert atr.id == "atr_14"


# ============================================================================
# BreakoutFactor Tests
# ============================================================================

class TestBreakoutFactor:
    """Test suite for BreakoutFactor."""

    def test_breakout_factor_initialization(self):
        """Test BreakoutFactor initializes with correct properties."""
        breakout = BreakoutFactor(entry_window=20)

        assert breakout.id == "breakout_20"
        assert breakout.name == "Breakout (20d)"
        assert breakout.category == FactorCategory.ENTRY
        assert breakout.inputs == ["high", "low", "close"]
        assert breakout.outputs == ["breakout_signal"]
        assert breakout.parameters == {"entry_window": 20}
        assert "breakout detection" in breakout.description

    def test_breakout_long_signal(self):
        """Test long breakout signal detection."""
        breakout = BreakoutFactor(entry_window=3)

        # Create data with upward breakout at position 4
        # First 3 bars: high=104, then bar 4 breaks out to 110
        data = pd.DataFrame({
            "high": [102, 104, 103, 110, 112],
            "low": [98, 100, 99, 106, 108],
            "close": [100, 102, 101, 108, 110]
        })

        result = breakout.execute(data)

        # Verify breakout_signal column exists
        assert "breakout_signal" in result.columns

        # Position 3 (index 3) should show long breakout (signal=1)
        # because close=108 > previous 3-day high=104
        assert result["breakout_signal"].iloc[3] == 1

    def test_breakout_short_signal(self):
        """Test short breakout signal detection."""
        breakout = BreakoutFactor(entry_window=3)

        # Create data with downward breakout at position 4
        # First 3 bars: low=98, then bar 4 breaks down to 92
        data = pd.DataFrame({
            "high": [102, 104, 103, 96, 94],
            "low": [98, 100, 99, 92, 90],
            "close": [100, 102, 101, 94, 92]
        })

        result = breakout.execute(data)

        # Position 3 (index 3) should show short breakout (signal=-1)
        # because close=94 < previous 3-day low=98
        assert result["breakout_signal"].iloc[3] == -1

    def test_breakout_no_signal(self):
        """Test no breakout signal in ranging market."""
        breakout = BreakoutFactor(entry_window=3)

        # Create ranging data with no breakouts
        data = pd.DataFrame({
            "high": [102, 103, 102, 103, 102],
            "low": [98, 99, 98, 99, 98],
            "close": [100, 101, 100, 101, 100]
        })

        result = breakout.execute(data)

        # All signals should be 0 (no breakout) after initial period
        signals = result["breakout_signal"].iloc[3:]
        assert all(signals == 0)

    def test_breakout_different_windows(self):
        """Test breakout with different entry windows."""
        data = pd.DataFrame({
            "high": [102, 104, 106, 108, 110, 112, 114, 116],
            "low": [98, 100, 102, 104, 106, 108, 110, 112],
            "close": [100, 102, 104, 106, 108, 110, 112, 114]
        })

        breakout_short = BreakoutFactor(entry_window=3)
        breakout_long = BreakoutFactor(entry_window=5)

        result_short = breakout_short.execute(data.copy())
        result_long = breakout_long.execute(data.copy())

        # Both should produce signals
        assert "breakout_signal" in result_short.columns
        assert "breakout_signal" in result_long.columns

        # Signals may differ based on window size
        assert result_short["breakout_signal"].dtype == result_long["breakout_signal"].dtype

    def test_breakout_factory_function(self):
        """Test create_breakout_factor factory function."""
        breakout = create_breakout_factor(entry_window=55)

        assert isinstance(breakout, BreakoutFactor)
        assert breakout.parameters == {"entry_window": 55}
        assert breakout.id == "breakout_55"


# ============================================================================
# DualMAFilterFactor Tests
# ============================================================================

class TestDualMAFilterFactor:
    """Test suite for DualMAFilterFactor."""

    def test_dual_ma_filter_initialization(self):
        """Test DualMAFilterFactor initializes with correct properties."""
        ma_filter = DualMAFilterFactor(short_ma=20, long_ma=60)

        assert ma_filter.id == "dual_ma_filter_20_60"
        assert ma_filter.name == "Dual MA Filter (20d/60d)"
        assert ma_filter.category == FactorCategory.MOMENTUM
        assert ma_filter.inputs == ["close"]
        assert ma_filter.outputs == ["dual_ma_filter"]
        assert ma_filter.parameters == {"short_ma": 20, "long_ma": 60}
        assert "Dual moving average filter" in ma_filter.description

    def test_dual_ma_filter_uptrend(self):
        """Test dual MA filter in strong uptrend."""
        ma_filter = DualMAFilterFactor(short_ma=3, long_ma=5)

        # Create uptrending data where price is above both MAs
        data = pd.DataFrame({
            "close": [100, 102, 104, 106, 108, 110, 112, 114, 116]
        })

        result = ma_filter.execute(data)

        # Verify dual_ma_filter column exists
        assert "dual_ma_filter" in result.columns

        # After initial period, filter should be True (price above both MAs)
        filter_values = result["dual_ma_filter"].iloc[5:]
        assert filter_values.sum() > 0  # At least some True values

    def test_dual_ma_filter_downtrend(self):
        """Test dual MA filter in strong downtrend."""
        ma_filter = DualMAFilterFactor(short_ma=3, long_ma=5)

        # Create downtrending data where price is below both MAs
        data = pd.DataFrame({
            "close": [116, 114, 112, 110, 108, 106, 104, 102, 100]
        })

        result = ma_filter.execute(data)

        # After initial period, filter should be False (price below both MAs)
        filter_values = result["dual_ma_filter"].iloc[5:]
        assert filter_values.sum() < len(filter_values)  # Not all True

    def test_dual_ma_filter_ranging(self):
        """Test dual MA filter in ranging market."""
        ma_filter = DualMAFilterFactor(short_ma=3, long_ma=5)

        # Create ranging data oscillating around 100
        data = pd.DataFrame({
            "close": [100, 102, 98, 101, 99, 103, 97, 102, 98]
        })

        result = ma_filter.execute(data)

        # Filter should toggle between True and False
        filter_values = result["dual_ma_filter"].dropna()
        assert len(filter_values) > 0
        # Should have both True and False values in ranging market
        assert filter_values.sum() > 0 and filter_values.sum() < len(filter_values)

    def test_dual_ma_filter_different_periods(self):
        """Test dual MA filter with different period combinations."""
        data = pd.DataFrame({
            "close": list(range(100, 120))  # Steady uptrend
        })

        ma_filter_fast = DualMAFilterFactor(short_ma=3, long_ma=5)
        ma_filter_slow = DualMAFilterFactor(short_ma=5, long_ma=10)

        result_fast = ma_filter_fast.execute(data.copy())
        result_slow = ma_filter_slow.execute(data.copy())

        # Both should produce filter values
        assert "dual_ma_filter" in result_fast.columns
        assert "dual_ma_filter" in result_slow.columns

        # Fast filter should have more data points (less NaN at start) or equal
        assert result_fast["dual_ma_filter"].notna().sum() >= result_slow["dual_ma_filter"].notna().sum()

    def test_dual_ma_filter_factory_function(self):
        """Test create_dual_ma_filter_factor factory function."""
        ma_filter = create_dual_ma_filter_factor(short_ma=10, long_ma=30)

        assert isinstance(ma_filter, DualMAFilterFactor)
        assert ma_filter.parameters == {"short_ma": 10, "long_ma": 30}
        assert ma_filter.id == "dual_ma_filter_10_30"


# ============================================================================
# ATRStopLossFactor Tests
# ============================================================================

class TestATRStopLossFactor:
    """Test suite for ATRStopLossFactor."""

    def test_atr_stop_loss_initialization(self):
        """Test ATRStopLossFactor initializes with correct properties."""
        stop_loss = ATRStopLossFactor(atr_multiplier=2.0)

        assert stop_loss.id == "atr_stop_loss_2_0"  # Float converted to underscore format
        assert stop_loss.name == "ATR Stop Loss (2.0x)"
        assert stop_loss.category == FactorCategory.EXIT
        assert stop_loss.inputs == ["close", "atr", "positions"]
        assert stop_loss.outputs == ["stop_loss_level"]
        assert stop_loss.parameters == {"atr_multiplier": 2.0}
        assert "ATR-based stop loss" in stop_loss.description

    def test_atr_stop_loss_long_position(self):
        """Test stop loss calculation for long positions."""
        stop_loss = ATRStopLossFactor(atr_multiplier=2.0)

        # Create data with long positions
        data = pd.DataFrame({
            "close": [100, 102, 104, 106, 108],
            "atr": [2.0, 2.1, 2.0, 2.2, 2.1],
            "positions": [1, 1, 1, 1, 1]  # All long positions
        })

        result = stop_loss.execute(data)

        # Verify stop_loss_level column exists
        assert "stop_loss_level" in result.columns

        # For long positions: stop = close - (atr * multiplier)
        # First position: 100 - (2.0 * 2.0) = 96.0
        expected_stop = 100 - (2.0 * 2.0)
        assert abs(result["stop_loss_level"].iloc[0] - expected_stop) < 0.01

    def test_atr_stop_loss_short_position(self):
        """Test stop loss calculation for short positions."""
        stop_loss = ATRStopLossFactor(atr_multiplier=2.0)

        # Create data with short positions
        data = pd.DataFrame({
            "close": [100, 98, 96, 94, 92],
            "atr": [2.0, 2.1, 2.0, 2.2, 2.1],
            "positions": [-1, -1, -1, -1, -1]  # All short positions
        })

        result = stop_loss.execute(data)

        # For short positions: stop = close + (atr * multiplier)
        # First position: 100 + (2.0 * 2.0) = 104.0
        expected_stop = 100 + (2.0 * 2.0)
        assert abs(result["stop_loss_level"].iloc[0] - expected_stop) < 0.01

    def test_atr_stop_loss_no_position(self):
        """Test stop loss with no positions."""
        stop_loss = ATRStopLossFactor(atr_multiplier=2.0)

        # Create data with no positions
        data = pd.DataFrame({
            "close": [100, 102, 104, 106, 108],
            "atr": [2.0, 2.1, 2.0, 2.2, 2.1],
            "positions": [0, 0, 0, 0, 0]  # No positions
        })

        result = stop_loss.execute(data)

        # All stop loss levels should be NaN when no positions
        assert result["stop_loss_level"].isna().all()

    def test_atr_stop_loss_mixed_positions(self):
        """Test stop loss with mixed long/short/no positions."""
        stop_loss = ATRStopLossFactor(atr_multiplier=2.5)

        # Create data with mixed positions
        data = pd.DataFrame({
            "close": [100, 102, 104, 106, 108],
            "atr": [2.0, 2.0, 2.0, 2.0, 2.0],
            "positions": [1, 0, -1, 1, 0]  # Long, None, Short, Long, None
        })

        result = stop_loss.execute(data)

        # Position 0 (long): stop = 100 - (2.0 * 2.5) = 95.0
        assert abs(result["stop_loss_level"].iloc[0] - 95.0) < 0.01

        # Position 1 (none): stop = NaN
        assert pd.isna(result["stop_loss_level"].iloc[1])

        # Position 2 (short): stop = 104 + (2.0 * 2.5) = 109.0
        assert abs(result["stop_loss_level"].iloc[2] - 109.0) < 0.01

        # Position 3 (long): stop = 106 - (2.0 * 2.5) = 101.0
        assert abs(result["stop_loss_level"].iloc[3] - 101.0) < 0.01

        # Position 4 (none): stop = NaN
        assert pd.isna(result["stop_loss_level"].iloc[4])

    def test_atr_stop_loss_different_multipliers(self):
        """Test stop loss with different ATR multipliers."""
        data = pd.DataFrame({
            "close": [100, 102, 104],
            "atr": [2.0, 2.0, 2.0],
            "positions": [1, 1, 1]
        })

        stop_tight = ATRStopLossFactor(atr_multiplier=1.5)
        stop_wide = ATRStopLossFactor(atr_multiplier=3.0)

        result_tight = stop_tight.execute(data.copy())
        result_wide = stop_wide.execute(data.copy())

        # Tight stop should be closer to price
        # Tight: 100 - (2.0 * 1.5) = 97.0
        # Wide: 100 - (2.0 * 3.0) = 94.0
        assert result_tight["stop_loss_level"].iloc[0] > result_wide["stop_loss_level"].iloc[0]

    def test_atr_stop_loss_factory_function(self):
        """Test create_atr_stop_loss_factor factory function."""
        stop_loss = create_atr_stop_loss_factor(atr_multiplier=2.5)

        assert isinstance(stop_loss, ATRStopLossFactor)
        assert stop_loss.parameters == {"atr_multiplier": 2.5}
        assert stop_loss.id == "atr_stop_loss_2_5"  # Float converted to underscore format


# ============================================================================
# Integration Tests
# ============================================================================

class TestTurtleFactorIntegration:
    """Integration tests for using multiple turtle factors together."""

    def test_atr_and_stop_loss_integration(self):
        """Test ATR factor output feeds into stop loss factor."""
        # Create factors
        atr = ATRFactor(atr_period=3)
        stop_loss = ATRStopLossFactor(atr_multiplier=2.0)

        # Create test data
        data = pd.DataFrame({
            "high": [102, 104, 106, 105, 107],
            "low": [98, 100, 102, 101, 103],
            "close": [100, 102, 104, 103, 105],
            "positions": [1, 1, 1, 1, 1]  # Long positions
        })

        # Execute ATR first, then stop loss
        result = atr.execute(data)
        result = stop_loss.execute(result)

        # Both outputs should exist
        assert "atr" in result.columns
        assert "stop_loss_level" in result.columns

        # Stop loss should be calculated using ATR
        atr_values = result["atr"].dropna()
        stop_values = result["stop_loss_level"].dropna()
        assert len(atr_values) > 0
        assert len(stop_values) > 0

    def test_breakout_and_ma_filter_integration(self):
        """Test breakout detection with MA filter confirmation."""
        # Create factors
        breakout = BreakoutFactor(entry_window=3)
        ma_filter = DualMAFilterFactor(short_ma=3, long_ma=5)

        # Create trending data with breakout
        data = pd.DataFrame({
            "high": [102, 104, 106, 110, 112, 114, 116, 118],
            "low": [98, 100, 102, 106, 108, 110, 112, 114],
            "close": [100, 102, 104, 108, 110, 112, 114, 116]
        })

        # Execute both factors
        result = breakout.execute(data)
        result = ma_filter.execute(result)

        # Both outputs should exist
        assert "breakout_signal" in result.columns
        assert "dual_ma_filter" in result.columns

        # Can combine signals: breakout AND ma_filter
        combined_signal = (result["breakout_signal"] == 1) & result["dual_ma_filter"]
        assert combined_signal.sum() >= 0  # Valid combined signal

    def test_complete_turtle_factor_chain(self):
        """Test all 4 turtle factors working together."""
        # Create all factors
        atr = ATRFactor(atr_period=3)
        breakout = BreakoutFactor(entry_window=3)
        ma_filter = DualMAFilterFactor(short_ma=3, long_ma=5)
        stop_loss = ATRStopLossFactor(atr_multiplier=2.0)

        # Create comprehensive test data
        data = pd.DataFrame({
            "high": [102, 104, 106, 110, 112, 114, 116, 118, 120],
            "low": [98, 100, 102, 106, 108, 110, 112, 114, 116],
            "close": [100, 102, 104, 108, 110, 112, 114, 116, 118],
            "positions": [0, 0, 0, 1, 1, 1, 1, 1, 1]  # Enter at breakout
        })

        # Execute full factor chain
        result = atr.execute(data)
        result = breakout.execute(result)
        result = ma_filter.execute(result)
        result = stop_loss.execute(result)

        # All outputs should exist
        assert "atr" in result.columns
        assert "breakout_signal" in result.columns
        assert "dual_ma_filter" in result.columns
        assert "stop_loss_level" in result.columns

        # Verify data integrity
        assert len(result) == len(data)
        assert result["close"].equals(data["close"])


# ============================================================================
# Parameter Validation Tests
# ============================================================================

class TestParameterVariations:
    """Test factors with various parameter combinations."""

    def test_atr_extreme_periods(self):
        """Test ATR with extreme period values."""
        data = pd.DataFrame({
            "high": list(range(100, 150)),
            "low": list(range(90, 140)),
            "close": list(range(95, 145))
        })

        # Very short period
        atr_short = ATRFactor(atr_period=1)
        result_short = atr_short.execute(data.copy())
        assert "atr" in result_short.columns

        # Very long period
        atr_long = ATRFactor(atr_period=30)
        result_long = atr_long.execute(data.copy())
        assert "atr" in result_long.columns

    def test_breakout_extreme_windows(self):
        """Test breakout with extreme window values."""
        data = pd.DataFrame({
            "high": list(range(100, 150)),
            "low": list(range(90, 140)),
            "close": list(range(95, 145))
        })

        # Very short window
        breakout_short = BreakoutFactor(entry_window=1)
        result_short = breakout_short.execute(data.copy())
        assert "breakout_signal" in result_short.columns

        # Very long window
        breakout_long = BreakoutFactor(entry_window=40)
        result_long = breakout_long.execute(data.copy())
        assert "breakout_signal" in result_long.columns

    def test_dual_ma_filter_equal_periods(self):
        """Test dual MA filter with equal short and long periods."""
        ma_filter = DualMAFilterFactor(short_ma=10, long_ma=10)

        data = pd.DataFrame({
            "close": list(range(100, 120))
        })

        result = ma_filter.execute(data)
        assert "dual_ma_filter" in result.columns

    def test_atr_stop_loss_extreme_multipliers(self):
        """Test ATR stop loss with extreme multipliers."""
        data = pd.DataFrame({
            "close": [100, 102, 104],
            "atr": [2.0, 2.0, 2.0],
            "positions": [1, 1, 1]
        })

        # Very tight stop (0.5x ATR)
        stop_tight = ATRStopLossFactor(atr_multiplier=0.5)
        result_tight = stop_tight.execute(data.copy())
        assert "stop_loss_level" in result_tight.columns

        # Very wide stop (5.0x ATR)
        stop_wide = ATRStopLossFactor(atr_multiplier=5.0)
        result_wide = stop_wide.execute(data.copy())
        assert "stop_loss_level" in result_wide.columns

        # Wide stop should be further from price
        assert result_tight["stop_loss_level"].iloc[0] > result_wide["stop_loss_level"].iloc[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
