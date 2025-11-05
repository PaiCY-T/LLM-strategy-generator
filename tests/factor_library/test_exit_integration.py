"""
Integration Tests for Exit Factors
===================================

Tests exit factors integrated with momentum and turtle factors in realistic
strategy DAGs. Verifies exit factors work correctly with other factor types.

Test Coverage:
-------------
1. Exit factors with momentum factors
2. Exit factors with turtle factors
3. Multi-layered exit strategies
4. Complete strategy DAG with exits
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
)
from src.factor_library.momentum_factors import (
    MomentumFactor,
    MAFilterFactor,
)
from src.factor_library.turtle_factors import (
    ATRFactor,
    BreakoutFactor,
    ATRStopLossFactor,
)


class TestExitWithMomentumFactors:
    """Test exit factors integrated with momentum factors."""

    def test_exit_with_momentum_signal(self):
        """Test exit factors work with momentum entry signals."""
        # Create momentum entry signal
        momentum = MomentumFactor(momentum_period=3)
        ma_filter = MAFilterFactor(ma_periods=3)

        # Create exit factors
        profit_target = ProfitTargetFactor(target_percent=0.20)
        trailing_stop = TrailingStopFactor(trail_percent=0.10, activation_profit=0.05)

        # Test data: uptrend followed by profit taking
        data = pd.DataFrame({
            "close": [100, 102, 105, 108, 125, 123, 120]
        })

        # Execute momentum factors
        result = momentum.execute(data)
        result = ma_filter.execute(result)

        # Simulate positions based on momentum
        result["positions"] = result["momentum"] > 0
        result["entry_price"] = 100  # Simplification

        # Execute exit factors
        result = profit_target.execute(result)
        result = trailing_stop.execute(result)

        # Verify exit signals generated correctly
        assert "profit_target_signal" in result.columns
        assert "trailing_stop_signal" in result.columns
        # Profit target should trigger at 125 (25% profit)
        assert result["profit_target_signal"].iloc[4] == True

    def test_composite_exit_with_momentum(self):
        """Test composite exit with momentum strategy."""
        # Create momentum factors
        momentum = MomentumFactor(momentum_period=3)
        ma_filter = MAFilterFactor(ma_periods=3)

        # Create composite exit
        profit_target = ProfitTargetFactor(target_percent=0.15)
        time_exit = TimeBasedExitFactor(max_holding_periods=5)
        composite = CompositeExitFactor(
            exit_signals=["profit_target_signal", "time_exit_signal"]
        )

        # Test data
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        data = pd.DataFrame({
            "close": [100, 102, 104, 106, 108, 110, 112, 114, 116, 118]
        }, index=dates)

        # Execute factors
        result = momentum.execute(data)
        result = ma_filter.execute(result)
        result["positions"] = True
        result["entry_price"] = 100
        result["entry_date"] = dates[0]

        result = profit_target.execute(result)
        result = time_exit.execute(result)
        result = composite.execute(result)

        # Verify composite exit
        assert "final_exit_signal" in result.columns
        # Should trigger when either profit target or time exit is met
        assert result["final_exit_signal"].any()


class TestExitWithTurtleFactors:
    """Test exit factors integrated with turtle factors."""

    def test_exit_with_breakout_entry(self):
        """Test exit factors with turtle breakout entry."""
        # Create turtle entry factors
        atr = ATRFactor(atr_period=5)
        breakout = BreakoutFactor(entry_window=5)

        # Create exit factors
        profit_target = ProfitTargetFactor(target_percent=0.25)
        atr_stop = ATRStopLossFactor(atr_multiplier=2.0)

        # Test data: breakout followed by profit
        data = pd.DataFrame({
            "high": [100, 101, 102, 103, 104, 120, 125, 123],
            "low": [98, 99, 100, 101, 102, 118, 122, 120],
            "close": [99, 100, 101, 102, 103, 119, 124, 122]
        })

        # Execute turtle factors
        result = atr.execute(data)
        result = breakout.execute(result)

        # Simulate positions from breakout
        result["positions"] = result["breakout_signal"] != 0
        result["entry_price"] = 103  # Entry at breakout

        # Execute exit factors
        result = profit_target.execute(result)
        result = atr_stop.execute(result)

        # Verify exit factors work with turtle indicators
        assert "profit_target_signal" in result.columns
        assert "atr_stop_loss_signal" in result.columns

    def test_multi_exit_turtle_strategy(self):
        """Test multiple exit factors in turtle strategy."""
        # Create turtle factors
        atr = ATRFactor(atr_period=5)
        breakout = BreakoutFactor(entry_window=5)

        # Create multiple exit factors
        profit_target = ProfitTargetFactor(target_percent=0.30)
        atr_stop = ATRStopLossFactor(atr_multiplier=2.0)
        time_exit = TimeBasedExitFactor(max_holding_periods=10)

        # Combine exits
        composite = CompositeExitFactor(
            exit_signals=["profit_target_signal", "atr_stop_loss_signal", "time_exit_signal"]
        )

        # Test data
        dates = pd.date_range("2023-01-01", periods=15, freq="D")
        data = pd.DataFrame({
            "high": [100 + i for i in range(15)],
            "low": [98 + i for i in range(15)],
            "close": [99 + i for i in range(15)]
        }, index=dates)

        # Execute factors
        result = atr.execute(data)
        result = breakout.execute(result)
        result["positions"] = True
        result["entry_price"] = 100
        result["entry_date"] = dates[0]

        result = profit_target.execute(result)
        result = atr_stop.execute(result)
        result = time_exit.execute(result)
        result = composite.execute(result)

        # Verify all exits integrated correctly
        assert "final_exit_signal" in result.columns
        assert result["final_exit_signal"].any()


class TestCompleteStrategyDAG:
    """Test complete strategy DAG with entry and exit factors."""

    def test_full_momentum_strategy_with_exits(self):
        """Test complete momentum strategy with multiple exits."""
        # Entry factors
        momentum = MomentumFactor(momentum_period=5)
        ma_filter = MAFilterFactor(ma_periods=10)

        # Exit factors
        trailing_stop = TrailingStopFactor(trail_percent=0.12, activation_profit=0.08)
        profit_target = ProfitTargetFactor(target_percent=0.40)
        time_exit = TimeBasedExitFactor(max_holding_periods=20)

        # Composite exit
        composite = CompositeExitFactor(
            exit_signals=["trailing_stop_signal", "profit_target_signal", "time_exit_signal"]
        )

        # Realistic price data
        dates = pd.date_range("2023-01-01", periods=30, freq="D")
        np.random.seed(42)
        close_prices = [100]
        for _ in range(29):
            change = np.random.randn() * 2  # Random daily change
            close_prices.append(close_prices[-1] * (1 + change / 100))

        data = pd.DataFrame({
            "close": close_prices
        }, index=dates)

        # Execute complete strategy
        result = momentum.execute(data)
        result = ma_filter.execute(result)

        # Generate positions based on momentum and MA filter
        result["positions"] = (result["momentum"] > 0) & result["ma_filter"]
        result["entry_price"] = result["close"].where(result["positions"], method="ffill")
        result["entry_date"] = result.index[0]

        # Execute exit factors
        result = trailing_stop.execute(result)
        result = profit_target.execute(result)
        result = time_exit.execute(result)
        result = composite.execute(result)

        # Verify complete strategy execution
        assert all(col in result.columns for col in [
            "momentum", "ma_filter", "positions",
            "trailing_stop_signal", "profit_target_signal", "time_exit_signal",
            "final_exit_signal"
        ])

    def test_full_turtle_strategy_with_exits(self):
        """Test complete turtle strategy with multiple exits."""
        # Entry factors
        atr = ATRFactor(atr_period=10)
        breakout = BreakoutFactor(entry_window=20)

        # Exit factors
        atr_stop = ATRStopLossFactor(atr_multiplier=2.5)
        profit_target = ProfitTargetFactor(target_percent=0.50)
        volatility_stop = VolatilityStopFactor(std_period=20, std_multiplier=2.0)

        # Composite exit
        composite = CompositeExitFactor(
            exit_signals=["atr_stop_loss_signal", "profit_target_signal", "volatility_stop_signal"]
        )

        # Realistic OHLC data
        dates = pd.date_range("2023-01-01", periods=50, freq="D")
        np.random.seed(42)
        close_prices = [100]
        for _ in range(49):
            change = np.random.randn() * 1.5
            close_prices.append(close_prices[-1] * (1 + change / 100))

        data = pd.DataFrame({
            "high": [p * 1.02 for p in close_prices],
            "low": [p * 0.98 for p in close_prices],
            "close": close_prices
        }, index=dates)

        # Execute complete strategy
        result = atr.execute(data)
        result = breakout.execute(result)

        # Generate positions from breakout
        result["positions"] = result["breakout_signal"] == 1  # Long only
        result["entry_price"] = result["close"].iloc[0]
        result["entry_date"] = dates[0]

        # Execute exit factors
        result = atr_stop.execute(result)
        result = profit_target.execute(result)
        result = volatility_stop.execute(result)
        result = composite.execute(result)

        # Verify complete strategy execution
        assert all(col in result.columns for col in [
            "atr", "breakout_signal", "positions",
            "atr_stop_loss_signal", "profit_target_signal", "volatility_stop_signal",
            "final_exit_signal"
        ])


class TestExitFactorEdgeCases:
    """Test edge cases and boundary conditions for exit factors."""

    def test_exit_with_zero_entry_price(self):
        """Test exit factors handle zero entry price gracefully."""
        profit_target = ProfitTargetFactor(target_percent=0.20)

        data = pd.DataFrame({
            "close": [100, 110, 120],
            "positions": [True, True, True],
            "entry_price": [0, 0, 0]  # Zero entry price
        })

        result = profit_target.execute(data)

        # Should not trigger any signals (no division by zero)
        assert not result["profit_target_signal"].any()

    def test_exit_with_nan_values(self):
        """Test exit factors handle NaN values correctly."""
        trailing_stop = TrailingStopFactor(trail_percent=0.10, activation_profit=0.05)

        data = pd.DataFrame({
            "close": [100, np.nan, 110, 105, 100],
            "positions": [True, True, True, True, True],
            "entry_price": [100, 100, 100, 100, 100]
        })

        result = trailing_stop.execute(data)

        # Should handle NaN gracefully
        assert "trailing_stop_signal" in result.columns

    def test_exit_with_single_row(self):
        """Test exit factors with single row of data."""
        profit_target = ProfitTargetFactor(target_percent=0.20)

        data = pd.DataFrame({
            "close": [100],
            "positions": [True],
            "entry_price": [100]
        })

        result = profit_target.execute(data)

        # Should not fail with single row
        assert "profit_target_signal" in result.columns
        assert len(result) == 1

    def test_exit_with_alternating_positions(self):
        """Test exit factors with positions that alternate on/off."""
        time_exit = TimeBasedExitFactor(max_holding_periods=3)

        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        data = pd.DataFrame({
            "positions": [True, True, False, True, True, True, False, True, True, True],
            "entry_date": [dates[i] if data_positions[i] else None
                          for i, data_positions in enumerate([True, True, False, True, True, True, False, True, True, True])]
        }, index=dates)

        # Fix entry_date to align with positions
        entry_dates = []
        last_entry = None
        for i, pos in enumerate(data["positions"]):
            if pos:
                if i == 0 or not data["positions"].iloc[i-1]:
                    last_entry = dates[i]
                entry_dates.append(last_entry)
            else:
                entry_dates.append(None)
        data["entry_date"] = entry_dates

        result = time_exit.execute(data)

        # Should handle alternating positions
        assert "time_exit_signal" in result.columns


class TestExitFactorPerformance:
    """Test exit factor performance characteristics."""

    def test_exit_factors_preserve_data_structure(self):
        """Test exit factors preserve DataFrame structure."""
        factors = [
            TrailingStopFactor(trail_percent=0.10, activation_profit=0.05),
            ProfitTargetFactor(target_percent=0.30),
            VolatilityStopFactor(std_period=20, std_multiplier=2.0)
        ]

        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        data = pd.DataFrame({
            "close": [100 + i * 0.5 for i in range(100)],
            "positions": [True] * 100,
            "entry_price": [100] * 100
        }, index=dates)

        original_index = data.index.copy()
        original_columns = set(data.columns)

        for factor in factors:
            result = factor.execute(data.copy())

            # Verify structure preserved
            assert result.index.equals(original_index)
            assert original_columns.issubset(set(result.columns))

    def test_composite_exit_with_many_signals(self):
        """Test composite exit handles many input signals."""
        # Create many exit signals
        num_signals = 10
        signal_names = [f"signal_{i}" for i in range(num_signals)]

        data = pd.DataFrame({
            name: [False] * 100 for name in signal_names
        })

        # Set some signals to True at different points
        for i, name in enumerate(signal_names):
            data.loc[i * 10, name] = True

        composite = CompositeExitFactor(exit_signals=signal_names)
        result = composite.execute(data)

        # Verify composite handles many signals
        assert "final_exit_signal" in result.columns
        assert result["final_exit_signal"].sum() == num_signals
