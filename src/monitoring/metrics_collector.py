"""Metrics Collector for Production Monitoring.

This module provides comprehensive metrics collection for the autonomous learning system.
Metrics are collected in Prometheus-compatible format and can be exported for monitoring
dashboards (Grafana, Prometheus, etc.).

Categories:
- Learning Metrics: Success rate, average Sharpe, champion update rate
- Performance Metrics: Iteration duration, metric extraction time
- Quality Metrics: Validation pass rate, preservation success rate
- System Metrics: API call counts, error rates, retry counts

Requirements: Task 99 - Monitoring Dashboard Metrics
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Deque
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric type classification for Prometheus export."""
    COUNTER = "counter"      # Monotonically increasing (e.g., total_iterations)
    GAUGE = "gauge"          # Can go up or down (e.g., current_sharpe)
    HISTOGRAM = "histogram"  # Distribution of values (e.g., iteration_duration)
    SUMMARY = "summary"      # Similar to histogram with percentiles


@dataclass
class MetricValue:
    """Single metric value with timestamp and metadata."""
    value: float
    timestamp: float  # Unix timestamp
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "value": self.value,
            "timestamp": self.timestamp,
            "labels": self.labels
        }


@dataclass
class Metric:
    """Metric definition with type and help text."""
    name: str
    metric_type: MetricType
    help_text: str
    unit: str = ""
    values: List[MetricValue] = field(default_factory=list)

    def add_value(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Add a new value to the metric time series."""
        metric_value = MetricValue(
            value=value,
            timestamp=time.time(),
            labels=labels or {}
        )
        self.values.append(metric_value)

    def get_latest(self) -> Optional[float]:
        """Get the most recent value."""
        return self.values[-1].value if self.values else None

    def get_average(self, window: Optional[int] = None) -> float:
        """Get average value over window (or all values if None)."""
        if not self.values:
            return 0.0

        values_to_avg = self.values[-window:] if window else self.values
        return sum(v.value for v in values_to_avg) / len(values_to_avg)


class MetricsCollector:
    """Central metrics collection system for autonomous learning loop.

    Collects metrics across four dimensions:
    1. Learning Metrics: Strategy performance and improvement tracking
    2. Performance Metrics: System execution speed and resource usage
    3. Quality Metrics: Validation and preservation success rates
    4. System Metrics: Error tracking and API usage

    Features:
    - Prometheus-compatible metric format
    - Time-series data storage
    - Automatic metric aggregation
    - Export to JSON and Prometheus text format
    - Rolling window statistics

    Example:
        >>> collector = MetricsCollector()
        >>> collector.record_iteration_success(sharpe_ratio=2.0, duration=120.5)
        >>> collector.record_champion_update(old_sharpe=1.8, new_sharpe=2.0)
        >>> metrics = collector.export_prometheus()
    """

    def __init__(self, history_window: int = 100):
        """Initialize metrics collector.

        Args:
            history_window: Number of recent values to keep in memory (default: 100)
        """
        self.history_window = history_window
        self.metrics: Dict[str, Metric] = {}
        self.start_time = time.time()

        # Initialize all metrics
        self._initialize_metrics()

        logger.info(f"MetricsCollector initialized with history_window={history_window}")

    def _initialize_metrics(self) -> None:
        """Initialize all metric definitions."""

        # ====================
        # Learning Metrics
        # ====================
        self._register_metric(
            "learning_iterations_total",
            MetricType.COUNTER,
            "Total number of iterations executed"
        )

        self._register_metric(
            "learning_iterations_successful",
            MetricType.COUNTER,
            "Number of successful iterations (passed validation and execution)"
        )

        self._register_metric(
            "learning_success_rate",
            MetricType.GAUGE,
            "Rolling success rate over recent iterations",
            unit="percentage"
        )

        self._register_metric(
            "learning_sharpe_ratio",
            MetricType.GAUGE,
            "Current iteration Sharpe ratio"
        )

        self._register_metric(
            "learning_sharpe_ratio_avg",
            MetricType.GAUGE,
            "Average Sharpe ratio over recent successful iterations"
        )

        self._register_metric(
            "learning_sharpe_ratio_best",
            MetricType.GAUGE,
            "Best Sharpe ratio achieved so far"
        )

        self._register_metric(
            "learning_champion_updates_total",
            MetricType.COUNTER,
            "Total number of champion strategy updates"
        )

        self._register_metric(
            "learning_champion_age_iterations",
            MetricType.GAUGE,
            "Number of iterations since last champion update"
        )

        self._register_metric(
            "learning_strategy_diversity",
            MetricType.GAUGE,
            "Strategy diversity score (unique templates in recent window)",
            unit="count"
        )

        # ====================
        # Performance Metrics
        # ====================
        self._register_metric(
            "performance_iteration_duration_seconds",
            MetricType.HISTOGRAM,
            "Time taken to complete one full iteration",
            unit="seconds"
        )

        self._register_metric(
            "performance_generation_duration_seconds",
            MetricType.HISTOGRAM,
            "Time taken for strategy generation",
            unit="seconds"
        )

        self._register_metric(
            "performance_validation_duration_seconds",
            MetricType.HISTOGRAM,
            "Time taken for code validation",
            unit="seconds"
        )

        self._register_metric(
            "performance_execution_duration_seconds",
            MetricType.HISTOGRAM,
            "Time taken for strategy execution",
            unit="seconds"
        )

        self._register_metric(
            "performance_metric_extraction_duration_seconds",
            MetricType.HISTOGRAM,
            "Time taken for metric extraction",
            unit="seconds"
        )

        self._register_metric(
            "performance_metric_extraction_method",
            MetricType.COUNTER,
            "Metric extraction method used (DIRECT, SIGNAL, DEFAULT)"
        )

        # ====================
        # Quality Metrics
        # ====================
        self._register_metric(
            "quality_validation_passed_total",
            MetricType.COUNTER,
            "Number of iterations that passed validation"
        )

        self._register_metric(
            "quality_validation_failed_total",
            MetricType.COUNTER,
            "Number of iterations that failed validation"
        )

        self._register_metric(
            "quality_validation_pass_rate",
            MetricType.GAUGE,
            "Rolling validation pass rate",
            unit="percentage"
        )

        self._register_metric(
            "quality_execution_success_total",
            MetricType.COUNTER,
            "Number of iterations with successful execution"
        )

        self._register_metric(
            "quality_execution_failed_total",
            MetricType.COUNTER,
            "Number of iterations with failed execution"
        )

        self._register_metric(
            "quality_preservation_validated_total",
            MetricType.COUNTER,
            "Number of iterations that passed preservation validation"
        )

        self._register_metric(
            "quality_preservation_failed_total",
            MetricType.COUNTER,
            "Number of iterations that failed preservation validation"
        )

        self._register_metric(
            "quality_suspicious_metrics_detected",
            MetricType.COUNTER,
            "Number of times suspicious metrics were detected"
        )

        # ====================
        # System Metrics
        # ====================
        self._register_metric(
            "system_api_calls_total",
            MetricType.COUNTER,
            "Total number of API calls made"
        )

        self._register_metric(
            "system_api_errors_total",
            MetricType.COUNTER,
            "Total number of API errors"
        )

        self._register_metric(
            "system_api_retries_total",
            MetricType.COUNTER,
            "Total number of API retries"
        )

        self._register_metric(
            "system_errors_total",
            MetricType.COUNTER,
            "Total number of system errors (by type)"
        )

        self._register_metric(
            "system_fallback_used_total",
            MetricType.COUNTER,
            "Number of times fallback strategy was used"
        )

        self._register_metric(
            "system_variance_alert_triggered",
            MetricType.COUNTER,
            "Number of times variance alert was triggered"
        )

        self._register_metric(
            "system_uptime_seconds",
            MetricType.GAUGE,
            "System uptime since metrics collector initialization",
            unit="seconds"
        )

        # ====================
        # Resource Monitoring Metrics (Task 5 - Resource Monitoring System)
        # ====================
        self._register_metric(
            "resource_memory_percent",
            MetricType.GAUGE,
            "System memory usage percentage",
            unit="percentage"
        )

        self._register_metric(
            "resource_memory_used_bytes",
            MetricType.GAUGE,
            "System memory used in bytes",
            unit="bytes"
        )

        self._register_metric(
            "resource_memory_total_bytes",
            MetricType.GAUGE,
            "Total system memory in bytes",
            unit="bytes"
        )

        self._register_metric(
            "resource_cpu_percent",
            MetricType.GAUGE,
            "System CPU usage percentage",
            unit="percentage"
        )

        self._register_metric(
            "resource_disk_percent",
            MetricType.GAUGE,
            "System disk usage percentage",
            unit="percentage"
        )

        self._register_metric(
            "resource_disk_used_bytes",
            MetricType.GAUGE,
            "System disk used in bytes",
            unit="bytes"
        )

        self._register_metric(
            "resource_disk_total_bytes",
            MetricType.GAUGE,
            "Total system disk in bytes",
            unit="bytes"
        )

        # ====================
        # Diversity Monitoring Metrics
        # ====================
        self._register_metric(
            "diversity_population_diversity",
            MetricType.GAUGE,
            "Population diversity score (0.0-1.0)",
            unit="score"
        )

        self._register_metric(
            "diversity_unique_count",
            MetricType.GAUGE,
            "Number of unique individuals in population",
            unit="count"
        )

        self._register_metric(
            "diversity_total_count",
            MetricType.GAUGE,
            "Total population size",
            unit="count"
        )

        self._register_metric(
            "diversity_collapse_detected",
            MetricType.GAUGE,
            "Whether diversity collapse is detected (1=yes, 0=no)",
            unit="boolean"
        )

        self._register_metric(
            "diversity_champion_staleness",
            MetricType.GAUGE,
            "Iterations since last champion update",
            unit="iterations"
        )

        # ====================
        # Container Monitoring Metrics
        # ====================
        self._register_metric(
            "container_active_count",
            MetricType.GAUGE,
            "Number of active containers",
            unit="count"
        )

        self._register_metric(
            "container_orphaned_count",
            MetricType.GAUGE,
            "Number of orphaned containers (exited but not cleaned up)",
            unit="count"
        )

        self._register_metric(
            "container_memory_usage_bytes",
            MetricType.GAUGE,
            "Container memory usage in bytes (per container)",
            unit="bytes"
        )

        self._register_metric(
            "container_memory_percent",
            MetricType.GAUGE,
            "Container memory usage percentage (per container)",
            unit="percentage"
        )

        self._register_metric(
            "container_cpu_percent",
            MetricType.GAUGE,
            "Container CPU usage percentage (per container)",
            unit="percentage"
        )

        self._register_metric(
            "container_created_total",
            MetricType.COUNTER,
            "Total number of containers created"
        )

        self._register_metric(
            "container_cleanup_success_total",
            MetricType.COUNTER,
            "Number of successful container cleanups"
        )

        self._register_metric(
            "container_cleanup_failed_total",
            MetricType.COUNTER,
            "Number of failed container cleanups"
        )

        # ====================
        # Alert Metrics
        # ====================
        self._register_metric(
            "alert_triggered_total",
            MetricType.COUNTER,
            "Total number of alerts triggered (by alert type)"
        )

        self._register_metric(
            "alert_active_count",
            MetricType.GAUGE,
            "Number of currently active alerts",
            unit="count"
        )

        # ====================
        # Exit Mutation Metrics (Task 8 - Exit Mutation Redesign)
        # ====================
        self._register_metric(
            "exit_mutations_total",
            MetricType.COUNTER,
            "Total number of exit parameter mutations performed"
        )

        self._register_metric(
            "exit_mutations_success",
            MetricType.COUNTER,
            "Number of successful exit parameter mutations"
        )

        self._register_metric(
            "exit_mutation_success_rate",
            MetricType.GAUGE,
            "Success rate of exit parameter mutations (0.0-1.0)",
            unit="percentage"
        )

        self._register_metric(
            "exit_mutation_duration_seconds",
            MetricType.HISTOGRAM,
            "Exit mutation latency distribution",
            unit="seconds"
        )

        # ====================
        # Validation Infrastructure Metrics (Task 6.5)
        # ====================
        self._register_metric(
            "validation_field_error_rate",
            MetricType.GAUGE,
            "Percentage of strategies with field errors",
            unit="percentage"
        )

        self._register_metric(
            "validation_llm_success_rate",
            MetricType.GAUGE,
            "Percentage of successful LLM validations",
            unit="percentage"
        )

        self._register_metric(
            "validation_total_latency_ms",
            MetricType.HISTOGRAM,
            "Total validation latency across all layers",
            unit="milliseconds"
        )

        self._register_metric(
            "validation_layer1_latency_ms",
            MetricType.HISTOGRAM,
            "Layer 1 (DataFieldManifest) validation latency",
            unit="milliseconds"
        )

        self._register_metric(
            "validation_layer2_latency_ms",
            MetricType.HISTOGRAM,
            "Layer 2 (FieldValidator) validation latency",
            unit="milliseconds"
        )

        self._register_metric(
            "validation_layer3_latency_ms",
            MetricType.HISTOGRAM,
            "Layer 3 (SchemaValidator) validation latency",
            unit="milliseconds"
        )

        self._register_metric(
            "validation_circuit_breaker_triggers",
            MetricType.COUNTER,
            "Total number of validation circuit breaker activations"
        )

        self._register_metric(
            "validation_error_signatures_unique",
            MetricType.GAUGE,
            "Number of unique error signatures tracked",
            unit="count"
        )

    def _register_metric(self, name: str, metric_type: MetricType, help_text: str, unit: str = "") -> None:
        """Register a new metric definition."""
        self.metrics[name] = Metric(
            name=name,
            metric_type=metric_type,
            help_text=help_text,
            unit=unit
        )

    # ====================
    # Learning Metrics Recording
    # ====================

    def record_iteration_start(self, iteration_num: int) -> None:
        """Record the start of a new iteration.

        Args:
            iteration_num: Current iteration number
        """
        self.metrics["learning_iterations_total"].add_value(iteration_num + 1)
        logger.debug(f"Recorded iteration start: {iteration_num}")

    def record_iteration_success(self, sharpe_ratio: float, duration: float) -> None:
        """Record a successful iteration completion.

        Args:
            sharpe_ratio: Sharpe ratio achieved
            duration: Total iteration duration in seconds
        """
        # Increment success counter
        current_successful = self.metrics["learning_iterations_successful"].get_latest() or 0
        self.metrics["learning_iterations_successful"].add_value(current_successful + 1)

        # Record Sharpe ratio
        self.metrics["learning_sharpe_ratio"].add_value(sharpe_ratio)

        # Update average Sharpe
        avg_sharpe = self.metrics["learning_sharpe_ratio"].get_average(window=20)
        self.metrics["learning_sharpe_ratio_avg"].add_value(avg_sharpe)

        # Update best Sharpe
        best_sharpe = self.metrics["learning_sharpe_ratio_best"].get_latest() or 0
        if sharpe_ratio > best_sharpe:
            self.metrics["learning_sharpe_ratio_best"].add_value(sharpe_ratio)

        # Update success rate
        total = self.metrics["learning_iterations_total"].get_latest() or 1
        successful = current_successful + 1
        success_rate = (successful / total) * 100
        self.metrics["learning_success_rate"].add_value(success_rate)

        # Record duration
        self.metrics["performance_iteration_duration_seconds"].add_value(duration)

        logger.info(f"Recorded successful iteration: sharpe={sharpe_ratio:.4f}, duration={duration:.2f}s")

    def record_champion_update(self, old_sharpe: float, new_sharpe: float, iteration_num: int) -> None:
        """Record a champion strategy update.

        Args:
            old_sharpe: Previous champion Sharpe ratio
            new_sharpe: New champion Sharpe ratio
            iteration_num: Iteration number of new champion
        """
        # Increment update counter
        current_updates = self.metrics["learning_champion_updates_total"].get_latest() or 0
        self.metrics["learning_champion_updates_total"].add_value(current_updates + 1)

        # Reset champion age
        self.metrics["learning_champion_age_iterations"].add_value(0)

        improvement = ((new_sharpe / old_sharpe) - 1) * 100 if old_sharpe > 0 else 0
        logger.info(f"Recorded champion update: {old_sharpe:.4f} -> {new_sharpe:.4f} (+{improvement:.1f}%)")

    def record_champion_age_increment(self) -> None:
        """Increment champion age by 1 iteration (called when champion not updated)."""
        current_age = self.metrics["learning_champion_age_iterations"].get_latest() or 0
        self.metrics["learning_champion_age_iterations"].add_value(current_age + 1)

    def record_strategy_diversity(self, unique_templates: int) -> None:
        """Record strategy diversity metric.

        Args:
            unique_templates: Number of unique templates used in recent window
        """
        self.metrics["learning_strategy_diversity"].add_value(unique_templates)

    # ====================
    # Performance Metrics Recording
    # ====================

    def record_generation_time(self, duration: float) -> None:
        """Record strategy generation time.

        Args:
            duration: Generation time in seconds
        """
        self.metrics["performance_generation_duration_seconds"].add_value(duration)

    def record_validation_time(self, duration: float) -> None:
        """Record validation time.

        Args:
            duration: Validation time in seconds
        """
        self.metrics["performance_validation_duration_seconds"].add_value(duration)

    def record_execution_time(self, duration: float) -> None:
        """Record execution time.

        Args:
            duration: Execution time in seconds
        """
        self.metrics["performance_execution_duration_seconds"].add_value(duration)

    def record_metric_extraction_time(self, duration: float, method: str) -> None:
        """Record metric extraction time and method.

        Args:
            duration: Extraction time in seconds
            method: Extraction method used (DIRECT, SIGNAL, DEFAULT)
        """
        self.metrics["performance_metric_extraction_duration_seconds"].add_value(duration)

        # Count method usage
        current_count = self.metrics["performance_metric_extraction_method"].get_latest() or 0
        self.metrics["performance_metric_extraction_method"].add_value(
            current_count + 1,
            labels={"method": method}
        )

    # ====================
    # Quality Metrics Recording
    # ====================

    def record_validation_result(self, passed: bool) -> None:
        """Record validation result.

        Args:
            passed: Whether validation passed
        """
        if passed:
            current = self.metrics["quality_validation_passed_total"].get_latest() or 0
            self.metrics["quality_validation_passed_total"].add_value(current + 1)
        else:
            current = self.metrics["quality_validation_failed_total"].get_latest() or 0
            self.metrics["quality_validation_failed_total"].add_value(current + 1)

        # Update pass rate
        passed_count = self.metrics["quality_validation_passed_total"].get_latest() or 0
        failed_count = self.metrics["quality_validation_failed_total"].get_latest() or 0
        total = passed_count + failed_count

        if total > 0:
            pass_rate = (passed_count / total) * 100
            self.metrics["quality_validation_pass_rate"].add_value(pass_rate)

    def record_execution_result(self, success: bool) -> None:
        """Record execution result.

        Args:
            success: Whether execution succeeded
        """
        if success:
            current = self.metrics["quality_execution_success_total"].get_latest() or 0
            self.metrics["quality_execution_success_total"].add_value(current + 1)
        else:
            current = self.metrics["quality_execution_failed_total"].get_latest() or 0
            self.metrics["quality_execution_failed_total"].add_value(current + 1)

    def record_preservation_result(self, preserved: bool) -> None:
        """Record preservation validation result.

        Args:
            preserved: Whether preservation validation passed
        """
        if preserved:
            current = self.metrics["quality_preservation_validated_total"].get_latest() or 0
            self.metrics["quality_preservation_validated_total"].add_value(current + 1)
        else:
            current = self.metrics["quality_preservation_failed_total"].get_latest() or 0
            self.metrics["quality_preservation_failed_total"].add_value(current + 1)

    def record_suspicious_metrics(self) -> None:
        """Record detection of suspicious metrics."""
        current = self.metrics["quality_suspicious_metrics_detected"].get_latest() or 0
        self.metrics["quality_suspicious_metrics_detected"].add_value(current + 1)

    # ====================
    # System Metrics Recording
    # ====================

    def record_api_call(self, success: bool, retries: int = 0) -> None:
        """Record an API call.

        Args:
            success: Whether the API call succeeded
            retries: Number of retries attempted
        """
        # Increment total calls
        current_calls = self.metrics["system_api_calls_total"].get_latest() or 0
        self.metrics["system_api_calls_total"].add_value(current_calls + 1)

        # Record errors
        if not success:
            current_errors = self.metrics["system_api_errors_total"].get_latest() or 0
            self.metrics["system_api_errors_total"].add_value(current_errors + 1)

        # Record retries
        if retries > 0:
            current_retries = self.metrics["system_api_retries_total"].get_latest() or 0
            self.metrics["system_api_retries_total"].add_value(current_retries + retries)

    def record_error(self, error_type: str) -> None:
        """Record a system error.

        Args:
            error_type: Type of error (e.g., 'validation', 'execution', 'api')
        """
        current = self.metrics["system_errors_total"].get_latest() or 0
        self.metrics["system_errors_total"].add_value(
            current + 1,
            labels={"error_type": error_type}
        )

    def record_fallback_usage(self) -> None:
        """Record usage of fallback strategy."""
        current = self.metrics["system_fallback_used_total"].get_latest() or 0
        self.metrics["system_fallback_used_total"].add_value(current + 1)

    def record_variance_alert(self) -> None:
        """Record variance alert trigger."""
        current = self.metrics["system_variance_alert_triggered"].get_latest() or 0
        self.metrics["system_variance_alert_triggered"].add_value(current + 1)

    def update_uptime(self) -> None:
        """Update system uptime metric."""
        uptime = time.time() - self.start_time
        self.metrics["system_uptime_seconds"].add_value(uptime)

    # ====================
    # Resource Monitoring Recording (Task 5)
    # ====================

    def record_resource_memory(self, used_bytes: float, total_bytes: float, percent: float) -> None:
        """Record system memory usage metrics.

        Args:
            used_bytes: Memory used in bytes
            total_bytes: Total memory in bytes
            percent: Memory usage percentage (0-100)
        """
        self.metrics["resource_memory_used_bytes"].add_value(used_bytes)
        self.metrics["resource_memory_total_bytes"].add_value(total_bytes)
        self.metrics["resource_memory_percent"].add_value(percent)

    def record_resource_cpu(self, percent: float) -> None:
        """Record system CPU usage.

        Args:
            percent: CPU usage percentage (0-100)
        """
        self.metrics["resource_cpu_percent"].add_value(percent)

    def record_resource_disk(self, used_bytes: float, total_bytes: float, percent: float) -> None:
        """Record system disk usage metrics.

        Args:
            used_bytes: Disk used in bytes
            total_bytes: Total disk in bytes
            percent: Disk usage percentage (0-100)
        """
        self.metrics["resource_disk_used_bytes"].add_value(used_bytes)
        self.metrics["resource_disk_total_bytes"].add_value(total_bytes)
        self.metrics["resource_disk_percent"].add_value(percent)

    # ====================
    # Diversity Monitoring Recording
    # ====================

    def record_diversity_metrics(
        self,
        diversity: float,
        unique_count: int,
        total_count: int,
        staleness: int,
        collapse_detected: bool = False
    ) -> None:
        """Record population diversity metrics.

        Args:
            diversity: Diversity score (0.0-1.0)
            unique_count: Number of unique individuals
            total_count: Total population size
            staleness: Iterations since last champion update
            collapse_detected: Whether diversity collapse is detected
        """
        self.metrics["diversity_population_diversity"].add_value(diversity)
        self.metrics["diversity_unique_count"].add_value(unique_count)
        self.metrics["diversity_total_count"].add_value(total_count)
        self.metrics["diversity_champion_staleness"].add_value(staleness)
        self.metrics["diversity_collapse_detected"].add_value(1.0 if collapse_detected else 0.0)

    # ====================
    # Container Monitoring Recording
    # ====================

    def record_container_counts(self, active: int, orphaned: int) -> None:
        """Record container counts.

        Args:
            active: Number of active running containers
            orphaned: Number of orphaned (exited) containers
        """
        self.metrics["container_active_count"].add_value(active)
        self.metrics["container_orphaned_count"].add_value(orphaned)

    def record_container_memory(
        self,
        container_id: str,
        memory_bytes: float,
        limit_bytes: float,
        percent: float
    ) -> None:
        """Record container memory usage.

        Args:
            container_id: Container identifier
            memory_bytes: Memory usage in bytes
            limit_bytes: Memory limit in bytes
            percent: Memory usage percentage
        """
        self.metrics["container_memory_usage_bytes"].add_value(
            memory_bytes,
            labels={"container_id": container_id[:12]}
        )
        self.metrics["container_memory_percent"].add_value(
            percent,
            labels={"container_id": container_id[:12]}
        )

    def record_container_cpu(self, container_id: str, cpu_percent: float) -> None:
        """Record container CPU usage.

        Args:
            container_id: Container identifier
            cpu_percent: CPU usage percentage
        """
        self.metrics["container_cpu_percent"].add_value(
            cpu_percent,
            labels={"container_id": container_id[:12]}
        )

    def record_container_created(self) -> None:
        """Increment container created counter."""
        current = self.metrics["container_created_total"].get_latest() or 0
        self.metrics["container_created_total"].add_value(current + 1)

    def record_container_cleanup(self, success: bool) -> None:
        """Record container cleanup result.

        Args:
            success: Whether cleanup was successful
        """
        if success:
            current = self.metrics["container_cleanup_success_total"].get_latest() or 0
            self.metrics["container_cleanup_success_total"].add_value(current + 1)
        else:
            current = self.metrics["container_cleanup_failed_total"].get_latest() or 0
            self.metrics["container_cleanup_failed_total"].add_value(current + 1)

    def record_orphaned_containers(self, count: int) -> None:
        """Record orphaned container count.

        Args:
            count: Number of orphaned containers detected
        """
        self.metrics["container_orphaned_count"].add_value(count)

    # ====================
    # Alert Recording
    # ====================

    def record_alert_triggered(self, alert_type: str) -> None:
        """Record alert triggered event.

        Args:
            alert_type: Type of alert (e.g., 'high_memory', 'diversity_collapse')
        """
        current = self.metrics["alert_triggered_total"].get_latest() or 0
        self.metrics["alert_triggered_total"].add_value(
            current + 1,
            labels={"alert_type": alert_type}
        )

    def record_active_alerts(self, count: int) -> None:
        """Record number of currently active alerts.

        Args:
            count: Number of active alerts
        """
        self.metrics["alert_active_count"].add_value(count)

    # ====================
    # Exit Mutation Metrics Recording (Task 8)
    # ====================

    def record_exit_mutation(self, success: bool, duration: Optional[float] = None) -> None:
        """Record an exit parameter mutation attempt.

        Args:
            success: Whether the mutation succeeded
            duration: Optional mutation duration in seconds
        """
        # Increment total counter
        current = self.metrics["exit_mutations_total"].get_latest() or 0
        self.metrics["exit_mutations_total"].add_value(current + 1)

        # Increment success counter if succeeded
        if success:
            current_success = self.metrics["exit_mutations_success"].get_latest() or 0
            self.metrics["exit_mutations_success"].add_value(current_success + 1)

        # Update success rate (based on recent history)
        # Track successes and failures separately for accurate rate calculation
        if not hasattr(self, '_exit_mutation_successes'):
            self._exit_mutation_successes = 0
            self._exit_mutation_failures = 0

        if success:
            self._exit_mutation_successes += 1
        else:
            self._exit_mutation_failures += 1

        total_exit_mutations = self._exit_mutation_successes + self._exit_mutation_failures
        if total_exit_mutations > 0:
            success_rate = self._exit_mutation_successes / total_exit_mutations
            self.metrics["exit_mutation_success_rate"].add_value(success_rate)

        # Record duration if provided
        if duration is not None:
            self.metrics["exit_mutation_duration_seconds"].add_value(duration)

    # ====================
    # Validation Infrastructure Metrics Recording (Task 6.5)
    # ====================

    def record_validation_field_errors(self, total_strategies: int, strategies_with_errors: int) -> None:
        """Record field error rate for validation monitoring.

        Args:
            total_strategies: Total number of strategies validated
            strategies_with_errors: Number of strategies that had field errors
        """
        if total_strategies > 0:
            error_rate = (strategies_with_errors / total_strategies) * 100
            self.metrics["validation_field_error_rate"].add_value(error_rate)

    def record_llm_validation_success(self, total_attempts: int, successful_validations: int) -> None:
        """Record LLM validation success rate.

        Args:
            total_attempts: Total number of LLM generation attempts
            successful_validations: Number of attempts that passed validation
        """
        if total_attempts > 0:
            success_rate = (successful_validations / total_attempts) * 100
            self.metrics["validation_llm_success_rate"].add_value(success_rate)

    def record_validation_latency(
        self,
        total_ms: float,
        layer1_ms: float = 0.0,
        layer2_ms: float = 0.0,
        layer3_ms: float = 0.0
    ) -> None:
        """Record validation latency metrics.

        Args:
            total_ms: Total validation latency in milliseconds
            layer1_ms: Layer 1 (DataFieldManifest) latency in milliseconds
            layer2_ms: Layer 2 (FieldValidator) latency in milliseconds
            layer3_ms: Layer 3 (SchemaValidator) latency in milliseconds
        """
        self.metrics["validation_total_latency_ms"].add_value(total_ms)
        if layer1_ms > 0:
            self.metrics["validation_layer1_latency_ms"].add_value(layer1_ms)
        if layer2_ms > 0:
            self.metrics["validation_layer2_latency_ms"].add_value(layer2_ms)
        if layer3_ms > 0:
            self.metrics["validation_layer3_latency_ms"].add_value(layer3_ms)

    def record_circuit_breaker_trigger(self) -> None:
        """Record validation circuit breaker activation."""
        current = self.metrics["validation_circuit_breaker_triggers"].get_latest() or 0
        self.metrics["validation_circuit_breaker_triggers"].add_value(current + 1)

    def record_unique_error_signatures(self, count: int) -> None:
        """Record number of unique error signatures.

        Args:
            count: Number of unique error signatures currently tracked
        """
        self.metrics["validation_error_signatures_unique"].add_value(count)

    def get_validation_latency_p99(self) -> float:
        """Calculate P99 validation latency.

        Returns:
            P99 latency in milliseconds, or 0.0 if insufficient data
        """
        latency_metric = self.metrics["validation_total_latency_ms"]
        if not latency_metric.values or len(latency_metric.values) < 2:
            return 0.0

        import numpy as np
        latencies = [v.value for v in latency_metric.values]
        return np.percentile(latencies, 99)

    def export_cloudwatch(self) -> str:
        """Export metrics in CloudWatch JSON format.

        Returns:
            CloudWatch-compatible JSON string

        Example output:
            {
                "Namespace": "StrategyValidation",
                "MetricData": [
                    {
                        "MetricName": "FieldErrorRate",
                        "Value": 5.0,
                        "Unit": "Percent",
                        "Timestamp": "2025-01-18T12:00:00Z"
                    }
                ]
            }
        """
        from datetime import datetime

        metric_data = []

        # Map our metrics to CloudWatch format
        cloudwatch_mappings = {
            "validation_field_error_rate": ("FieldErrorRate", "Percent"),
            "validation_llm_success_rate": ("LLMSuccessRate", "Percent"),
            "validation_total_latency_ms": ("TotalLatency", "Milliseconds"),
            "validation_layer1_latency_ms": ("Layer1Latency", "Milliseconds"),
            "validation_layer2_latency_ms": ("Layer2Latency", "Milliseconds"),
            "validation_layer3_latency_ms": ("Layer3Latency", "Milliseconds"),
            "validation_circuit_breaker_triggers": ("CircuitBreakerTriggers", "Count"),
            "validation_error_signatures_unique": ("UniqueErrorSignatures", "Count"),
        }

        for metric_name, metric in self.metrics.items():
            if metric_name not in cloudwatch_mappings or not metric.values:
                continue

            cw_name, cw_unit = cloudwatch_mappings[metric_name]
            latest = metric.values[-1]

            metric_datum = {
                "MetricName": cw_name,
                "Value": latest.value,
                "Unit": cw_unit,
                "Timestamp": datetime.fromtimestamp(latest.timestamp).isoformat() + "Z"
            }

            # Add dimensions if labels present
            if latest.labels:
                metric_datum["Dimensions"] = [
                    {"Name": k, "Value": v}
                    for k, v in latest.labels.items()
                ]

            metric_data.append(metric_datum)

        cloudwatch_output = {
            "Namespace": "StrategyValidation",
            "MetricData": metric_data
        }

        import json
        return json.dumps(cloudwatch_output, indent=2)

    # ====================
    # Metric Export
    # ====================

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics string

        Example output:
            # HELP learning_iterations_total Total number of iterations executed
            # TYPE learning_iterations_total counter
            learning_iterations_total 10

            # HELP learning_sharpe_ratio Current iteration Sharpe ratio
            # TYPE learning_sharpe_ratio gauge
            learning_sharpe_ratio 2.0
        """
        lines = []

        for metric_name, metric in self.metrics.items():
            # Skip metrics with no values
            if not metric.values:
                continue

            # Add HELP line
            lines.append(f"# HELP {metric_name} {metric.help_text}")

            # Add TYPE line
            lines.append(f"# TYPE {metric_name} {metric.metric_type.value}")

            # Add metric value(s)
            latest = metric.values[-1]

            if latest.labels:
                # Format labels
                label_str = ",".join(f'{k}="{v}"' for k, v in latest.labels.items())
                lines.append(f"{metric_name}{{{label_str}}} {latest.value} {int(latest.timestamp * 1000)}")
            else:
                lines.append(f"{metric_name} {latest.value} {int(latest.timestamp * 1000)}")

            lines.append("")  # Blank line between metrics

        return "\n".join(lines)

    def export_json(self, include_history: bool = False) -> str:
        """Export metrics as JSON.

        Args:
            include_history: If True, include full time-series history.
                           If False, only include latest values.

        Returns:
            JSON string of metrics
        """
        data = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self.start_time,
            "metrics": {}
        }

        for metric_name, metric in self.metrics.items():
            if not metric.values:
                continue

            metric_data = {
                "type": metric.metric_type.value,
                "help": metric.help_text,
                "unit": metric.unit,
                "latest": metric.get_latest()
            }

            if include_history:
                metric_data["history"] = [v.to_dict() for v in metric.values[-self.history_window:]]

            data["metrics"][metric_name] = metric_data

        return json.dumps(data, indent=2)

    def get_summary(self) -> Dict[str, Any]:
        """Get high-level summary of current metrics.

        Returns:
            Dictionary with key metric summaries
        """
        return {
            "learning": {
                "total_iterations": self.metrics["learning_iterations_total"].get_latest(),
                "successful_iterations": self.metrics["learning_iterations_successful"].get_latest(),
                "success_rate": self.metrics["learning_success_rate"].get_latest(),
                "current_sharpe": self.metrics["learning_sharpe_ratio"].get_latest(),
                "average_sharpe": self.metrics["learning_sharpe_ratio_avg"].get_latest(),
                "best_sharpe": self.metrics["learning_sharpe_ratio_best"].get_latest(),
                "champion_updates": self.metrics["learning_champion_updates_total"].get_latest(),
                "champion_age": self.metrics["learning_champion_age_iterations"].get_latest(),
            },
            "performance": {
                "avg_iteration_duration": self.metrics["performance_iteration_duration_seconds"].get_average(window=10),
                "avg_generation_time": self.metrics["performance_generation_duration_seconds"].get_average(window=10),
                "avg_execution_time": self.metrics["performance_execution_duration_seconds"].get_average(window=10),
                "avg_extraction_time": self.metrics["performance_metric_extraction_duration_seconds"].get_average(window=10),
            },
            "quality": {
                "validation_pass_rate": self.metrics["quality_validation_pass_rate"].get_latest(),
                "validation_passed": self.metrics["quality_validation_passed_total"].get_latest(),
                "validation_failed": self.metrics["quality_validation_failed_total"].get_latest(),
                "execution_success": self.metrics["quality_execution_success_total"].get_latest(),
                "execution_failed": self.metrics["quality_execution_failed_total"].get_latest(),
                "preservation_validated": self.metrics["quality_preservation_validated_total"].get_latest(),
                "preservation_failed": self.metrics["quality_preservation_failed_total"].get_latest(),
            },
            "system": {
                "api_calls": self.metrics["system_api_calls_total"].get_latest(),
                "api_errors": self.metrics["system_api_errors_total"].get_latest(),
                "api_retries": self.metrics["system_api_retries_total"].get_latest(),
                "fallback_used": self.metrics["system_fallback_used_total"].get_latest(),
                "variance_alerts": self.metrics["system_variance_alert_triggered"].get_latest(),
                "uptime_seconds": time.time() - self.start_time,
            },
            "resources": {
                "memory_percent": self.metrics["resource_memory_percent"].get_latest(),
                "cpu_percent": self.metrics["resource_cpu_percent"].get_latest(),
                "disk_percent": self.metrics["resource_disk_percent"].get_latest(),
            },
            "diversity": {
                "population_diversity": self.metrics["diversity_population_diversity"].get_latest(),
                "unique_count": self.metrics["diversity_unique_count"].get_latest(),
                "total_count": self.metrics["diversity_total_count"].get_latest(),
                "champion_staleness": self.metrics["diversity_champion_staleness"].get_latest(),
                "collapse_detected": self.metrics["diversity_collapse_detected"].get_latest(),
            },
            "containers": {
                "active_count": self.metrics["container_active_count"].get_latest(),
                "orphaned_count": self.metrics["container_orphaned_count"].get_latest(),
                "created_total": self.metrics["container_created_total"].get_latest(),
                "cleanup_success": self.metrics["container_cleanup_success_total"].get_latest(),
                "cleanup_failed": self.metrics["container_cleanup_failed_total"].get_latest(),
            },
            "alerts": {
                "triggered_total": self.metrics["alert_triggered_total"].get_latest(),
                "active_count": self.metrics["alert_active_count"].get_latest(),
            },
            "exit_mutations": {
                "total": self.metrics["exit_mutations_total"].get_latest(),
                "successes": self.metrics["exit_mutations_success"].get_latest(),
                "success_rate": self.metrics["exit_mutation_success_rate"].get_latest(),
                "avg_duration": self.metrics["exit_mutation_duration_seconds"].get_average(window=20),
                "internal_successes": getattr(self, '_exit_mutation_successes', 0),
                "internal_failures": getattr(self, '_exit_mutation_failures', 0),
            }
        }

    def get_exit_mutation_statistics(self) -> Dict[str, Any]:
        """Get detailed exit mutation statistics.

        Returns:
            Dictionary with comprehensive exit mutation metrics including:
                - total: Total mutations attempted
                - successes: Total successful mutations
                - failures: Total failed mutations
                - success_rate: Success percentage (0.0-1.0)
                - avg_duration: Average mutation duration in seconds
                - recent_avg_duration: Average duration over last 10 mutations
        """
        total = self.metrics["exit_mutations_total"].get_latest() or 0
        successes = self.metrics["exit_mutations_success"].get_latest() or 0
        failures = total - successes
        success_rate = self.metrics["exit_mutation_success_rate"].get_latest() or 0.0

        # Get duration statistics
        avg_duration = self.metrics["exit_mutation_duration_seconds"].get_average()
        recent_avg_duration = self.metrics["exit_mutation_duration_seconds"].get_average(window=10)

        # Get all duration values for more detailed stats
        duration_metric = self.metrics["exit_mutation_duration_seconds"]
        duration_values = [v.value for v in duration_metric.values] if duration_metric.values else []

        # Calculate min/max/percentiles if we have data
        duration_stats = {}
        if duration_values:
            import numpy as np
            duration_stats = {
                "min": min(duration_values),
                "max": max(duration_values),
                "p50": np.percentile(duration_values, 50),
                "p95": np.percentile(duration_values, 95),
                "p99": np.percentile(duration_values, 99),
            }

        return {
            "total": int(total),
            "successes": int(successes),
            "failures": int(failures),
            "success_rate": success_rate,
            "success_percentage": success_rate * 100,
            "avg_duration_seconds": avg_duration,
            "recent_avg_duration_seconds": recent_avg_duration,
            "duration_statistics": duration_stats,
            "total_duration_samples": len(duration_values)
        }

    def reset(self) -> None:
        """Reset all metrics (useful for testing)."""
        for metric in self.metrics.values():
            metric.values.clear()
        self.start_time = time.time()
        logger.info("All metrics reset")
