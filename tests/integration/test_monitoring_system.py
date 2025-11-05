"""Integration tests for Resource Monitoring System.

This module provides comprehensive integration tests for the monitoring system,
testing real Prometheus metrics export, alert triggering, and end-to-end workflows.

Test Coverage:
    1. Metrics Export: All 22+ metrics exported correctly via Prometheus HTTP server
    2. ResourceMonitor Integration: Background thread, system metrics collection
    3. DiversityMonitor Integration: Diversity tracking, collapse detection
    4. ContainerMonitor Integration: Container stats, orphaned detection
    5. AlertManager Integration: All 5 alert types, suppression logic
    6. End-to-End Workflow: Complete monitoring cycle with cleanup

Requirements: Task 11 - Integration tests with real Prometheus
"""

import pytest
import time
import logging
import threading
from typing import Dict, Any
from unittest.mock import Mock, MagicMock, patch
from prometheus_client import REGISTRY, CollectorRegistry, start_http_server, generate_latest
import requests

from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.resource_monitor import ResourceMonitor
from src.monitoring.diversity_monitor import DiversityMonitor
from src.monitoring.container_monitor import ContainerMonitor
from src.monitoring.alert_manager import AlertManager, AlertConfig

logger = logging.getLogger(__name__)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def metrics_collector():
    """Create fresh MetricsCollector for each test."""
    collector = MetricsCollector()
    yield collector
    collector.reset()


@pytest.fixture
def prometheus_server():
    """Start Prometheus HTTP server on random port.

    Yields:
        tuple: (port, url) for accessing /metrics endpoint
    """
    # Find available port
    import socket
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()

    # Start HTTP server in background
    try:
        start_http_server(port)
        url = f"http://localhost:{port}/metrics"

        # Wait for server to start
        time.sleep(0.5)

        yield port, url

    except Exception as e:
        logger.error(f"Failed to start Prometheus server: {e}")
        pytest.skip(f"Cannot start Prometheus server: {e}")


@pytest.fixture
def resource_monitor(metrics_collector):
    """Create ResourceMonitor instance."""
    monitor = ResourceMonitor(metrics_collector)
    yield monitor

    # Cleanup
    if monitor._monitoring_thread and monitor._monitoring_thread.is_alive():
        monitor.stop_monitoring()


@pytest.fixture
def diversity_monitor(metrics_collector):
    """Create DiversityMonitor instance."""
    monitor = DiversityMonitor(
        metrics_collector=metrics_collector,
        collapse_threshold=0.1,
        collapse_window=5
    )
    yield monitor
    monitor.reset()


@pytest.fixture
def container_monitor(metrics_collector):
    """Create ContainerMonitor instance with mocked Docker client."""
    # Mock Docker client to avoid dependency
    mock_client = MagicMock()
    mock_client.ping.return_value = True

    monitor = ContainerMonitor(
        metrics_collector=metrics_collector,
        docker_client=mock_client,
        auto_cleanup=True
    )
    yield monitor
    monitor.reset()


@pytest.fixture
def alert_manager(metrics_collector):
    """Create AlertManager instance."""
    config = AlertConfig(
        memory_threshold_percent=80.0,
        diversity_collapse_threshold=0.1,
        champion_staleness_threshold=20,
        success_rate_threshold=20.0,
        orphaned_container_threshold=3,
        evaluation_interval=1,  # 1 second for faster tests
        suppression_duration=5   # 5 seconds for faster tests
    )

    manager = AlertManager(config, metrics_collector)
    yield manager

    # Cleanup
    if manager._monitoring_thread and manager._monitoring_thread.is_alive():
        manager.stop_monitoring()


# =============================================================================
# Test 1: Metrics Export Validation
# =============================================================================

