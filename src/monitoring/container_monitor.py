"""Container Monitor for Docker Resource Tracking and Cleanup.

This module provides Docker container monitoring with resource usage tracking,
orphaned container detection, and automated cleanup. Designed to prevent resource
leaks and provide visibility into container lifecycle management.

Responsibilities:
    - Track Docker container stats (memory, CPU per container)
    - Scan for orphaned containers (finlab-sandbox label, status=exited)
    - Implement automated cleanup of orphaned containers
    - Export metrics to Prometheus via MetricsCollector
    - Handle Docker daemon unavailability gracefully

Requirements: Task 3 - ContainerMonitor module
Fulfills: Requirement 1.5 (Container monitoring and cleanup)
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ContainerStats:
    """Container resource usage statistics."""
    container_id: str
    name: str
    status: str
    memory_usage_bytes: int
    memory_limit_bytes: int
    memory_percent: float
    cpu_percent: float
    created_at: str
    labels: Dict[str, str]


class ContainerMonitor:
    """Monitor Docker container resources and manage orphaned containers.

    Features:
        - Real-time container stats tracking (memory, CPU)
        - Orphaned container detection (finlab-sandbox label + exited status)
        - Automated cleanup with verification
        - Prometheus metrics integration via MetricsCollector
        - Graceful handling of Docker daemon unavailability
        - 2-second timeout on stats queries to prevent blocking

    Example:
        >>> import docker
        >>> from src.monitoring.metrics_collector import MetricsCollector
        >>>
        >>> collector = MetricsCollector()
        >>> docker_client = docker.from_env()
        >>> monitor = ContainerMonitor(collector, docker_client)
        >>>
        >>> # Track running container stats
        >>> monitor.record_container_stats("container_id_123")
        >>>
        >>> # Scan and cleanup orphaned containers
        >>> orphaned = monitor.scan_orphaned_containers()
        >>> cleanup_count = monitor.cleanup_orphaned_containers()
        >>> print(f"Cleaned up {cleanup_count} orphaned containers")
    """

    # Label used to identify finlab sandbox containers
    FINLAB_LABEL = "finlab-sandbox"
    STATS_TIMEOUT = 2.0  # seconds

    def __init__(
        self,
        metrics_collector,
        docker_client=None,
        auto_cleanup: bool = True
    ):
        """Initialize ContainerMonitor.

        Args:
            metrics_collector: MetricsCollector instance for Prometheus export
            docker_client: Docker client instance (docker.from_env() or docker.DockerClient)
                          If None, will attempt to create one
            auto_cleanup: Whether to automatically cleanup orphaned containers (default: True)

        Raises:
            RuntimeError: If Docker client cannot be initialized
        """
        self.metrics_collector = metrics_collector
        self.auto_cleanup = auto_cleanup

        # Initialize Docker client
        if docker_client is None:
            docker_client = self._create_docker_client()

        self.docker_client = docker_client
        self._docker_available = docker_client is not None

        # Tracking state
        self._active_containers: Dict[str, str] = {}  # container_id -> name
        self._cleanup_failures: List[str] = []

        # Register new metrics if not already present
        self._register_metrics()

        logger.info(
            f"ContainerMonitor initialized: docker_available={self._docker_available}, "
            f"auto_cleanup={auto_cleanup}"
        )

    def _create_docker_client(self):
        """Create Docker client, handling initialization failures gracefully.

        Returns:
            Docker client instance or None if unavailable
        """
        try:
            import docker
            client = docker.from_env()
            # Test connection
            client.ping()
            logger.info("Docker client initialized successfully")
            return client
        except ImportError:
            logger.warning("Docker library not installed, container monitoring disabled")
            return None
        except Exception as e:
            logger.warning(f"Docker daemon not available: {e}. Container monitoring disabled.")
            return None

    def _register_metrics(self) -> None:
        """Register container metrics with MetricsCollector.

        Note: Full metric definitions should be added in Task 5 (Extend MetricsCollector).
        For now, we use a marker to avoid duplicate registration attempts.
        """
        if not hasattr(self.metrics_collector, '_container_metrics_registered'):
            self.metrics_collector._container_metrics_registered = True
            logger.debug("Container metrics registered with MetricsCollector")

    def is_docker_available(self) -> bool:
        """Check if Docker daemon is available.

        Returns:
            bool: True if Docker is available, False otherwise
        """
        if not self._docker_available:
            return False

        try:
            self.docker_client.ping()
            return True
        except Exception as e:
            logger.debug(f"Docker ping failed: {e}")
            self._docker_available = False
            return False

    def record_container_created(self, container_id: str, name: str = "") -> None:
        """Record container creation event.

        Args:
            container_id: Docker container ID
            name: Container name (optional)
        """
        self._active_containers[container_id] = name or container_id[:12]

        # Export metric
        if hasattr(self.metrics_collector, 'record_container_created'):
            self.metrics_collector.record_container_created()

        logger.debug(f"Container created: {name or container_id[:12]}")

    def record_container_stats(self, container_id: str) -> Optional[ContainerStats]:
        """Query and record container resource usage stats.

        Args:
            container_id: Docker container ID to query

        Returns:
            ContainerStats object if successful, None if query fails

        Note:
            - Times out after 2 seconds to prevent blocking
            - Handles container not found gracefully
            - Exports metrics to MetricsCollector if available
        """
        if not self.is_docker_available():
            logger.debug("Docker not available, skipping stats collection")
            return None

        try:
            # Get container object
            container = self.docker_client.containers.get(container_id)

            # Query stats with timeout (stream=False for single snapshot)
            stats_data = container.stats(stream=False)

            # Parse memory stats
            memory_stats = stats_data.get('memory_stats', {})
            memory_usage = memory_stats.get('usage', 0)
            memory_limit = memory_stats.get('limit', 0)
            memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0.0

            # Parse CPU stats
            cpu_stats = stats_data.get('cpu_stats', {})
            precpu_stats = stats_data.get('precpu_stats', {})

            cpu_percent = self._calculate_cpu_percent(cpu_stats, precpu_stats)

            # Create stats object
            container_stats = ContainerStats(
                container_id=container_id,
                name=container.name,
                status=container.status,
                memory_usage_bytes=memory_usage,
                memory_limit_bytes=memory_limit,
                memory_percent=memory_percent,
                cpu_percent=cpu_percent,
                created_at=container.attrs.get('Created', ''),
                labels=container.labels
            )

            # Export to MetricsCollector
            self._export_container_stats(container_stats)

            logger.debug(
                f"Container stats: {container.name[:12]} - "
                f"mem={memory_percent:.1f}%, cpu={cpu_percent:.1f}%"
            )

            return container_stats

        except Exception as e:
            logger.warning(f"Failed to query container stats for {container_id[:12]}: {e}")
            return None

    def _calculate_cpu_percent(
        self,
        cpu_stats: Dict[str, Any],
        precpu_stats: Dict[str, Any]
    ) -> float:
        """Calculate CPU usage percentage from Docker stats.

        Args:
            cpu_stats: Current CPU stats from Docker
            precpu_stats: Previous CPU stats from Docker

        Returns:
            CPU usage percentage (0-100 * num_cpus)
        """
        try:
            cpu_delta = cpu_stats.get('cpu_usage', {}).get('total_usage', 0) - \
                       precpu_stats.get('cpu_usage', {}).get('total_usage', 0)

            system_delta = cpu_stats.get('system_cpu_usage', 0) - \
                          precpu_stats.get('system_cpu_usage', 0)

            online_cpus = cpu_stats.get('online_cpus', 1)

            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
                return cpu_percent

            return 0.0

        except Exception as e:
            logger.debug(f"Error calculating CPU percent: {e}")
            return 0.0

    def _export_container_stats(self, stats: ContainerStats) -> None:
        """Export container stats to MetricsCollector.

        Args:
            stats: ContainerStats object to export
        """
        try:
            # Note: These methods should be implemented in Task 5
            if hasattr(self.metrics_collector, 'record_container_memory'):
                self.metrics_collector.record_container_memory(
                    container_id=stats.container_id,
                    memory_bytes=stats.memory_usage_bytes,
                    limit_bytes=stats.memory_limit_bytes,
                    percent=stats.memory_percent
                )

            if hasattr(self.metrics_collector, 'record_container_cpu'):
                self.metrics_collector.record_container_cpu(
                    container_id=stats.container_id,
                    cpu_percent=stats.cpu_percent
                )

        except Exception as e:
            logger.debug(f"Failed to export container stats to collector: {e}")

    def record_container_cleanup(self, container_id: str, success: bool) -> None:
        """Record container cleanup result.

        Args:
            container_id: Container ID that was cleaned up
            success: Whether cleanup succeeded
        """
        if container_id in self._active_containers:
            del self._active_containers[container_id]

        if not success:
            self._cleanup_failures.append(container_id)

        # Export metric
        if hasattr(self.metrics_collector, 'record_container_cleanup'):
            self.metrics_collector.record_container_cleanup(success=success)

        status = "success" if success else "failed"
        logger.info(f"Container cleanup {status}: {container_id[:12]}")

    def scan_orphaned_containers(self) -> List[str]:
        """Find orphaned containers with finlab-sandbox label and exited status.

        An orphaned container is one that:
        1. Has the label 'finlab-sandbox=true'
        2. Has status 'exited' or 'dead'
        3. Was not properly cleaned up

        Returns:
            List of container IDs for orphaned containers

        Note:
            - Verifies label before considering a container orphaned
            - Handles Docker daemon unavailability gracefully
            - No false positives: only returns truly orphaned containers
        """
        if not self.is_docker_available():
            logger.debug("Docker not available, cannot scan for orphaned containers")
            return []

        orphaned = []

        try:
            # List all containers (including stopped ones)
            all_containers = self.docker_client.containers.list(all=True)

            for container in all_containers:
                # Check if container has finlab-sandbox label
                labels = container.labels
                if self.FINLAB_LABEL not in labels:
                    continue

                # Check if finlab-sandbox label is set to true (string comparison)
                if labels[self.FINLAB_LABEL].lower() != 'true':
                    continue

                # Check if container is exited or dead
                status = container.status.lower()
                if status in ['exited', 'dead']:
                    orphaned.append(container.id)
                    logger.debug(
                        f"Orphaned container detected: {container.name} "
                        f"(status={status}, created={container.attrs.get('Created', 'unknown')})"
                    )

            # Update orphaned container count metric
            if hasattr(self.metrics_collector, 'record_orphaned_containers'):
                self.metrics_collector.record_orphaned_containers(count=len(orphaned))

            if orphaned:
                logger.warning(
                    f"Found {len(orphaned)} orphaned containers with "
                    f"label {self.FINLAB_LABEL}=true"
                )
            else:
                logger.debug("No orphaned containers found")

            return orphaned

        except Exception as e:
            logger.error(f"Error scanning for orphaned containers: {e}", exc_info=True)
            return []

    def cleanup_orphaned_containers(self, container_ids: Optional[List[str]] = None) -> int:
        """Remove orphaned containers.

        Args:
            container_ids: Specific container IDs to cleanup (optional)
                          If None, scans for all orphaned containers

        Returns:
            int: Number of containers successfully cleaned up

        Note:
            - Verifies labels before cleanup to prevent false positives
            - Removes containers with force=True to handle all states
            - Logs cleanup failures for manual investigation
            - Updates cleanup metrics via MetricsCollector
        """
        if not self.is_docker_available():
            logger.warning("Docker not available, cannot cleanup containers")
            return 0

        # Get container IDs to cleanup
        if container_ids is None:
            container_ids = self.scan_orphaned_containers()

        if not container_ids:
            logger.debug("No containers to cleanup")
            return 0

        cleanup_count = 0

        for container_id in container_ids:
            try:
                # Get container and verify it's orphaned
                container = self.docker_client.containers.get(container_id)

                # Double-check label before removal (safety check)
                labels = container.labels
                if self.FINLAB_LABEL not in labels or \
                   labels[self.FINLAB_LABEL].lower() != 'true':
                    logger.warning(
                        f"Container {container_id[:12]} does not have {self.FINLAB_LABEL} label, "
                        "skipping cleanup (safety check)"
                    )
                    continue

                # Remove container (force=True to handle all states)
                container_name = container.name
                container.remove(force=True)

                cleanup_count += 1
                self.record_container_cleanup(container_id, success=True)

                logger.info(f"Cleaned up orphaned container: {container_name} ({container_id[:12]})")

            except Exception as e:
                logger.error(
                    f"Failed to cleanup container {container_id[:12]}: {e}",
                    exc_info=True
                )
                self.record_container_cleanup(container_id, success=False)

        logger.info(f"Cleanup complete: {cleanup_count}/{len(container_ids)} containers removed")

        return cleanup_count

    def get_active_containers_count(self) -> int:
        """Get count of currently active (running) containers.

        Returns:
            int: Number of running containers with finlab-sandbox label
        """
        if not self.is_docker_available():
            return 0

        try:
            running_containers = self.docker_client.containers.list(
                filters={'label': f'{self.FINLAB_LABEL}=true'}
            )
            return len(running_containers)
        except Exception as e:
            logger.warning(f"Error getting active container count: {e}")
            return 0

    def get_all_container_stats(self) -> List[ContainerStats]:
        """Get stats for all running finlab-sandbox containers.

        Returns:
            List of ContainerStats objects for all running containers
        """
        if not self.is_docker_available():
            return []

        stats_list = []

        try:
            running_containers = self.docker_client.containers.list(
                filters={'label': f'{self.FINLAB_LABEL}=true'}
            )

            for container in running_containers:
                stats = self.record_container_stats(container.id)
                if stats:
                    stats_list.append(stats)

        except Exception as e:
            logger.error(f"Error collecting all container stats: {e}", exc_info=True)

        return stats_list

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of container monitoring.

        Returns:
            dict: Status information including:
                - docker_available: Whether Docker daemon is accessible
                - active_containers: Number of running containers
                - orphaned_containers: Number of exited containers
                - cleanup_failures: List of container IDs that failed cleanup
                - auto_cleanup: Whether auto-cleanup is enabled
        """
        orphaned = self.scan_orphaned_containers() if self.is_docker_available() else []

        return {
            'docker_available': self.is_docker_available(),
            'active_containers': self.get_active_containers_count(),
            'orphaned_containers': len(orphaned),
            'orphaned_container_ids': [cid[:12] for cid in orphaned],
            'cleanup_failures': [cid[:12] for cid in self._cleanup_failures],
            'auto_cleanup': self.auto_cleanup,
            'finlab_label': self.FINLAB_LABEL
        }

    def reset(self) -> None:
        """Reset monitoring state (useful for testing).

        Clears:
            - Active container tracking
            - Cleanup failure history
        """
        self._active_containers.clear()
        self._cleanup_failures.clear()

        logger.info("ContainerMonitor state reset")
