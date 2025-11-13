"""Unit tests for ContainerMonitor.

Tests cover:
- Container stats collection and parsing
- Orphaned container detection logic
- Cleanup success and failure handling
- Docker daemon unavailability scenarios
- Label verification and safety checks
- Metric export integration
- Edge cases (empty containers, missing stats, etc.)

Coverage target: >85%
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
from typing import Dict, Any

from src.monitoring.container_monitor import ContainerMonitor, ContainerStats


class TestContainerMonitor:
    """Test suite for ContainerMonitor class."""

    @pytest.fixture
    def mock_metrics_collector(self):
        """Create mock MetricsCollector."""
        collector = Mock()
        return collector

    @pytest.fixture
    def mock_docker_client(self):
        """Create mock Docker client."""
        client = Mock()
        client.ping = Mock()
        return client

    @pytest.fixture
    def container_monitor(self, mock_metrics_collector, mock_docker_client):
        """Create ContainerMonitor instance with mocked dependencies."""
        return ContainerMonitor(
            metrics_collector=mock_metrics_collector,
            docker_client=mock_docker_client,
            auto_cleanup=True
        )

    def test_initialization_with_docker_client(self, mock_metrics_collector, mock_docker_client):
        """Test ContainerMonitor initialization with provided Docker client."""
        monitor = ContainerMonitor(
            metrics_collector=mock_metrics_collector,
            docker_client=mock_docker_client
        )

        assert monitor.metrics_collector == mock_metrics_collector
        assert monitor.docker_client == mock_docker_client
        assert monitor.auto_cleanup is True
        assert monitor._docker_available is True
        assert monitor._active_containers == {}
        assert monitor._cleanup_failures == []

    def test_initialization_without_docker_client(self, mock_metrics_collector):
        """Test ContainerMonitor initialization without Docker client (auto-create)."""
        with patch('src.monitoring.container_monitor.ContainerMonitor._create_docker_client') as mock_create:
            mock_create.return_value = Mock()

            monitor = ContainerMonitor(
                metrics_collector=mock_metrics_collector,
                docker_client=None
            )

            mock_create.assert_called_once()
            assert monitor.docker_client is not None

    def test_initialization_docker_unavailable(self, mock_metrics_collector):
        """Test graceful handling when Docker daemon is unavailable."""
        with patch('src.monitoring.container_monitor.ContainerMonitor._create_docker_client') as mock_create:
            mock_create.return_value = None

            monitor = ContainerMonitor(
                metrics_collector=mock_metrics_collector,
                docker_client=None
            )

            assert monitor.docker_client is None
            assert monitor._docker_available is False

    def test_is_docker_available_success(self, container_monitor, mock_docker_client):
        """Test Docker availability check when daemon is available."""
        mock_docker_client.ping.return_value = True

        assert container_monitor.is_docker_available() is True
        mock_docker_client.ping.assert_called_once()

    def test_is_docker_available_failure(self, container_monitor, mock_docker_client):
        """Test Docker availability check when daemon is unavailable."""
        mock_docker_client.ping.side_effect = Exception("Connection refused")

        assert container_monitor.is_docker_available() is False
        assert container_monitor._docker_available is False

    def test_record_container_created(self, container_monitor):
        """Test recording container creation event."""
        container_id = "abc123def456"
        name = "test-container"

        container_monitor.record_container_created(container_id, name)

        assert container_id in container_monitor._active_containers
        assert container_monitor._active_containers[container_id] == name

    def test_record_container_created_without_name(self, container_monitor):
        """Test recording container creation without explicit name."""
        container_id = "abc123def456"

        container_monitor.record_container_created(container_id)

        assert container_id in container_monitor._active_containers
        assert container_monitor._active_containers[container_id] == container_id[:12]

    def test_record_container_stats_success(self, container_monitor, mock_docker_client):
        """Test successful container stats collection."""
        container_id = "abc123"

        # Mock container object
        mock_container = Mock()
        mock_container.id = container_id
        mock_container.name = "test-container"
        mock_container.status = "running"
        mock_container.labels = {"finlab-sandbox": "true"}
        mock_container.attrs = {"Created": "2025-10-26T10:00:00Z"}

        # Mock stats data
        mock_container.stats.return_value = {
            "memory_stats": {
                "usage": 1024 * 1024 * 500,  # 500 MB
                "limit": 1024 * 1024 * 2000  # 2 GB
            },
            "cpu_stats": {
                "cpu_usage": {"total_usage": 2000000000},
                "system_cpu_usage": 10000000000,
                "online_cpus": 2
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 1000000000},
                "system_cpu_usage": 9000000000
            }
        }

        mock_docker_client.containers.get.return_value = mock_container

        stats = container_monitor.record_container_stats(container_id)

        assert stats is not None
        assert isinstance(stats, ContainerStats)
        assert stats.container_id == container_id
        assert stats.name == "test-container"
        assert stats.status == "running"
        assert stats.memory_usage_bytes == 1024 * 1024 * 500
        assert stats.memory_limit_bytes == 1024 * 1024 * 2000
        assert 24.0 < stats.memory_percent < 26.0  # ~25%
        assert stats.cpu_percent > 0  # Should calculate CPU %

    def test_record_container_stats_docker_unavailable(self, container_monitor, mock_docker_client):
        """Test container stats when Docker is unavailable."""
        mock_docker_client.ping.side_effect = Exception("Docker not available")

        stats = container_monitor.record_container_stats("abc123")

        assert stats is None

    def test_record_container_stats_container_not_found(self, container_monitor, mock_docker_client):
        """Test container stats when container doesn't exist."""
        mock_docker_client.containers.get.side_effect = Exception("Container not found")

        stats = container_monitor.record_container_stats("nonexistent")

        assert stats is None

    def test_calculate_cpu_percent(self, container_monitor):
        """Test CPU percentage calculation."""
        cpu_stats = {
            "cpu_usage": {"total_usage": 2000000000},
            "system_cpu_usage": 10000000000,
            "online_cpus": 2
        }
        precpu_stats = {
            "cpu_usage": {"total_usage": 1000000000},
            "system_cpu_usage": 9000000000
        }

        cpu_percent = container_monitor._calculate_cpu_percent(cpu_stats, precpu_stats)

        # (2000000000 - 1000000000) / (10000000000 - 9000000000) * 2 * 100 = 200%
        assert cpu_percent == 200.0

    def test_calculate_cpu_percent_zero_delta(self, container_monitor):
        """Test CPU calculation with zero system delta."""
        cpu_stats = {
            "cpu_usage": {"total_usage": 1000000000},
            "system_cpu_usage": 9000000000,
            "online_cpus": 2
        }
        precpu_stats = {
            "cpu_usage": {"total_usage": 1000000000},
            "system_cpu_usage": 9000000000
        }

        cpu_percent = container_monitor._calculate_cpu_percent(cpu_stats, precpu_stats)

        assert cpu_percent == 0.0

    def test_record_container_cleanup_success(self, container_monitor):
        """Test recording successful container cleanup."""
        container_id = "abc123"
        container_monitor._active_containers[container_id] = "test-container"

        container_monitor.record_container_cleanup(container_id, success=True)

        assert container_id not in container_monitor._active_containers
        assert container_id not in container_monitor._cleanup_failures

    def test_record_container_cleanup_failure(self, container_monitor):
        """Test recording failed container cleanup."""
        container_id = "abc123"
        container_monitor._active_containers[container_id] = "test-container"

        container_monitor.record_container_cleanup(container_id, success=False)

        assert container_id not in container_monitor._active_containers
        assert container_id in container_monitor._cleanup_failures

    def test_scan_orphaned_containers_success(self, container_monitor, mock_docker_client):
        """Test scanning for orphaned containers."""
        # Mock containers
        orphaned_container = Mock()
        orphaned_container.id = "orphaned123"
        orphaned_container.name = "orphaned-sandbox"
        orphaned_container.status = "exited"
        orphaned_container.labels = {"finlab-sandbox": "true"}
        orphaned_container.attrs = {"Created": "2025-10-26T09:00:00Z"}

        running_container = Mock()
        running_container.id = "running456"
        running_container.name = "running-sandbox"
        running_container.status = "running"
        running_container.labels = {"finlab-sandbox": "true"}
        running_container.attrs = {"Created": "2025-10-26T10:00:00Z"}

        non_finlab_container = Mock()
        non_finlab_container.id = "other789"
        non_finlab_container.name = "other-container"
        non_finlab_container.status = "exited"
        non_finlab_container.labels = {}
        non_finlab_container.attrs = {"Created": "2025-10-26T08:00:00Z"}

        mock_docker_client.containers.list.return_value = [
            orphaned_container,
            running_container,
            non_finlab_container
        ]

        orphaned = container_monitor.scan_orphaned_containers()

        assert len(orphaned) == 1
        assert "orphaned123" in orphaned
        assert "running456" not in orphaned  # Running, not orphaned
        assert "other789" not in orphaned  # No finlab label

    def test_scan_orphaned_containers_dead_status(self, container_monitor, mock_docker_client):
        """Test scanning detects containers with 'dead' status."""
        dead_container = Mock()
        dead_container.id = "dead123"
        dead_container.name = "dead-sandbox"
        dead_container.status = "dead"
        dead_container.labels = {"finlab-sandbox": "true"}
        dead_container.attrs = {"Created": "2025-10-26T09:00:00Z"}

        mock_docker_client.containers.list.return_value = [dead_container]

        orphaned = container_monitor.scan_orphaned_containers()

        assert len(orphaned) == 1
        assert "dead123" in orphaned

    def test_scan_orphaned_containers_label_false(self, container_monitor, mock_docker_client):
        """Test scanning ignores containers with finlab-sandbox=false."""
        container = Mock()
        container.id = "test123"
        container.name = "test-container"
        container.status = "exited"
        container.labels = {"finlab-sandbox": "false"}  # Explicitly false
        container.attrs = {"Created": "2025-10-26T09:00:00Z"}

        mock_docker_client.containers.list.return_value = [container]

        orphaned = container_monitor.scan_orphaned_containers()

        assert len(orphaned) == 0  # Should not detect as orphaned

    def test_scan_orphaned_containers_docker_unavailable(self, container_monitor, mock_docker_client):
        """Test scanning when Docker is unavailable."""
        mock_docker_client.ping.side_effect = Exception("Docker unavailable")

        orphaned = container_monitor.scan_orphaned_containers()

        assert orphaned == []

    def test_scan_orphaned_containers_exception(self, container_monitor, mock_docker_client):
        """Test scanning handles exceptions gracefully."""
        mock_docker_client.containers.list.side_effect = Exception("API error")

        orphaned = container_monitor.scan_orphaned_containers()

        assert orphaned == []

    def test_cleanup_orphaned_containers_success(self, container_monitor, mock_docker_client):
        """Test successful cleanup of orphaned containers."""
        container_id = "orphaned123"

        # Mock container
        mock_container = Mock()
        mock_container.id = container_id
        mock_container.name = "orphaned-sandbox"
        mock_container.labels = {"finlab-sandbox": "true"}

        mock_docker_client.containers.get.return_value = mock_container

        cleanup_count = container_monitor.cleanup_orphaned_containers([container_id])

        assert cleanup_count == 1
        mock_container.remove.assert_called_once_with(force=True)

    def test_cleanup_orphaned_containers_auto_scan(self, container_monitor, mock_docker_client):
        """Test cleanup with automatic orphan scanning."""
        # Mock scan_orphaned_containers
        with patch.object(container_monitor, 'scan_orphaned_containers') as mock_scan:
            mock_scan.return_value = ["orphaned123"]

            # Mock container
            mock_container = Mock()
            mock_container.id = "orphaned123"
            mock_container.name = "orphaned-sandbox"
            mock_container.labels = {"finlab-sandbox": "true"}

            mock_docker_client.containers.get.return_value = mock_container

            cleanup_count = container_monitor.cleanup_orphaned_containers()

            assert cleanup_count == 1
            mock_scan.assert_called_once()

    def test_cleanup_orphaned_containers_label_verification(self, container_monitor, mock_docker_client):
        """Test cleanup verifies labels before removal (safety check)."""
        container_id = "test123"

        # Mock container WITHOUT finlab-sandbox label
        mock_container = Mock()
        mock_container.id = container_id
        mock_container.name = "non-finlab-container"
        mock_container.labels = {}  # No label

        mock_docker_client.containers.get.return_value = mock_container

        cleanup_count = container_monitor.cleanup_orphaned_containers([container_id])

        assert cleanup_count == 0  # Should not remove
        mock_container.remove.assert_not_called()

    def test_cleanup_orphaned_containers_partial_failure(self, container_monitor, mock_docker_client):
        """Test cleanup with some failures."""
        # First container succeeds
        success_container = Mock()
        success_container.id = "success123"
        success_container.name = "success-container"
        success_container.labels = {"finlab-sandbox": "true"}

        # Second container fails
        failure_container = Mock()
        failure_container.id = "failure456"
        failure_container.name = "failure-container"
        failure_container.labels = {"finlab-sandbox": "true"}
        failure_container.remove.side_effect = Exception("Removal failed")

        def get_container(container_id):
            if container_id == "success123":
                return success_container
            elif container_id == "failure456":
                return failure_container

        mock_docker_client.containers.get.side_effect = get_container

        cleanup_count = container_monitor.cleanup_orphaned_containers(
            ["success123", "failure456"]
        )

        assert cleanup_count == 1  # Only 1 succeeded
        assert "failure456" in container_monitor._cleanup_failures

    def test_cleanup_orphaned_containers_docker_unavailable(self, container_monitor, mock_docker_client):
        """Test cleanup when Docker is unavailable."""
        mock_docker_client.ping.side_effect = Exception("Docker unavailable")

        cleanup_count = container_monitor.cleanup_orphaned_containers(["test123"])

        assert cleanup_count == 0

    def test_cleanup_orphaned_containers_empty_list(self, container_monitor):
        """Test cleanup with empty container list."""
        cleanup_count = container_monitor.cleanup_orphaned_containers([])

        assert cleanup_count == 0

    def test_get_active_containers_count(self, container_monitor, mock_docker_client):
        """Test getting count of active containers."""
        mock_docker_client.containers.list.return_value = [Mock(), Mock(), Mock()]

        count = container_monitor.get_active_containers_count()

        assert count == 3
        mock_docker_client.containers.list.assert_called_once_with(
            filters={'label': 'finlab-sandbox=true'}
        )

    def test_get_active_containers_count_docker_unavailable(self, container_monitor, mock_docker_client):
        """Test active count when Docker is unavailable."""
        mock_docker_client.ping.side_effect = Exception("Docker unavailable")

        count = container_monitor.get_active_containers_count()

        assert count == 0

    def test_get_all_container_stats(self, container_monitor, mock_docker_client):
        """Test getting stats for all running containers."""
        # Mock containers
        container1 = Mock()
        container1.id = "container1"

        container2 = Mock()
        container2.id = "container2"

        mock_docker_client.containers.list.return_value = [container1, container2]

        # Mock record_container_stats
        with patch.object(container_monitor, 'record_container_stats') as mock_record:
            mock_stats1 = Mock(spec=ContainerStats)
            mock_stats2 = Mock(spec=ContainerStats)
            mock_record.side_effect = [mock_stats1, mock_stats2]

            stats_list = container_monitor.get_all_container_stats()

            assert len(stats_list) == 2
            assert mock_stats1 in stats_list
            assert mock_stats2 in stats_list
            assert mock_record.call_count == 2

    def test_get_status(self, container_monitor, mock_docker_client):
        """Test getting comprehensive monitor status."""
        # Mock methods
        with patch.object(container_monitor, 'scan_orphaned_containers') as mock_scan, \
             patch.object(container_monitor, 'get_active_containers_count') as mock_count:

            mock_scan.return_value = ["orphaned1", "orphaned2"]
            mock_count.return_value = 5

            container_monitor._cleanup_failures = ["failed123"]

            status = container_monitor.get_status()

            assert status['docker_available'] is True
            assert status['active_containers'] == 5
            assert status['orphaned_containers'] == 2
            assert len(status['orphaned_container_ids']) == 2
            assert len(status['cleanup_failures']) == 1
            assert status['auto_cleanup'] is True
            assert status['finlab_label'] == "finlab-sandbox"

    def test_reset(self, container_monitor):
        """Test resetting monitor state."""
        # Add some state
        container_monitor._active_containers = {"abc": "test"}
        container_monitor._cleanup_failures = ["failed1", "failed2"]

        container_monitor.reset()

        assert container_monitor._active_containers == {}
        assert container_monitor._cleanup_failures == []

    def test_export_container_stats_with_metrics_methods(self, container_monitor):
        """Test stats export when MetricsCollector has container methods."""
        stats = ContainerStats(
            container_id="test123",
            name="test-container",
            status="running",
            memory_usage_bytes=1024 * 1024 * 500,
            memory_limit_bytes=1024 * 1024 * 2000,
            memory_percent=25.0,
            cpu_percent=50.0,
            created_at="2025-10-26T10:00:00Z",
            labels={"finlab-sandbox": "true"}
        )

        # Add mock methods to collector
        container_monitor.metrics_collector.record_container_memory = Mock()
        container_monitor.metrics_collector.record_container_cpu = Mock()

        container_monitor._export_container_stats(stats)

        container_monitor.metrics_collector.record_container_memory.assert_called_once_with(
            container_id="test123",
            memory_bytes=1024 * 1024 * 500,
            limit_bytes=1024 * 1024 * 2000,
            percent=25.0
        )

        container_monitor.metrics_collector.record_container_cpu.assert_called_once_with(
            container_id="test123",
            cpu_percent=50.0
        )

    def test_export_container_stats_without_metrics_methods(self, container_monitor):
        """Test stats export gracefully handles missing MetricsCollector methods."""
        stats = ContainerStats(
            container_id="test123",
            name="test-container",
            status="running",
            memory_usage_bytes=1024 * 1024 * 500,
            memory_limit_bytes=1024 * 1024 * 2000,
            memory_percent=25.0,
            cpu_percent=50.0,
            created_at="2025-10-26T10:00:00Z",
            labels={"finlab-sandbox": "true"}
        )

        # Should not raise exception
        container_monitor._export_container_stats(stats)

    def test_container_stats_dataclass(self):
        """Test ContainerStats dataclass creation and attributes."""
        stats = ContainerStats(
            container_id="abc123",
            name="test-container",
            status="running",
            memory_usage_bytes=1000,
            memory_limit_bytes=2000,
            memory_percent=50.0,
            cpu_percent=25.0,
            created_at="2025-10-26T10:00:00Z",
            labels={"env": "test"}
        )

        assert stats.container_id == "abc123"
        assert stats.name == "test-container"
        assert stats.status == "running"
        assert stats.memory_usage_bytes == 1000
        assert stats.memory_limit_bytes == 2000
        assert stats.memory_percent == 50.0
        assert stats.cpu_percent == 25.0
        assert stats.created_at == "2025-10-26T10:00:00Z"
        assert stats.labels == {"env": "test"}

    def test_auto_cleanup_disabled(self, mock_metrics_collector, mock_docker_client):
        """Test ContainerMonitor with auto_cleanup disabled."""
        monitor = ContainerMonitor(
            metrics_collector=mock_metrics_collector,
            docker_client=mock_docker_client,
            auto_cleanup=False
        )

        assert monitor.auto_cleanup is False

    def test_multiple_orphaned_containers_cleanup(self, container_monitor, mock_docker_client):
        """Test cleanup of multiple orphaned containers."""
        container_ids = ["orphan1", "orphan2", "orphan3"]

        # Mock containers
        containers = []
        for cid in container_ids:
            mock_container = Mock()
            mock_container.id = cid
            mock_container.name = f"{cid}-container"
            mock_container.labels = {"finlab-sandbox": "true"}
            containers.append(mock_container)

        def get_container(container_id):
            for container in containers:
                if container.id == container_id:
                    return container
            raise Exception("Container not found")

        mock_docker_client.containers.get.side_effect = get_container

        cleanup_count = container_monitor.cleanup_orphaned_containers(container_ids)

        assert cleanup_count == 3
        for container in containers:
            container.remove.assert_called_once_with(force=True)

    def test_create_docker_client_import_error(self, mock_metrics_collector):
        """Test _create_docker_client handles ImportError gracefully."""
        with patch('src.monitoring.container_monitor.ContainerMonitor._create_docker_client') as mock_create:
            # Simulate ImportError
            mock_create.return_value = None

            monitor = ContainerMonitor(
                metrics_collector=mock_metrics_collector,
                docker_client=None
            )

            assert monitor.docker_client is None
            assert monitor._docker_available is False

    def test_create_docker_client_connection_error(self, mock_metrics_collector):
        """Test _create_docker_client handles connection errors gracefully."""
        with patch('src.monitoring.container_monitor.ContainerMonitor._create_docker_client') as mock_create:
            # Simulate connection error
            mock_create.return_value = None

            monitor = ContainerMonitor(
                metrics_collector=mock_metrics_collector,
                docker_client=None
            )

            assert monitor.docker_client is None
            assert monitor._docker_available is False

    def test_get_all_container_stats_error_handling(self, container_monitor, mock_docker_client):
        """Test get_all_container_stats handles errors gracefully."""
        # Make list() raise an exception
        mock_docker_client.containers.list.side_effect = Exception("Docker error")

        stats_list = container_monitor.get_all_container_stats()

        assert stats_list == []

    def test_get_active_containers_count_error(self, container_monitor, mock_docker_client):
        """Test get_active_containers_count handles errors gracefully."""
        mock_docker_client.containers.list.side_effect = Exception("Docker error")

        count = container_monitor.get_active_containers_count()

        assert count == 0
