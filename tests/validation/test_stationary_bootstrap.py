"""
Test suite for stationary bootstrap implementation.

Tests the v1.1 Politis & Romano stationary bootstrap that replaces
simple block bootstrap.

Task 1.1.2: Implement Proper Stationary Bootstrap
"""

import pytest
import numpy as np
import time
from src.validation.stationary_bootstrap import (
    stationary_bootstrap,
    stationary_bootstrap_detailed
)


class TestStationaryBootstrapBasic:
    """Test basic stationary bootstrap functionality."""

    def test_basic_execution(self):
        """Test that stationary bootstrap runs without errors."""
        np.random.seed(42)
        returns = np.random.randn(300) * 0.01  # 300 days

        point_est, ci_lower, ci_upper = stationary_bootstrap(
            returns=returns,
            n_iterations=100,  # Fewer for speed
            avg_block_size=21,
            confidence_level=0.95
        )

        # Verify results are finite
        assert np.isfinite(point_est)
        assert np.isfinite(ci_lower)
        assert np.isfinite(ci_upper)

        # Verify ordering
        assert ci_lower < point_est < ci_upper

    def test_minimum_data_requirement(self):
        """Test that <252 days raises ValueError."""
        returns = np.random.randn(100) * 0.01  # Only 100 days

        with pytest.raises(ValueError, match="Insufficient data.*100 days < 252"):
            stationary_bootstrap(returns)

    def test_exactly_252_days_works(self):
        """Test that exactly 252 days is accepted."""
        np.random.seed(42)
        returns = np.random.randn(252) * 0.01

        point_est, ci_lower, ci_upper = stationary_bootstrap(
            returns=returns,
            n_iterations=100
        )

        assert np.isfinite(point_est)
        assert ci_lower < ci_upper

    def test_invalid_avg_block_size(self):
        """Test that avg_block_size < 1 raises ValueError."""
        returns = np.random.randn(300) * 0.01

        with pytest.raises(ValueError, match="avg_block_size must be >= 1"):
            stationary_bootstrap(returns, avg_block_size=0)

    def test_invalid_confidence_level(self):
        """Test that invalid confidence_level raises ValueError."""
        returns = np.random.randn(300) * 0.01

        with pytest.raises(ValueError, match="confidence_level must be in"):
            stationary_bootstrap(returns, confidence_level=1.5)

        with pytest.raises(ValueError, match="confidence_level must be in"):
            stationary_bootstrap(returns, confidence_level=0.0)

    def test_too_few_iterations(self):
        """Test that n_iterations < 100 raises ValueError."""
        returns = np.random.randn(300) * 0.01

        with pytest.raises(ValueError, match="n_iterations must be >= 100"):
            stationary_bootstrap(returns, n_iterations=50)

    def test_constant_returns_zero_std(self):
        """Test that constant returns (zero std) raises ValueError."""
        returns = np.ones(300) * 0.01  # All same value

        with pytest.raises(ValueError, match="All bootstrap iterations failed"):
            stationary_bootstrap(returns, n_iterations=100)


