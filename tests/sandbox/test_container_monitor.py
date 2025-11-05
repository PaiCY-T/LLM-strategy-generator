"""
Unit Tests for ContainerMonitor Module

Tests container resource monitoring, orphaned container detection,
and Prometheus metrics export with mocked Docker SDK.

Coverage target: >85% (mocking all Docker interactions)
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from typing import Dict, Any

from src.monitoring.metrics_collector import MetricsCollector

# Mock docker module before importing container_monitor
import sys
from unittest.mock import MagicMock

# Create mock docker module
mock_docker = MagicMock()
mock_docker.errors = MagicMock()
mock_docker.errors.DockerException = Exception
mock_docker.errors.NotFound = type('NotFound', (Exception,), {})
mock_docker.errors.APIError = type('APIError', (Exception,), {})
sys.modules['docker'] = mock_docker
sys.modules['docker.errors'] = mock_docker.errors
sys.modules['docker.models'] = MagicMock()
sys.modules['docker.models.containers'] = MagicMock()

# Now import after mocking
from src.sandbox.container_monitor import (
    ContainerMonitor,
    ContainerStats,
    ContainerStatus,
)


@pytest.fixture
def mock_docker_client():
    """Create mock Docker client."""
    with patch('src.sandbox.container_monitor.docker') as mock_docker:
        client = MagicMock()
        client.ping.return_value = True
        mock_docker.from_env.return_value = client
        yield client


@pytest.fixture
def metrics_collector():
    """Create MetricsCollector instance."""
    return MetricsCollector()


@pytest.fixture
def container_monitor(mock_docker_client, metrics_collector):
    """Create ContainerMonitor instance with mocked Docker client."""
    monitor = ContainerMonitor(
        metrics_collector=metrics_collector,
        docker_client=mock_docker_client,
        alert_threshold=3,
        cleanup_enabled=True
    )
    return monitor


def create_mock_container(
    container_id: str = "abc123456789",
    name: str = "test-container",
    status: str = "running",
    labels: Dict[str, str] = None,
    created: str = "2024-10-26T00:00:00Z",
    finished: str = None
) -> Mock:
    """Create a mock Docker container object.

    Args:
        container_id: Full container ID
        name: Container name
        status: Container status
        labels: Container labels
        created: Creation timestamp
        finished: Finish timestamp (if exited)

    Returns:
        Mock container object with required attributes
    """
    container = Mock()
    container.short_id = container_id[:12]
    container.name = name
    container.status = status
    container.labels = labels or {}

    # Mock attrs
    container.attrs = {
        'State': {
            'Status': status,
            'Created': created,
        }
    }

    if finished:
        container.attrs['State']['FinishedAt'] = finished
    else:
        container.attrs['State']['FinishedAt'] = '0001-01-01T00:00:00Z'

    # Mock reload method
    container.reload = Mock()

    # Mock stats method (for running containers)
    if status == 'running':
        container.stats = Mock(return_value={
            'memory_stats': {
                'usage': 500 * 1024 * 1024,  # 500 MB
                'limit': 2 * 1024 * 1024 * 1024,  # 2 GB
            },
            'cpu_stats': {
                'cpu_usage': {'total_usage': 1000000000},
                'system_cpu_usage': 10000000000,
                'online_cpus': 4
            },
            'precpu_stats': {
                'cpu_usage': {'total_usage': 900000000},
                'system_cpu_usage': 9500000000
            }
        })

    # Mock remove method
    container.remove = Mock()

    return container


class TestContainerMonitorInitialization:
    """Test ContainerMonitor initialization."""

    def test_successful_initialization(self, mock_docker_client, metrics_collector):
        """Test successful monitor initialization."""
        monitor = ContainerMonitor(
            metrics_collector=metrics_collector,
            docker_client=mock_docker_client,
            alert_threshold=5,
            cleanup_enabled=True
        )

        assert monitor.client == mock_docker_client
        assert monitor.metrics_collector == metrics_collector
        assert monitor.alert_threshold == 5
        assert monitor.cleanup_enabled is True
        assert monitor.FINLAB_LABEL == "finlab-sandbox"

        # Verify Docker ping was called
        mock_docker_client.ping.assert_called_once()

    def test_initialization_without_metrics_collector(self, mock_docker_client):
        """Test initialization without MetricsCollector."""
        monitor = ContainerMonitor(
            metrics_collector=None,
            docker_client=mock_docker_client
        )

        assert monitor.metrics_collector is None
        assert monitor.client == mock_docker_client

    def test_initialization_creates_docker_client_if_none(self, metrics_collector):
        """Test Docker client creation when not provided."""
        with patch('src.sandbox.container_monitor.docker') as mock_docker:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_docker.from_env.return_value = mock_client

            monitor = ContainerMonitor(
                metrics_collector=metrics_collector,
                docker_client=None
            )

            assert monitor.client == mock_client
            mock_docker.from_env.assert_called_once()

    def test_initialization_fails_when_docker_unavailable(self, metrics_collector):
        """Test initialization failure when Docker daemon unavailable."""
        with patch('src.sandbox.container_monitor.docker') as mock_docker:
            from docker.errors import DockerException

            mock_client = MagicMock()
            mock_client.ping.side_effect = DockerException("Connection refused")
            mock_docker.from_env.return_value = mock_client

            with pytest.raises(RuntimeError, match="Failed to connect to Docker daemon"):
                ContainerMonitor(
                    metrics_collector=metrics_collector,
                    docker_client=None
                )

    def test_initialization_fails_when_docker_sdk_missing(self, metrics_collector):
        """Test initialization fails gracefully without Docker SDK."""
        with patch('src.sandbox.container_monitor.DOCKER_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="Docker SDK not available"):
                ContainerMonitor(metrics_collector=metrics_collector)


class TestContainerStats:
    """Test ContainerStats dataclass."""

    def test_container_stats_creation(self):
        """Test ContainerStats initialization."""
        created_at = datetime.now()
        stats = ContainerStats(
            container_id="abc123",
            container_name="test-container",
            status=ContainerStatus.RUNNING,
            cpu_percent=45.5,
            memory_usage_mb=500.0,
            memory_limit_mb=2000.0,
            memory_percent=25.0,
            created_at=created_at
        )

        assert stats.container_id == "abc123"
        assert stats.container_name == "test-container"
        assert stats.status == ContainerStatus.RUNNING
        assert stats.cpu_percent == 45.5
        assert stats.memory_usage_mb == 500.0
        assert stats.memory_limit_mb == 2000.0
        assert stats.memory_percent == 25.0
        assert stats.created_at == created_at

    def test_container_stats_to_dict(self):
        """Test ContainerStats serialization to dictionary."""
        created_at = datetime(2024, 10, 26, 12, 0, 0)
        finished_at = datetime(2024, 10, 26, 12, 5, 0)

        stats = ContainerStats(
            container_id="abc123",
            container_name="test-container",
            status=ContainerStatus.EXITED,
            memory_usage_mb=100.0,
            created_at=created_at,
            finished_at=finished_at
        )

        stats_dict = stats.to_dict()

        assert stats_dict['container_id'] == "abc123"
        assert stats_dict['container_name'] == "test-container"
        assert stats_dict['status'] == "exited"
        assert stats_dict['memory_usage_mb'] == 100.0
        assert stats_dict['created_at'] == created_at.isoformat()
        assert stats_dict['finished_at'] == finished_at.isoformat()


class TestGetContainerStats:
    """Test get_container_stats method."""

    def test_get_stats_for_running_container(self, container_monitor, mock_docker_client):
        """Test collecting stats for running container."""
        mock_container = create_mock_container(
            container_id="abc123456789",
            name="test-container",
            status="running",
            labels={"finlab-sandbox": "true"}
        )

        mock_docker_client.containers.get.return_value = mock_container

        stats = container_monitor.get_container_stats("abc123456789")

        assert stats is not None
        assert stats.container_id == "abc123456789"
        assert stats.container_name == "test-container"
        assert stats.status == ContainerStatus.RUNNING
        assert stats.memory_usage_mb == pytest.approx(500.0, rel=0.01)
        assert stats.memory_limit_mb == pytest.approx(2048.0, rel=0.01)  # 2GB in MB
        assert stats.memory_percent == pytest.approx(24.4140625, rel=0.01)  # 500/2048 * 100
        assert stats.cpu_percent > 0  # Should have calculated CPU

        # Verify Docker client calls
        mock_docker_client.containers.get.assert_called_once_with("abc123456789")
        mock_container.reload.assert_called_once()
        mock_container.stats.assert_called_once_with(stream=False)

    def test_get_stats_for_exited_container(self, container_monitor, mock_docker_client):
        """Test collecting stats for exited container (no resource stats)."""
        mock_container = create_mock_container(
            container_id="xyz987654321",
            name="stopped-container",
            status="exited",
            finished="2024-10-26T00:05:00Z"
        )

        mock_docker_client.containers.get.return_value = mock_container

        stats = container_monitor.get_container_stats("xyz987654321")

        assert stats is not None
        assert stats.status == ContainerStatus.EXITED
        assert stats.cpu_percent == 0.0  # No stats for exited containers
        assert stats.memory_usage_mb == 0.0
        assert stats.finished_at is not None

    def test_get_stats_for_nonexistent_container(self, container_monitor, mock_docker_client):
        """Test getting stats for container that doesn't exist."""
        from docker.errors import NotFound

        mock_docker_client.containers.get.side_effect = NotFound("Container not found")

        stats = container_monitor.get_container_stats("nonexistent")

        assert stats is None
        mock_docker_client.containers.get.assert_called_once_with("nonexistent")

    def test_get_stats_handles_api_error(self, container_monitor, mock_docker_client):
        """Test handling of Docker API errors."""
        from docker.errors import APIError

        mock_docker_client.containers.get.side_effect = APIError("API error")

        with pytest.raises(Exception):  # DockerException
            container_monitor.get_container_stats("container123")


