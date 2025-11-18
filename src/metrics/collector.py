"""
Rollout sampling and metrics collection for Layer 1 validation deployment.

This module implements:
1. RolloutSampler: Deterministic 10% sampling based on strategy hash
2. MetricsCollector: Real-time metrics tracking for validation effectiveness

Design Principles:
- Deterministic: Same strategy hash always returns same rollout decision
- Performance: Hash-based sampling is O(1) with <1μs overhead
- Observable: Metrics exportable to Prometheus/CloudWatch format

Usage:
    from src.metrics.collector import RolloutSampler, MetricsCollector

    # Initialize sampler
    sampler = RolloutSampler(rollout_percentage=10)

    # Check if strategy should get validation
    if sampler.is_enabled(strategy_hash):
        # Apply Layer 1 validation
        pass

    # Collect metrics
    collector = MetricsCollector()
    collector.record_validation_event(
        strategy_hash="strategy_123",
        validation_enabled=True,
        field_errors=0,
        llm_success=True,
        validation_latency_ms=0.5
    )

    # Export metrics
    metrics = collector.export_metrics()
"""

import hashlib
from collections import deque
from datetime import datetime
from typing import Dict, Any


class RolloutSampler:
    """
    Deterministic sampling for gradual rollout of Layer 1 validation.

    Uses hash-based sampling to ensure:
    - Same strategy hash always gets same result (deterministic)
    - Approximately N% of strategies are selected (statistical)
    - Zero state required (stateless, no DB lookups)

    Algorithm:
        hash(strategy_id) % 100 < rollout_percentage

    Performance: O(1) with <1μs overhead per check
    """

    def __init__(self, rollout_percentage: int = 10):
        """
        Initialize RolloutSampler.

        Args:
            rollout_percentage: Percentage of traffic to enable (0-100)

        Raises:
            ValueError: If percentage not in range [0, 100]
        """
        if not 0 <= rollout_percentage <= 100:
            raise ValueError(
                f"rollout_percentage must be 0-100, got {rollout_percentage}"
            )

        self.rollout_percentage = rollout_percentage

    def is_enabled(self, strategy_hash: str) -> bool:
        """
        Check if validation should be enabled for this strategy.

        Uses deterministic hash-based sampling:
        1. Hash the strategy identifier
        2. Take modulo 100 to get range [0, 99]
        3. Compare to rollout_percentage

        Args:
            strategy_hash: Unique identifier for strategy (e.g., "strategy_123")

        Returns:
            True if validation should be enabled, False otherwise

        Examples:
            >>> sampler = RolloutSampler(rollout_percentage=10)
            >>> # Same hash always returns same result
            >>> result1 = sampler.is_enabled("strategy_abc")
            >>> result2 = sampler.is_enabled("strategy_abc")
            >>> assert result1 == result2
        """
        # Hash strategy identifier to get deterministic number
        hash_bytes = hashlib.md5(strategy_hash.encode()).digest()

        # Take first byte and compute modulo 100
        hash_value = hash_bytes[0] % 100

        # Enable if hash falls within rollout percentage
        return hash_value < self.rollout_percentage


class MetricsCollector:
    """
    Real-time metrics collector for validation rollout effectiveness.

    Tracks:
    - field_error_rate: Percentage of strategies with field errors
    - llm_success_rate: Percentage of successful LLM generations
    - validation_latency_avg_ms: Average validation time
    - total_requests: Total number of validation attempts
    - validation_enabled_count: Number of requests with validation enabled

    Metrics are exportable to Prometheus/CloudWatch format.
    """

    def __init__(self):
        """Initialize MetricsCollector with empty state."""
        # Raw event counters
        self._total_requests = 0
        self._validation_enabled_count = 0
        self._field_error_count = 0
        self._llm_success_count = 0
        self._validation_latency_sum_ms = 0.0

        # For debugging/troubleshooting - bounded to last 1000 events
        self._events = deque(maxlen=1000)

    def record_validation_event(
        self,
        strategy_hash: str,
        validation_enabled: bool,
        field_errors: int,
        llm_success: bool,
        validation_latency_ms: float
    ) -> None:
        """
        Record a single validation event for metrics tracking.

        Args:
            strategy_hash: Unique strategy identifier
            validation_enabled: Whether Layer 1 validation was applied
            field_errors: Number of field errors detected (0 if validation disabled)
            llm_success: Whether LLM generation succeeded
            validation_latency_ms: Time spent on validation in milliseconds

        Note:
            Only validation_enabled=True events contribute to error/success rates.
            All events contribute to total_requests counter.
        """
        self._total_requests += 1

        if validation_enabled:
            self._validation_enabled_count += 1

            # Track field errors (only count if validation was enabled)
            if field_errors > 0:
                self._field_error_count += 1

            # Track LLM success
            if llm_success:
                self._llm_success_count += 1

            # Track validation latency
            self._validation_latency_sum_ms += validation_latency_ms

        # Store event for debugging
        self._events.append({
            "strategy_hash": strategy_hash,
            "validation_enabled": validation_enabled,
            "field_errors": field_errors,
            "llm_success": llm_success,
            "validation_latency_ms": validation_latency_ms,
            "timestamp": datetime.now().isoformat()
        })

    def get_metrics(self) -> Dict[str, float]:
        """
        Get current metrics as a dictionary.

        Returns:
            Dictionary with metric names and values:
            - field_error_rate: 0.0-1.0 (percentage with field errors)
            - llm_success_rate: 0.0-1.0 (percentage with successful generation)
            - validation_latency_avg_ms: Average latency in milliseconds
            - total_requests: Total number of requests
            - validation_enabled_count: Number of requests with validation

        Note:
            Returns 0.0 for rates when no validation events recorded.
        """
        # Avoid division by zero
        if self._validation_enabled_count == 0:
            return {
                "field_error_rate": 0.0,
                "llm_success_rate": 0.0,
                "validation_latency_avg_ms": 0.0,
                "total_requests": self._total_requests,
                "validation_enabled_count": 0
            }

        # Calculate rates based on validation-enabled requests only
        field_error_rate = self._field_error_count / self._validation_enabled_count
        llm_success_rate = self._llm_success_count / self._validation_enabled_count
        avg_latency = self._validation_latency_sum_ms / self._validation_enabled_count

        return {
            "field_error_rate": field_error_rate,
            "llm_success_rate": llm_success_rate,
            "validation_latency_avg_ms": avg_latency,
            "total_requests": self._total_requests,
            "validation_enabled_count": self._validation_enabled_count
        }

    def export_metrics(self) -> Dict[str, Any]:
        """
        Export metrics in format suitable for monitoring systems.

        Returns:
            Dictionary with timestamp and metrics:
            {
                "timestamp": "2025-11-18T12:00:00",
                "metrics": {
                    "field_error_rate": 0.0,
                    "llm_success_rate": 1.0,
                    "validation_latency_avg_ms": 0.5,
                    ...
                }
            }

        This format is compatible with:
        - Prometheus (convert to gauge metrics)
        - CloudWatch (put_metric_data)
        - Custom monitoring dashboards
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.get_metrics()
        }

    def reset(self) -> None:
        """
        Reset all metrics to zero.

        Used for testing or when starting a new monitoring period.
        """
        self._total_requests = 0
        self._validation_enabled_count = 0
        self._field_error_count = 0
        self._llm_success_count = 0
        self._validation_latency_sum_ms = 0.0
        self._events.clear()
