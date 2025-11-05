"""Alert Manager for Resource Monitoring System.

This module evaluates alert conditions and triggers notifications based on configurable
thresholds for memory usage, diversity collapse, champion staleness, success rate,
and orphaned containers.

Responsibilities:
    - Evaluate alert conditions every 10 seconds without impacting iteration loop
    - Trigger alerts via structured logging and metrics increment
    - Implement alert suppression to avoid alert fatigue
    - Support configurable thresholds via AlertConfig

Requirements: Task 4 - AlertManager module
Fulfills: Requirements 3.1-3.5 (All alert conditions)
"""

import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Set, Any, Callable
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Structured alert event.

    Attributes:
        alert_type: Identifier for alert (e.g., "high_memory", "diversity_collapse")
        severity: "warning" or "critical"
        message: Human-readable alert message
        current_value: Current metric value that triggered alert
        threshold_value: Threshold that was exceeded
        timestamp: ISO-formatted timestamp
        iteration_context: Current iteration number (if applicable)
    """
    alert_type: str
    severity: str
    message: str
    current_value: float
    threshold_value: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    iteration_context: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for logging."""
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "timestamp": self.timestamp,
            "iteration_context": self.iteration_context
        }


@dataclass
class AlertConfig:
    """Alert threshold configuration.

    Attributes:
        memory_threshold_percent: Memory usage threshold (default: 80%)
        diversity_collapse_threshold: Diversity score threshold (default: 0.1)
        diversity_collapse_window: Consecutive iterations below threshold (default: 5)
        champion_staleness_threshold: Iterations without champion update (default: 20)
        success_rate_threshold: Minimum success rate (default: 20%)
        success_rate_window: Iterations to calculate success rate over (default: 10)
        orphaned_container_threshold: Maximum orphaned containers (default: 3)
        evaluation_interval: Seconds between alert evaluations (default: 10)
        suppression_duration: Seconds to suppress duplicate alerts (default: 300)
    """
    memory_threshold_percent: float = 80.0
    diversity_collapse_threshold: float = 0.1
    diversity_collapse_window: int = 5
    champion_staleness_threshold: int = 20
    success_rate_threshold: float = 20.0
    success_rate_window: int = 10
    orphaned_container_threshold: int = 3
    evaluation_interval: int = 10
    suppression_duration: int = 300  # 5 minutes

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'AlertConfig':
        """Load configuration from dictionary.

        Args:
            config: Dictionary with alert configuration

        Returns:
            AlertConfig instance
        """
        return cls(
            memory_threshold_percent=config.get('memory_threshold_percent', 80.0),
            diversity_collapse_threshold=config.get('diversity_collapse_threshold', 0.1),
            diversity_collapse_window=config.get('diversity_collapse_window', 5),
            champion_staleness_threshold=config.get('champion_staleness_threshold', 20),
            success_rate_threshold=config.get('success_rate_threshold', 20.0),
            success_rate_window=config.get('success_rate_window', 10),
            orphaned_container_threshold=config.get('orphaned_container_threshold', 3),
            evaluation_interval=config.get('evaluation_interval', 10),
            suppression_duration=config.get('suppression_duration', 300)
        )