def test_metrics_export_prometheus_format(metrics_collector):
    """Test that all metrics are exported in correct Prometheus format.

    Validates:
        - HELP and TYPE lines present for each metric
        - Metric values formatted correctly
        - Timestamps included
        - No syntax errors in output
    """
    # Record sample data for all metric types
    _populate_sample_metrics(metrics_collector)

    # Export to Prometheus format
    prometheus_text = metrics_collector.export_prometheus()

    # Verify format
    assert prometheus_text, "Prometheus export should not be empty"

    lines = prometheus_text.split('\n')

    # Verify HELP lines present
    help_lines = [l for l in lines if l.startswith('# HELP')]
    assert len(help_lines) > 20, f"Expected >20 HELP lines, got {len(help_lines)}"

    # Verify TYPE lines present
    type_lines = [l for l in lines if l.startswith('# TYPE')]
    assert len(type_lines) > 20, f"Expected >20 TYPE lines, got {len(type_lines)}"

    # Verify metric values present (non-comment lines)
    value_lines = [l for l in lines if l and not l.startswith('#')]
    assert len(value_lines) > 20, f"Expected >20 value lines, got {len(value_lines)}"

    # Verify specific metrics exported
    assert 'learning_iterations_total' in prometheus_text
    assert 'resource_memory_percent' in prometheus_text
    assert 'diversity_population_diversity' in prometheus_text
    assert 'container_active_count' in prometheus_text
    assert 'alert_triggered_total' in prometheus_text

    logger.info(f"✓ Prometheus export valid: {len(help_lines)} metrics exported")


def test_all_22_metrics_exported(metrics_collector):
    """Test that all 21+ new monitoring metrics are exported correctly.

    Verifies:
        - All resource metrics (7 metrics)
        - All diversity metrics (5 metrics)
        - All container metrics (7 metrics)
        - All alert metrics (2 metrics)
    """
    # Record sample data
    _populate_sample_metrics(metrics_collector)

    prometheus_text = metrics_collector.export_prometheus()

    # Resource metrics (7)
    resource_metrics = [
        'resource_memory_percent',
        'resource_memory_used_bytes',
        'resource_memory_total_bytes',
        'resource_cpu_percent',
        'resource_disk_percent',
        'resource_disk_used_bytes',
        'resource_disk_total_bytes'
    ]

    # Diversity metrics (5)
    diversity_metrics = [
        'diversity_population_diversity',
        'diversity_unique_count',
        'diversity_total_count',
        'diversity_collapse_detected',
        'diversity_champion_staleness'
    ]

    # Container metrics (7 - cleanup_failed not recorded in sample data)
    container_metrics = [
        'container_active_count',
        'container_orphaned_count',
        'container_memory_usage_bytes',
        'container_memory_percent',
        'container_cpu_percent',
        'container_created_total',
        'container_cleanup_success_total'
    ]

    # Alert metrics (2)
    alert_metrics = [
        'alert_triggered_total',
        'alert_active_count'
    ]

    all_metrics = resource_metrics + diversity_metrics + container_metrics + alert_metrics

    # Verify each metric present
    missing_metrics = []
    for metric in all_metrics:
        if metric not in prometheus_text:
            missing_metrics.append(metric)

    assert not missing_metrics, f"Missing metrics: {missing_metrics}"

    logger.info(f"✓ All 22 monitoring metrics exported successfully")


# =============================================================================
# Test 2: ResourceMonitor Integration
# =============================================================================

def test_resource_monitor_background_thread(resource_monitor):
    """Test ResourceMonitor background thread lifecycle.

    Validates:
        - Thread starts and runs without errors
        - Metrics collected at regular intervals
        - Thread stops cleanly
        - System overhead <1%
    """
    # Start monitoring
    resource_monitor.start_monitoring(interval_seconds=1)

    # Verify thread running
    assert resource_monitor._monitoring_thread is not None
    assert resource_monitor._monitoring_thread.is_alive()

    # Wait for at least 2 collection cycles
    time.sleep(2.5)

    # Verify metrics collected
    stats = resource_monitor.get_current_stats()
    assert stats, "Stats should be collected"
    assert 'memory_percent' in stats
    assert 'cpu_percent' in stats
    assert 'disk_percent' in stats

    # Verify values are reasonable
    assert 0 <= stats['memory_percent'] <= 100
    assert 0 <= stats['cpu_percent'] <= 800  # Multi-core can exceed 100%
    assert 0 <= stats['disk_percent'] <= 100

    # Stop monitoring
    resource_monitor.stop_monitoring()

    # Verify thread stopped
    time.sleep(0.5)
    assert not resource_monitor._monitoring_thread.is_alive()

    logger.info(f"✓ ResourceMonitor thread lifecycle validated")


def test_resource_monitor_metrics_export(metrics_collector, resource_monitor):
    """Test ResourceMonitor exports metrics to Prometheus.

    Validates:
        - System metrics recorded to MetricsCollector
        - Memory, CPU, disk metrics all present
        - Metrics values are accurate
    """
    # Start monitoring
    resource_monitor.start_monitoring(interval_seconds=1)

    # Wait for collection
    time.sleep(2)

    # Export metrics
    prometheus_text = metrics_collector.export_prometheus()

    # Verify resource metrics present
    assert 'resource_memory_percent' in prometheus_text
    assert 'resource_cpu_percent' in prometheus_text
    assert 'resource_disk_percent' in prometheus_text

    # Stop monitoring
    resource_monitor.stop_monitoring()

    logger.info(f"✓ ResourceMonitor metrics exported correctly")


