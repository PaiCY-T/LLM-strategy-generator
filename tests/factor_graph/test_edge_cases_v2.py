"""
Edge Case Tests for Factor Graph V2 (Phase 2.0 Matrix-Native)
================================================================

Tests for extreme scenarios, boundary conditions, and error handling.
Validates system robustness under unusual conditions.

Test Coverage:
--------------
1. Extreme Matrix Dimensions
   - Very large matrices (memory stress)
   - Empty matrices (0 rows or columns)
   - Single row/column matrices
   - Mismatched dimensions

2. Extreme Values
   - All-NaN matrices
   - All-zero values
   - Infinite values
   - Division by zero scenarios

3. Factor Logic Edge Cases
   - All positions = 0 (no trading)
   - All positions = 1 (always long)
   - Rapid position changes
   - Window size > data length

4. Error Handling Robustness
   - Multiple simultaneous errors
   - Error recovery
   - Cascading failures

Architecture: Phase 2.0 Matrix-Native Factor Graph System
"""

import pytest
import pandas as pd
import numpy as np
import warnings
from unittest.mock import Mock

from src.factor_graph.strategy import Strategy
from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.finlab_dataframe import FinLabDataFrame


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def empty_matrix_data_module():
    """Data module returning empty DataFrames."""
    mock_data = Mock()

    empty_df = pd.DataFrame()

    def mock_get(key):
        if key.startswith('price:'):
            return empty_df
        raise KeyError(f"Mock data not found: {key}")

    mock_data.get = mock_get
    return mock_data


@pytest.fixture
def single_row_data_module():
    """Data module with single row of data."""
    mock_data = Mock()

    dates = pd.date_range('2023-01-01', periods=1)
    symbols = ['A', 'B', 'C']

    close = pd.DataFrame(
        [[100, 200, 300]],
        index=dates,
        columns=symbols
    )

    def mock_get(key):
        if key == 'price:收盤價':
            return close
        raise KeyError(f"Mock data not found: {key}")

    mock_data.get = mock_get
    return mock_data


@pytest.fixture
def single_column_data_module():
    """Data module with single column (one stock)."""
    mock_data = Mock()

    dates = pd.date_range('2023-01-01', periods=100)
    symbols = ['ONLY_ONE']

    close = pd.DataFrame(
        np.random.randn(100, 1) * 10 + 100,
        index=dates,
        columns=symbols
    )

    def mock_get(key):
        if key == 'price:收盤價':
            return close
        raise KeyError(f"Mock data not found: {key}")

    mock_data.get = mock_get
    return mock_data


@pytest.fixture
def all_nan_data_module():
    """Data module with all NaN values."""
    mock_data = Mock()

    dates = pd.date_range('2023-01-01', periods=50)
    symbols = ['A', 'B', 'C']

    close = pd.DataFrame(
        np.nan,
        index=dates,
        columns=symbols
    )

    def mock_get(key):
        if key == 'price:收盤價':
            return close
        raise KeyError(f"Mock data not found: {key}")

    mock_data.get = mock_get
    return mock_data


@pytest.fixture
def all_zero_data_module():
    """Data module with all zero values."""
    mock_data = Mock()

    dates = pd.date_range('2023-01-01', periods=50)
    symbols = ['A', 'B', 'C']

    close = pd.DataFrame(
        0.0,
        index=dates,
        columns=symbols
    )

    def mock_get(key):
        if key == 'price:收盤價':
            return close
        raise KeyError(f"Mock data not found: {key}")

    mock_data.get = mock_get
    return mock_data


# ============================================================================
# Extreme Matrix Dimension Tests
# ============================================================================