class AlertManager:
    """Evaluate alert conditions and trigger notifications.

    Features:
        - Configurable thresholds for 5 alert types
        - Alert suppression to avoid duplicate notifications
        - Background evaluation without blocking main loop
        - Structured logging for alert events
        - Prometheus metrics integration

    Alert Types:
        1. high_memory: Memory usage exceeds threshold
        2. diversity_collapse: Diversity below threshold for consecutive iterations
        3. champion_staleness: Champion not updated for threshold iterations
        4. low_success_rate: Success rate below threshold over window
        5. orphaned_containers: Too many containers not cleaned up

    Example:
        >>> config = AlertConfig(memory_threshold_percent=85.0)
        >>> manager = AlertManager(config, metrics_collector)
        >>> manager.start_monitoring()
        >>> # Set data sources
        >>> manager.set_memory_source(lambda: resource_monitor.get_current_stats())
        >>> manager.set_diversity_source(lambda: diversity_monitor.get_current_diversity())
        >>> # ... run workload ...
        >>> manager.stop_monitoring()
    """

    def __init__(
        self,
        config: AlertConfig,
        metrics_collector,
        event_logger: Optional[Any] = None
    ):
        """Initialize AlertManager.

        Args:
            config: Alert threshold configuration
            metrics_collector: MetricsCollector instance for Prometheus export
            event_logger: Optional EventLogger for structured alert logging
        """
        self.config = config
        self.metrics_collector = metrics_collector
        self.event_logger = event_logger

        # Alert suppression tracking
        self._active_alerts: Set[str] = set()
        self._last_alert_time: Dict[str, float] = {}

        # Data sources (set by external components)
        self._memory_source: Optional[Callable] = None
        self._diversity_source: Optional[Callable] = None
        self._staleness_source: Optional[Callable] = None
        self._success_rate_source: Optional[Callable] = None
        self._container_source: Optional[Callable] = None
        self._iteration_source: Optional[Callable] = None

        # Background monitoring
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Success rate tracking (if no external source)
        self._success_history: deque = deque(maxlen=config.success_rate_window)

        # Register metrics
        self._register_metrics()

        logger.info(
            f"AlertManager initialized with evaluation_interval={config.evaluation_interval}s, "
            f"suppression_duration={config.suppression_duration}s"
        )

    def _register_metrics(self) -> None:
        """Register alert metrics with MetricsCollector."""
        # Alert metrics will be added in Task 5 (MetricsCollector extension)
        # For now, use existing metric structure
        if self.metrics_collector and not hasattr(self.metrics_collector, '_alert_metrics_registered'):
            self.metrics_collector._alert_metrics_registered = True
            logger.debug("Alert metrics registered with MetricsCollector")

    # =========================================================================
    # Data Source Configuration
    # =========================================================================

    def set_memory_source(self, source: Callable[[], Dict[str, float]]) -> None:
        """Set memory stats data source.

        Args:
            source: Callable returning dict with 'memory_percent' key
        """
        self._memory_source = source

    def set_diversity_source(self, source: Callable[[], Optional[float]]) -> None:
        """Set diversity data source.

        Args:
            source: Callable returning current diversity score (0.0-1.0)
        """
        self._diversity_source = source

    def set_staleness_source(self, source: Callable[[], int]) -> None:
        """Set champion staleness data source.

        Args:
            source: Callable returning iterations since last champion update
        """
        self._staleness_source = source

    def set_success_rate_source(self, source: Callable[[], float]) -> None:
        """Set success rate data source.

        Args:
            source: Callable returning success rate percentage (0-100)
        """
        self._success_rate_source = source

    def set_container_source(self, source: Callable[[], int]) -> None:
        """Set orphaned container count data source.

        Args:
            source: Callable returning number of orphaned containers
        """
        self._container_source = source

    def set_iteration_source(self, source: Callable[[], int]) -> None:
        """Set current iteration number source.

        Args:
            source: Callable returning current iteration number
        """
        self._iteration_source = source

    # =========================================================================
    # Manual Tracking Methods (if no external data sources)
    # =========================================================================

    def record_iteration_result(self, success: bool) -> None:
        """Record iteration result for success rate tracking.

        Args:
            success: Whether iteration succeeded
        """
        self._success_history.append(1.0 if success else 0.0)

    # =========================================================================
    # Background Monitoring
    # =========================================================================

    def start_monitoring(self) -> None:
        """Start background alert evaluation thread.

        Raises:
            RuntimeError: If monitoring already started
        """
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            raise RuntimeError("Alert monitoring already started")

        self._stop_event.clear()

        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="AlertManager",
            daemon=True
        )
        self._monitoring_thread.start()

        logger.info("AlertManager background monitoring started")

    def stop_monitoring(self) -> None:
        """Stop background alert evaluation thread."""
        if not self._monitoring_thread or not self._monitoring_thread.is_alive():
            logger.warning("Alert monitoring not running, nothing to stop")
            return

        logger.info("Stopping AlertManager...")
        self._stop_event.set()

        # Wait for thread to exit (max 15 seconds)
        self._monitoring_thread.join(timeout=15.0)

        if self._monitoring_thread.is_alive():
            logger.error("AlertManager thread did not stop within timeout")
        else:
            logger.info("AlertManager stopped successfully")

    def _monitoring_loop(self) -> None:
        """Background thread loop for alert evaluation.

        Evaluates all alert conditions every evaluation_interval seconds.
        """
        logger.info("AlertManager background thread started")

        while not self._stop_event.is_set():
            start_time = time.time()

            try:
                self.evaluate_alerts()
            except Exception as e:
                logger.error(f"Error evaluating alerts: {e}", exc_info=True)

            # Track evaluation time
            elapsed = time.time() - start_time
            if elapsed > 0.05:  # >50ms
                logger.warning(f"Alert evaluation took {elapsed*1000:.1f}ms (target: <50ms)")

            # Sleep until next evaluation
            self._stop_event.wait(timeout=self.config.evaluation_interval)

        logger.info("AlertManager background thread exited")

    # =========================================================================
    # Alert Evaluation
    # =========================================================================

    def evaluate_alerts(self) -> None:
        """Evaluate all alert conditions.

        Checks each alert type and triggers notifications if thresholds exceeded
        and alert not currently suppressed.
        """
        # Get current iteration context
        current_iteration = self._iteration_source() if self._iteration_source else None

        # Evaluate each alert type
        alerts = [
            self._check_memory_threshold(),
            self._check_diversity_collapse(),
            self._check_champion_staleness(),
            self._check_success_rate(),
            self._check_orphaned_containers()
        ]

        # Trigger alerts
        for alert in alerts:
            if alert:
                alert.iteration_context = current_iteration
                self._trigger_alert(alert)

    def _check_memory_threshold(self) -> Optional[Alert]:
        """Check if memory usage exceeds threshold.

        Returns:
            Alert if threshold exceeded, None otherwise
        """
        if not self._memory_source:
            return None

        try:
            stats = self._memory_source()
            memory_percent = stats.get('memory_percent', 0)

            if memory_percent > self.config.memory_threshold_percent:
                return Alert(
                    alert_type="high_memory",
                    severity="critical",
                    message=f"High memory usage detected: {memory_percent:.1f}% (threshold: {self.config.memory_threshold_percent:.1f}%)",
                    current_value=memory_percent,
                    threshold_value=self.config.memory_threshold_percent
                )
        except Exception as e:
            logger.warning(f"Error checking memory threshold: {e}")

        return None

    def _check_diversity_collapse(self) -> Optional[Alert]:
        """Check if diversity collapse occurred.

        Returns:
            Alert if collapse detected, None otherwise
        """
        if not self._diversity_source:
            return None

        try:
            diversity = self._diversity_source()
            if diversity is None:
                return None

            # Check if below threshold (actual collapse detection done in DiversityMonitor)
            if diversity < self.config.diversity_collapse_threshold:
                return Alert(
                    alert_type="diversity_collapse",
                    severity="warning",
                    message=f"Diversity collapse detected: {diversity:.4f} (threshold: {self.config.diversity_collapse_threshold:.4f})",
                    current_value=diversity,
                    threshold_value=self.config.diversity_collapse_threshold
                )
        except Exception as e:
            logger.warning(f"Error checking diversity collapse: {e}")

        return None

    def _check_champion_staleness(self) -> Optional[Alert]:
        """Check if champion has not been updated for too long.

        Returns:
            Alert if staleness threshold exceeded, None otherwise
        """
        if not self._staleness_source:
            return None

        try:
            staleness = self._staleness_source()

            if staleness >= self.config.champion_staleness_threshold:
                return Alert(
                    alert_type="champion_staleness",
                    severity="warning",
                    message=f"Champion staleness detected: {staleness} iterations (threshold: {self.config.champion_staleness_threshold})",
                    current_value=float(staleness),
                    threshold_value=float(self.config.champion_staleness_threshold)
                )
        except Exception as e:
            logger.warning(f"Error checking champion staleness: {e}")

        return None

    def _check_success_rate(self) -> Optional[Alert]:
        """Check if success rate is too low.

        Returns:
            Alert if success rate below threshold, None otherwise
        """
        # Use external source if available
        if self._success_rate_source:
            try:
                success_rate = self._success_rate_source()

                if success_rate < self.config.success_rate_threshold:
                    return Alert(
                        alert_type="low_success_rate",
                        severity="warning",
                        message=f"Low success rate detected: {success_rate:.1f}% (threshold: {self.config.success_rate_threshold:.1f}%)",
                        current_value=success_rate,
                        threshold_value=self.config.success_rate_threshold
                    )
            except Exception as e:
                logger.warning(f"Error checking success rate: {e}")

        # Fall back to internal tracking
        elif len(self._success_history) >= self.config.success_rate_window:
            success_rate = (sum(self._success_history) / len(self._success_history)) * 100

            if success_rate < self.config.success_rate_threshold:
                return Alert(
                    alert_type="low_success_rate",
                    severity="warning",
                    message=f"Low success rate detected: {success_rate:.1f}% (threshold: {self.config.success_rate_threshold:.1f}%)",
                    current_value=success_rate,
                    threshold_value=self.config.success_rate_threshold
                )

        return None

    def _check_orphaned_containers(self) -> Optional[Alert]:
        """Check if too many orphaned containers exist.

        Returns:
            Alert if orphaned container count exceeds threshold, None otherwise
        """
        if not self._container_source:
            return None

        try:
            orphaned_count = self._container_source()

            if orphaned_count > self.config.orphaned_container_threshold:
                return Alert(
                    alert_type="orphaned_containers",
                    severity="critical",
                    message=f"Container cleanup failures detected: {orphaned_count} orphaned containers (threshold: {self.config.orphaned_container_threshold})",
                    current_value=float(orphaned_count),
                    threshold_value=float(self.config.orphaned_container_threshold)
                )
        except Exception as e:
            logger.warning(f"Error checking orphaned containers: {e}")

        return None

    # =========================================================================
    # Alert Triggering
    # =========================================================================

    def _trigger_alert(self, alert: Alert) -> None:
        """Trigger alert notification.

        Checks suppression state and triggers alert via logging and metrics
        if not currently suppressed.

        Args:
            alert: Alert to trigger
        """
        # Check if alert is suppressed
        if self._is_alert_suppressed(alert.alert_type):
            logger.debug(f"Alert {alert.alert_type} suppressed (active within suppression window)")
            return

        # Mark alert as active
        self._active_alerts.add(alert.alert_type)
        self._last_alert_time[alert.alert_type] = time.time()

        # Log alert
        self._log_alert(alert)

        # Increment metrics
        self._increment_alert_metric(alert.alert_type)

        # Log alert trigger (don't include 'message' in extra - it's reserved)
        alert_dict = alert.to_dict()
        alert_dict.pop('message', None)
        logger.warning(
            f"ALERT TRIGGERED: {alert.alert_type} - {alert.message}",
            extra=alert_dict
        )

    def _is_alert_suppressed(self, alert_type: str) -> bool:
        """Check if alert is currently suppressed.

        Args:
            alert_type: Type of alert to check

        Returns:
            bool: True if alert is suppressed, False otherwise
        """
        if alert_type not in self._last_alert_time:
            return False

        last_time = self._last_alert_time[alert_type]
        elapsed = time.time() - last_time

        # Alert is suppressed if within suppression duration
        if elapsed < self.config.suppression_duration:
            return True

        # Alert is no longer suppressed
        self._active_alerts.discard(alert_type)
        return False

    def _log_alert(self, alert: Alert) -> None:
        """Log alert event.

        Args:
            alert: Alert to log
        """
        # Use EventLogger if available
        if self.event_logger:
            try:
                self.event_logger.log_event(
                    logging.WARNING if alert.severity == "warning" else logging.ERROR,
                    f"alert_{alert.alert_type}",
                    alert.message,
                    **alert.to_dict()
                )
            except Exception as e:
                logger.warning(f"Failed to log alert via EventLogger: {e}")

        # Always log to standard logger
        # Don't include 'message' in extra (it's a reserved field)
        alert_dict = alert.to_dict()
        alert_dict.pop('message', None)  # Remove message from extra
        logger.warning(
            f"Alert: {alert.alert_type} - {alert.message}",
            extra=alert_dict
        )

    def _increment_alert_metric(self, alert_type: str) -> None:
        """Increment alert counter metric.

        Args:
            alert_type: Type of alert to increment
        """
        try:
            # Use MetricsCollector extension from Task 5 when available
            if hasattr(self.metrics_collector, 'record_alert_triggered'):
                self.metrics_collector.record_alert_triggered(alert_type)
            else:
                # Fallback: increment generic error counter
                self.metrics_collector.record_error(f"alert_{alert_type}")
        except Exception as e:
            logger.warning(f"Failed to increment alert metric: {e}")

    # =========================================================================
    # Status and Control
    # =========================================================================

    def get_active_alerts(self) -> Set[str]:
        """Get set of currently active alerts.

        Returns:
            Set of alert types currently active
        """
        return self._active_alerts.copy()

    def clear_alert(self, alert_type: str) -> None:
        """Manually clear an active alert.

        Args:
            alert_type: Type of alert to clear
        """
        self._active_alerts.discard(alert_type)
        self._last_alert_time.pop(alert_type, None)
        logger.info(f"Alert {alert_type} manually cleared")

    def reset_suppression(self) -> None:
        """Reset all alert suppression (useful for testing)."""
        self._active_alerts.clear()
        self._last_alert_time.clear()
        logger.info("Alert suppression reset")

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive alert manager status.

        Returns:
            Dictionary with status information
        """
        return {
            'active_alerts': list(self._active_alerts),
            'suppressed_count': len(self._active_alerts),
            'config': {
                'memory_threshold': self.config.memory_threshold_percent,
                'diversity_threshold': self.config.diversity_collapse_threshold,
                'staleness_threshold': self.config.champion_staleness_threshold,
                'success_rate_threshold': self.config.success_rate_threshold,
                'container_threshold': self.config.orphaned_container_threshold,
                'evaluation_interval': self.config.evaluation_interval,
                'suppression_duration': self.config.suppression_duration
            },
            'monitoring_active': self._monitoring_thread and self._monitoring_thread.is_alive()
        }

    def __enter__(self):
        """Context manager entry - start monitoring."""
        self.start_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop monitoring."""
        self.stop_monitoring()
        return False
