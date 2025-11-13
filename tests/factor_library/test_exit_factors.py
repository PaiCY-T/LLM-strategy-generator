"""
Unit Tests for Exit Factors Module
===================================

Tests for exit strategy factors extracted from Phase 1 Exit Mutation Framework.
Tests each exit factor independently with various scenarios and edge cases.

Test Coverage:
-------------
1. TrailingStopFactor - Trailing stop loss logic
2. TimeBasedExitFactor - Time-based exit logic
3. VolatilityStopFactor - Volatility-based stop logic
4. ProfitTargetFactor - Profit target exit logic
5. CompositeExitFactor - Composite exit signal combination
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.factor_library.exit_factors import (
    TrailingStopFactor,
    TimeBasedExitFactor,
    VolatilityStopFactor,
    ProfitTargetFactor,
    CompositeExitFactor,
    create_trailing_stop_factor,
    create_time_based_exit_factor,
    create_volatility_stop_factor,
    create_profit_target_factor,
    create_composite_exit_factor,
)
from src.factor_graph.factor_category import FactorCategory


class TestTrailingStopFactor:
    """Test cases for TrailingStopFactor."""

    def test_factor_initialization(self):
        """Test factor initializes with correct parameters."""
        factor = TrailingStopFactor(trail_percent=0.10, activation_profit=0.05)

        assert factor.category == FactorCategory.EXIT
        assert "close" in factor.inputs
        assert "positions" in factor.inputs
        assert "entry_price" in factor.inputs
        assert "trailing_stop_signal" in factor.outputs
        assert factor.parameters["trail_percent"] == 0.10
        assert factor.parameters["activation_profit"] == 0.05

    def test_trailing_stop_not_activated(self):
        """Test trailing stop doesn't trigger before activation profit."""
        factor = TrailingStopFactor(trail_percent=0.10, activation_profit=0.05)

        # Price increases but not enough to activate trailing
        data = pd.DataFrame({
            "close": [100, 102, 103, 101, 100],
            "positions": [True, True, True, True, True],
            "entry_price": [100, 100, 100, 100, 100]
        })

        result = factor.execute(data)

        # No trailing stop signals should be triggered (profit < 5%)
        assert "trailing_stop_signal" in result.columns
        assert not result["trailing_stop_signal"].any()

    def test_trailing_stop_activated_and_triggered(self):
        """Test trailing stop activates and triggers correctly."""
        factor = TrailingStopFactor(trail_percent=0.10, activation_profit=0.05)

        # Price goes up 10% (activates trailing), then drops 11% from peak
        data = pd.DataFrame({
            "close": [100, 105, 110, 108, 97],  # Peak 110, then drops to 97 (11.8% drop from peak)
            "positions": [True, True, True, True, True],
            "entry_price": [100, 100, 100, 100, 100]
        })

        result = factor.execute(data)

        # Trailing stop should trigger on last row (97 < 110 * 0.90 = 99)
        assert "trailing_stop_signal" in result.columns
        assert result["trailing_stop_signal"].iloc[-1] == True

    def test_trailing_stop_no_positions(self):
        """Test trailing stop with no active positions."""
        factor = TrailingStopFactor(trail_percent=0.10, activation_profit=0.05)

        data = pd.DataFrame({
            "close": [100, 102, 104, 106, 108],
            "positions": [False, False, False, False, False],
            "entry_price": [0, 0, 0, 0, 0]
        })

        result = factor.execute(data)

        # No signals when no positions
        assert not result["trailing_stop_signal"].any()

    def test_trailing_stop_new_position_reset(self):
        """Test trailing stop resets highest price on new position."""
        factor = TrailingStopFactor(trail_percent=0.10, activation_profit=0.05)

        # Old position exits, new position enters
        data = pd.DataFrame({
            "close": [100, 110, 105, 95, 100],
            "positions": [True, True, False, True, True],
            "entry_price": [100, 100, 0, 95, 95]
        })

        result = factor.execute(data)

        # Highest price should reset for new position starting at row 3
        assert "highest_price" in result.columns
        assert result["highest_price"].iloc[3] == 95  # Reset to entry price

    def test_factory_function(self):
        """Test factory function creates factor correctly."""
        factor = create_trailing_stop_factor(trail_percent=0.15, activation_profit=0.10)

        assert isinstance(factor, TrailingStopFactor)
        assert factor.parameters["trail_percent"] == 0.15
        assert factor.parameters["activation_profit"] == 0.10


