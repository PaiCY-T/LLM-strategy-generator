"""Unit tests for VarianceMonitor.

Tests convergence monitoring, alert conditions, and variance reporting.

Requirements: F1.1 (rolling variance), F1.2 (alert conditions), F1.3 (convergence reports)
"""

import pytest
import numpy as np
from src.monitoring.variance_monitor import VarianceMonitor


class TestVarianceMonitorBasics:
    """Test basic VarianceMonitor functionality."""

    def test_initialization(self):
        """Test VarianceMonitor initializes with correct defaults."""
        monitor = VarianceMonitor()

        assert monitor.alert_threshold == 0.8
        assert len(monitor.sharpes) == 0
        assert len(monitor.all_sharpes) == 0
        assert monitor.consecutive_high_variance_count == 0

    def test_initialization_custom_threshold(self):
        """Test VarianceMonitor accepts custom alert threshold."""
        monitor = VarianceMonitor(alert_threshold=0.5)

        assert monitor.alert_threshold == 0.5

    def test_update_stores_sharpes(self):
        """Test update() stores Sharpe ratios correctly."""
        monitor = VarianceMonitor()

        # Add some values
        monitor.update(0, 1.0)
        monitor.update(1, 1.5)
        monitor.update(2, 0.8)

        assert len(monitor.sharpes) == 3
        assert len(monitor.all_sharpes) == 3
        assert list(monitor.sharpes) == [1.0, 1.5, 0.8]
        assert monitor.all_sharpes == [1.0, 1.5, 0.8]


class TestRollingVariance:
    """Test rolling variance calculation."""

    def test_get_rolling_variance_insufficient_data(self):
        """Test variance returns 0.0 with insufficient data."""
        monitor = VarianceMonitor()

        # No data
        assert monitor.get_rolling_variance() == 0.0

        # Only one data point
        monitor.update(0, 1.0)
        assert monitor.get_rolling_variance() == 0.0

    def test_get_rolling_variance_with_known_data(self):
        """Test variance calculation with known values."""
        monitor = VarianceMonitor()

        # Add data with known variance
        # Values: [1.0, 2.0, 3.0, 4.0, 5.0]
        # Expected std (sample): ~1.58
        for i, value in enumerate([1.0, 2.0, 3.0, 4.0, 5.0]):
            monitor.update(i, value)

        variance = monitor.get_rolling_variance()

        # Standard deviation of [1, 2, 3, 4, 5] ≈ 1.58 (sample std)
        expected_std = np.std([1.0, 2.0, 3.0, 4.0, 5.0], ddof=1)
        assert abs(variance - expected_std) < 0.01

    def test_get_rolling_variance_low_variance(self):
        """Test variance with stable (low variance) data."""
        monitor = VarianceMonitor()

        # Add very stable data
        for i in range(10):
            monitor.update(i, 1.0 + i * 0.01)  # Very small changes

        variance = monitor.get_rolling_variance()
        assert variance < 0.1  # Should be very low

    def test_get_rolling_variance_high_variance(self):
        """Test variance with unstable (high variance) data."""
        monitor = VarianceMonitor()

        # Add highly variable data
        values = [1.0, 3.0, 0.5, 2.5, 0.2, 2.8, 0.1, 3.2, 0.3, 2.9]
        for i, value in enumerate(values):
            monitor.update(i, value)

        variance = monitor.get_rolling_variance()
        assert variance > 1.0  # Should be high

    def test_rolling_window_maxlen_10(self):
        """Test rolling window only uses last 10 values."""
        monitor = VarianceMonitor()

        # Add 15 values
        for i in range(15):
            monitor.update(i, float(i))

        # Deque should only contain last 10
        assert len(monitor.sharpes) == 10
        assert list(monitor.sharpes) == list(range(5, 15))

        # But all_sharpes should have all 15
        assert len(monitor.all_sharpes) == 15

        # Variance should be calculated on last 10 only
        variance = monitor.get_rolling_variance()
        expected_std = np.std(list(range(5, 15)), ddof=1)
        assert abs(variance - expected_std) < 0.01