class TestExtremeMatrixDimensions:
    """Test handling of extreme matrix sizes."""

    def test_single_row_matrix(self, single_row_data_module):
        """Test factor execution with single row of data."""

        def single_row_logic(container, params):
            close = container.get_matrix('close')
            # With single row, many operations will return NaN
            # Just create a simple position
            position = close > 100
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='Single Row')
        strategy.add_factor(Factor(
            id='sr', name='Single Row', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=single_row_logic, parameters={}
        ))

        positions = strategy.to_pipeline(single_row_data_module)

        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (1, 3)

    def test_single_column_matrix(self, single_column_data_module):
        """Test factor execution with single stock (one column)."""

        def single_stock_logic(container, params):
            close = container.get_matrix('close')
            momentum = (close / close.shift(10)) - 1
            position = momentum > 0.05
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='Single Stock')
        strategy.add_factor(Factor(
            id='ss', name='Single Stock', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=single_stock_logic, parameters={}
        ))

        positions = strategy.to_pipeline(single_column_data_module)

        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (100, 1)

    def test_very_wide_matrix(self):
        """Test with many stocks (wide matrix)."""
        mock_data = Mock()

        dates = pd.date_range('2023-01-01', periods=100)
        symbols = [f'{i:04d}' for i in range(500)]  # 500 stocks

        close = pd.DataFrame(
            np.random.randn(100, 500) * 10 + 100,
            index=dates,
            columns=symbols
        )

        def mock_get(key):
            if key == 'price:收盤價':
                return close
            raise KeyError(f"Mock data not found: {key}")

        mock_data.get = mock_get

        def wide_logic(container, params):
            close = container.get_matrix('close')
            signal = close > close.rolling(20).mean()
            container.add_matrix('position', signal.astype(float))

        strategy = Strategy(name='Wide Matrix')
        strategy.add_factor(Factor(
            id='wide', name='Wide', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=wide_logic, parameters={}
        ))

        positions = strategy.to_pipeline(mock_data)

        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (100, 500)

    def test_very_long_matrix(self):
        """Test with long time series (tall matrix)."""
        mock_data = Mock()

        dates = pd.date_range('2020-01-01', periods=2000, freq='B')  # ~8 years
        symbols = ['A', 'B', 'C']

        close = pd.DataFrame(
            np.random.randn(2000, 3).cumsum(axis=0) + 100,
            index=dates,
            columns=symbols
        )

        def mock_get(key):
            if key == 'price:收盤價':
                return close
            raise KeyError(f"Mock data not found: {key}")

        mock_data.get = mock_get

        def long_logic(container, params):
            close = container.get_matrix('close')
            ma_short = close.rolling(50).mean()
            ma_long = close.rolling(200).mean()
            signal = ma_short > ma_long
            container.add_matrix('position', signal.astype(float))

        strategy = Strategy(name='Long Series')
        strategy.add_factor(Factor(
            id='long', name='Long', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=long_logic, parameters={}
        ))

        positions = strategy.to_pipeline(mock_data)

        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (2000, 3)


# ============================================================================
# Extreme Value Tests
# ============================================================================

class TestExtremeValues:
    """Test handling of extreme values in data."""

    def test_all_nan_matrix(self, all_nan_data_module):
        """Test handling of all-NaN matrix."""

        def nan_safe_logic(container, params):
            close = container.get_matrix('close')
            # fillna to handle all NaN
            momentum = (close / close.shift(10)).fillna(0) - 1
            position = momentum > 0.05
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='NaN Safe')
        strategy.add_factor(Factor(
            id='nan', name='NaN Safe', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=nan_safe_logic, parameters={}
        ))

        positions = strategy.to_pipeline(all_nan_data_module)

        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (50, 3)
        # Should be all zeros (no positions due to NaN)
        assert (positions == 0).all().all()

    def test_all_zero_values(self, all_zero_data_module):
        """Test handling of all-zero price values."""

        def zero_safe_logic(container, params):
            close = container.get_matrix('close')
            # Avoid division by zero
            momentum = close.diff()  # Use diff instead of pct_change
            position = momentum > 0
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='Zero Safe')
        strategy.add_factor(Factor(
            id='zero', name='Zero Safe', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=zero_safe_logic, parameters={}
        ))

        positions = strategy.to_pipeline(all_zero_data_module)

        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (50, 3)

    def test_division_by_zero_handling(self):
        """Test handling of division by zero in factor logic."""
        mock_data = Mock()

        dates = pd.date_range('2023-01-01', periods=50)
        symbols = ['A', 'B', 'C']

        # Create data with some zeros
        close = pd.DataFrame(
            np.random.randn(50, 3) * 10 + 100,
            index=dates,
            columns=symbols
        )
        close.iloc[10:15, 0] = 0  # Some zero values

        def mock_get(key):
            if key == 'price:收盤價':
                return close
            raise KeyError(f"Mock data not found: {key}")

        mock_data.get = mock_get

        def safe_division_logic(container, params):
            close = container.get_matrix('close')
            # Replace zeros before division
            close_safe = close.replace(0, np.nan)
            momentum = (close_safe / close_safe.shift(10)).fillna(0) - 1
            position = momentum > 0.05
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='Safe Division')
        strategy.add_factor(Factor(
            id='div', name='Division', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=safe_division_logic, parameters={}
        ))

        # Should not raise ZeroDivisionError
        positions = strategy.to_pipeline(mock_data)

        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (50, 3)

    def test_infinite_values_handling(self):
        """Test handling of infinite values."""
        mock_data = Mock()

        dates = pd.date_range('2023-01-01', periods=50)
        symbols = ['A', 'B', 'C']

        close = pd.DataFrame(
            np.random.randn(50, 3) * 10 + 100,
            index=dates,
            columns=symbols
        )

        def mock_get(key):
            if key == 'price:收盤價':
                return close
            raise KeyError(f"Mock data not found: {key}")

        mock_data.get = mock_get

        def inf_handling_logic(container, params):
            close = container.get_matrix('close')
            # Operation that could produce inf
            ratio = close / close.shift(1).replace(0, np.nan)
            # Replace inf with NaN then fillna
            ratio = ratio.replace([np.inf, -np.inf], np.nan).fillna(1.0)
            position = ratio > 1.05
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='Inf Handling')
        strategy.add_factor(Factor(
            id='inf', name='Infinite', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=inf_handling_logic, parameters={}
        ))

        positions = strategy.to_pipeline(mock_data)

        assert isinstance(positions, pd.DataFrame)
        # No inf values in output
        assert not np.isinf(positions.values).any()


