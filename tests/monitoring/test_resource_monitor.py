"""Unit tests for ResourceMonitor module.

Tests cover:
- Background thread lifecycle (start/stop)
- System metric collection via psutil
- Error handling and graceful degradation
- MetricsCollector integration
- Context manager usage
- Edge cases (psutil failures, concurrent access)

Coverage target: >85%
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from collections import namedtuple

from src.monitoring.resource_monitor import ResourceMonitor


# Mock psutil return types
VirtualMemory = namedtuple('VirtualMemory', ['used', 'total', 'percent'])
DiskUsage = namedtuple('DiskUsage', ['used', 'total', 'percent'])


class TestResourceMonitorInit:
    """Test ResourceMonitor initialization."""

    def test_init_without_collector(self):
        """Test initialization without MetricsCollector."""
        monitor = ResourceMonitor()
        assert monitor.metrics_collector is None
        assert monitor._monitoring_thread is None
        assert not monitor._stop_event.is_set()

    def test_init_with_collector(self):
        """Test initialization with MetricsCollector."""
        mock_collector = Mock()
        monitor = ResourceMonitor(metrics_collector=mock_collector)
        assert monitor.metrics_collector is mock_collector


class TestResourceMonitorLifecycle:
    """Test monitoring thread lifecycle."""

    def test_start_monitoring_default_interval(self):
        """Test starting monitoring with default 5s interval."""
        monitor = ResourceMonitor()
        monitor.start_monitoring()

        assert monitor._monitoring_thread is not None
        assert monitor._monitoring_thread.is_alive()
        assert monitor._collection_interval == 5

        monitor.stop_monitoring()

    def test_start_monitoring_custom_interval(self):
        """Test starting monitoring with custom interval."""
        monitor = ResourceMonitor()
        monitor.start_monitoring(interval_seconds=10)

        assert monitor._collection_interval == 10
        assert monitor._monitoring_thread.is_alive()

        monitor.stop_monitoring()

    def test_start_monitoring_already_running_raises_error(self):
        """Test that starting monitoring twice raises RuntimeError."""
        monitor = ResourceMonitor()
        monitor.start_monitoring()

        with pytest.raises(RuntimeError, match="already started"):
            monitor.start_monitoring()

        monitor.stop_monitoring()

    def test_stop_monitoring_gracefully(self):
        """Test stopping monitoring thread gracefully."""
        monitor = ResourceMonitor()
        monitor.start_monitoring()

        # Give thread time to start
        time.sleep(0.5)

        monitor.stop_monitoring()

        # Thread should be stopped
        assert not monitor._monitoring_thread.is_alive()

    def test_stop_monitoring_when_not_running(self):
        """Test stopping when monitoring not running (should not raise)."""
        monitor = ResourceMonitor()
        # Should log warning but not raise
        monitor.stop_monitoring()

    def test_thread_is_daemon(self):
        """Test that monitoring thread is daemon (won't block process exit)."""
        monitor = ResourceMonitor()
        monitor.start_monitoring()

        assert monitor._monitoring_thread.daemon is True

        monitor.stop_monitoring()


class TestMetricCollection:
    """Test system metric collection."""

    @patch('src.monitoring.resource_monitor.psutil.virtual_memory')
    @patch('src.monitoring.resource_monitor.psutil.cpu_percent')
    @patch('src.monitoring.resource_monitor.psutil.disk_usage')
    def test_collect_metrics_success(self, mock_disk, mock_cpu, mock_memory):
        """Test successful metric collection."""
        # Mock psutil responses
        mock_memory.return_value = VirtualMemory(
            used=8 * (1024 ** 3),  # 8 GB
            total=16 * (1024 ** 3),  # 16 GB
            percent=50.0
        )
        mock_cpu.return_value = 25.5
        mock_disk.return_value = DiskUsage(
            used=100 * (1024 ** 3),  # 100 GB
            total=200 * (1024 ** 3),  # 200 GB
            percent=50.0
        )

        monitor = ResourceMonitor()
        monitor._record_system_metrics()

        stats = monitor.get_current_stats()

        assert stats['memory_percent'] == 50.0
        assert stats['memory_used_gb'] == pytest.approx(8.0, rel=0.01)
        assert stats['memory_total_gb'] == pytest.approx(16.0, rel=0.01)
        assert stats['cpu_percent'] == 25.5
        assert stats['disk_percent'] == 50.0
        assert stats['disk_used_gb'] == pytest.approx(100.0, rel=0.01)
        assert stats['disk_total_gb'] == pytest.approx(200.0, rel=0.01)
        assert 'timestamp' in stats

    @patch('src.monitoring.resource_monitor.psutil.virtual_memory')
    def test_collect_metrics_psutil_error_handled(self, mock_memory):
        """Test that psutil errors are handled gracefully."""
        import psutil
        mock_memory.side_effect = psutil.Error("Simulated psutil error")

        monitor = ResourceMonitor()
        # Should not raise - errors handled gracefully
        monitor._record_system_metrics()

        # Stats should remain empty after error
        stats = monitor.get_current_stats()
        assert stats == {}

    @patch('src.monitoring.resource_monitor.psutil.virtual_memory')
    def test_collect_metrics_unexpected_error_handled(self, mock_memory):
        """Test that unexpected errors are handled gracefully."""
        mock_memory.side_effect = ValueError("Unexpected error")

        monitor = ResourceMonitor()
        # Should not raise - errors logged and handled
        monitor._record_system_metrics()

        # Stats should remain empty after error
        stats = monitor.get_current_stats()
        assert stats == {}

    @patch('src.monitoring.resource_monitor.psutil.virtual_memory')
    @patch('src.monitoring.resource_monitor.psutil.cpu_percent')
    @patch('src.monitoring.resource_monitor.psutil.disk_usage')
    def test_get_current_stats_thread_safe(self, mock_disk, mock_cpu, mock_memory):
        """Test that get_current_stats is thread-safe."""
        mock_memory.return_value = VirtualMemory(
            used=8 * (1024 ** 3),
            total=16 * (1024 ** 3),
            percent=50.0
        )
        mock_cpu.return_value = 25.5
        mock_disk.return_value = DiskUsage(
            used=100 * (1024 ** 3),
            total=200 * (1024 ** 3),
            percent=50.0
        )

        monitor = ResourceMonitor()
        monitor._record_system_metrics()

        # Access stats from multiple threads
        results = []

        def read_stats():
            stats = monitor.get_current_stats()
            results.append(stats)

        threads = [threading.Thread(target=read_stats) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should get valid data
        assert len(results) == 10
        for stats in results:
            assert stats['memory_percent'] == 50.0

    @patch('src.monitoring.resource_monitor.psutil.virtual_memory')
    @patch('src.monitoring.resource_monitor.psutil.cpu_percent')
    @patch('src.monitoring.resource_monitor.psutil.disk_usage')
    def test_stats_updated_over_time(self, mock_disk, mock_cpu, mock_memory):
        """Test that stats are updated with new values."""
        # First collection
        mock_memory.return_value = VirtualMemory(
            used=8 * (1024 ** 3),
            total=16 * (1024 ** 3),
            percent=50.0
        )
        mock_cpu.return_value = 25.0
        mock_disk.return_value = DiskUsage(
            used=100 * (1024 ** 3),
            total=200 * (1024 ** 3),
            percent=50.0
        )

        monitor = ResourceMonitor()
        monitor._record_system_metrics()
        stats1 = monitor.get_current_stats()

        # Second collection with different values
        mock_memory.return_value = VirtualMemory(
            used=12 * (1024 ** 3),
            total=16 * (1024 ** 3),
            percent=75.0
        )
        mock_cpu.return_value = 50.0

        monitor._record_system_metrics()
        stats2 = monitor.get_current_stats()

        # Stats should be updated
        assert stats2['memory_percent'] == 75.0
        assert stats2['cpu_percent'] == 50.0
        assert stats2['timestamp'] > stats1['timestamp']


class TestMetricsCollectorIntegration:
    """Test integration with MetricsCollector."""

    @patch('src.monitoring.resource_monitor.psutil.virtual_memory')
    @patch('src.monitoring.resource_monitor.psutil.cpu_percent')
    @patch('src.monitoring.resource_monitor.psutil.disk_usage')
    def test_export_to_metrics_collector(self, mock_disk, mock_cpu, mock_memory):
        """Test that metrics are exported to MetricsCollector."""
        mock_memory.return_value = VirtualMemory(
            used=8 * (1024 ** 3),
            total=16 * (1024 ** 3),
            percent=50.0
        )
        mock_cpu.return_value = 25.5
        mock_disk.return_value = DiskUsage(
            used=100 * (1024 ** 3),
            total=200 * (1024 ** 3),
            percent=50.0
        )

        mock_collector = Mock()
        mock_collector.record_resource_memory = Mock()
        mock_collector.record_resource_cpu = Mock()
        mock_collector.record_resource_disk = Mock()

        monitor = ResourceMonitor(metrics_collector=mock_collector)
        monitor._record_system_metrics()

        # Verify collector methods called
        mock_collector.record_resource_memory.assert_called_once()
        mock_collector.record_resource_cpu.assert_called_once()
        mock_collector.record_resource_disk.assert_called_once()

        # Verify arguments
        mem_call = mock_collector.record_resource_memory.call_args
        assert mem_call[1]['percent'] == 50.0
        assert mem_call[1]['used_bytes'] == pytest.approx(8 * (1024 ** 3), rel=0.01)

        cpu_call = mock_collector.record_resource_cpu.call_args
        assert cpu_call[1]['percent'] == 25.5

    @patch('src.monitoring.resource_monitor.psutil.virtual_memory')
    @patch('src.monitoring.resource_monitor.psutil.cpu_percent')
    @patch('src.monitoring.resource_monitor.psutil.disk_usage')
    def test_export_fails_gracefully_if_collector_missing_methods(
        self, mock_disk, mock_cpu, mock_memory
    ):
        """Test export handles missing collector methods gracefully."""
        mock_memory.return_value = VirtualMemory(
            used=8 * (1024 ** 3),
            total=16 * (1024 ** 3),
            percent=50.0
        )
        mock_cpu.return_value = 25.5
        mock_disk.return_value = DiskUsage(
            used=100 * (1024 ** 3),
            total=200 * (1024 ** 3),
            percent=50.0
        )

        # Collector without record methods
        mock_collector = Mock(spec=[])

        monitor = ResourceMonitor(metrics_collector=mock_collector)
        # Should not raise even if collector doesn't have methods
        monitor._record_system_metrics()

    @patch('src.monitoring.resource_monitor.psutil.virtual_memory')
    @patch('src.monitoring.resource_monitor.psutil.cpu_percent')
    @patch('src.monitoring.resource_monitor.psutil.disk_usage')
    def test_export_handles_collector_exceptions(self, mock_disk, mock_cpu, mock_memory):
        """Test that collector exceptions don't halt monitoring."""
        mock_memory.return_value = VirtualMemory(
            used=8 * (1024 ** 3),
            total=16 * (1024 ** 3),
            percent=50.0
        )
        mock_cpu.return_value = 25.5
        mock_disk.return_value = DiskUsage(
            used=100 * (1024 ** 3),
            total=200 * (1024 ** 3),
            percent=50.0
        )

        mock_collector = Mock()
        mock_collector.record_resource_memory = Mock(side_effect=Exception("Export error"))

        monitor = ResourceMonitor(metrics_collector=mock_collector)
        # Should not raise - export errors handled
        monitor._record_system_metrics()

        # Stats should still be collected locally
        stats = monitor.get_current_stats()
        assert stats['memory_percent'] == 50.0


class TestContextManager:
    """Test context manager interface."""

    def test_context_manager_starts_and_stops(self):
        """Test that context manager starts and stops monitoring."""
        monitor = ResourceMonitor()

        with monitor:
            # Monitoring should be active
            assert monitor._monitoring_thread is not None
            assert monitor._monitoring_thread.is_alive()

        # Monitoring should be stopped after exit
        assert not monitor._monitoring_thread.is_alive()

    @patch('src.monitoring.resource_monitor.psutil.virtual_memory')
    @patch('src.monitoring.resource_monitor.psutil.cpu_percent')
    @patch('src.monitoring.resource_monitor.psutil.disk_usage')
    def test_context_manager_collects_metrics(self, mock_disk, mock_cpu, mock_memory):
        """Test that metrics are collected within context."""
        mock_memory.return_value = VirtualMemory(
            used=8 * (1024 ** 3),
            total=16 * (1024 ** 3),
            percent=50.0
        )
        mock_cpu.return_value = 25.5
        mock_disk.return_value = DiskUsage(
            used=100 * (1024 ** 3),
            total=200 * (1024 ** 3),
            percent=50.0
        )

        monitor = ResourceMonitor()

        with monitor:
            # Give thread time to collect metrics
            time.sleep(1.5)
            stats = monitor.get_current_stats()

        # Should have collected stats
        assert stats.get('memory_percent') == 50.0

    def test_context_manager_exception_handling(self):
        """Test that context manager stops monitoring even if exception raised."""
        monitor = ResourceMonitor()

        try:
            with monitor:
                assert monitor._monitoring_thread.is_alive()
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Monitoring should still be stopped
        assert not monitor._monitoring_thread.is_alive()


class TestPerformance:
    """Test performance characteristics."""

    @patch('src.monitoring.resource_monitor.psutil.virtual_memory')
    @patch('src.monitoring.resource_monitor.psutil.cpu_percent')
    @patch('src.monitoring.resource_monitor.psutil.disk_usage')
    def test_collection_overhead_low(self, mock_disk, mock_cpu, mock_memory):
        """Test that metric collection has low overhead."""
        mock_memory.return_value = VirtualMemory(
            used=8 * (1024 ** 3),
            total=16 * (1024 ** 3),
            percent=50.0
        )
        mock_cpu.return_value = 25.5
        mock_disk.return_value = DiskUsage(
            used=100 * (1024 ** 3),
            total=200 * (1024 ** 3),
            percent=50.0
        )

        monitor = ResourceMonitor()

        # Measure collection time
        start = time.time()
        for _ in range(100):
            monitor._record_system_metrics()
        elapsed = time.time() - start

        # 100 collections should be fast (< 1 second)
        assert elapsed < 1.0, f"Collection too slow: {elapsed:.3f}s for 100 iterations"

    @patch('src.monitoring.resource_monitor.psutil.virtual_memory')
    @patch('src.monitoring.resource_monitor.psutil.cpu_percent')
    @patch('src.monitoring.resource_monitor.psutil.disk_usage')
    def test_get_stats_fast(self, mock_disk, mock_cpu, mock_memory):
        """Test that getting stats is fast."""
        mock_memory.return_value = VirtualMemory(
            used=8 * (1024 ** 3),
            total=16 * (1024 ** 3),
            percent=50.0
        )
        mock_cpu.return_value = 25.5
        mock_disk.return_value = DiskUsage(
            used=100 * (1024 ** 3),
            total=200 * (1024 ** 3),
            percent=50.0
        )

        monitor = ResourceMonitor()
        monitor._record_system_metrics()

        # Measure stats retrieval time
        start = time.time()
        for _ in range(10000):
            stats = monitor.get_current_stats()
        elapsed = time.time() - start

        # 10000 reads should be very fast (< 0.1 seconds)
        assert elapsed < 0.1, f"Stats retrieval too slow: {elapsed:.3f}s for 10000 reads"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_stats_before_collection(self):
        """Test that stats are empty before first collection."""
        monitor = ResourceMonitor()
        stats = monitor.get_current_stats()
        assert stats == {}

    @patch('src.monitoring.resource_monitor.psutil.virtual_memory')
    @patch('src.monitoring.resource_monitor.psutil.cpu_percent')
    @patch('src.monitoring.resource_monitor.psutil.disk_usage')
    def test_zero_values_handled(self, mock_disk, mock_cpu, mock_memory):
        """Test that zero values are handled correctly."""
        mock_memory.return_value = VirtualMemory(
            used=0,
            total=16 * (1024 ** 3),
            percent=0.0
        )
        mock_cpu.return_value = 0.0
        mock_disk.return_value = DiskUsage(
            used=0,
            total=200 * (1024 ** 3),
            percent=0.0
        )

        monitor = ResourceMonitor()
        monitor._record_system_metrics()

        stats = monitor.get_current_stats()
        assert stats['memory_percent'] == 0.0
        assert stats['cpu_percent'] == 0.0
        assert stats['disk_percent'] == 0.0

    @patch('src.monitoring.resource_monitor.psutil.virtual_memory')
    @patch('src.monitoring.resource_monitor.psutil.cpu_percent')
    @patch('src.monitoring.resource_monitor.psutil.disk_usage')
    def test_very_high_values_handled(self, mock_disk, mock_cpu, mock_memory):
        """Test that very high values (100%) are handled correctly."""
        mock_memory.return_value = VirtualMemory(
            used=16 * (1024 ** 3),
            total=16 * (1024 ** 3),
            percent=100.0
        )
        mock_cpu.return_value = 100.0
        mock_disk.return_value = DiskUsage(
            used=200 * (1024 ** 3),
            total=200 * (1024 ** 3),
            percent=100.0
        )

        monitor = ResourceMonitor()
        monitor._record_system_metrics()

        stats = monitor.get_current_stats()
        assert stats['memory_percent'] == 100.0
        assert stats['cpu_percent'] == 100.0
        assert stats['disk_percent'] == 100.0

    def test_multiple_start_stop_cycles(self):
        """Test multiple start/stop cycles work correctly."""
        monitor = ResourceMonitor()

        for _ in range(3):
            monitor.start_monitoring()
            assert monitor._monitoring_thread.is_alive()
            time.sleep(0.5)
            monitor.stop_monitoring()
            assert not monitor._monitoring_thread.is_alive()

    @patch('src.monitoring.resource_monitor.ResourceMonitor._record_system_metrics')
    def test_monitoring_loop_handles_exceptions(self, mock_record):
        """Test monitoring loop handles exceptions in metric collection."""
        # Make _record_system_metrics raise an exception
        mock_record.side_effect = Exception("Test exception")

        monitor = ResourceMonitor()
        monitor.start_monitoring(interval_seconds=1)

        # Give time for exception to be raised and handled
        time.sleep(2)

        # Thread should still be alive despite exception
        assert monitor._monitoring_thread.is_alive()

        monitor.stop_monitoring()

    def test_stop_monitoring_thread_timeout(self):
        """Test logging when thread doesn't stop within timeout."""
        monitor = ResourceMonitor()

        # Patch the thread's join to simulate timeout
        monitor.start_monitoring()
        original_join = monitor._monitoring_thread.join

        # Make join return immediately but thread reports as still alive
        def mock_join(timeout=None):
            # Don't actually join, simulating timeout
            pass

        with patch.object(monitor._monitoring_thread, 'join', side_effect=mock_join):
            with patch.object(monitor._monitoring_thread, 'is_alive', return_value=True):
                # This should trigger the timeout error log
                monitor.stop_monitoring()

        # Clean up the actual thread
        monitor._stop_event.set()
        original_join(timeout=1)
