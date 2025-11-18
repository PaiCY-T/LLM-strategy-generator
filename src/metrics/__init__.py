"""
Metrics collection module for validation rollout tracking.

This module provides:
- RolloutSampler: Deterministic sampling for gradual rollout
- MetricsCollector: Baseline metrics tracking for validation effectiveness
"""

from src.metrics.collector import RolloutSampler, MetricsCollector

__all__ = ["RolloutSampler", "MetricsCollector"]