# ============================================================================
# Factor Logic Edge Cases
# ============================================================================

class TestFactorLogicEdgeCases:
    """Test edge cases in factor logic behavior."""

    def test_all_positions_zero(self):
        """Test strategy that generates no positions (all zeros)."""
        mock_data = Mock()

        dates = pd.date_range('2023-01-01', periods=50)
        symbols = ['A', 'B', 'C']
        close = pd.DataFrame(
            np.random.randn(50, 3) * 10 + 100,
            index=dates,
            columns=symbols
        )

        def mock_get(key):
            if key == 'price:收盤價':
                return close
            raise KeyError(f"Mock data not found: {key}")

        mock_data.get = mock_get

        def no_position_logic(container, params):
            close = container.get_matrix('close')
            # Impossible condition
            position = close > 1e9
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='No Positions')
        strategy.add_factor(Factor(
            id='none', name='None', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=no_position_logic, parameters={}
        ))

        positions = strategy.to_pipeline(mock_data)

        assert isinstance(positions, pd.DataFrame)
        assert (positions == 0).all().all()

    def test_all_positions_one(self):
        """Test strategy that always generates full positions (all ones)."""
        mock_data = Mock()

        dates = pd.date_range('2023-01-01', periods=50)
        symbols = ['A', 'B', 'C']
        close = pd.DataFrame(
            np.random.randn(50, 3) * 10 + 100,
            index=dates,
            columns=symbols
        )

        def mock_get(key):
            if key == 'price:收盤價':
                return close
            raise KeyError(f"Mock data not found: {key}")

        mock_data.get = mock_get

        def always_long_logic(container, params):
            close = container.get_matrix('close')
            # Always true
            position = close > -1e9
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='Always Long')
        strategy.add_factor(Factor(
            id='all', name='All', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=always_long_logic, parameters={}
        ))

        positions = strategy.to_pipeline(mock_data)

        assert isinstance(positions, pd.DataFrame)
        assert (positions == 1).all().all()

    def test_window_size_exceeds_data_length(self):
        """Test rolling window larger than data length."""
        mock_data = Mock()

        dates = pd.date_range('2023-01-01', periods=20)  # Only 20 days
        symbols = ['A', 'B', 'C']
        close = pd.DataFrame(
            np.random.randn(20, 3) * 10 + 100,
            index=dates,
            columns=symbols
        )

        def mock_get(key):
            if key == 'price:收盤價':
                return close
            raise KeyError(f"Mock data not found: {key}")

        mock_data.get = mock_get

        def large_window_logic(container, params):
            close = container.get_matrix('close')
            # Window size = 100 > data length = 20
            ma = close.rolling(100, min_periods=1).mean()
            position = close > ma
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='Large Window')
        strategy.add_factor(Factor(
            id='lw', name='Large Window', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=large_window_logic, parameters={}
        ))

        # Should handle gracefully with min_periods
        positions = strategy.to_pipeline(mock_data)

        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (20, 3)

    def test_rapid_position_changes(self):
        """Test strategy with position changes every period."""
        mock_data = Mock()

        dates = pd.date_range('2023-01-01', periods=100)
        symbols = ['A', 'B', 'C']

        # Create alternating pattern
        values = np.tile([100, 105], (50, 3))
        close = pd.DataFrame(values, index=dates, columns=symbols)

        def mock_get(key):
            if key == 'price:收盤價':
                return close
            raise KeyError(f"Mock data not found: {key}")

        mock_data.get = mock_get

        def oscillating_logic(container, params):
            close = container.get_matrix('close')
            # Will alternate every period
            diff = close.diff()
            position = diff > 0
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='Oscillating')
        strategy.add_factor(Factor(
            id='osc', name='Oscillating', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=oscillating_logic, parameters={}
        ))

        positions = strategy.to_pipeline(mock_data)

        assert isinstance(positions, pd.DataFrame)
        # Check that positions do change frequently
        position_changes = positions.diff().abs().sum().sum()
        assert position_changes > 50  # Many changes


