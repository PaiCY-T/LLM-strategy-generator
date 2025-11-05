"""Monitoring integration patch for autonomous_loop.py

This module contains the monitoring integration code to be added to autonomous_loop.py.
Task 8: Integrate monitoring into autonomous loop

Integration Points:
1. Import monitoring modules (after existing imports)
2. Initialize monitoring in __init__
3. Record metrics at key iteration points
4. Cleanup monitoring in loop shutdown

Usage:
- Merge this code into autonomous_loop.py following the comments
"""

# =========================================================================
# PATCH 1: Add imports after line 38 (after get_event_logger import)
# =========================================================================
IMPORTS_PATCH = """
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.resource_monitor import ResourceMonitor
from src.monitoring.diversity_monitor import DiversityMonitor
from src.monitoring.container_monitor import ContainerMonitor
from src.monitoring.alert_manager import AlertManager, AlertConfig
"""

# =========================================================================
# PATCH 2: Add _initialize_monitoring method (before _load_multi_objective_config)
# =========================================================================
INITIALIZE_MONITORING_METHOD = '''
    def _initialize_monitoring(self) -> None:
        """Initialize monitoring components for resource tracking.

        Task 8: Integrate monitoring into autonomous loop
        - Creates MetricsCollector, ResourceMonitor, DiversityMonitor, ContainerMonitor, AlertManager
        - Starts background threads for resource and alert monitoring
        - Configures data sources for alert evaluation
        - Gracefully handles initialization failures (monitoring optional)

        Integration points:
        1. Loop initialization: Create monitoring components, start threads
        2. Start of iteration: Record resource snapshot, check alerts
        3. After strategy execution: Record diversity, container stats
        4. After champion update: Record staleness, update champion metrics
        5. Loop shutdown: Stop monitoring threads cleanly
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Initialize MetricsCollector for Prometheus export
            self.metrics_collector = MetricsCollector()
            logger.info("MetricsCollector initialized")

            # Initialize ResourceMonitor for system resource tracking
            self.resource_monitor = ResourceMonitor(self.metrics_collector)
            self.resource_monitor.start_monitoring(interval_seconds=5)
            logger.info("ResourceMonitor started (5s interval)")

            # Initialize DiversityMonitor for population diversity tracking
            self.diversity_monitor = DiversityMonitor(
                self.metrics_collector,
                collapse_threshold=0.1,
                collapse_window=5
            )
            logger.info("DiversityMonitor initialized")

            # Initialize ContainerMonitor for Docker resource tracking
            try:
                # Attempt to initialize Docker client
                import docker
                docker_client = docker.from_env()
                self.container_monitor = ContainerMonitor(
                    self.metrics_collector,
                    docker_client,
                    auto_cleanup=True
                )
                logger.info("ContainerMonitor initialized with Docker client")
            except Exception as e:
                # Docker not available - create monitor without client
                logger.warning(f"Docker not available, ContainerMonitor disabled: {e}")
                self.container_monitor = ContainerMonitor(
                    self.metrics_collector,
                    docker_client=None,
                    auto_cleanup=False
                )

            # Initialize AlertManager with configuration
            alert_config = AlertConfig(
                memory_threshold_percent=80.0,
                diversity_collapse_threshold=0.1,
                diversity_collapse_window=5,
                champion_staleness_threshold=20,
                success_rate_threshold=20.0,
                success_rate_window=10,
                orphaned_container_threshold=3,
                evaluation_interval=10,
                suppression_duration=300
            )
            self.alert_manager = AlertManager(alert_config, self.metrics_collector)

            # Configure alert data sources
            self.alert_manager.set_memory_source(
                lambda: self.resource_monitor.get_current_stats()
            )
            self.alert_manager.set_diversity_source(
                lambda: self.diversity_monitor.get_current_diversity()
            )
            self.alert_manager.set_staleness_source(
                lambda: self.diversity_monitor.get_current_staleness()
            )
            self.alert_manager.set_container_source(
                lambda: len(self.container_monitor.scan_orphaned_containers()) if self.container_monitor.is_docker_available() else 0
            )

            # Start alert monitoring
            self.alert_manager.start_monitoring()
            logger.info("AlertManager started (10s evaluation interval)")

            # Mark monitoring as enabled
            self._monitoring_enabled = True
            logger.info("Monitoring system fully initialized")

        except Exception as e:
            # Monitoring initialization failed - log warning but continue
            logger.warning(f"Monitoring initialization failed: {e}. Continuing without monitoring.")
            self.metrics_collector = None
            self.resource_monitor = None
            self.diversity_monitor = None
            self.container_monitor = None
            self.alert_manager = None
            self._monitoring_enabled = False
'''

# =========================================================================
# PATCH 3: Call _initialize_monitoring in __init__ (after anti_churn initialization)
# =========================================================================
INIT_CALL_PATCH = """
        # Resource monitoring system (Task 8: Integration)
        self._initialize_monitoring()
"""

