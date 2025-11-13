"""
Test Suite for Momentum Factors (Phase 2.0 Matrix-Native)
==========================================================

Comprehensive tests for momentum factors using FinLabDataFrame container.
Tests cover logic function execution with Dates×Symbols matrices.

Test Coverage:
--------------
1. Component Tests - Logic Function Calculations
   - momentum_logic: Rolling mean of returns calculation
   - ma_filter_logic: Moving average filter calculation
   - revenue_catalyst_logic: Revenue acceleration detection
   - earnings_catalyst_logic: ROE improvement detection

2. Matrix Operations Tests
   - Dates×Symbols shape preservation
   - Multi-symbol vectorization
   - NaN value handling
   - Edge cases (insufficient data, single symbol)

3. Container Integration Tests
   - get_matrix() retrieval
   - add_matrix() output
   - Shape validation
   - Error messages

Architecture: Phase 2.0 Matrix-Native Factor Graph System
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from src.factor_graph.finlab_dataframe import FinLabDataFrame
from src.factor_library.momentum_factors import (
    _momentum_logic,
    _ma_filter_logic,
    _revenue_catalyst_logic,
    _earnings_catalyst_logic,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_matrix_data():
    """Create sample Dates×Symbols matrix data for testing."""
    dates = pd.date_range('2023-01-01', periods=20)
    symbols = ['2330', '2317', '2454']  # 3 stocks

    # Create price matrix with upward trend
    np.random.seed(42)
    base_prices = np.array([100, 200, 150])  # Different starting prices
    price_changes = np.random.randn(20, 3) * 2  # Random changes

    close_matrix = pd.DataFrame(
        base_prices + np.cumsum(price_changes, axis=0),
        index=dates,
        columns=symbols
    )

    return close_matrix


@pytest.fixture
def sample_container(sample_matrix_data):
    """Create FinLabDataFrame container with sample data."""
    container = FinLabDataFrame()
    container.add_matrix('close', sample_matrix_data)
    return container


# ============================================================================
# Component Tests - Momentum Logic
# ============================================================================

class TestMomentumLogic:
    """Test momentum_logic function with matrix operations."""

    def test_momentum_calculation_correctness(self, sample_container):
        """Test momentum calculation matches expected formula."""
        parameters = {'momentum_period': 5}

        # Execute logic
        _momentum_logic(sample_container, parameters)

        # Check output exists
        assert sample_container.has_matrix('momentum')

        # Get result
        momentum = sample_container.get_matrix('momentum')
        close = sample_container.get_matrix('close')

        # Verify shape
        assert momentum.shape == close.shape

        # Manual calculation for verification
        daily_returns = close / close.shift(1) - 1
        expected_momentum = daily_returns.rolling(window=5).mean()

        # Compare non-NaN values (skip first 5 rows)
        pd.testing.assert_frame_equal(
            momentum.iloc[5:],
            expected_momentum.iloc[5:],
            check_dtype=False
        )

    def test_momentum_with_different_periods(self, sample_container):
        """Test momentum with various period parameters."""
        test_periods = [3, 5, 10, 15]

        for period in test_periods:
            # Create new container for each test
            container = FinLabDataFrame()
            close = sample_container.get_matrix('close')
            container.add_matrix('close', close)

            parameters = {'momentum_period': period}
            _momentum_logic(container, parameters)

            momentum = container.get_matrix('momentum')

            # Check that first (period-1) rows are NaN
            assert momentum.iloc[:period-1].isna().all().all()

            # Check that later rows have values
            assert not momentum.iloc[period:].isna().all().all()

    def test_momentum_with_single_symbol(self):
        """Test momentum calculation with single symbol."""
        dates = pd.date_range('2023-01-01', periods=10)
        close = pd.DataFrame(
            [100, 102, 101, 103, 105, 107, 106, 108, 110, 112],
            index=dates,
            columns=['2330']
        )

        container = FinLabDataFrame()
        container.add_matrix('close', close)

        parameters = {'momentum_period': 3}
        _momentum_logic(container, parameters)

        momentum = container.get_matrix('momentum')
        assert momentum.shape == (10, 1)
        assert not momentum.iloc[3:].isna().all()

    def test_momentum_with_nan_values(self):
        """Test momentum handles NaN values correctly."""
        dates = pd.date_range('2023-01-01', periods=10)
        close = pd.DataFrame(
            [100, 102, np.nan, 103, 105, np.nan, 106, 108, 110, 112],
            index=dates,
            columns=['2330']
        )

        container = FinLabDataFrame()
        container.add_matrix('close', close)

        parameters = {'momentum_period': 3}
        _momentum_logic(container, parameters)

        momentum = container.get_matrix('momentum')

        # NaN values should propagate
        assert momentum.isna().any().any()
        assert momentum.shape == (10, 1)


# ============================================================================
# Component Tests - MA Filter Logic
# ============================================================================

class TestMAFilterLogic:
    """Test ma_filter_logic function with matrix operations."""

    def test_ma_filter_calculation_correctness(self, sample_container):
        """Test MA filter calculation matches expected formula."""
        parameters = {'ma_periods': 5}

        # Execute logic
        _ma_filter_logic(sample_container, parameters)

        # Check output exists
        assert sample_container.has_matrix('ma_filter')

        # Get result
        ma_filter = sample_container.get_matrix('ma_filter')
        close = sample_container.get_matrix('close')

        # Verify shape
        assert ma_filter.shape == close.shape

        # Manual calculation for verification
        ma = close.rolling(window=5).mean()
        expected_filter = close > ma

        # Compare all values
        pd.testing.assert_frame_equal(
            ma_filter,
            expected_filter,
            check_dtype=False
        )

    def test_ma_filter_boolean_output(self, sample_container):
        """Test MA filter produces boolean output."""
        parameters = {'ma_periods': 5}
        _ma_filter_logic(sample_container, parameters)

        ma_filter = sample_container.get_matrix('ma_filter')

        # Check dtype is boolean
        assert ma_filter.dtypes.apply(lambda x: x == bool or x == 'bool').all()

    def test_ma_filter_with_uptrend(self):
        """Test MA filter with consistent uptrend (should be mostly True)."""
        dates = pd.date_range('2023-01-01', periods=15)
        # Strong uptrend
        close = pd.DataFrame(
            np.arange(100, 115),
            index=dates,
            columns=['2330']
        )

        container = FinLabDataFrame()
        container.add_matrix('close', close)

        parameters = {'ma_periods': 5}
        _ma_filter_logic(container, parameters)

        ma_filter = container.get_matrix('ma_filter')

        # After MA stabilizes, most values should be True in uptrend
        assert ma_filter.iloc[10:].sum().values[0] > 3  # Most of last 5 rows


# ============================================================================
# Component Tests - Revenue Catalyst Logic
# ============================================================================

class TestRevenueCatalystLogic:
    """Test revenue_catalyst_logic function with mocked DataCache."""

    @patch('src.factor_library.momentum_factors.DataCache')
    def test_revenue_catalyst_basic_execution(self, mock_cache_class):
        """Test basic revenue catalyst execution."""
        # Create mock revenue data (Dates×Symbols matrix)
        dates = pd.date_range('2023-01-01', periods=15, freq='MS')  # Monthly
        symbols = ['2330', '2317']

        # Short-term MA > Long-term MA (acceleration)
        revenue = pd.DataFrame(
            np.array([[100, 200], [110, 210], [120, 220], [130, 230], [140, 240],
                      [150, 250], [160, 260], [170, 270], [180, 280], [190, 290],
                      [200, 300], [210, 310], [220, 320], [230, 330], [240, 340]]),
            index=dates,
            columns=symbols
        )

        # Mock DataCache
        mock_revenue_obj = Mock()
        mock_revenue_obj.average = Mock(side_effect=lambda n: revenue.rolling(n).mean())

        mock_cache = Mock()
        mock_cache.get.return_value = mock_revenue_obj
        mock_cache_class.get_instance.return_value = mock_cache

        # Create container
        container = FinLabDataFrame()

        # Execute logic
        parameters = {'catalyst_lookback': 3}
        _revenue_catalyst_logic(container, parameters)

        # Check output
        assert container.has_matrix('revenue_catalyst')
        catalyst = container.get_matrix('revenue_catalyst')

        # Verify shape matches
        assert catalyst.shape == revenue.shape

    @patch('src.factor_library.momentum_factors.DataCache')
    def test_revenue_catalyst_datacache_call(self, mock_cache_class):
        """Test that DataCache is called with correct parameters."""
        mock_cache = Mock()
        mock_cache_class.get_instance.return_value = mock_cache

        # Mock return value
        mock_revenue = Mock()
        mock_revenue.average = Mock(return_value=pd.DataFrame([[True, True]]))
        mock_revenue.__gt__ = Mock(return_value=pd.DataFrame([[True, True]]))
        mock_cache.get.return_value = mock_revenue

        container = FinLabDataFrame()
        parameters = {'catalyst_lookback': 4}

        _revenue_catalyst_logic(container, parameters)

        # Verify DataCache.get was called correctly
        mock_cache.get.assert_called_once_with('monthly_revenue:當月營收', verbose=False)


# ============================================================================
# Component Tests - Earnings Catalyst Logic
# ============================================================================

class TestEarningsCatalystLogic:
    """Test earnings_catalyst_logic function with mocked DataCache."""

    @patch('src.factor_library.momentum_factors.DataCache')
    def test_earnings_catalyst_basic_execution(self, mock_cache_class):
        """Test basic earnings catalyst execution."""
        # Create mock ROE data (Dates×Symbols matrix)
        dates = pd.date_range('2023-01-01', periods=12, freq='QS')  # Quarterly
        symbols = ['2330', '2317']

        # ROE improving over time
        roe = pd.DataFrame(
            np.array([[10, 12], [11, 13], [12, 14], [13, 15], [14, 16],
                      [15, 17], [16, 18], [17, 19], [18, 20], [19, 21],
                      [20, 22], [21, 23]]),
            index=dates,
            columns=symbols
        )

        # Mock DataCache
        mock_roe_obj = Mock()
        mock_roe_obj.average = Mock(side_effect=lambda n: roe.rolling(n).mean())

        mock_cache = Mock()
        mock_cache.get.return_value = mock_roe_obj
        mock_cache_class.get_instance.return_value = mock_cache

        # Create container
        container = FinLabDataFrame()

        # Execute logic
        parameters = {'catalyst_lookback': 3}
        _earnings_catalyst_logic(container, parameters)

        # Check output
        assert container.has_matrix('earnings_catalyst')
        catalyst = container.get_matrix('earnings_catalyst')

        # Verify shape matches
        assert catalyst.shape == roe.shape

    @patch('src.factor_library.momentum_factors.DataCache')
    def test_earnings_catalyst_datacache_call(self, mock_cache_class):
        """Test that DataCache is called with correct parameters."""
        mock_cache = Mock()
        mock_cache_class.get_instance.return_value = mock_cache

        # Mock return value
        mock_roe = Mock()
        mock_roe.average = Mock(return_value=pd.DataFrame([[True, True]]))
        mock_roe.__gt__ = Mock(return_value=pd.DataFrame([[True, True]]))
        mock_cache.get.return_value = mock_roe

        container = FinLabDataFrame()
        parameters = {'catalyst_lookback': 4}

        _earnings_catalyst_logic(container, parameters)

        # Verify DataCache.get was called correctly
        mock_cache.get.assert_called_once_with('fundamental_features:ROE綜合損益', verbose=False)


# ============================================================================
# Matrix Shape Validation Tests
# ============================================================================

class TestMatrixShapeValidation:
    """Test that all logic functions preserve matrix shapes."""

    def test_all_outputs_preserve_shape(self, sample_container):
        """Test that all momentum factors preserve Dates×Symbols shape."""
        original_shape = sample_container.get_matrix('close').shape

        # Test momentum
        _momentum_logic(sample_container, {'momentum_period': 5})
        assert sample_container.get_matrix('momentum').shape == original_shape

        # Test ma_filter
        _ma_filter_logic(sample_container, {'ma_periods': 5})
        assert sample_container.get_matrix('ma_filter').shape == original_shape


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