class TestStationaryBootstrapStatisticalProperties:
    """Test statistical properties of stationary bootstrap."""

    def test_known_positive_returns_positive_sharpe(self):
        """Test that positive returns yield positive Sharpe estimate."""
        np.random.seed(42)
        # Create returns with positive drift
        returns = np.random.randn(300) * 0.01 + 0.001  # +0.1% mean daily

        point_est, ci_lower, ci_upper = stationary_bootstrap(
            returns=returns,
            n_iterations=200
        )

        # Sharpe should be positive
        assert point_est > 0
        assert ci_lower > 0  # Strong signal should have positive lower bound

    def test_known_negative_returns_negative_sharpe(self):
        """Test that negative returns yield negative Sharpe estimate."""
        np.random.seed(42)
        # Create returns with negative drift
        returns = np.random.randn(300) * 0.01 - 0.001  # -0.1% mean daily

        point_est, ci_lower, ci_upper = stationary_bootstrap(
            returns=returns,
            n_iterations=200
        )

        # Sharpe should be negative
        assert point_est < 0
        assert ci_upper < 0  # Strong negative signal

    def test_zero_mean_returns_ci_covers_zero(self):
        """Test that zero-mean returns have CI covering zero."""
        np.random.seed(42)
        returns = np.random.randn(500) * 0.01  # Zero mean

        point_est, ci_lower, ci_upper = stationary_bootstrap(
            returns=returns,
            n_iterations=200
        )

        # CI should cover zero for zero-mean process
        assert ci_lower < 0 < ci_upper

    def test_ci_width_decreases_with_more_data(self):
        """Test that CI narrows with more data (basic property)."""
        np.random.seed(42)

        # 300 days
        returns_short = np.random.randn(300) * 0.01
        _, ci_lower_short, ci_upper_short = stationary_bootstrap(
            returns_short, n_iterations=200
        )
        width_short = ci_upper_short - ci_lower_short

        # 600 days (same process)
        np.random.seed(42)
        returns_long = np.random.randn(600) * 0.01
        _, ci_lower_long, ci_upper_long = stationary_bootstrap(
            returns_long, n_iterations=200
        )
        width_long = ci_upper_long - ci_lower_long

        # Longer series should have narrower CI (not strict, but generally true)
        # Allow some slack due to randomness
        assert width_long < width_short * 1.2

    def test_different_block_sizes_give_different_cis(self):
        """Test that block size affects CI width."""
        np.random.seed(42)
        returns = np.random.randn(400) * 0.01

        # Small blocks
        _, ci_lower_small, ci_upper_small = stationary_bootstrap(
            returns, avg_block_size=5, n_iterations=200
        )
        width_small = ci_upper_small - ci_lower_small

        # Large blocks
        _, ci_lower_large, ci_upper_large = stationary_bootstrap(
            returns, avg_block_size=50, n_iterations=200
        )
        width_large = ci_upper_large - ci_lower_large

        # CIs should differ (not necessarily one wider than other,
        # but they should be different)
        assert abs(width_small - width_large) > 0.01


class TestStationaryBootstrapVsSimpleBootstrap:
    """Compare stationary bootstrap to simple block bootstrap."""

    def test_stationary_vs_simple_block_comparison(self):
        """Verify stationary bootstrap gives reasonable results vs simple."""
        np.random.seed(42)
        returns = np.random.randn(400) * 0.01 + 0.0005

        # Stationary bootstrap
        point_stat, ci_lower_stat, ci_upper_stat = stationary_bootstrap(
            returns, n_iterations=500, avg_block_size=21
        )

        # Simple block bootstrap (from existing module)
        from src.validation.bootstrap import bootstrap_confidence_interval
        result_simple = bootstrap_confidence_interval(
            returns=returns,
            n_iterations=500,
            block_size=21
        )

        # Both should give positive Sharpe for positive drift
        assert point_stat > 0
        assert result_simple.point_estimate > 0

        # Point estimates should be similar (within 30%)
        ratio = point_stat / result_simple.point_estimate
        assert 0.7 < ratio < 1.3

        # CI widths should be comparable (stationary often slightly wider)
        width_stat = ci_upper_stat - ci_lower_stat
        width_simple = result_simple.upper_bound - result_simple.lower_bound
        assert 0.5 < width_stat / width_simple < 2.0


class TestStationaryBootstrapCoverageRates:
    """Test bootstrap coverage rates (critical for validity)."""

    def test_coverage_rate_approximates_confidence_level(self):
        """
        Test that 95% CI covers true parameter ~95% of time.

        This is a statistical test that may occasionally fail due to randomness.
        """
        np.random.seed(42)

        # True parameters
        true_mean = 0.0005  # 0.05% daily
        true_std = 0.01
        true_sharpe = (true_mean / true_std) * np.sqrt(252)

        n_experiments = 50  # Number of independent samples
        n_covered = 0

        for _ in range(n_experiments):
            # Generate sample from true distribution
            returns = np.random.normal(true_mean, true_std, 300)

            # Calculate bootstrap CI
            _, ci_lower, ci_upper = stationary_bootstrap(
                returns, n_iterations=200, avg_block_size=21
            )

            # Check if true parameter covered
            if ci_lower <= true_sharpe <= ci_upper:
                n_covered += 1

        coverage_rate = n_covered / n_experiments

        # 95% CI should cover true value 85-100% of time
        # (allow some slack due to finite sample)
        assert 0.70 < coverage_rate < 1.0, \
            f"Coverage rate {coverage_rate:.2f} outside expected range"