class TestScanOrphanedContainers:
    """Test scan_orphaned_containers method."""

    def test_scan_finds_orphaned_containers(self, container_monitor, mock_docker_client):
        """Test scanning successfully finds orphaned containers."""
        # Create mock orphaned containers
        orphaned1 = create_mock_container(
            container_id="orphan1",
            name="orphan-1",
            status="exited",
            labels={"finlab-sandbox": "true"}
        )
        orphaned2 = create_mock_container(
            container_id="orphan2",
            name="orphan-2",
            status="dead",
            labels={"finlab-sandbox": "true"}
        )

        mock_docker_client.containers.list.return_value = [orphaned1, orphaned2]

        orphaned_ids = container_monitor.scan_orphaned_containers()

        assert len(orphaned_ids) == 2
        assert "orphan1" in orphaned_ids
        assert "orphan2" in orphaned_ids

        # Verify correct filters were used
        mock_docker_client.containers.list.assert_called_once()
        call_args = mock_docker_client.containers.list.call_args
        assert call_args.kwargs['all'] is True
        assert 'finlab-sandbox' in call_args.kwargs['filters']['label']
        assert 'exited' in call_args.kwargs['filters']['status']

    def test_scan_no_orphaned_containers(self, container_monitor, mock_docker_client):
        """Test scanning when no orphaned containers exist."""
        mock_docker_client.containers.list.return_value = []

        orphaned_ids = container_monitor.scan_orphaned_containers()

        assert len(orphaned_ids) == 0

    def test_scan_triggers_alert_when_threshold_exceeded(
        self,
        container_monitor,
        mock_docker_client,
        metrics_collector
    ):
        """Test alert triggered when orphaned container threshold exceeded."""
        # Create 4 orphaned containers (threshold is 3)
        orphaned = [
            create_mock_container(
                container_id=f"orphan{i}",
                name=f"orphan-{i}",
                status="exited",
                labels={"finlab-sandbox": "true"}
            )
            for i in range(4)
        ]

        mock_docker_client.containers.list.return_value = orphaned

        orphaned_ids = container_monitor.scan_orphaned_containers()

        assert len(orphaned_ids) == 4

        # Verify error was recorded
        errors_total = metrics_collector.metrics['system_errors_total'].get_latest()
        assert errors_total == 1  # Should have recorded alert

    def test_scan_exports_metrics(self, container_monitor, mock_docker_client, metrics_collector):
        """Test orphaned container count exported to metrics."""
        orphaned = [
            create_mock_container(
                container_id="orphan1",
                status="exited",
                labels={"finlab-sandbox": "true"}
            )
        ]

        mock_docker_client.containers.list.return_value = orphaned

        container_monitor.scan_orphaned_containers()

        # Verify orphaned count metric
        orphaned_metric = metrics_collector.metrics['sandbox_containers_orphaned']
        assert orphaned_metric.get_latest() == 1