class TestAlertConditions:
    """Test alert condition checking."""

    def test_check_alert_no_alert_low_variance(self):
        """Test no alert triggered with low variance."""
        monitor = VarianceMonitor(alert_threshold=0.8)

        # Add stable data (low variance)
        for i in range(10):
            monitor.update(i, 1.0 + i * 0.01)

        alert, msg = monitor.check_alert_condition()
        assert alert is False
        assert msg == ""

    def test_check_alert_no_alert_below_threshold(self):
        """Test no alert with variance below threshold."""
        monitor = VarianceMonitor(alert_threshold=1.0)

        # Add data with variance ~0.5
        for i, value in enumerate([1.0, 1.5, 1.2, 1.3, 1.4]):
            monitor.update(i, value)

        alert, msg = monitor.check_alert_condition()
        assert alert is False

    def test_check_alert_triggers_after_5_consecutive(self):
        """Test alert triggers after 5 consecutive high variance iterations."""
        monitor = VarianceMonitor(alert_threshold=0.5)

        # Add highly variable data to trigger alerts
        # Use extreme variations to ensure variance > 0.5
        # Pattern: 0, 5, 0, 5, 0, 5... creates high variance
        values = [0.0, 5.0, 0.0, 5.0, 0.0, 5.0, 0.0, 5.0, 0.0, 5.0]

        alert_triggered = False
        for i, value in enumerate(values):
            monitor.update(i, value)
            alert, msg = monitor.check_alert_condition()

            # Track when alert first triggers
            if alert and not alert_triggered:
                alert_triggered = True
                # Should trigger at iteration 5 (after 5 consecutive high variance checks)
                assert i >= 5, f"Alert triggered too early at iteration {i}"
                assert "High variance" in msg
                assert "consecutive iterations" in msg

        # Verify alert was triggered at some point
        assert alert_triggered, "Alert should have triggered after 5 consecutive high variance iterations"
        assert monitor.consecutive_high_variance_count >= 5

    def test_check_alert_resets_on_low_variance(self):
        """Test consecutive count resets when variance drops."""
        monitor = VarianceMonitor(alert_threshold=0.5)

        # Add 3 high variance iterations (extreme values)
        values = [0.0, 5.0, 0.0]
        for i, value in enumerate(values):
            monitor.update(i, value)

        # Check variance is high for these first 3
        variance_after_3 = monitor.get_rolling_variance()
        assert variance_after_3 > 0.5, f"Variance after 3 values: {variance_after_3}"

        # Now add stable data to drop variance and reset counter
        # Add many stable values so rolling window becomes low variance
        for i in range(3, 13):
            monitor.update(i, 1.0)

        # After 10 stable values (1.0), variance should be near zero
        final_variance = monitor.get_rolling_variance()
        assert final_variance < 0.5, f"Final variance should be low: {final_variance}"

        # Should not trigger alert (consecutive count reset)
        alert, _ = monitor.check_alert_condition()
        assert alert is False
        assert monitor.consecutive_high_variance_count == 0

    def test_check_alert_continues_after_trigger(self):
        """Test alert continues to trigger while variance stays high."""
        monitor = VarianceMonitor(alert_threshold=0.5)

        # Create sustained high variance with extreme values
        # IMPORTANT: Must call check_alert_condition() in loop to build consecutive count
        for i in range(10):
            monitor.update(i, float((i % 2) * 5))  # Oscillate 0, 5, 0, 5...
            monitor.check_alert_condition()  # Build up consecutive count

        # Verify variance is actually high
        final_variance = monitor.get_rolling_variance()
        assert final_variance > 0.5, f"Variance should be high: {final_variance}"

        # After 5+ iterations with high variance, alert should still be triggered
        alert, msg = monitor.check_alert_condition()
        assert alert is True
        assert monitor.consecutive_high_variance_count >= 5