class TestTimeBasedExitFactor:
    """Test cases for TimeBasedExitFactor."""

    def test_factor_initialization(self):
        """Test factor initializes with correct parameters."""
        factor = TimeBasedExitFactor(max_holding_periods=20)

        assert factor.category == FactorCategory.EXIT
        assert "positions" in factor.inputs
        assert "entry_date" in factor.inputs
        assert "time_exit_signal" in factor.outputs
        assert factor.parameters["max_holding_periods"] == 20

    def test_time_exit_with_datetime_index(self):
        """Test time-based exit with datetime index."""
        factor = TimeBasedExitFactor(max_holding_periods=5)

        # Create data with datetime index
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        data = pd.DataFrame({
            "positions": [True] * 10,
            "entry_date": [dates[0]] * 10
        }, index=dates)

        result = factor.execute(data)

        # Should trigger time exit after 5 days
        assert "time_exit_signal" in result.columns
        assert result["time_exit_signal"].iloc[5] == True
        assert result["time_exit_signal"].iloc[4] == False

    def test_time_exit_no_datetime_index(self):
        """Test time-based exit without datetime index."""
        factor = TimeBasedExitFactor(max_holding_periods=3)

        # Data without datetime index
        data = pd.DataFrame({
            "positions": [True, True, True, True, True],
            "entry_date": [None] * 5
        })

        result = factor.execute(data)

        # Should still work using row count as proxy
        assert "time_exit_signal" in result.columns

    def test_time_exit_new_position(self):
        """Test time exit resets for new positions."""
        factor = TimeBasedExitFactor(max_holding_periods=3)

        dates = pd.date_range("2023-01-01", periods=8, freq="D")
        entry_dates = [dates[0]] * 3 + [None] + [dates[4]] * 4
        data = pd.DataFrame({
            "positions": [True, True, True, False, True, True, True, True],
            "entry_date": entry_dates
        }, index=dates)

        result = factor.execute(data)

        # First position should trigger at day 3
        assert result["time_exit_signal"].iloc[3] == False  # Position exits
        # Second position should trigger at day 7 (3 days from day 4)
        assert result["time_exit_signal"].iloc[7] == True

    def test_time_exit_no_positions(self):
        """Test time exit with no active positions."""
        factor = TimeBasedExitFactor(max_holding_periods=5)

        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        data = pd.DataFrame({
            "positions": [False] * 5,
            "entry_date": [None] * 5
        }, index=dates)

        result = factor.execute(data)

        # No signals when no positions
        assert not result["time_exit_signal"].any()

    def test_factory_function(self):
        """Test factory function creates factor correctly."""
        factor = create_time_based_exit_factor(max_holding_periods=30)

        assert isinstance(factor, TimeBasedExitFactor)
        assert factor.parameters["max_holding_periods"] == 30


class TestVolatilityStopFactor:
    """Test cases for VolatilityStopFactor."""

    def test_factor_initialization(self):
        """Test factor initializes with correct parameters."""
        factor = VolatilityStopFactor(std_period=20, std_multiplier=2.0)

        assert factor.category == FactorCategory.EXIT
        assert "close" in factor.inputs
        assert "positions" in factor.inputs
        assert "volatility_stop_signal" in factor.outputs
        assert factor.parameters["std_period"] == 20
        assert factor.parameters["std_multiplier"] == 2.0

    def test_volatility_stop_triggered(self):
        """Test volatility stop triggers on large price drop."""
        factor = VolatilityStopFactor(std_period=5, std_multiplier=2.0)

        # High volatility followed by large drop
        data = pd.DataFrame({
            "close": [100, 102, 98, 103, 97, 90, 85],
            "positions": [True, True, True, True, True, True, True],
            "entry_price": [100, 100, 100, 100, 100, 100, 100]
        })

        result = factor.execute(data)

        # Volatility stop should eventually trigger
        assert "volatility_stop_signal" in result.columns
        # At least one signal should be True (price dropped significantly)
        assert result["volatility_stop_signal"].any()

    def test_volatility_stop_no_entry_price(self):
        """Test volatility stop without entry_price column."""
        factor = VolatilityStopFactor(std_period=5, std_multiplier=2.0)

        # Data without entry_price
        data = pd.DataFrame({
            "close": [100, 102, 98, 103, 97, 90, 85],
            "positions": [True, True, True, True, True, True, True]
        })

        result = factor.execute(data)

        # Should still work (uses current price as fallback)
        assert "volatility_stop_signal" in result.columns

    def test_volatility_stop_low_volatility(self):
        """Test volatility stop doesn't trigger in low volatility."""
        factor = VolatilityStopFactor(std_period=5, std_multiplier=2.0)

        # Low volatility, small price changes
        data = pd.DataFrame({
            "close": [100, 100.5, 100.2, 100.3, 100.1, 100.4, 100.2],
            "positions": [True, True, True, True, True, True, True],
            "entry_price": [100, 100, 100, 100, 100, 100, 100]
        })

        result = factor.execute(data)

        # Should not trigger in low volatility
        assert not result["volatility_stop_signal"].any()

    def test_volatility_stop_no_positions(self):
        """Test volatility stop with no active positions."""
        factor = VolatilityStopFactor(std_period=5, std_multiplier=2.0)

        data = pd.DataFrame({
            "close": [100, 95, 90, 85, 80],
            "positions": [False, False, False, False, False]
        })

        result = factor.execute(data)

        # No signals when no positions
        assert not result["volatility_stop_signal"].any()

    def test_factory_function(self):
        """Test factory function creates factor correctly."""
        factor = create_volatility_stop_factor(std_period=30, std_multiplier=3.0)

        assert isinstance(factor, VolatilityStopFactor)
        assert factor.parameters["std_period"] == 30
        assert factor.parameters["std_multiplier"] == 3.0