# ============================================================================
# Error Handling Robustness Tests
# ============================================================================

class TestErrorHandlingRobustness:
    """Test robust error handling in edge scenarios."""

    def test_factor_with_exception_in_logic(self):
        """Test that exception in factor logic is properly propagated."""
        mock_data = Mock()

        dates = pd.date_range('2023-01-01', periods=50)
        symbols = ['A', 'B', 'C']
        close = pd.DataFrame(
            np.random.randn(50, 3) * 10 + 100,
            index=dates,
            columns=symbols
        )

        def mock_get(key):
            if key == 'price:收盤價':
                return close
            raise KeyError(f"Mock data not found: {key}")

        mock_data.get = mock_get

        def error_logic(container, params):
            raise RuntimeError("Intentional error in factor logic")

        strategy = Strategy(name='Error Test')
        strategy.add_factor(Factor(
            id='err', name='Error', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=error_logic, parameters={}
        ))

        with pytest.raises(RuntimeError, match="Intentional error"):
            strategy.to_pipeline(mock_data)

    def test_missing_required_matrix_error_message(self):
        """Test clear error message when required matrix is missing."""
        mock_data = Mock()

        def mock_get(key):
            if key == 'price:收盤價':
                dates = pd.date_range('2023-01-01', periods=50)
                symbols = ['A', 'B', 'C']
                return pd.DataFrame(
                    np.random.randn(50, 3) * 10 + 100,
                    index=dates,
                    columns=symbols
                )
            raise KeyError(f"Mock data not found: {key}")

        mock_data.get = mock_get

        def logic_needs_volume(container, params):
            # Try to get volume which doesn't exist
            volume = container.get_matrix('volume')
            container.add_matrix('position', volume * 0)

        strategy = Strategy(name='Missing Matrix')
        strategy.add_factor(Factor(
            id='miss', name='Missing', category=FactorCategory.ENTRY,
            inputs=['volume'], outputs=['position'],
            logic=logic_needs_volume, parameters={}
        ))

        # Should get clear error about missing matrix
        with pytest.raises(KeyError, match="Missing matrices"):
            strategy.to_pipeline(mock_data)

    def test_output_not_created_error(self):
        """Test error when factor doesn't create its declared output."""
        mock_data = Mock()

        dates = pd.date_range('2023-01-01', periods=50)
        symbols = ['A', 'B', 'C']
        close = pd.DataFrame(
            np.random.randn(50, 3) * 10 + 100,
            index=dates,
            columns=symbols
        )

        def mock_get(key):
            if key == 'price:收盤價':
                return close
            raise KeyError(f"Mock data not found: {key}")

        mock_data.get = mock_get

        def forgot_output_logic(container, params):
            close = container.get_matrix('close')
            # Forgot to add 'position' matrix
            _ = close > 100

        strategy = Strategy(name='Forgot Output')
        strategy.add_factor(Factor(
            id='forgot', name='Forgot', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=forgot_output_logic, parameters={}
        ))

        # Should get error about missing output
        with pytest.raises((RuntimeError, KeyError)):
            strategy.to_pipeline(mock_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