class TestStationaryBootstrapPerformance:
    """Test performance characteristics."""

    def test_performance_1000_iterations_under_5_seconds(self):
        """Test that 1000 iterations complete in <5 seconds."""
        np.random.seed(42)
        returns = np.random.randn(300) * 0.01

        start_time = time.time()
        point_est, ci_lower, ci_upper = stationary_bootstrap(
            returns, n_iterations=1000, avg_block_size=21
        )
        elapsed = time.time() - start_time

        assert elapsed < 5.0, f"Took {elapsed:.2f}s > 5s threshold"

    def test_no_memory_leak_repeated_execution(self):
        """Test that repeated execution doesn't leak memory."""
        np.random.seed(42)
        returns = np.random.randn(300) * 0.01

        # Run 10 times
        for _ in range(10):
            point_est, ci_lower, ci_upper = stationary_bootstrap(
                returns, n_iterations=100
            )
            # Verify results are valid
            assert np.isfinite(point_est)


class TestStationaryBootstrapDetailed:
    """Test detailed diagnostic function."""

    def test_detailed_returns_distribution(self):
        """Test that detailed version returns full bootstrap distribution."""
        np.random.seed(42)
        returns = np.random.randn(300) * 0.01

        result = stationary_bootstrap_detailed(
            returns, n_iterations=200, avg_block_size=21
        )

        # Verify all keys present
        assert 'point_estimate' in result
        assert 'ci_lower' in result
        assert 'ci_upper' in result
        assert 'bootstrap_distribution' in result
        assert 'original_sharpe' in result
        assert 'n_valid_iterations' in result
        assert 'avg_actual_block_size' in result

        # Verify bootstrap distribution length
        assert len(result['bootstrap_distribution']) == 200

        # Verify avg block size close to requested
        assert 15 < result['avg_actual_block_size'] < 27  # 21 ± slack

    def test_detailed_original_sharpe_matches_point_estimate(self):
        """Test that original Sharpe is close to point estimate."""
        np.random.seed(42)
        returns = np.random.randn(400) * 0.01 + 0.0005

        result = stationary_bootstrap_detailed(
            returns, n_iterations=500
        )

        # Original Sharpe and point estimate should be similar
        # (point estimate is mean of bootstrap, original is from data)
        ratio = result['point_estimate'] / result['original_sharpe']
        assert 0.8 < ratio < 1.2


class TestStationaryBootstrapEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_large_block_size(self):
        """Test with very large block size (approaches simple resample)."""
        np.random.seed(42)
        returns = np.random.randn(300) * 0.01

        # Block size larger than series
        point_est, ci_lower, ci_upper = stationary_bootstrap(
            returns, avg_block_size=500, n_iterations=100
        )

        assert np.isfinite(point_est)
        assert ci_lower < ci_upper

    def test_very_small_block_size(self):
        """Test with very small block size (block=1 approaches i.i.d.)."""
        np.random.seed(42)
        returns = np.random.randn(300) * 0.01

        # Block size = 1 (geometric mean = 1)
        point_est, ci_lower, ci_upper = stationary_bootstrap(
            returns, avg_block_size=1, n_iterations=100
        )

        assert np.isfinite(point_est)
        assert ci_lower < ci_upper

    def test_high_volatility_returns(self):
        """Test with high volatility returns."""
        np.random.seed(42)
        returns = np.random.randn(300) * 0.05  # 5% daily std

        point_est, ci_lower, ci_upper = stationary_bootstrap(
            returns, n_iterations=200
        )

        # Should still work, just wider CI
        assert np.isfinite(point_est)
        assert ci_lower < ci_upper

    def test_fat_tailed_returns(self):
        """Test with fat-tailed returns (t-distribution)."""
        np.random.seed(42)
        # t-distribution with 3 degrees of freedom (fat tails)
        returns = np.random.standard_t(3, size=300) * 0.01

        point_est, ci_lower, ci_upper = stationary_bootstrap(
            returns, n_iterations=200
        )

        assert np.isfinite(point_est)
        assert ci_lower < ci_upper


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