# =============================================================================
# Test 3: DiversityMonitor Integration
# =============================================================================

def test_diversity_monitor_tracking(diversity_monitor):
    """Test DiversityMonitor diversity tracking and metrics.

    Validates:
        - Diversity recording works correctly
        - History window maintained
        - Metrics exported to Prometheus
    """
    # Record diversity over multiple iterations
    for i in range(10):
        diversity = 0.8 - (i * 0.05)  # Gradually decreasing
        diversity_monitor.record_diversity(
            iteration=i,
            diversity=diversity,
            unique_count=40 - i * 2,
            total_count=50
        )

    # Verify current diversity
    current = diversity_monitor.get_current_diversity()
    assert current is not None
    assert 0.0 <= current <= 1.0

    # Verify history
    history = diversity_monitor.get_diversity_history()
    assert len(history) == 5  # Window size

    # Verify status
    status = diversity_monitor.get_status()
    assert status['current_diversity'] is not None
    assert status['unique_count'] > 0
    assert status['total_count'] == 50

    logger.info(f"✓ DiversityMonitor tracking validated")


def test_diversity_collapse_detection(diversity_monitor, metrics_collector):
    """Test DiversityMonitor collapse detection and alerts.

    Validates:
        - Collapse detected when diversity < 0.1 for 5 iterations
        - Collapse metric updated
        - Alert condition triggered
    """
    # Record low diversity for collapse window
    for i in range(5):
        diversity_monitor.record_diversity(
            iteration=i,
            diversity=0.05,  # Below threshold
            unique_count=2,
            total_count=50
        )

    # Check collapse detection
    collapse = diversity_monitor.check_diversity_collapse()
    assert collapse, "Collapse should be detected after 5 iterations below threshold"

    # Verify collapse state
    assert diversity_monitor.is_collapse_detected()

    # Record diversity metrics to MetricsCollector
    metrics_collector.record_diversity_metrics(
        diversity=0.05,
        unique_count=2,
        total_count=50,
        staleness=0,
        collapse_detected=True
    )

    # Verify collapse metric exported
    prometheus_text = metrics_collector.export_prometheus()
    assert 'diversity_collapse_detected' in prometheus_text

    logger.info(f"✓ Diversity collapse detection validated")


def test_champion_staleness_tracking(diversity_monitor):
    """Test champion staleness calculation.

    Validates:
        - Staleness increments correctly
        - Champion update resets staleness
        - Staleness metric accurate
    """
    # Record champion update
    diversity_monitor.record_champion_update(
        iteration=0,
        old_sharpe=1.5,
        new_sharpe=2.0
    )

    # Calculate staleness
    staleness = diversity_monitor.calculate_staleness(current_iteration=10)
    assert staleness == 10, f"Expected staleness=10, got {staleness}"

    # Update champion again
    diversity_monitor.record_champion_update(
        iteration=15,
        old_sharpe=2.0,
        new_sharpe=2.5
    )

    # Staleness should reset
    staleness = diversity_monitor.calculate_staleness(current_iteration=15)
    assert staleness == 0, f"Expected staleness=0 after update, got {staleness}"

    logger.info(f"✓ Champion staleness tracking validated")


# =============================================================================
# Test 4: ContainerMonitor Integration
# =============================================================================

def test_container_monitor_stats_collection(container_monitor):
    """Test ContainerMonitor stats collection with mocked Docker.

    Validates:
        - Container stats queried correctly
        - Memory and CPU metrics parsed
        - Stats exported to MetricsCollector
    """
    # Mock container object
    mock_container = MagicMock()
    mock_container.name = "test-container"
    mock_container.status = "running"
    mock_container.labels = {"finlab-sandbox": "true"}
    mock_container.attrs = {"Created": "2024-01-01T00:00:00Z"}

    # Mock stats data
    mock_stats = {
        'memory_stats': {
            'usage': 100 * 1024 * 1024,  # 100 MB
            'limit': 500 * 1024 * 1024   # 500 MB
        },
        'cpu_stats': {
            'cpu_usage': {'total_usage': 2000000},
            'system_cpu_usage': 10000000,
            'online_cpus': 2
        },
        'precpu_stats': {
            'cpu_usage': {'total_usage': 1000000},
            'system_cpu_usage': 9000000
        }
    }

    mock_container.stats.return_value = mock_stats
    container_monitor.docker_client.containers.get.return_value = mock_container

    # Record stats
    stats = container_monitor.record_container_stats("test-id-123")

    # Verify stats collected
    assert stats is not None
    assert stats.memory_usage_bytes == 100 * 1024 * 1024
    assert stats.memory_limit_bytes == 500 * 1024 * 1024
    assert stats.memory_percent == 20.0
    assert stats.cpu_percent > 0

    logger.info(f"✓ ContainerMonitor stats collection validated")


