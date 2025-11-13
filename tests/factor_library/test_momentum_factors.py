"""
Test Suite for Momentum Factors
================================

Comprehensive tests for momentum-related factors extracted from MomentumTemplate.
Tests cover factor creation, execution, parameter validation, and data integration.

Test Coverage:
--------------
1. Factor Creation Tests
   - MomentumFactor instantiation
   - MAFilterFactor instantiation
   - RevenueCatalystFactor instantiation
   - EarningsCatalystFactor instantiation

2. Factory Function Tests
   - create_momentum_factor with various periods
   - create_ma_filter_factor with various periods
   - create_revenue_catalyst_factor with various lookbacks
   - create_earnings_catalyst_factor with various lookbacks

3. Execution Tests
   - Factor execution with valid data
   - Output column validation
   - Input dependency validation
   - Error handling for missing inputs

4. Parameter Validation Tests
   - Valid parameter ranges
   - Edge cases
   - Integration with DataCache

5. Integration Tests
   - Multi-factor execution
   - Data compatibility
   - Real finlab data structures

Architecture: Phase 2.0+ Factor Graph System
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from src.factor_library.momentum_factors import (
    MomentumFactor,
    MAFilterFactor,
    RevenueCatalystFactor,
    EarningsCatalystFactor,
    create_momentum_factor,
    create_ma_filter_factor,
    create_revenue_catalyst_factor,
    create_earnings_catalyst_factor,
    _momentum_logic,
    _ma_filter_logic,
)
from src.factor_graph.factor_category import FactorCategory


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_price_data():
    """Create sample price data for testing."""
    return pd.DataFrame({
        'close': [100, 102, 101, 103, 105, 107, 106, 108, 110, 112],
        '_dummy': [True] * 10  # Add dummy column for catalyst factors
    })


@pytest.fixture
def mock_revenue_data():
    """Create mock revenue data structure (finlab format)."""
    mock_data = Mock()

    # Mock average() method for short and long MA
    short_ma = Mock()
    long_ma = Mock()

    # Mock comparison operator
    condition_mock = Mock()
    short_ma.__gt__ = Mock(return_value=condition_mock)

    def average_side_effect(period):
        if period <= 6:
            return short_ma
        else:
            return long_ma

    mock_data.average = Mock(side_effect=average_side_effect)
    return mock_data


@pytest.fixture
def mock_roe_data():
    """Create mock ROE data structure (finlab format)."""
    mock_data = Mock()

    # Mock average() method for short and long MA
    short_ma = Mock()
    long_ma = Mock()

    # Mock comparison operator
    condition_mock = Mock()
    short_ma.__gt__ = Mock(return_value=condition_mock)

    def average_side_effect(period):
        if period <= 6:
            return short_ma
        else:
            return long_ma

    mock_data.average = Mock(side_effect=average_side_effect)
    return mock_data


# ============================================================================
# Factor Creation Tests
# ============================================================================

class TestFactorCreation:
    """Test factor instantiation and configuration."""

    def test_momentum_factor_creation(self):
        """Test MomentumFactor instantiation."""
        factor = MomentumFactor(momentum_period=20)

        assert factor.id == "momentum_20"
        assert factor.name == "Momentum (20d)"
        assert factor.category == FactorCategory.MOMENTUM
        assert factor.inputs == ["close"]
        assert factor.outputs == ["momentum"]
        assert factor.parameters == {"momentum_period": 20}

    def test_ma_filter_factor_creation(self):
        """Test MAFilterFactor instantiation."""
        factor = MAFilterFactor(ma_periods=60)

        assert factor.id == "ma_filter_60"
        assert factor.name == "MA Filter (60d)"
        assert factor.category == FactorCategory.MOMENTUM
        assert factor.inputs == ["close"]
        assert factor.outputs == ["ma_filter"]
        assert factor.parameters == {"ma_periods": 60}

    def test_revenue_catalyst_factor_creation(self):
        """Test RevenueCatalystFactor instantiation."""
        factor = RevenueCatalystFactor(catalyst_lookback=3)

        assert factor.id == "revenue_catalyst_3"
        assert factor.name == "Revenue Catalyst (3M)"
        assert factor.category == FactorCategory.VALUE
        assert factor.inputs == ["_dummy"]  # Placeholder for validation
        assert factor.outputs == ["revenue_catalyst"]
        assert factor.parameters == {"catalyst_lookback": 3}

    def test_earnings_catalyst_factor_creation(self):
        """Test EarningsCatalystFactor instantiation."""
        factor = EarningsCatalystFactor(catalyst_lookback=3)

        assert factor.id == "earnings_catalyst_3"
        assert factor.name == "Earnings Catalyst (3Q)"
        assert factor.category == FactorCategory.QUALITY
        assert factor.inputs == ["_dummy"]  # Placeholder for validation
        assert factor.outputs == ["earnings_catalyst"]
        assert factor.parameters == {"catalyst_lookback": 3}


# ============================================================================
# Factory Function Tests
# ============================================================================

class TestFactoryFunctions:
    """Test factory functions for factor creation."""

    def test_create_momentum_factor(self):
        """Test create_momentum_factor factory function."""
        factor = create_momentum_factor(momentum_period=10)

        assert isinstance(factor, MomentumFactor)
        assert factor.parameters["momentum_period"] == 10
        assert factor.id == "momentum_10"

    def test_create_momentum_factor_default(self):
        """Test create_momentum_factor with default parameters."""
        factor = create_momentum_factor()

        assert factor.parameters["momentum_period"] == 20
        assert factor.id == "momentum_20"

    def test_create_ma_filter_factor(self):
        """Test create_ma_filter_factor factory function."""
        factor = create_ma_filter_factor(ma_periods=90)

        assert isinstance(factor, MAFilterFactor)
        assert factor.parameters["ma_periods"] == 90
        assert factor.id == "ma_filter_90"

    def test_create_ma_filter_factor_default(self):
        """Test create_ma_filter_factor with default parameters."""
        factor = create_ma_filter_factor()

        assert factor.parameters["ma_periods"] == 60
        assert factor.id == "ma_filter_60"

    def test_create_revenue_catalyst_factor(self):
        """Test create_revenue_catalyst_factor factory function."""
        factor = create_revenue_catalyst_factor(catalyst_lookback=4)

        assert isinstance(factor, RevenueCatalystFactor)
        assert factor.parameters["catalyst_lookback"] == 4
        assert factor.id == "revenue_catalyst_4"

    def test_create_revenue_catalyst_factor_default(self):
        """Test create_revenue_catalyst_factor with default parameters."""
        factor = create_revenue_catalyst_factor()

        assert factor.parameters["catalyst_lookback"] == 3
        assert factor.id == "revenue_catalyst_3"

    def test_create_earnings_catalyst_factor(self):
        """Test create_earnings_catalyst_factor factory function."""
        factor = create_earnings_catalyst_factor(catalyst_lookback=6)

        assert isinstance(factor, EarningsCatalystFactor)
        assert factor.parameters["catalyst_lookback"] == 6
        assert factor.id == "earnings_catalyst_6"

    def test_create_earnings_catalyst_factor_default(self):
        """Test create_earnings_catalyst_factor with default parameters."""
        factor = create_earnings_catalyst_factor()

        assert factor.parameters["catalyst_lookback"] == 3
        assert factor.id == "earnings_catalyst_3"


# ============================================================================
# Factor Execution Tests
# ============================================================================

class TestFactorExecution:
    """Test factor execution with various data inputs."""

    def test_momentum_factor_execution(self, sample_price_data):
        """Test MomentumFactor execution."""
        factor = MomentumFactor(momentum_period=5)
        result = factor.execute(sample_price_data)

        # Check output column exists
        assert "momentum" in result.columns

        # Check momentum calculation is correct (rolling mean of returns)
        # First 5 values should be NaN due to rolling window
        assert pd.isna(result['momentum'].iloc[:5]).all()

        # Check later values are calculated
        assert not pd.isna(result['momentum'].iloc[5:]).all()

    def test_ma_filter_factor_execution(self, sample_price_data):
        """Test MAFilterFactor execution."""
        factor = MAFilterFactor(ma_periods=5)
        result = factor.execute(sample_price_data)

        # Check output column exists
        assert "ma_filter" in result.columns

        # Check output is boolean
        assert result['ma_filter'].dtype == bool or result['ma_filter'].dtype == 'bool'

        # With ascending prices, later values should be True (price > MA)
        # First 5 values might be False/NaN due to rolling window
        assert result['ma_filter'].iloc[5:].any()

    @patch('src.factor_library.momentum_factors.DataCache')
    def test_revenue_catalyst_factor_execution(self, mock_cache_class, mock_revenue_data, sample_price_data):
        """Test RevenueCatalystFactor execution with mocked DataCache."""
        # Setup mock
        mock_cache = Mock()
        mock_cache.get.return_value = mock_revenue_data
        mock_cache_class.get_instance.return_value = mock_cache

        factor = RevenueCatalystFactor(catalyst_lookback=3)
        result = factor.execute(sample_price_data)

        # Check output column exists
        assert "revenue_catalyst" in result.columns

        # Verify DataCache was called correctly
        mock_cache.get.assert_called_once_with('monthly_revenue:當月營收', verbose=False)

    @patch('src.factor_library.momentum_factors.DataCache')
    def test_earnings_catalyst_factor_execution(self, mock_cache_class, mock_roe_data, sample_price_data):
        """Test EarningsCatalystFactor execution with mocked DataCache."""
        # Setup mock
        mock_cache = Mock()
        mock_cache.get.return_value = mock_roe_data
        mock_cache_class.get_instance.return_value = mock_cache

        factor = EarningsCatalystFactor(catalyst_lookback=3)
        result = factor.execute(sample_price_data)

        # Check output column exists
        assert "earnings_catalyst" in result.columns

        # Verify DataCache was called correctly
        mock_cache.get.assert_called_once_with('fundamental_features:ROE綜合損益', verbose=False)

    def test_momentum_factor_missing_input(self):
        """Test MomentumFactor execution with missing input column."""
        factor = MomentumFactor(momentum_period=5)
        data = pd.DataFrame({'volume': [1000, 1100, 1200]})

        with pytest.raises(KeyError, match="requires columns.*close.*missing"):
            factor.execute(data)

    def test_ma_filter_factor_missing_input(self):
        """Test MAFilterFactor execution with missing input column."""
        factor = MAFilterFactor(ma_periods=5)
        data = pd.DataFrame({'volume': [1000, 1100, 1200]})

        with pytest.raises(KeyError, match="requires columns.*close.*missing"):
            factor.execute(data)


# ============================================================================
# Parameter Validation Tests
# ============================================================================

class TestParameterValidation:
    """Test parameter variations and edge cases."""

    @pytest.mark.parametrize("momentum_period", [5, 10, 20, 30])
    def test_momentum_factor_parameter_variations(self, momentum_period, sample_price_data):
        """Test MomentumFactor with various parameter values."""
        factor = MomentumFactor(momentum_period=momentum_period)
        result = factor.execute(sample_price_data)

        assert "momentum" in result.columns
        assert factor.parameters["momentum_period"] == momentum_period

    @pytest.mark.parametrize("ma_periods", [20, 60, 90, 120])
    def test_ma_filter_factor_parameter_variations(self, ma_periods):
        """Test MAFilterFactor with various parameter values."""
        factor = MAFilterFactor(ma_periods=ma_periods)

        assert factor.parameters["ma_periods"] == ma_periods
        # With short data, just verify factor is created correctly
        assert factor.id == f"ma_filter_{ma_periods}"

    @pytest.mark.parametrize("catalyst_lookback", [2, 3, 4, 6])
    def test_revenue_catalyst_parameter_variations(self, catalyst_lookback):
        """Test RevenueCatalystFactor with various parameter values."""
        factor = RevenueCatalystFactor(catalyst_lookback=catalyst_lookback)

        assert factor.parameters["catalyst_lookback"] == catalyst_lookback
        assert factor.id == f"revenue_catalyst_{catalyst_lookback}"

    @pytest.mark.parametrize("catalyst_lookback", [2, 3, 4, 6])
    def test_earnings_catalyst_parameter_variations(self, catalyst_lookback):
        """Test EarningsCatalystFactor with various parameter values."""
        factor = EarningsCatalystFactor(catalyst_lookback=catalyst_lookback)

        assert factor.parameters["catalyst_lookback"] == catalyst_lookback
        assert factor.id == f"earnings_catalyst_{catalyst_lookback}"


# ============================================================================
# Logic Function Tests
# ============================================================================

class TestLogicFunctions:
    """Test individual logic functions directly."""

    def test_momentum_logic_function(self, sample_price_data):
        """Test _momentum_logic function directly."""
        params = {"momentum_period": 5}
        result = _momentum_logic(sample_price_data.copy(), params)

        assert "momentum" in result.columns
        # Check calculation correctness
        daily_returns = sample_price_data['close'] / sample_price_data['close'].shift(1) - 1
        expected_momentum = daily_returns.rolling(window=5).mean()

        # Compare non-NaN values (skip first 5 due to rolling window)
        pd.testing.assert_series_equal(
            result['momentum'].iloc[5:],
            expected_momentum.iloc[5:],
            check_names=False
        )

    def test_ma_filter_logic_function(self, sample_price_data):
        """Test _ma_filter_logic function directly."""
        params = {"ma_periods": 5}
        result = _ma_filter_logic(sample_price_data.copy(), params)

        assert "ma_filter" in result.columns
        # Check calculation correctness
        ma = sample_price_data['close'].rolling(window=5).mean()
        expected_filter = sample_price_data['close'] > ma

        # Compare all values
        pd.testing.assert_series_equal(
            result['ma_filter'],
            expected_filter,
            check_names=False
        )


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test multi-factor integration and composition."""

    def test_multi_factor_execution_sequence(self, sample_price_data):
        """Test executing multiple factors in sequence."""
        # Create factors
        momentum = MomentumFactor(momentum_period=5)
        ma_filter = MAFilterFactor(ma_periods=5)

        # Execute in sequence
        result = momentum.execute(sample_price_data)
        result = ma_filter.execute(result)

        # Check all outputs exist
        assert "momentum" in result.columns
        assert "ma_filter" in result.columns
        assert "close" in result.columns  # Original data preserved

    def test_factor_input_validation(self):
        """Test input validation for factors."""
        momentum = MomentumFactor(momentum_period=5)

        # Should validate successfully with close column
        assert momentum.validate_inputs(["close"])
        assert momentum.validate_inputs(["open", "high", "low", "close", "volume"])

        # Should fail without close column
        assert not momentum.validate_inputs(["open", "high", "low"])
        assert not momentum.validate_inputs([])

    def test_factor_representation(self):
        """Test factor string representations."""
        momentum = MomentumFactor(momentum_period=20)

        # Test __repr__
        repr_str = repr(momentum)
        assert "momentum_20" in repr_str
        assert "MOMENTUM" in repr_str

        # Test __str__
        str_str = str(momentum)
        assert "Momentum" in str_str
        assert "close" in str_str
        assert "momentum" in str_str


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_momentum_with_insufficient_data(self):
        """Test MomentumFactor with insufficient data points."""
        factor = MomentumFactor(momentum_period=10)
        # Only 5 data points, but momentum_period is 10
        data = pd.DataFrame({'close': [100, 102, 101, 103, 105]})

        result = factor.execute(data)

        # Should execute without error
        assert "momentum" in result.columns
        # All values should be NaN due to insufficient data
        assert result['momentum'].isna().all()

    def test_ma_filter_with_insufficient_data(self):
        """Test MAFilterFactor with insufficient data points."""
        factor = MAFilterFactor(ma_periods=10)
        # Only 5 data points, but ma_periods is 10
        data = pd.DataFrame({'close': [100, 102, 101, 103, 105]})

        result = factor.execute(data)

        # Should execute without error
        assert "ma_filter" in result.columns

    def test_momentum_with_single_data_point(self):
        """Test MomentumFactor with single data point."""
        factor = MomentumFactor(momentum_period=5)
        data = pd.DataFrame({'close': [100]})

        result = factor.execute(data)

        assert "momentum" in result.columns
        assert pd.isna(result['momentum'].iloc[0])

    def test_factor_with_nan_values(self):
        """Test factors handle NaN values correctly."""
        factor = MomentumFactor(momentum_period=3)
        data = pd.DataFrame({'close': [100, np.nan, 101, 103, np.nan, 105]})

        result = factor.execute(data)

        # Should execute without error
        assert "momentum" in result.columns
        # NaN values should propagate through calculation
        assert result['momentum'].isna().any()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