class TestCleanupOrphanedContainers:
    """Test cleanup_orphaned_containers method."""

    def test_cleanup_specific_containers(self, container_monitor, mock_docker_client):
        """Test cleaning up specific container IDs."""
        mock_container = create_mock_container(
            container_id="orphan1",
            status="exited",
            labels={"finlab-sandbox": "true"}
        )

        mock_docker_client.containers.get.return_value = mock_container

        cleaned_count = container_monitor.cleanup_orphaned_containers(
            container_ids=["orphan1"],
            force=True
        )

        assert cleaned_count == 1
        mock_docker_client.containers.get.assert_called_once_with("orphan1")
        mock_container.remove.assert_called_once_with(force=True)

    def test_cleanup_scans_and_cleans_all_orphaned(self, container_monitor, mock_docker_client):
        """Test cleanup scans for orphaned containers if none provided."""
        orphaned = create_mock_container(
            container_id="orphan1",
            status="exited",
            labels={"finlab-sandbox": "true"}
        )

        # Mock list to return orphaned containers
        mock_docker_client.containers.list.return_value = [orphaned]
        # Mock get to return same container
        mock_docker_client.containers.get.return_value = orphaned

        cleaned_count = container_monitor.cleanup_orphaned_containers()

        assert cleaned_count == 1
        orphaned.remove.assert_called_once()

    def test_cleanup_skips_containers_without_label(self, container_monitor, mock_docker_client):
        """Test cleanup skips containers without finlab-sandbox label (safety check)."""
        mock_container = create_mock_container(
            container_id="nolabel",
            status="exited",
            labels={}  # Missing finlab-sandbox label
        )

        mock_docker_client.containers.get.return_value = mock_container

        cleaned_count = container_monitor.cleanup_orphaned_containers(
            container_ids=["nolabel"]
        )

        assert cleaned_count == 0
        mock_container.remove.assert_not_called()  # Should not remove

    def test_cleanup_handles_already_removed_containers(
        self,
        container_monitor,
        mock_docker_client
    ):
        """Test cleanup handles containers already removed."""
        from docker.errors import NotFound

        mock_docker_client.containers.get.side_effect = NotFound("Not found")

        cleaned_count = container_monitor.cleanup_orphaned_containers(
            container_ids=["already-gone"]
        )

        assert cleaned_count == 1  # Count as cleaned

    def test_cleanup_continues_on_error(self, container_monitor, mock_docker_client):
        """Test cleanup continues with other containers on error."""
        from docker.errors import APIError

        # First container fails, second succeeds
        error_container = create_mock_container(
            container_id="error1",
            labels={"finlab-sandbox": "true"}
        )
        error_container.remove.side_effect = APIError("Remove failed")

        success_container = create_mock_container(
            container_id="success1",
            labels={"finlab-sandbox": "true"}
        )

        mock_docker_client.containers.get.side_effect = [error_container, success_container]

        cleaned_count = container_monitor.cleanup_orphaned_containers(
            container_ids=["error1", "success1"]
        )

        assert cleaned_count == 1  # Only success1
        success_container.remove.assert_called_once()

    def test_cleanup_disabled_returns_zero(self, mock_docker_client, metrics_collector):
        """Test cleanup returns 0 when cleanup disabled."""
        monitor = ContainerMonitor(
            metrics_collector=metrics_collector,
            docker_client=mock_docker_client,
            cleanup_enabled=False
        )

        cleaned_count = monitor.cleanup_orphaned_containers(container_ids=["test"])

        assert cleaned_count == 0
        mock_docker_client.containers.get.assert_not_called()

    def test_cleanup_updates_metrics(self, container_monitor, mock_docker_client, metrics_collector):
        """Test cleanup updates cleaned containers metric."""
        mock_container = create_mock_container(
            container_id="orphan1",
            labels={"finlab-sandbox": "true"}
        )

        mock_docker_client.containers.get.return_value = mock_container

        container_monitor.cleanup_orphaned_containers(container_ids=["orphan1"])

        # Verify metric updated
        cleaned_metric = metrics_collector.metrics['sandbox_containers_cleaned_total']
        assert cleaned_metric.get_latest() == 1