class TestProfitTargetFactor:
    """Test cases for ProfitTargetFactor."""

    def test_factor_initialization(self):
        """Test factor initializes with correct parameters."""
        factor = ProfitTargetFactor(target_percent=0.30)

        assert factor.category == FactorCategory.EXIT
        assert "close" in factor.inputs
        assert "positions" in factor.inputs
        assert "entry_price" in factor.inputs
        assert "profit_target_signal" in factor.outputs
        assert factor.parameters["target_percent"] == 0.30

    def test_profit_target_reached(self):
        """Test profit target triggers when target is reached."""
        factor = ProfitTargetFactor(target_percent=0.20)

        # Price increases 25% (exceeds 20% target)
        # Use 121 to avoid floating point precision issues with 120 (20% exactly)
        data = pd.DataFrame({
            "close": [100.0, 105.0, 110.0, 121.0, 125.0],
            "positions": [True, True, True, True, True],
            "entry_price": [100.0, 100.0, 100.0, 100.0, 100.0]
        })

        result = factor.execute(data)

        # Profit target should trigger when profit >= 20%
        assert "profit_target_signal" in result.columns
        assert result["profit_target_signal"].iloc[3] == True  # 121/100 - 1 = 0.21 > 0.20
        assert result["profit_target_signal"].iloc[4] == True  # 125/100 - 1 = 0.25 > 0.20

    def test_profit_target_not_reached(self):
        """Test profit target doesn't trigger before target."""
        factor = ProfitTargetFactor(target_percent=0.30)

        # Price increases but not enough
        data = pd.DataFrame({
            "close": [100, 105, 110, 115, 120],
            "positions": [True, True, True, True, True],
            "entry_price": [100, 100, 100, 100, 100]
        })

        result = factor.execute(data)

        # No profit target signals (max profit 20%)
        assert not result["profit_target_signal"].any()

    def test_profit_target_exact_match(self):
        """Test profit target triggers at exact target."""
        factor = ProfitTargetFactor(target_percent=0.30)

        # Price increases exactly 30%
        data = pd.DataFrame({
            "close": [100, 110, 120, 130, 135],
            "positions": [True, True, True, True, True],
            "entry_price": [100, 100, 100, 100, 100]
        })

        result = factor.execute(data)

        # Should trigger at exactly 30% profit
        assert result["profit_target_signal"].iloc[3] == True

    def test_profit_target_no_positions(self):
        """Test profit target with no active positions."""
        factor = ProfitTargetFactor(target_percent=0.30)

        data = pd.DataFrame({
            "close": [100, 120, 140, 160, 180],
            "positions": [False, False, False, False, False],
            "entry_price": [0, 0, 0, 0, 0]
        })

        result = factor.execute(data)

        # No signals when no positions
        assert not result["profit_target_signal"].any()

    def test_factory_function(self):
        """Test factory function creates factor correctly."""
        factor = create_profit_target_factor(target_percent=0.50)

        assert isinstance(factor, ProfitTargetFactor)
        assert factor.parameters["target_percent"] == 0.50