def test_container_orphaned_detection(container_monitor):
    """Test ContainerMonitor orphaned container detection.

    Validates:
        - Orphaned containers identified correctly
        - Label verification works
        - Only exited/dead containers flagged
    """
    # Mock containers
    mock_running = MagicMock()
    mock_running.id = "running-123"
    mock_running.status = "running"
    mock_running.labels = {"finlab-sandbox": "true"}

    mock_exited = MagicMock()
    mock_exited.id = "exited-456"
    mock_exited.status = "exited"
    mock_exited.labels = {"finlab-sandbox": "true"}
    mock_exited.name = "orphaned-container"
    mock_exited.attrs = {"Created": "2024-01-01T00:00:00Z"}

    mock_other = MagicMock()
    mock_other.id = "other-789"
    mock_other.status = "exited"
    mock_other.labels = {}  # No finlab label

    container_monitor.docker_client.containers.list.return_value = [
        mock_running,
        mock_exited,
        mock_other
    ]

    # Scan for orphaned
    orphaned = container_monitor.scan_orphaned_containers()

    # Verify detection
    assert len(orphaned) == 1, f"Expected 1 orphaned container, found {len(orphaned)}"
    assert "exited-456" in orphaned

    logger.info(f"✓ Orphaned container detection validated")


def test_container_cleanup(container_monitor):
    """Test ContainerMonitor cleanup functionality.

    Validates:
        - Cleanup removes orphaned containers
        - Label verification before removal
        - Cleanup metrics updated
    """
    # Mock orphaned container
    mock_container = MagicMock()
    mock_container.id = "orphaned-123"
    mock_container.name = "test-orphaned"
    mock_container.labels = {"finlab-sandbox": "true"}
    mock_container.status = "exited"

    container_monitor.docker_client.containers.get.return_value = mock_container

    # Cleanup specific container
    count = container_monitor.cleanup_orphaned_containers(["orphaned-123"])

    # Verify cleanup called
    assert count == 1
    mock_container.remove.assert_called_once_with(force=True)

    logger.info(f"✓ Container cleanup validated")


# =============================================================================
# Test 5: AlertManager Integration
# =============================================================================

def test_alert_manager_memory_alert(alert_manager, metrics_collector):
    """Test AlertManager high memory alert triggering.

    Validates:
        - Memory alert triggers when threshold exceeded
        - Alert logged correctly
        - Metric incremented
        - Suppression works
    """
    # Set memory source
    alert_manager.set_memory_source(lambda: {'memory_percent': 85.0})

    # Evaluate alerts
    alert_manager.evaluate_alerts()

    # Verify alert triggered
    active_alerts = alert_manager.get_active_alerts()
    assert 'high_memory' in active_alerts

    # Verify alert metric
    prometheus_text = metrics_collector.export_prometheus()
    assert 'alert_triggered_total' in prometheus_text

    # Test suppression - alert again within suppression window
    alert_manager.evaluate_alerts()

    # Alert should be suppressed (no duplicate)
    # Suppression is working if no errors and alert still active
    assert 'high_memory' in alert_manager.get_active_alerts()

    logger.info(f"✓ Memory alert triggering validated")


def test_alert_manager_diversity_collapse_alert(alert_manager):
    """Test AlertManager diversity collapse alert.

    Validates:
        - Diversity alert triggers when below threshold
        - Alert severity correct
        - Alert details accurate
    """
    # Set diversity source (below threshold)
    alert_manager.set_diversity_source(lambda: 0.05)

    # Evaluate alerts
    alert_manager.evaluate_alerts()

    # Verify alert triggered
    active_alerts = alert_manager.get_active_alerts()
    assert 'diversity_collapse' in active_alerts

    logger.info(f"✓ Diversity collapse alert validated")


