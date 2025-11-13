"""
Test Suite for Exit Factors (Phase 2.0 Matrix-Native)
=====================================================

Comprehensive tests for exit strategy factors using FinLabDataFrame container.
Tests cover trailing stop, time-based exit, volatility stop, profit target, and composite exit.

Test Coverage:
--------------
1. Component Tests - Logic Function Calculations
   - trailing_stop_logic: Highest price tracking and trailing stop
   - time_based_exit_logic: Holding period calculation
   - volatility_stop_logic: Volatility-based stop levels
   - profit_target_logic: Fixed profit target exits
   - composite_exit_logic: Multi-signal OR combination

2. Stateful Logic Tests
   - Position run tracking
   - Highest price updates
   - Holding period counting
   - Entry/exit detection

Architecture: Phase 2.0 Matrix-Native Factor Graph System
"""

import pytest
import pandas as pd
import numpy as np

from src.factor_graph.finlab_dataframe import FinLabDataFrame
from src.factor_library.exit_factors import (
    _trailing_stop_logic,
    _time_based_exit_logic,
    _volatility_stop_logic,
    _profit_target_logic,
    _composite_exit_logic,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_position_data():
    """Create sample position data with entry prices."""
    dates = pd.date_range('2023-01-01', periods=20)
    symbols = ['2330', '2317']

    # Create price data with trend
    close = pd.DataFrame({
        '2330': [100, 102, 105, 108, 110, 109, 107, 105, 103, 101,
                 100, 102, 104, 106, 108, 110, 112, 114, 116, 118],
        '2317': [200, 202, 204, 206, 208, 210, 212, 214, 216, 218,
                 220, 222, 224, 226, 228, 230, 232, 234, 236, 238]
    }, index=dates)

    # Position: 1 for long, 0 for no position
    positions = pd.DataFrame({
        '2330': [1, 1, 1, 1, 1, 1, 1, 1, 0, 0,
                 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        '2317': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]
    }, index=dates)

    # Entry price (price when position started)
    entry_price = pd.DataFrame({
        '2330': [100] * 8 + [0, 0] + [100] * 10,
        '2317': [200] * 10 + [0, 0] + [224] * 8
    }, index=dates)

    return {'close': close, 'positions': positions, 'entry_price': entry_price}


@pytest.fixture
def sample_container_positions(sample_position_data):
    """Create FinLabDataFrame container with position data."""
    container = FinLabDataFrame()
    container.add_matrix('close', sample_position_data['close'])
    container.add_matrix('positions', sample_position_data['positions'])
    container.add_matrix('entry_price', sample_position_data['entry_price'])
    return container


# ============================================================================
# Component Tests - Trailing Stop Logic
# ============================================================================

class TestTrailingStopLogic:
    """Test trailing_stop_logic function with stateful highest price tracking."""

    def test_trailing_stop_basic_execution(self, sample_container_positions):
        """Test basic trailing stop execution."""
        parameters = {'trail_percent': 0.10, 'activation_profit': 0.05}

        # Execute logic
        _trailing_stop_logic(sample_container_positions, parameters)

        # Check output exists
        assert sample_container_positions.has_matrix('trailing_stop_signal')

        # Get result
        trailing_stop = sample_container_positions.get_matrix('trailing_stop_signal')
        close = sample_container_positions.get_matrix('close')

        # Verify shape
        assert trailing_stop.shape == close.shape

        # Verify boolean output
        assert trailing_stop.dtypes.apply(lambda x: x == bool or x == 'bool').all()

    def test_trailing_stop_activation(self):
        """Test trailing stop activation after profit threshold."""
        dates = pd.date_range('2023-01-01', periods=10)
        symbols = ['2330']

        # Price rises 15%, then falls 12% (should trigger 10% trailing stop)
        close = pd.DataFrame(
            [100, 105, 110, 115, 115, 115, 110, 105, 100, 95],
            index=dates,
            columns=symbols
        )
        positions = pd.DataFrame([1] * 10, index=dates, columns=symbols)
        entry_price = pd.DataFrame([100] * 10, index=dates, columns=symbols)

        container = FinLabDataFrame()
        container.add_matrix('close', close)
        container.add_matrix('positions', positions)
        container.add_matrix('entry_price', entry_price)

        parameters = {'trail_percent': 0.10, 'activation_profit': 0.05}
        _trailing_stop_logic(container, parameters)

        trailing_stop = container.get_matrix('trailing_stop_signal')

        # Should trigger around row 7-8 when price falls from 115 peak
        # Highest = 115, Stop level = 115 * 0.9 = 103.5
        # Price at row 7 = 105 (ok), row 8 = 100 (trigger)
        assert (trailing_stop.iloc[8:] == True).any().any()

    def test_trailing_stop_no_activation_without_profit(self):
        """Test trailing stop doesn't activate below profit threshold."""
        dates = pd.date_range('2023-01-01', periods=10)
        symbols = ['2330']

        # Price only rises 3% (below 5% activation threshold)
        close = pd.DataFrame(
            [100, 101, 102, 103, 102, 101, 100, 99, 98, 97],
            index=dates,
            columns=symbols
        )
        positions = pd.DataFrame([1] * 10, index=dates, columns=symbols)
        entry_price = pd.DataFrame([100] * 10, index=dates, columns=symbols)

        container = FinLabDataFrame()
        container.add_matrix('close', close)
        container.add_matrix('positions', positions)
        container.add_matrix('entry_price', entry_price)

        parameters = {'trail_percent': 0.10, 'activation_profit': 0.05}
        _trailing_stop_logic(container, parameters)

        trailing_stop = container.get_matrix('trailing_stop_signal')

        # Should NOT trigger because never reached 5% profit
        assert not trailing_stop.any().any()


# ============================================================================
# Component Tests - Time-Based Exit Logic
# ============================================================================

class TestTimeBasedExitLogic:
    """Test time_based_exit_logic function with holding period tracking."""

    def test_time_exit_basic_execution(self, sample_container_positions):
        """Test basic time-based exit execution."""
        dates = sample_container_positions.get_matrix('close').index
        entry_date = pd.DataFrame(
            dates[0],
            index=dates,
            columns=['2330', '2317']
        )
        sample_container_positions.add_matrix('entry_date', entry_date)

        parameters = {'max_holding_periods': 10}

        # Execute logic
        _time_based_exit_logic(sample_container_positions, parameters)

        # Check output exists
        assert sample_container_positions.has_matrix('time_exit_signal')

        time_exit = sample_container_positions.get_matrix('time_exit_signal')
        close = sample_container_positions.get_matrix('close')

        # Verify shape
        assert time_exit.shape == close.shape

    def test_time_exit_with_datetime_index(self):
        """Test time exit with datetime index (date calculation)."""
        dates = pd.date_range('2023-01-01', periods=25)
        symbols = ['2330']

        positions = pd.DataFrame([1] * 25, index=dates, columns=symbols)
        entry_date = pd.DataFrame([dates[0]] * 25, index=dates, columns=symbols)

        container = FinLabDataFrame()
        container.add_matrix('positions', positions)
        container.add_matrix('entry_date', entry_date)

        parameters = {'max_holding_periods': 20}
        _time_based_exit_logic(container, parameters)

        time_exit = container.get_matrix('time_exit_signal')

        # After 20 days, should trigger exit
        assert (time_exit.iloc[20:] == True).any().any()


# ============================================================================
# Component Tests - Volatility Stop Logic
# ============================================================================

class TestVolatilityStopLogic:
    """Test volatility_stop_logic function with std-based calculations."""

    def test_volatility_stop_calculation(self, sample_container_positions):
        """Test volatility stop calculation."""
        parameters = {'std_period': 10, 'std_multiplier': 2.0}

        # Execute logic
        _volatility_stop_logic(sample_container_positions, parameters)

        # Check output exists
        assert sample_container_positions.has_matrix('volatility_stop_signal')

        volatility_stop = sample_container_positions.get_matrix('volatility_stop_signal')
        close = sample_container_positions.get_matrix('close')

        # Verify shape
        assert volatility_stop.shape == close.shape

        # Verify boolean output
        assert volatility_stop.dtypes.apply(lambda x: x == bool or x == 'bool').all()

    def test_volatility_stop_trigger(self):
        """Test volatility stop triggering on large price drop."""
        dates = pd.date_range('2023-01-01', periods=25)
        symbols = ['2330']

        # Stable prices, then sudden drop
        close = pd.DataFrame(
            [100] * 20 + [80, 75, 70, 65, 60],
            index=dates,
            columns=symbols
        )
        positions = pd.DataFrame([1] * 25, index=dates, columns=symbols)
        entry_price = pd.DataFrame([100] * 25, index=dates, columns=symbols)

        container = FinLabDataFrame()
        container.add_matrix('close', close)
        container.add_matrix('positions', positions)
        container.add_matrix('entry_price', entry_price)

        parameters = {'std_period': 10, 'std_multiplier': 2.0}
        _volatility_stop_logic(container, parameters)

        volatility_stop = container.get_matrix('volatility_stop_signal')

        # Should trigger after large drop
        assert (volatility_stop.iloc[20:] == True).any().any()


# ============================================================================
# Component Tests - Profit Target Logic
# ============================================================================

class TestProfitTargetLogic:
    """Test profit_target_logic function with vectorized calculations."""

    def test_profit_target_calculation(self, sample_container_positions):
        """Test profit target calculation."""
        parameters = {'target_percent': 0.20}

        # Execute logic
        _profit_target_logic(sample_container_positions, parameters)

        # Check output exists
        assert sample_container_positions.has_matrix('profit_target_signal')

        profit_target = sample_container_positions.get_matrix('profit_target_signal')
        close = sample_container_positions.get_matrix('close')

        # Verify shape
        assert profit_target.shape == close.shape

        # Verify boolean output
        assert profit_target.dtypes.apply(lambda x: x == bool or x == 'bool').all()

    def test_profit_target_trigger(self):
        """Test profit target triggering when target reached."""
        dates = pd.date_range('2023-01-01', periods=10)
        symbols = ['2330']

        # Price rises 25% (above 20% target)
        close = pd.DataFrame(
            [100, 105, 110, 115, 120, 125, 125, 125, 125, 125],
            index=dates,
            columns=symbols
        )
        positions = pd.DataFrame([1] * 10, index=dates, columns=symbols)
        entry_price = pd.DataFrame([100] * 10, index=dates, columns=symbols)

        container = FinLabDataFrame()
        container.add_matrix('close', close)
        container.add_matrix('positions', positions)
        container.add_matrix('entry_price', entry_price)

        parameters = {'target_percent': 0.20}
        _profit_target_logic(container, parameters)

        profit_target = container.get_matrix('profit_target_signal')

        # Should trigger around row 4 when price = 120 (20% profit)
        assert (profit_target.iloc[4:] == True).any().any()

    def test_profit_target_no_trigger_below_threshold(self):
        """Test profit target doesn't trigger below threshold."""
        dates = pd.date_range('2023-01-01', periods=10)
        symbols = ['2330']

        # Price only rises 15% (below 20% target)
        close = pd.DataFrame(
            [100, 105, 110, 115, 115, 115, 115, 115, 115, 115],
            index=dates,
            columns=symbols
        )
        positions = pd.DataFrame([1] * 10, index=dates, columns=symbols)
        entry_price = pd.DataFrame([100] * 10, index=dates, columns=symbols)

        container = FinLabDataFrame()
        container.add_matrix('close', close)
        container.add_matrix('positions', positions)
        container.add_matrix('entry_price', entry_price)

        parameters = {'target_percent': 0.20}
        _profit_target_logic(container, parameters)

        profit_target = container.get_matrix('profit_target_signal')

        # Should NOT trigger
        assert not profit_target.any().any()


# ============================================================================
# Component Tests - Composite Exit Logic
# ============================================================================

class TestCompositeExitLogic:
    """Test composite_exit_logic function with OR combination."""

    def test_composite_exit_or_logic(self):
        """Test composite exit combines signals with OR logic."""
        dates = pd.date_range('2023-01-01', periods=10)
        symbols = ['2330', '2317']

        # Create different exit signals
        trailing_stop = pd.DataFrame(
            [[False, False], [True, False], [False, False], [False, False], [False, False],
             [False, False], [False, False], [False, False], [False, False], [False, False]],
            index=dates,
            columns=symbols
        )
        time_exit = pd.DataFrame(
            [[False, False], [False, False], [False, True], [False, False], [False, False],
             [False, False], [False, False], [False, False], [False, False], [False, False]],
            index=dates,
            columns=symbols
        )
        profit_target = pd.DataFrame(
            [[False, False], [False, False], [False, False], [False, False], [True, False],
             [False, False], [False, False], [False, False], [False, False], [False, False]],
            index=dates,
            columns=symbols
        )

        container = FinLabDataFrame()
        container.add_matrix('trailing_stop_signal', trailing_stop)
        container.add_matrix('time_exit_signal', time_exit)
        container.add_matrix('profit_target_signal', profit_target)

        parameters = {'exit_signals': ['trailing_stop_signal', 'time_exit_signal', 'profit_target_signal']}
        _composite_exit_logic(container, parameters)

        final_exit = container.get_matrix('final_exit_signal')

        # Verify shape
        assert final_exit.shape == trailing_stop.shape

        # Check OR logic
        # Row 1, col 0: trailing_stop=True → final=True
        assert final_exit.iloc[1, 0] == True

        # Row 2, col 1: time_exit=True → final=True
        assert final_exit.iloc[2, 1] == True

        # Row 4, col 0: profit_target=True → final=True
        assert final_exit.iloc[4, 0] == True

        # Row 0: all False → final=False
        assert final_exit.iloc[0, 0] == False
        assert final_exit.iloc[0, 1] == False

    def test_composite_exit_missing_signal_error(self):
        """Test composite exit raises error for missing signals."""
        dates = pd.date_range('2023-01-01', periods=10)
        symbols = ['2330']

        trailing_stop = pd.DataFrame(False, index=dates, columns=symbols)

        container = FinLabDataFrame()
        container.add_matrix('trailing_stop_signal', trailing_stop)

        # Request signal that doesn't exist
        parameters = {'exit_signals': ['trailing_stop_signal', 'nonexistent_signal']}

        with pytest.raises(ValueError, match="Missing exit signal matrices"):
            _composite_exit_logic(container, parameters)


# ============================================================================
# Integration Tests
# ============================================================================

class TestExitFactorsIntegration:
    """Test integration of multiple exit factors."""

    def test_full_exit_pipeline(self, sample_container_positions):
        """Test executing full exit factor pipeline."""
        # Add entry_date for time exit
        dates = sample_container_positions.get_matrix('close').index
        entry_date = pd.DataFrame(
            dates[0],
            index=dates,
            columns=['2330', '2317']
        )
        sample_container_positions.add_matrix('entry_date', entry_date)

        # Execute all exit factors
        _trailing_stop_logic(sample_container_positions, {'trail_percent': 0.10, 'activation_profit': 0.05})
        _time_based_exit_logic(sample_container_positions, {'max_holding_periods': 15})
        _volatility_stop_logic(sample_container_positions, {'std_period': 10, 'std_multiplier': 2.0})
        _profit_target_logic(sample_container_positions, {'target_percent': 0.30})

        # Composite exit
        _composite_exit_logic(
            sample_container_positions,
            {'exit_signals': ['trailing_stop_signal', 'time_exit_signal', 'volatility_stop_signal', 'profit_target_signal']}
        )

        # Verify all outputs exist
        assert sample_container_positions.has_matrix('trailing_stop_signal')
        assert sample_container_positions.has_matrix('time_exit_signal')
        assert sample_container_positions.has_matrix('volatility_stop_signal')
        assert sample_container_positions.has_matrix('profit_target_signal')
        assert sample_container_positions.has_matrix('final_exit_signal')

        # Verify all outputs have correct shape
        original_shape = sample_container_positions.get_matrix('close').shape
        assert sample_container_positions.get_matrix('trailing_stop_signal').shape == original_shape
        assert sample_container_positions.get_matrix('time_exit_signal').shape == original_shape
        assert sample_container_positions.get_matrix('volatility_stop_signal').shape == original_shape
        assert sample_container_positions.get_matrix('profit_target_signal').shape == original_shape
        assert sample_container_positions.get_matrix('final_exit_signal').shape == original_shape


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