class TestGetRunningContainers:
    """Test get_running_containers method."""

    def test_get_running_containers_success(self, container_monitor, mock_docker_client):
        """Test getting statistics for running containers."""
        running1 = create_mock_container(
            container_id="run1",
            name="running-1",
            status="running",
            labels={"finlab-sandbox": "true"}
        )
        running2 = create_mock_container(
            container_id="run2",
            name="running-2",
            status="running",
            labels={"finlab-sandbox": "true"}
        )

        mock_docker_client.containers.list.return_value = [running1, running2]

        stats_list = container_monitor.get_running_containers()

        assert len(stats_list) == 2
        assert all(s.status == ContainerStatus.RUNNING for s in stats_list)
        assert {s.container_id for s in stats_list} == {"run1", "run2"}

        # Verify correct filters
        call_args = mock_docker_client.containers.list.call_args
        assert 'finlab-sandbox' in call_args.kwargs['filters']['label']
        assert call_args.kwargs['filters']['status'] == 'running'

    def test_get_running_containers_updates_metrics(
        self,
        container_monitor,
        mock_docker_client,
        metrics_collector
    ):
        """Test running container count exported to metrics."""
        running = create_mock_container(status="running", labels={"finlab-sandbox": "true"})
        mock_docker_client.containers.list.return_value = [running]

        container_monitor.get_running_containers()

        running_metric = metrics_collector.metrics['sandbox_containers_running']
        assert running_metric.get_latest() == 1


