"""Monitoring module for learning system convergence tracking.

This module provides monitoring components for tracking learning system stability,
convergence, and performance metrics over iteration cycles.

Components:
- VarianceMonitor: Legacy variance tracking for learning system
- EvolutionMetricsTracker: Real-time evolution metrics tracking (Phase 6)
- AlertManager: Anomaly detection and alerting system (Phase 6)
- DiversityMonitor: Population diversity and champion staleness tracking (Resource Monitoring System)
- ContainerMonitor: Docker container resource tracking and orphaned container cleanup (Resource Monitoring System)
"""

from .variance_monitor import VarianceMonitor
from .evolution_metrics import (
    EvolutionMetricsTracker,
    GenerationMetrics,
    EvolutionAlert
)
from .alerts import (
    AlertManager,
    Alert,
    AlertSeverity,
    AlertChannel,
    create_fitness_drop_alert,
    create_diversity_collapse_alert,
    create_no_improvement_alert,
    create_system_error_alert
)
from .diversity_monitor import DiversityMonitor
from .container_monitor import ContainerMonitor, ContainerStats

__all__ = [
    "VarianceMonitor",
    "EvolutionMetricsTracker",
    "GenerationMetrics",
    "EvolutionAlert",
    "AlertManager",
    "Alert",
    "AlertSeverity",
    "AlertChannel",
    "create_fitness_drop_alert",
    "create_diversity_collapse_alert",
    "create_no_improvement_alert",
    "create_system_error_alert",
    "DiversityMonitor",
    "ContainerMonitor",
    "ContainerStats"
]