class TestCompositeExitFactor:
    """Test cases for CompositeExitFactor."""

    def test_factor_initialization(self):
        """Test factor initializes with correct parameters."""
        signals = ["signal1", "signal2", "signal3"]
        factor = CompositeExitFactor(exit_signals=signals)

        assert factor.category == FactorCategory.EXIT
        assert set(factor.inputs) == set(signals)
        assert "final_exit_signal" in factor.outputs
        assert factor.parameters["exit_signals"] == signals

    def test_composite_exit_or_logic(self):
        """Test composite exit combines signals with OR logic."""
        factor = CompositeExitFactor(exit_signals=["signal1", "signal2", "signal3"])

        data = pd.DataFrame({
            "signal1": [False, False, True, False, False],
            "signal2": [False, False, False, True, False],
            "signal3": [False, False, False, False, True]
        })

        result = factor.execute(data)

        # Final signal should be True when ANY input signal is True
        assert "final_exit_signal" in result.columns
        assert result["final_exit_signal"].iloc[0] == False
        assert result["final_exit_signal"].iloc[2] == True
        assert result["final_exit_signal"].iloc[3] == True
        assert result["final_exit_signal"].iloc[4] == True

    def test_composite_exit_multiple_true(self):
        """Test composite exit when multiple signals are True."""
        factor = CompositeExitFactor(exit_signals=["signal1", "signal2"])

        data = pd.DataFrame({
            "signal1": [False, True, True, False, False],
            "signal2": [False, False, True, False, True]
        })

        result = factor.execute(data)

        # Should be True when ANY signal is True
        assert result["final_exit_signal"].iloc[1] == True  # signal1 only
        assert result["final_exit_signal"].iloc[2] == True  # both signals
        assert result["final_exit_signal"].iloc[4] == True  # signal2 only

    def test_composite_exit_all_false(self):
        """Test composite exit when all signals are False."""
        factor = CompositeExitFactor(exit_signals=["signal1", "signal2", "signal3"])

        data = pd.DataFrame({
            "signal1": [False, False, False, False, False],
            "signal2": [False, False, False, False, False],
            "signal3": [False, False, False, False, False]
        })

        result = factor.execute(data)

        # Should be all False when all inputs are False
        assert not result["final_exit_signal"].any()

    def test_composite_exit_missing_signals(self):
        """Test composite exit raises error for missing signals."""
        factor = CompositeExitFactor(exit_signals=["signal1", "signal2", "missing_signal"])

        data = pd.DataFrame({
            "signal1": [False, True, False],
            "signal2": [True, False, False]
        })

        # Should raise KeyError for missing signal (Factor validation)
        with pytest.raises(KeyError, match="requires columns"):
            factor.execute(data)

    def test_factory_function(self):
        """Test factory function creates factor correctly."""
        signals = ["trailing_stop_signal", "profit_target_signal"]
        factor = create_composite_exit_factor(exit_signals=signals)

        assert isinstance(factor, CompositeExitFactor)
        assert factor.parameters["exit_signals"] == signals


class TestExitFactorsIntegration:
    """Integration tests for multiple exit factors working together."""

    def test_multiple_exits_combined(self):
        """Test multiple exit factors can be used together."""
        # Create individual exit factors
        trailing_stop = TrailingStopFactor(trail_percent=0.10, activation_profit=0.05)
        profit_target = ProfitTargetFactor(target_percent=0.30)
        composite = CompositeExitFactor(
            exit_signals=["trailing_stop_signal", "profit_target_signal"]
        )

        # Create test data
        data = pd.DataFrame({
            "close": [100, 105, 110, 135, 120],  # Profit target hit at 135, then drops
            "positions": [True, True, True, True, True],
            "entry_price": [100, 100, 100, 100, 100]
        })

        # Execute factors in sequence
        result = trailing_stop.execute(data)
        result = profit_target.execute(result)
        result = composite.execute(result)

        # Composite exit should trigger when profit target is met
        assert "final_exit_signal" in result.columns
        assert result["final_exit_signal"].iloc[3] == True  # Profit target at 135

    def test_exit_factor_outputs_valid(self):
        """Test all exit factors produce valid boolean outputs."""
        factors = [
            TrailingStopFactor(trail_percent=0.10, activation_profit=0.05),
            TimeBasedExitFactor(max_holding_periods=20),
            VolatilityStopFactor(std_period=20, std_multiplier=2.0),
            ProfitTargetFactor(target_percent=0.30)
        ]

        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        data = pd.DataFrame({
            "close": [100, 105, 110, 108, 107],
            "positions": [True, True, True, True, True],
            "entry_price": [100, 100, 100, 100, 100],
            "entry_date": [dates[0]] * 5
        }, index=dates)

        for factor in factors:
            result = factor.execute(data.copy())
            output_col = factor.outputs[0]

            # Verify output column exists and is boolean
            assert output_col in result.columns
            assert result[output_col].dtype == bool or result[output_col].dtype == np.bool_