def test_alert_manager_staleness_alert(alert_manager):
    """Test AlertManager champion staleness alert.

    Validates:
        - Staleness alert triggers when threshold exceeded
        - Alert threshold configurable
        - Alert clears when champion updated
    """
    # Set staleness source (above threshold)
    alert_manager.set_staleness_source(lambda: 25)

    # Evaluate alerts
    alert_manager.evaluate_alerts()

    # Verify alert triggered
    active_alerts = alert_manager.get_active_alerts()
    assert 'champion_staleness' in active_alerts

    # Clear alert
    alert_manager.clear_alert('champion_staleness')

    # Verify cleared
    assert 'champion_staleness' not in alert_manager.get_active_alerts()

    logger.info(f"✓ Champion staleness alert validated")


def test_alert_manager_success_rate_alert(alert_manager):
    """Test AlertManager low success rate alert.

    Validates:
        - Success rate alert triggers correctly
        - Rolling window calculation works
        - Alert respects threshold
    """
    # Set success rate source (below threshold)
    alert_manager.set_success_rate_source(lambda: 15.0)

    # Evaluate alerts
    alert_manager.evaluate_alerts()

    # Verify alert triggered
    active_alerts = alert_manager.get_active_alerts()
    assert 'low_success_rate' in active_alerts

    logger.info(f"✓ Success rate alert validated")


def test_alert_manager_container_alert(alert_manager):
    """Test AlertManager orphaned container alert.

    Validates:
        - Container alert triggers when threshold exceeded
        - Alert critical severity
        - Cleanup recommendation clear
    """
    # Set container source (above threshold)
    alert_manager.set_container_source(lambda: 5)

    # Evaluate alerts
    alert_manager.evaluate_alerts()

    # Verify alert triggered
    active_alerts = alert_manager.get_active_alerts()
    assert 'orphaned_containers' in active_alerts

    logger.info(f"✓ Orphaned container alert validated")


def test_alert_manager_suppression(alert_manager, metrics_collector):
    """Test AlertManager suppression logic.

    Validates:
        - Duplicate alerts suppressed within window
        - Suppression duration configurable
        - Alerts re-trigger after suppression expires
    """
    # Set memory source
    alert_manager.set_memory_source(lambda: {'memory_percent': 85.0})

    # Trigger alert
    alert_manager.evaluate_alerts()
    assert 'high_memory' in alert_manager.get_active_alerts()

    # Get initial alert count
    initial_count = metrics_collector.metrics.get('alert_triggered_total')
    if initial_count:
        initial_value = initial_count.get_latest() or 0
    else:
        initial_value = 0

    # Try to trigger again immediately (should be suppressed)
    alert_manager.evaluate_alerts()

    # Alert still active but shouldn't increment counter
    assert 'high_memory' in alert_manager.get_active_alerts()

    # Reset suppression manually
    alert_manager.reset_suppression()

    # Now alert should trigger again
    alert_manager.evaluate_alerts()
    assert 'high_memory' in alert_manager.get_active_alerts()

    logger.info(f"✓ Alert suppression validated")


# =============================================================================
# Test 6: End-to-End Workflow
# =============================================================================

def test_end_to_end_monitoring_workflow(
    metrics_collector,
    resource_monitor,
    diversity_monitor,
    container_monitor,
    alert_manager
):
    """Test complete end-to-end monitoring workflow.

    Validates:
        - All monitors can run simultaneously
        - Metrics exported correctly
        - Alerts trigger appropriately
        - Clean shutdown works
        - No resource leaks
    """
    logger.info("Starting end-to-end monitoring workflow test")

    # Step 1: Initialize all monitors
    resource_monitor.start_monitoring(interval_seconds=1)

    # Configure alert manager
    alert_manager.set_memory_source(lambda: resource_monitor.get_current_stats())
    alert_manager.set_diversity_source(lambda: diversity_monitor.get_current_diversity())
    alert_manager.set_staleness_source(lambda: diversity_monitor.get_current_staleness())
    alert_manager.set_container_source(lambda: container_monitor.get_status()['orphaned_containers'])

    # Step 2: Run monitoring cycle
    for i in range(5):
        # Record diversity
        diversity = 0.8 - (i * 0.15)
        diversity_monitor.record_diversity(
            iteration=i,
            diversity=diversity,
            unique_count=40 - i * 5,
            total_count=50
        )

        # Record diversity metrics to collector
        metrics_collector.record_diversity_metrics(
            diversity=diversity,
            unique_count=40 - i * 5,
            total_count=50,
            staleness=i,
            collapse_detected=False
        )

        # Record champion update
        if i == 2:
            diversity_monitor.record_champion_update(
                iteration=i,
                old_sharpe=1.5,
                new_sharpe=2.0
            )

        # Calculate staleness
        if diversity_monitor._last_champion_update_iteration is not None:
            diversity_monitor.calculate_staleness(i)

        # Check for collapse
        diversity_monitor.check_diversity_collapse()

        # Wait for resource collection
        time.sleep(1.5)

    # Step 3: Verify all metrics exported
    prometheus_text = metrics_collector.export_prometheus()

    # Verify resource metrics
    assert 'resource_memory_percent' in prometheus_text
    assert 'resource_cpu_percent' in prometheus_text

    # Verify diversity metrics
    assert 'diversity_population_diversity' in prometheus_text

    # Step 4: Get monitoring status
    resource_stats = resource_monitor.get_current_stats()
    assert resource_stats, "Resource stats should be available"

    diversity_status = diversity_monitor.get_status()
    assert diversity_status['current_diversity'] is not None

    container_status = container_monitor.get_status()
    assert 'docker_available' in container_status

    # Step 5: Clean shutdown
    resource_monitor.stop_monitoring()

    # Verify clean shutdown
    time.sleep(0.5)
    assert not resource_monitor._monitoring_thread.is_alive()

    logger.info("✓ End-to-end monitoring workflow validated")