class TestConvergenceReport:
    """Test convergence report generation."""

    def test_generate_convergence_report_early_iterations(self):
        """Test report with insufficient data (< 10 iterations)."""
        monitor = VarianceMonitor()

        # Add 5 iterations
        for i in range(5):
            monitor.update(i, 1.0 + i * 0.1)

        report = monitor.generate_convergence_report()

        assert report['convergence_status'] == 'converging'
        assert report['total_iterations'] == 5
        assert report['convergence_iteration'] is None  # Too early
        assert len(report['recommendations']) > 0

    def test_generate_convergence_report_converged(self):
        """Test report detects convergence (σ < 0.5 after iter 10)."""
        monitor = VarianceMonitor()

        # Add 15 iterations with low variance after iteration 10
        for i in range(15):
            if i < 10:
                # Early iterations: higher variance
                monitor.update(i, 1.0 + (i % 3) * 0.5)
            else:
                # After iter 10: converge to stable values
                monitor.update(i, 1.5 + i * 0.01)

        report = monitor.generate_convergence_report()

        assert report['convergence_status'] == 'converged'
        assert report['convergence_iteration'] is not None
        assert report['convergence_iteration'] >= 10
        assert report['current_variance'] < 0.5
        assert 'converged' in report['recommendations'][0].lower()

    def test_generate_convergence_report_unstable(self):
        """Test report detects instability (σ > 0.8)."""
        monitor = VarianceMonitor()

        # Add 15 iterations with sustained high variance
        for i in range(15):
            monitor.update(i, float((i % 3) * 2))  # 0, 2, 4, 0, 2, 4...

        report = monitor.generate_convergence_report()

        assert report['convergence_status'] == 'unstable'
        assert report['current_variance'] > 0.8
        assert 'High variance detected' in report['recommendations'][0]

    def test_generate_convergence_report_converging_long_run(self):
        """Test report suggests improvements for slow convergence."""
        monitor = VarianceMonitor()

        # Add 25 iterations without converging
        for i in range(25):
            # Moderate variance that doesn't converge
            monitor.update(i, 1.0 + (i % 5) * 0.3)

        report = monitor.generate_convergence_report()

        # Should be 'converging' but with recommendations
        assert report['total_iterations'] == 25
        assert len(report['recommendations']) > 0

        # Should suggest tuning
        if report['convergence_status'] == 'converging':
            assert any('20+ iterations' in rec for rec in report['recommendations'])

    def test_generate_convergence_report_variance_trend(self):
        """Test variance trend calculation in report."""
        monitor = VarianceMonitor()

        # Add 20 iterations
        for i in range(20):
            monitor.update(i, 1.0 + i * 0.1)

        report = monitor.generate_convergence_report()

        # Variance trend should have entries for iterations with enough data
        assert len(report['variance_trend']) > 0
        assert all(isinstance(entry, tuple) for entry in report['variance_trend'])
        assert all(len(entry) == 2 for entry in report['variance_trend'])  # (iteration, variance)

        # First trend entry should be at iteration 9 (need 10 points)
        first_iteration = report['variance_trend'][0][0]
        assert first_iteration >= 9


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_zero_sharpe_handling(self):
        """Test monitor handles zero Sharpe ratios correctly."""
        monitor = VarianceMonitor()

        # Add zeros
        for i in range(5):
            monitor.update(i, 0.0)

        variance = monitor.get_rolling_variance()
        assert variance == 0.0  # All zeros = zero variance

    def test_negative_sharpe_handling(self):
        """Test monitor handles negative Sharpe ratios."""
        monitor = VarianceMonitor()

        # Add negative values
        for i, value in enumerate([-1.0, -0.5, -1.5, -0.8, -1.2]):
            monitor.update(i, value)

        variance = monitor.get_rolling_variance()
        assert variance > 0  # Should calculate variance normally

    def test_mixed_positive_negative_sharpes(self):
        """Test monitor handles mixed positive/negative Sharpes."""
        monitor = VarianceMonitor()

        # Mix of positive and negative
        values = [1.0, -0.5, 1.5, -1.0, 0.8, -0.3, 1.2, -0.7]
        for i, value in enumerate(values):
            monitor.update(i, value)

        variance = monitor.get_rolling_variance()
        assert variance > 0  # Should have high variance

        report = monitor.generate_convergence_report()
        assert report['convergence_status'] in ['converging', 'unstable']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
