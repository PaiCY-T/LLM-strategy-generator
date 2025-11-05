"""
Integration Tests for Momentum Factors
=======================================

Tests integration between extracted factors and MomentumTemplate.
Verifies that factors produce equivalent results to the original template methods.

Test Coverage:
--------------
1. Factor outputs match template method outputs
2. Parameters map correctly between factors and template
3. DataCache integration works as expected
4. Multi-factor composition works correctly

Architecture: Phase 2.0+ Factor Graph System
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from src.factor_library.momentum_factors import (
    create_momentum_factor,
    create_ma_filter_factor,
    create_revenue_catalyst_factor,
    create_earnings_catalyst_factor,
)
from src.templates.momentum_template import MomentumTemplate


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_data():
    """Create sample data for integration tests."""
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    close_prices = 100 + np.cumsum(np.random.randn(100) * 2)

    return pd.DataFrame({
        'close': close_prices,
        '_dummy': [True] * 100
    }, index=dates)


@pytest.fixture
def template():
    """Create MomentumTemplate instance."""
    return MomentumTemplate()


# ============================================================================
# Logic Equivalence Tests
# ============================================================================

class TestLogicEquivalence:
    """Test that factor logic matches original template methods."""

    def test_momentum_factor_matches_template(self, sample_data):
        """Test MomentumFactor produces same results as template._calculate_momentum."""
        # Create factor
        factor = create_momentum_factor(momentum_period=20)

        # Execute factor
        factor_result = factor.execute(sample_data.copy())

        # Calculate expected result using template logic
        daily_returns = sample_data['close'] / sample_data['close'].shift(1) - 1
        expected_momentum = daily_returns.rolling(window=20).mean()

        # Compare results (skip NaN values)
        pd.testing.assert_series_equal(
            factor_result['momentum'].iloc[20:],
            expected_momentum.iloc[20:],
            check_names=False,
            rtol=1e-10
        )

    def test_ma_filter_factor_matches_template(self, sample_data):
        """Test MAFilterFactor produces same results as template MA filter logic."""
        # Create factor
        factor = create_ma_filter_factor(ma_periods=60)

        # Execute factor
        factor_result = factor.execute(sample_data.copy())

        # Calculate expected result using template logic
        ma = sample_data['close'].rolling(window=60).mean()
        expected_filter = sample_data['close'] > ma

        # Compare results
        pd.testing.assert_series_equal(
            factor_result['ma_filter'],
            expected_filter,
            check_names=False
        )


# ============================================================================
# Parameter Mapping Tests
# ============================================================================

class TestParameterMapping:
    """Test that parameters map correctly between factors and template."""

    @pytest.mark.parametrize("momentum_period", [5, 10, 20, 30])
    def test_momentum_period_mapping(self, momentum_period, sample_data):
        """Test momentum_period parameter maps correctly."""
        factor = create_momentum_factor(momentum_period=momentum_period)

        assert factor.parameters['momentum_period'] == momentum_period

        # Verify execution works with parameter
        result = factor.execute(sample_data)
        assert 'momentum' in result.columns

    @pytest.mark.parametrize("ma_periods", [20, 60, 90, 120])
    def test_ma_periods_mapping(self, ma_periods, sample_data):
        """Test ma_periods parameter maps correctly."""
        factor = create_ma_filter_factor(ma_periods=ma_periods)

        assert factor.parameters['ma_periods'] == ma_periods

        # Verify execution works with parameter
        result = factor.execute(sample_data)
        assert 'ma_filter' in result.columns

    @pytest.mark.parametrize("catalyst_lookback", [2, 3, 4, 6])
    def test_revenue_catalyst_lookback_mapping(self, catalyst_lookback):
        """Test revenue catalyst_lookback parameter maps correctly."""
        factor = create_revenue_catalyst_factor(catalyst_lookback=catalyst_lookback)

        assert factor.parameters['catalyst_lookback'] == catalyst_lookback

    @pytest.mark.parametrize("catalyst_lookback", [2, 3, 4, 6])
    def test_earnings_catalyst_lookback_mapping(self, catalyst_lookback):
        """Test earnings catalyst_lookback parameter maps correctly."""
        factor = create_earnings_catalyst_factor(catalyst_lookback=catalyst_lookback)

        assert factor.parameters['catalyst_lookback'] == catalyst_lookback


# ============================================================================
# Multi-Factor Composition Tests
# ============================================================================

class TestMultiFactorComposition:
    """Test composing multiple factors together."""

    def test_momentum_strategy_composition(self, sample_data):
        """Test composing momentum + MA filter factors."""
        # Create factors
        momentum = create_momentum_factor(momentum_period=10)
        ma_filter = create_ma_filter_factor(ma_periods=20)

        # Execute in sequence
        result = momentum.execute(sample_data)
        result = ma_filter.execute(result)

        # Verify all outputs exist
        assert 'momentum' in result.columns
        assert 'ma_filter' in result.columns
        assert 'close' in result.columns

        # Verify data integrity
        assert len(result) == len(sample_data)
        assert (result['close'] == sample_data['close']).all()

    @patch('src.factor_library.momentum_factors.DataCache')
    def test_full_momentum_strategy(self, mock_cache_class, sample_data):
        """Test full momentum strategy with all factors."""
        # Setup mock
        mock_cache = Mock()
        mock_revenue = Mock()
        mock_revenue.average = Mock(side_effect=lambda p: Mock(__gt__=Mock(return_value=True)))
        mock_cache.get.return_value = mock_revenue
        mock_cache_class.get_instance.return_value = mock_cache

        # Create all factors
        momentum = create_momentum_factor(momentum_period=20)
        ma_filter = create_ma_filter_factor(ma_periods=60)
        catalyst = create_revenue_catalyst_factor(catalyst_lookback=3)

        # Execute in sequence
        result = momentum.execute(sample_data)
        result = ma_filter.execute(result)
        result = catalyst.execute(result)

        # Verify all outputs exist
        assert 'momentum' in result.columns
        assert 'ma_filter' in result.columns
        assert 'revenue_catalyst' in result.columns

        # Verify data integrity
        assert len(result) == len(sample_data)


# ============================================================================
# DataCache Integration Tests
# ============================================================================

class TestDataCacheIntegration:
    """Test DataCache integration with catalyst factors."""

    @patch('src.factor_library.momentum_factors.DataCache')
    def test_revenue_catalyst_uses_datacache(self, mock_cache_class, sample_data):
        """Test RevenueCatalystFactor uses DataCache correctly."""
        # Setup mock
        mock_cache = Mock()
        mock_revenue = Mock()
        short_ma = Mock()
        long_ma = Mock()
        condition = Mock()
        short_ma.__gt__ = Mock(return_value=condition)

        def average_side_effect(period):
            return short_ma if period <= 6 else long_ma

        mock_revenue.average = Mock(side_effect=average_side_effect)
        mock_cache.get.return_value = mock_revenue
        mock_cache_class.get_instance.return_value = mock_cache

        # Create and execute factor
        factor = create_revenue_catalyst_factor(catalyst_lookback=3)
        result = factor.execute(sample_data)

        # Verify DataCache was called
        mock_cache_class.get_instance.assert_called()
        mock_cache.get.assert_called_once_with('monthly_revenue:當月營收', verbose=False)

        # Verify average was called with correct periods
        calls = mock_revenue.average.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == 3  # catalyst_lookback
        assert calls[1][0][0] == 12  # fixed baseline

    @patch('src.factor_library.momentum_factors.DataCache')
    def test_earnings_catalyst_uses_datacache(self, mock_cache_class, sample_data):
        """Test EarningsCatalystFactor uses DataCache correctly."""
        # Setup mock
        mock_cache = Mock()
        mock_roe = Mock()
        short_ma = Mock()
        long_ma = Mock()
        condition = Mock()
        short_ma.__gt__ = Mock(return_value=condition)

        def average_side_effect(period):
            return short_ma if period <= 6 else long_ma

        mock_roe.average = Mock(side_effect=average_side_effect)
        mock_cache.get.return_value = mock_roe
        mock_cache_class.get_instance.return_value = mock_cache

        # Create and execute factor
        factor = create_earnings_catalyst_factor(catalyst_lookback=3)
        result = factor.execute(sample_data)

        # Verify DataCache was called
        mock_cache_class.get_instance.assert_called()
        mock_cache.get.assert_called_once_with('fundamental_features:ROE綜合損益', verbose=False)

        # Verify average was called with correct periods
        calls = mock_roe.average.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == 3  # catalyst_lookback
        assert calls[1][0][0] == 8  # fixed baseline


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
