"""Alerting System for Multi-Template Evolution.

This module provides real-time alerting for evolution anomalies and system health issues.

Requirements:
- Task 42: Basic alerting for sandbox deployment
- Integration with EvolutionMetricsTracker
- Supports multiple alert channels (logging, file, webhook)

Alert Types:
- System: crashes, memory issues, timeout
- Evolution: fitness drop, diversity collapse, no improvement
- Performance: slow generation, high latency
- Template: template collapse, mutation failures
"""

import logging
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert delivery channels."""
    LOG = "log"  # Log to logging system
    FILE = "file"  # Write to file
    WEBHOOK = "webhook"  # HTTP webhook (for future use)
    CONSOLE = "console"  # Print to console


@dataclass
class Alert:
    """Alert data structure."""
    timestamp: float
    severity: AlertSeverity
    alert_type: str
    message: str
    generation: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['datetime'] = datetime.fromtimestamp(self.timestamp).isoformat()
        return data

    def to_log_message(self) -> str:
        """Format as log message."""
        gen_str = f" Gen {self.generation}" if self.generation is not None else ""
        return f"[{self.severity.value.upper()}]{gen_str}: {self.alert_type} - {self.message}"


class AlertManager:
    """Manages alert generation, storage, and delivery.

    Features:
    - Multiple alert channels (log, file, webhook)
    - Alert rate limiting to prevent spam
    - Alert history tracking
    - Custom alert handlers
    - Severity-based filtering

    Example:
        >>> manager = AlertManager(alert_file="alerts.json")
        >>> manager.send_alert(
        ...     severity=AlertSeverity.HIGH,
        ...     alert_type="fitness_drop",
        ...     message="Fitness dropped 25%",
        ...     generation=50
        ... )
    """

    def __init__(
        self,
        alert_file: Optional[Path] = None,
        channels: Optional[List[AlertChannel]] = None,
        min_severity: AlertSeverity = AlertSeverity.LOW,
        rate_limit_seconds: int = 60
    ):
        """Initialize alert manager.

        Args:
            alert_file: Path to JSON file for storing alerts (optional)
            channels: List of alert channels to use (default: [LOG, FILE])
            min_severity: Minimum severity to process (default: LOW)
            rate_limit_seconds: Minimum seconds between duplicate alerts (default: 60)
        """
        self.alert_file = Path(alert_file) if alert_file else None
        self.channels = channels or [AlertChannel.LOG, AlertChannel.FILE]
        self.min_severity = min_severity
        self.rate_limit_seconds = rate_limit_seconds

        # Alert storage
        self.alert_history: List[Alert] = []
        self.last_alert_time: Dict[str, float] = {}  # {alert_type: timestamp}

        # Custom handlers
        self.custom_handlers: List[Callable[[Alert], None]] = []

        # Initialize alert file if specified
        if self.alert_file:
            self.alert_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.alert_file.exists():
                self.alert_file.write_text(json.dumps([], indent=2))

        logger.info(f"AlertManager initialized with channels={[c.value for c in self.channels]}")

    def send_alert(
        self,
        severity: AlertSeverity,
        alert_type: str,
        message: str,
        generation: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[Alert]:
        """Send an alert through configured channels.

        Args:
            severity: Alert severity level
            alert_type: Type of alert
            message: Alert message
            generation: Generation number (if applicable)
            details: Additional details (optional)

        Returns:
            Alert object if sent, None if filtered/rate-limited
        """
        # Check severity filter
        severity_levels = {
            AlertSeverity.LOW: 0,
            AlertSeverity.MEDIUM: 1,
            AlertSeverity.HIGH: 2,
            AlertSeverity.CRITICAL: 3
        }

        if severity_levels[severity] < severity_levels[self.min_severity]:
            logger.debug(f"Alert filtered (severity too low): {alert_type}")
            return None

        # Check rate limiting
        current_time = time.time()
        last_time = self.last_alert_time.get(alert_type, 0)

        if current_time - last_time < self.rate_limit_seconds:
            logger.debug(f"Alert rate-limited: {alert_type} (last sent {current_time - last_time:.0f}s ago)")
            return None

        # Create alert
        alert = Alert(
            timestamp=current_time,
            severity=severity,
            alert_type=alert_type,
            message=message,
            generation=generation,
            details=details or {}
        )

        # Store in history
        self.alert_history.append(alert)
        self.last_alert_time[alert_type] = current_time

        # Deliver through channels
        self._deliver_alert(alert)

        # Call custom handlers
        for handler in self.custom_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Custom alert handler failed: {e}")

        return alert

    def _deliver_alert(self, alert: Alert) -> None:
        """Deliver alert through configured channels.

        Args:
            alert: Alert to deliver
        """
        # LOG channel
        if AlertChannel.LOG in self.channels:
            log_msg = alert.to_log_message()
            if alert.severity == AlertSeverity.CRITICAL:
                logger.error(log_msg)
            elif alert.severity == AlertSeverity.HIGH:
                logger.warning(log_msg)
            else:
                logger.info(log_msg)

        # FILE channel
        if AlertChannel.FILE in self.channels and self.alert_file:
            self._write_to_file(alert)

        # CONSOLE channel
        if AlertChannel.CONSOLE in self.channels:
            print(f"\n⚠️  {alert.to_log_message()}")
            if alert.details:
                print(f"   Details: {json.dumps(alert.details, indent=4)}")

    def _write_to_file(self, alert: Alert) -> None:
        """Write alert to JSON file.

        Args:
            alert: Alert to write
        """
        if not self.alert_file:
            return

        try:
            # Read existing alerts
            if self.alert_file.exists():
                existing_alerts = json.loads(self.alert_file.read_text())
            else:
                existing_alerts = []

            # Append new alert
            existing_alerts.append(alert.to_dict())

            # Keep only last 1000 alerts to prevent file bloat
            if len(existing_alerts) > 1000:
                existing_alerts = existing_alerts[-1000:]

            # Write back
            self.alert_file.write_text(json.dumps(existing_alerts, indent=2))

        except Exception as e:
            logger.error(f"Failed to write alert to file: {e}")

    def add_custom_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add a custom alert handler.

        Args:
            handler: Callable that takes Alert object as input
        """
        self.custom_handlers.append(handler)
        logger.info(f"Added custom alert handler: {handler.__name__}")

    def get_recent_alerts(self, count: int = 10, min_severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get recent alerts.

        Args:
            count: Number of recent alerts to return
            min_severity: Filter by minimum severity (optional)

        Returns:
            List of recent alerts
        """
        filtered_alerts = self.alert_history

        if min_severity:
            severity_levels = {
                AlertSeverity.LOW: 0,
                AlertSeverity.MEDIUM: 1,
                AlertSeverity.HIGH: 2,
                AlertSeverity.CRITICAL: 3
            }
            min_level = severity_levels[min_severity]
            filtered_alerts = [
                a for a in filtered_alerts
                if severity_levels[a.severity] >= min_level
            ]

        return filtered_alerts[-count:]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of all alerts.

        Returns:
            Dictionary with alert statistics
        """
        if not self.alert_history:
            return {"total_alerts": 0}

        # Count by severity
        severity_counts = {
            "low": sum(1 for a in self.alert_history if a.severity == AlertSeverity.LOW),
            "medium": sum(1 for a in self.alert_history if a.severity == AlertSeverity.MEDIUM),
            "high": sum(1 for a in self.alert_history if a.severity == AlertSeverity.HIGH),
            "critical": sum(1 for a in self.alert_history if a.severity == AlertSeverity.CRITICAL),
        }

        # Count by type
        type_counts = {}
        for alert in self.alert_history:
            type_counts[alert.alert_type] = type_counts.get(alert.alert_type, 0) + 1

        # Recent alerts (last 10)
        recent = [a.to_dict() for a in self.alert_history[-10:]]

        return {
            "total_alerts": len(self.alert_history),
            "by_severity": severity_counts,
            "by_type": type_counts,
            "recent_alerts": recent,
            "oldest_alert": self.alert_history[0].to_dict() if self.alert_history else None,
            "newest_alert": self.alert_history[-1].to_dict() if self.alert_history else None,
        }

    def acknowledge_alert(self, alert: Alert) -> None:
        """Mark an alert as acknowledged.

        Args:
            alert: Alert to acknowledge
        """
        alert.acknowledged = True
        logger.info(f"Alert acknowledged: {alert.alert_type} at {alert.timestamp}")

    def clear_old_alerts(self, max_age_hours: int = 24) -> int:
        """Clear alerts older than specified age.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of alerts cleared
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        original_count = len(self.alert_history)

        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]

        cleared_count = original_count - len(self.alert_history)

        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} alerts older than {max_age_hours} hours")

        return cleared_count


# Predefined alert helper functions for common scenarios

def create_fitness_drop_alert(
    manager: AlertManager,
    generation: int,
    prev_fitness: float,
    current_fitness: float
) -> Optional[Alert]:
    """Create alert for significant fitness drop.

    Args:
        manager: AlertManager instance
        generation: Current generation
        prev_fitness: Previous generation fitness
        current_fitness: Current generation fitness

    Returns:
        Alert if sent, None otherwise
    """
    drop_percentage = ((prev_fitness - current_fitness) / prev_fitness * 100) if prev_fitness > 0 else 0

    if drop_percentage > 20:
        severity = AlertSeverity.HIGH if drop_percentage > 50 else AlertSeverity.MEDIUM

        return manager.send_alert(
            severity=severity,
            alert_type="fitness_drop",
            message=f"Fitness dropped {drop_percentage:.1f}%",
            generation=generation,
            details={
                "prev_fitness": prev_fitness,
                "current_fitness": current_fitness,
                "drop_percentage": drop_percentage
            }
        )

    return None


def create_diversity_collapse_alert(
    manager: AlertManager,
    generation: int,
    diversity: float,
    threshold: float = 0.1
) -> Optional[Alert]:
    """Create alert for diversity collapse.

    Args:
        manager: AlertManager instance
        generation: Current generation
        diversity: Current diversity value
        threshold: Threshold below which to alert

    Returns:
        Alert if sent, None otherwise
    """
    if diversity < threshold:
        return manager.send_alert(
            severity=AlertSeverity.HIGH,
            alert_type="diversity_collapse",
            message=f"Diversity collapsed to {diversity:.4f}",
            generation=generation,
            details={"diversity": diversity, "threshold": threshold}
        )

    return None


def create_no_improvement_alert(
    manager: AlertManager,
    generation: int,
    last_improvement_generation: int,
    threshold_generations: int = 20
) -> Optional[Alert]:
    """Create alert for lack of improvement.

    Args:
        manager: AlertManager instance
        generation: Current generation
        last_improvement_generation: Last generation with improvement
        threshold_generations: Number of generations without improvement to alert

    Returns:
        Alert if sent, None otherwise
    """
    gens_since_improvement = generation - last_improvement_generation

    if gens_since_improvement >= threshold_generations:
        return manager.send_alert(
            severity=AlertSeverity.LOW,
            alert_type="no_improvement",
            message=f"No improvement in {gens_since_improvement} generations",
            generation=generation,
            details={
                "last_improvement_generation": last_improvement_generation,
                "generations_since_improvement": gens_since_improvement
            }
        )

    return None


def create_system_error_alert(
    manager: AlertManager,
    generation: Optional[int],
    error_type: str,
    error_message: str,
    traceback: Optional[str] = None
) -> Alert:
    """Create alert for system errors.

    Args:
        manager: AlertManager instance
        generation: Current generation (if applicable)
        error_type: Type of error
        error_message: Error message
        traceback: Error traceback (optional)

    Returns:
        Alert object
    """
    details = {"error_type": error_type, "error_message": error_message}
    if traceback:
        details["traceback"] = traceback

    return manager.send_alert(
        severity=AlertSeverity.CRITICAL,
        alert_type="system_error",
        message=f"{error_type}: {error_message}",
        generation=generation,
        details=details
    )