class TestMonitorAllContainers:
    """Test monitor_all_containers method."""

    def test_monitor_all_containers(self, container_monitor, mock_docker_client):
        """Test monitoring all containers (running and stopped)."""
        running = create_mock_container(
            container_id="run1",
            status="running",
            labels={"finlab-sandbox": "true"}
        )
        stopped = create_mock_container(
            container_id="stop1",
            status="exited",
            labels={"finlab-sandbox": "true"}
        )

        mock_docker_client.containers.list.return_value = [running, stopped]

        all_stats = container_monitor.monitor_all_containers()

        assert len(all_stats) == 2
        assert "run1" in all_stats
        assert "stop1" in all_stats
        assert all_stats["run1"].status == ContainerStatus.RUNNING
        assert all_stats["stop1"].status == ContainerStatus.EXITED


class TestResourceAlerts:
    """Test check_resource_alerts method."""

    def test_memory_threshold_alert(self, container_monitor, mock_docker_client):
        """Test alert triggered when memory exceeds threshold."""
        # Create container with high memory usage
        high_mem_container = create_mock_container(
            container_id="highmem",
            name="high-memory",
            status="running",
            labels={"finlab-sandbox": "true"}
        )

        # Override stats to return high memory usage
        high_mem_container.stats = Mock(return_value={
            'memory_stats': {
                'usage': 1900 * 1024 * 1024,  # 1900 MB (95%)
                'limit': 2000 * 1024 * 1024,  # 2000 MB
            },
            'cpu_stats': {
                'cpu_usage': {'total_usage': 1000000000},
                'system_cpu_usage': 10000000000,
                'online_cpus': 4
            },
            'precpu_stats': {
                'cpu_usage': {'total_usage': 900000000},
                'system_cpu_usage': 9500000000
            }
        })

        mock_docker_client.containers.list.return_value = [high_mem_container]

        alerts = container_monitor.check_resource_alerts(
            memory_threshold_percent=90.0,
            cpu_threshold_percent=90.0
        )

        assert len(alerts) == 1
        assert alerts[0]['container_id'] == "highmem"
        assert 'memory_violation' in alerts[0]
        assert alerts[0]['memory_violation']['current'] >= 90.0

    def test_no_alerts_when_under_threshold(self, container_monitor, mock_docker_client):
        """Test no alerts when resources under threshold."""
        normal_container = create_mock_container(
            status="running",
            labels={"finlab-sandbox": "true"}
        )

        mock_docker_client.containers.list.return_value = [normal_container]

        alerts = container_monitor.check_resource_alerts(
            memory_threshold_percent=90.0,
            cpu_threshold_percent=90.0
        )

        assert len(alerts) == 0