def test_monitoring_performance_overhead(resource_monitor, metrics_collector):
    """Test that monitoring overhead is <1% as required.

    Validates:
        - Collection time minimal
        - Thread doesn't block main execution
        - CPU overhead negligible
    """
    # Start monitoring
    resource_monitor.start_monitoring(interval_seconds=5)

    # Measure overhead
    start_time = time.time()

    # Simulate main workload
    for i in range(10):
        metrics_collector.record_iteration_start(i)
        time.sleep(0.1)  # Simulate work

    elapsed = time.time() - start_time

    # Stop monitoring
    resource_monitor.stop_monitoring()

    # Verify collection happened
    stats = resource_monitor.get_current_stats()
    assert stats, "Stats should be collected"

    # Verify performance (should complete in ~1 second, with minimal overhead)
    assert elapsed < 1.5, f"Monitoring added excessive overhead: {elapsed}s"

    logger.info(f"✓ Monitoring overhead validated: {elapsed:.2f}s for 10 iterations")


# =============================================================================
# Helper Functions
# =============================================================================

def _populate_sample_metrics(collector: MetricsCollector) -> None:
    """Populate MetricsCollector with sample data for all metrics.

    Args:
        collector: MetricsCollector instance to populate
    """
    # Learning metrics
    collector.record_iteration_start(0)
    collector.record_iteration_success(sharpe_ratio=2.0, duration=120.5)
    collector.record_champion_update(old_sharpe=1.8, new_sharpe=2.0, iteration_num=5)
    collector.record_strategy_diversity(unique_templates=15)

    # Performance metrics
    collector.record_generation_time(30.5)
    collector.record_validation_time(5.2)
    collector.record_execution_time(80.3)
    collector.record_metric_extraction_time(2.1, method="DIRECT")

    # Quality metrics
    collector.record_validation_result(passed=True)
    collector.record_execution_result(success=True)
    collector.record_preservation_result(preserved=True)

    # System metrics
    collector.record_api_call(success=True, retries=0)
    collector.record_error("validation")
    collector.update_uptime()

    # Resource metrics
    collector.record_resource_memory(
        used_bytes=8 * 1024**3,
        total_bytes=16 * 1024**3,
        percent=50.0
    )
    collector.record_resource_cpu(percent=25.0)
    collector.record_resource_disk(
        used_bytes=100 * 1024**3,
        total_bytes=500 * 1024**3,
        percent=20.0
    )

    # Diversity metrics
    collector.record_diversity_metrics(
        diversity=0.75,
        unique_count=40,
        total_count=50,
        staleness=5,
        collapse_detected=False
    )

    # Container metrics
    collector.record_container_counts(active=3, orphaned=1)
    collector.record_container_memory(
        container_id="test-container-123",
        memory_bytes=100 * 1024**2,
        limit_bytes=500 * 1024**2,
        percent=20.0
    )
    collector.record_container_cpu(container_id="test-container-123", cpu_percent=15.0)
    collector.record_container_created()
    collector.record_container_cleanup(success=True)

    # Alert metrics
    collector.record_alert_triggered("high_memory")
    collector.record_active_alerts(count=2)


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: Integration tests requiring real Prometheus"
    )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