# =========================================================================
# PATCH 4: Add _record_iteration_monitoring in _run_freeform_iteration
# (After champion update section, around line 700)
# =========================================================================
RECORD_MONITORING_METHOD = '''
    def _record_iteration_monitoring(
        self,
        iteration_num: int,
        execution_success: bool,
        metrics: Optional[Dict[str, float]] = None
    ) -> None:
        """Record monitoring metrics for current iteration.

        Integration Point 3: After strategy execution
        Records diversity, container stats, and iteration results to monitoring system.

        Args:
            iteration_num: Current iteration number
            execution_success: Whether iteration succeeded
            metrics: Performance metrics if available
        """
        if not self._monitoring_enabled:
            return

        import logging
        logger = logging.getLogger(__name__)

        try:
            # Record iteration result for success rate tracking
            if self.alert_manager:
                self.alert_manager.record_iteration_result(execution_success)

            # Record diversity if metrics available (placeholder - requires population manager integration)
            # This is a simplified version - full integration would calculate actual diversity
            if self.diversity_monitor and metrics and execution_success:
                # For now, use a placeholder diversity calculation
                # In production, this should call population_manager.calculate_diversity()
                diversity = 0.5  # Placeholder
                unique_count = 1
                total_count = 1

                self.diversity_monitor.record_diversity(
                    iteration=iteration_num,
                    diversity=diversity,
                    unique_count=unique_count,
                    total_count=total_count
                )

                # Check for diversity collapse
                if self.diversity_monitor.check_diversity_collapse():
                    logger.warning(f"Diversity collapse detected at iteration {iteration_num}")

            # Record container stats if available
            if self.container_monitor and self.container_monitor.is_docker_available():
                # Scan for orphaned containers periodically (every 10 iterations)
                if iteration_num % 10 == 0:
                    orphaned = self.container_monitor.scan_orphaned_containers()
                    if orphaned:
                        logger.warning(f"Found {len(orphaned)} orphaned containers")
                        # Auto-cleanup if enabled
                        if self.container_monitor.auto_cleanup:
                            cleaned = self.container_monitor.cleanup_orphaned_containers(orphaned)
                            logger.info(f"Cleaned up {cleaned} orphaned containers")

        except Exception as e:
            # Monitoring should never break the iteration loop
            logger.warning(f"Monitoring recording failed (non-fatal): {e}")
'''

# =========================================================================
# PATCH 5: Update _update_champion to record champion updates
# (After champion creation, around line 975)
# =========================================================================
CHAMPION_MONITORING_PATCH = '''
            # Record champion update to DiversityMonitor (Task 8)
            if self._monitoring_enabled and self.diversity_monitor:
                try:
                    self.diversity_monitor.record_champion_update(
                        iteration=iteration_num,
                        old_sharpe=champion_sharpe,
                        new_sharpe=current_sharpe
                    )
                except Exception as e:
                    logger.warning(f"Failed to record champion update to monitoring: {e}")
'''

# =========================================================================
# PATCH 6: Add _cleanup_monitoring method (after _check_champion_staleness)
# =========================================================================
CLEANUP_MONITORING_METHOD = '''
    def _cleanup_monitoring(self) -> None:
        """Cleanup monitoring threads and resources.

        Integration Point 5: Loop shutdown
        Stops all monitoring threads gracefully.
        """
        import logging
        logger = logging.getLogger(__name__)

        if not self._monitoring_enabled:
            return

        logger.info("Shutting down monitoring system...")

        try:
            # Stop ResourceMonitor
            if self.resource_monitor:
                try:
                    self.resource_monitor.stop_monitoring()
                    logger.info("ResourceMonitor stopped")
                except Exception as e:
                    logger.error(f"Failed to stop ResourceMonitor: {e}")

            # Stop AlertManager
            if self.alert_manager:
                try:
                    self.alert_manager.stop_monitoring()
                    logger.info("AlertManager stopped")
                except Exception as e:
                    logger.error(f"Failed to stop AlertManager: {e}")

            logger.info("Monitoring system shutdown complete")

        except Exception as e:
            logger.error(f"Error during monitoring cleanup: {e}")
'''

# =========================================================================
# PATCH 7: Add cleanup call in run() method (at the end, before return)
# =========================================================================
RUN_CLEANUP_PATCH = """
        # Cleanup monitoring system (Task 8)
        self._cleanup_monitoring()
"""

# =========================================================================
# INTEGRATION INSTRUCTIONS
# =========================================================================
INTEGRATION_INSTRUCTIONS = """
Monitoring Integration for autonomous_loop.py - Task 8

Apply these patches in order:

1. IMPORTS_PATCH: Add after line 38 (after get_event_logger import)

2. INITIALIZE_MONITORING_METHOD: Add before _load_multi_objective_config() method

3. INIT_CALL_PATCH: Add in __init__ after anti_churn initialization

4. RECORD_MONITORING_METHOD: Add as new method after _check_champion_staleness()

5. CHAMPION_MONITORING_PATCH: Add in _update_champion after champion creation (line ~975)

6. CLEANUP_MONITORING_METHOD: Add as new method after _check_champion_staleness()

7. RUN_CLEANUP_PATCH: Add in run() method before final return statement

Integration Points:
- Loop initialization: Create monitors, start background threads
- After champion update: Record to DiversityMonitor
- After iteration: Record diversity, check containers
- Loop shutdown: Stop monitoring threads cleanly

Error Handling:
- All monitoring operations wrapped in try/except
- Failures logged but don't break iteration loop
- Graceful degradation if monitoring unavailable
"""

if __name__ == '__main__':
    print(INTEGRATION_INSTRUCTIONS)
