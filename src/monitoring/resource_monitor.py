"""Resource Monitor for System Resource Tracking.

This module provides real-time system resource monitoring (CPU, memory, disk) with
background thread collection and Prometheus metric export. Designed for <1% overhead
while providing critical visibility into resource exhaustion and memory leaks.

Architecture:
- Background thread runs every 5 seconds collecting psutil metrics
- Non-blocking operation - failures don't halt main thread
- Integrates with existing MetricsCollector for Prometheus export
- Graceful degradation on psutil errors

Requirements: Task 1 - Resource Monitoring System
"""

import logging
import threading
import time
from typing import Dict, Any, Optional
import psutil

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitor system resources (CPU, memory, disk) in background thread.

    Features:
    - Background thread collection every 5 seconds
    - CPU, memory, and disk usage tracking via psutil
    - Non-blocking operation with <1% CPU overhead
    - Graceful error handling for psutil failures
    - Integration with MetricsCollector for Prometheus export

    Example:
        >>> from src.monitoring.metrics_collector import MetricsCollector
        >>> collector = MetricsCollector()
        >>> monitor = ResourceMonitor(collector)
        >>> monitor.start_monitoring()
        >>> # ... run your workload ...
        >>> stats = monitor.get_current_stats()
        >>> monitor.stop_monitoring()
    """

    def __init__(self, metrics_collector: Optional['MetricsCollector'] = None):
        """Initialize ResourceMonitor.

        Args:
            metrics_collector: Shared MetricsCollector instance for Prometheus export.
                             If None, monitoring runs but metrics not exported.
        """
        self.metrics_collector = metrics_collector
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._current_stats: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._collection_interval = 5  # seconds

        logger.info("ResourceMonitor initialized")

    def start_monitoring(self, interval_seconds: int = 5) -> None:
        """Start background thread collecting resource stats.

        Args:
            interval_seconds: Collection interval in seconds (default: 5)

        Raises:
            RuntimeError: If monitoring already started
        """
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            raise RuntimeError("Monitoring already started")

        self._collection_interval = interval_seconds
        self._stop_event.clear()

        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="ResourceMonitor",
            daemon=True
        )
        self._monitoring_thread.start()

        logger.info(f"ResourceMonitor started with {interval_seconds}s interval")

    def stop_monitoring(self) -> None:
        """Stop background monitoring thread.

        Blocks until thread exits gracefully (max 10 seconds).
        """
        if not self._monitoring_thread or not self._monitoring_thread.is_alive():
            logger.warning("Monitoring not running, nothing to stop")
            return

        logger.info("Stopping ResourceMonitor...")
        self._stop_event.set()

        # Wait for thread to exit (max 10 seconds)
        self._monitoring_thread.join(timeout=10.0)

        if self._monitoring_thread.is_alive():
            logger.error("ResourceMonitor thread did not stop within timeout")
        else:
            logger.info("ResourceMonitor stopped successfully")

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current resource statistics.

        Returns:
            Dictionary with current CPU%, memory%, disk% and absolute values.
            Returns empty dict if no stats collected yet.

        Example:
            {
                'memory_percent': 45.2,
                'memory_used_gb': 7.2,
                'memory_total_gb': 16.0,
                'cpu_percent': 15.3,
                'disk_percent': 62.1,
                'disk_used_gb': 124.5,
                'disk_total_gb': 200.0
            }
        """
        with self._lock:
            return self._current_stats.copy()

    def _monitoring_loop(self) -> None:
        """Background thread loop for collecting metrics.

        Runs until stop_event is set. Collects metrics every interval_seconds.
        Handles psutil errors gracefully without halting thread.
        """
        logger.info("ResourceMonitor background thread started")

        while not self._stop_event.is_set():
            try:
                self._record_system_metrics()
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}", exc_info=True)

            # Sleep with interruptible check for stop event
            self._stop_event.wait(timeout=self._collection_interval)

        logger.info("ResourceMonitor background thread exited")

    def _record_system_metrics(self) -> None:
        """Collect and record system metrics to Prometheus.

        Collects:
        - Memory: used, total, percent
        - CPU: percent usage (averaged over 1 second)
        - Disk: used, total, percent (root partition)

        Updates internal _current_stats and exports to MetricsCollector if available.
        """
        try:
            # Collect memory stats
            memory = psutil.virtual_memory()
            memory_used_gb = memory.used / (1024 ** 3)
            memory_total_gb = memory.total / (1024 ** 3)
            memory_percent = memory.percent

            # Collect CPU stats (1-second average)
            cpu_percent = psutil.cpu_percent(interval=1.0)

            # Collect disk stats (root partition)
            disk = psutil.disk_usage('/')
            disk_used_gb = disk.used / (1024 ** 3)
            disk_total_gb = disk.total / (1024 ** 3)
            disk_percent = disk.percent

            # Update internal state
            stats = {
                'memory_percent': memory_percent,
                'memory_used_gb': memory_used_gb,
                'memory_total_gb': memory_total_gb,
                'cpu_percent': cpu_percent,
                'disk_percent': disk_percent,
                'disk_used_gb': disk_used_gb,
                'disk_total_gb': disk_total_gb,
                'timestamp': time.time()
            }

            with self._lock:
                self._current_stats = stats

            # Export to MetricsCollector if available
            if self.metrics_collector:
                self._export_to_metrics_collector(stats)

            logger.debug(
                f"Collected system metrics: "
                f"mem={memory_percent:.1f}%, cpu={cpu_percent:.1f}%, disk={disk_percent:.1f}%"
            )

        except psutil.Error as e:
            logger.warning(f"psutil error collecting metrics: {e}")
        except Exception as e:
            logger.error(f"Unexpected error collecting metrics: {e}", exc_info=True)

    def _export_to_metrics_collector(self, stats: Dict[str, Any]) -> None:
        """Export collected stats to MetricsCollector.

        Args:
            stats: Dictionary of collected statistics
        """
        try:
            # Record memory metrics
            if hasattr(self.metrics_collector, 'record_resource_memory'):
                self.metrics_collector.record_resource_memory(
                    used_bytes=stats['memory_used_gb'] * (1024 ** 3),
                    total_bytes=stats['memory_total_gb'] * (1024 ** 3),
                    percent=stats['memory_percent']
                )

            # Record CPU metric
            if hasattr(self.metrics_collector, 'record_resource_cpu'):
                self.metrics_collector.record_resource_cpu(percent=stats['cpu_percent'])

            # Record disk metrics
            if hasattr(self.metrics_collector, 'record_resource_disk'):
                self.metrics_collector.record_resource_disk(
                    used_bytes=stats['disk_used_gb'] * (1024 ** 3),
                    total_bytes=stats['disk_total_gb'] * (1024 ** 3),
                    percent=stats['disk_percent']
                )

        except Exception as e:
            logger.warning(f"Failed to export metrics to collector: {e}")

    def __enter__(self):
        """Context manager entry - start monitoring."""
        self.start_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop monitoring."""
        self.stop_monitoring()
        return False
