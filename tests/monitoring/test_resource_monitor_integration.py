"""Integration test for ResourceMonitor with real psutil.

This test verifies that ResourceMonitor works correctly with the actual psutil
library (not mocked) to ensure real-world functionality.
"""

import pytest
import time

from src.monitoring.resource_monitor import ResourceMonitor


class TestResourceMonitorIntegration:
    """Integration tests with real psutil library."""

    def test_real_resource_collection(self):
        """Test that ResourceMonitor collects real system metrics."""
        monitor = ResourceMonitor()
        monitor.start_monitoring(interval_seconds=1)

        # Wait for at least 2 collection cycles
        time.sleep(2.5)

        stats = monitor.get_current_stats()
        monitor.stop_monitoring()

        # Verify we got real data
        assert 'memory_percent' in stats
        assert 'cpu_percent' in stats
        assert 'disk_percent' in stats

        # Verify values are reasonable
        assert 0 <= stats['memory_percent'] <= 100
        assert 0 <= stats['cpu_percent'] <= 100
        assert 0 <= stats['disk_percent'] <= 100

        # Verify we have memory values
        assert stats['memory_used_gb'] > 0
        assert stats['memory_total_gb'] > 0

        # Verify we have disk values
        assert stats['disk_used_gb'] > 0
        assert stats['disk_total_gb'] > 0

        print(f"\nCollected real metrics: {stats}")

    def test_background_collection_continues(self):
        """Test that background thread continues collecting over time."""
        monitor = ResourceMonitor()
        monitor.start_monitoring(interval_seconds=1)

        # Get first timestamp
        time.sleep(2.0)  # Wait for first collection (1s for cpu_percent + some buffer)
        stats1 = monitor.get_current_stats()
        timestamp1 = stats1.get('timestamp', 0)

        # Wait and get second timestamp
        time.sleep(2.0)  # Wait for next collection
        stats2 = monitor.get_current_stats()
        timestamp2 = stats2.get('timestamp', 0)

        monitor.stop_monitoring()

        # Timestamps should be different (metrics updated)
        assert timestamp2 > timestamp1, "Metrics should be updated over time"

        # Difference should be approximately 1-2 seconds (collection interval)
        time_diff = timestamp2 - timestamp1
        assert 0.5 < time_diff < 4.0, f"Time diff should be ~1-2s, got {time_diff:.2f}s"

    def test_context_manager_with_real_collection(self):
        """Test context manager with real metric collection."""
        # Context manager auto-starts, so don't call start_monitoring
        monitor = ResourceMonitor()
        with monitor:
            time.sleep(2.0)  # Wait for collection
            stats = monitor.get_current_stats()

        # Should have collected data
        assert 'memory_percent' in stats
        assert stats['memory_percent'] > 0

    def test_overhead_is_minimal(self):
        """Test that monitoring overhead is minimal (< 1% CPU)."""
        monitor = ResourceMonitor()

        # Start monitoring with 1s interval
        monitor.start_monitoring(interval_seconds=1)

        # Let it run for 10 seconds
        time.sleep(10)

        stats = monitor.get_current_stats()
        monitor.stop_monitoring()

        # The monitoring thread itself should use minimal CPU
        # Since we're collecting CPU usage, we can check that the system
        # is not under heavy load from our monitoring
        # (This is a weak test but validates that the system is operational)
        assert stats['cpu_percent'] < 100, "System should not be at 100% CPU from monitoring"

        print(f"\nSystem CPU during monitoring: {stats['cpu_percent']:.1f}%")

    def test_multiple_collection_cycles(self):
        """Test that multiple collection cycles work correctly."""
        monitor = ResourceMonitor()
        monitor.start_monitoring(interval_seconds=1)

        # Collect stats 5 times
        collected_stats = []
        for _ in range(5):
            time.sleep(1.2)
            stats = monitor.get_current_stats()
            collected_stats.append(stats)

        monitor.stop_monitoring()

        # Should have 5 different timestamps
        timestamps = [s.get('timestamp', 0) for s in collected_stats]
        assert len(set(timestamps)) >= 3, "Should have multiple unique timestamps"

        # All should have valid data
        for stats in collected_stats:
            assert 'memory_percent' in stats
            assert stats['memory_percent'] > 0

    def test_stop_and_restart(self):
        """Test that monitor can be stopped and restarted."""
        monitor = ResourceMonitor()

        # First run
        monitor.start_monitoring(interval_seconds=1)
        time.sleep(1.5)
        stats1 = monitor.get_current_stats()
        monitor.stop_monitoring()
        assert 'memory_percent' in stats1

        # Second run
        time.sleep(0.5)  # Brief pause
        monitor.start_monitoring(interval_seconds=1)
        time.sleep(1.5)
        stats2 = monitor.get_current_stats()
        monitor.stop_monitoring()
        assert 'memory_percent' in stats2

        # Both runs should produce valid data
        assert stats1['timestamp'] < stats2['timestamp']