class TestMetricsExport:
    """Test Prometheus metrics export."""

    def test_container_stats_exported_to_prometheus(
        self,
        container_monitor,
        mock_docker_client,
        metrics_collector
    ):
        """Test container statistics exported to Prometheus metrics."""
        mock_container = create_mock_container(
            container_id="metrics-test",
            status="running",
            labels={"finlab-sandbox": "true"}
        )

        mock_docker_client.containers.get.return_value = mock_container

        container_monitor.get_container_stats("metrics-test")

        # Verify metrics were registered and populated
        assert 'sandbox_container_memory_usage_mb' in metrics_collector.metrics
        assert 'sandbox_container_cpu_percent' in metrics_collector.metrics
        assert 'sandbox_container_memory_percent' in metrics_collector.metrics

        # Verify values
        mem_usage = metrics_collector.metrics['sandbox_container_memory_usage_mb']
        assert mem_usage.get_latest() == pytest.approx(500.0, rel=0.01)


class TestMonitoringOverhead:
    """Test monitoring overhead calculation."""

    def test_get_monitoring_overhead_initial_state(self, container_monitor):
        """Test overhead calculation in initial state."""
        overhead = container_monitor.get_monitoring_overhead()
        assert overhead == 0.0  # No stats collected yet

    def test_monitoring_overhead_estimation(self, container_monitor):
        """Test overhead estimation with collected stats."""
        # Simulate stats collection time
        container_monitor._last_stats_time = {
            'container1': 0.05,  # 50ms
            'container2': 0.03,  # 30ms
        }

        overhead = container_monitor.get_monitoring_overhead()

        # Average collection time = 40ms
        # Collection interval = 10s
        # Overhead = (0.04 / 10) * 100 = 0.4%
        assert overhead == pytest.approx(0.4, rel=0.1)
        assert overhead < 1.0  # Should be under 1%


class TestCloseMonitor:
    """Test monitor cleanup."""

    def test_close_monitor(self, container_monitor, mock_docker_client):
        """Test closing monitor closes Docker client."""
        container_monitor.close()

        mock_docker_client.close.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_container_with_invalid_status(self, container_monitor, mock_docker_client):
        """Test handling container with unknown status."""
        mock_container = create_mock_container(
            container_id="unknown",
            status="unknown-status"
        )

        mock_docker_client.containers.get.return_value = mock_container

        stats = container_monitor.get_container_stats("unknown")

        # Should default to EXITED for unknown status
        assert stats.status == ContainerStatus.EXITED

    def test_container_with_missing_timestamps(self, container_monitor, mock_docker_client):
        """Test handling container with missing timestamp fields."""
        mock_container = create_mock_container(container_id="notime")
        # Clear timestamp fields
        mock_container.attrs['State'] = {'Status': 'running'}

        mock_docker_client.containers.get.return_value = mock_container

        stats = container_monitor.get_container_stats("notime")

        assert stats.created_at is None

    def test_stats_collection_with_missing_fields(self, container_monitor, mock_docker_client):
        """Test stats collection handles missing stats fields gracefully."""
        mock_container = create_mock_container(container_id="partial", status="running")

        # Return incomplete stats
        mock_container.stats = Mock(return_value={
            'memory_stats': {},  # Missing fields
            'cpu_stats': {}
        })

        mock_docker_client.containers.get.return_value = mock_container

        stats = container_monitor.get_container_stats("partial")

        # Should not crash, defaults to 0
        assert stats.memory_usage_mb == 0.0
        assert stats.cpu_percent == 0.0
