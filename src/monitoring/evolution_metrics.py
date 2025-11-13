"""Evolution Metrics Tracker for Multi-Template Evolution System.

This module provides real-time monitoring and metrics collection for the
Template Evolution System (Phase 6, Task 42).

Tracks:
- Per-generation performance metrics (fitness, diversity, convergence)
- Template distribution evolution over time
- Mutation and crossover event logging
- System health and alerting

Requirements:
- Task 42: Basic runtime monitoring for sandbox deployment
- Real-time tracking for 1-week sandbox evolution (Task 43)

Integration:
- Works with PopulationManager, EvolutionMonitor, GeneticOperators
- Compatible with existing MetricsCollector for system-wide metrics
- Exports to Prometheus and JSON formats
"""

import time
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GenerationMetrics:
    """Metrics for a single evolution generation."""
    generation: int
    timestamp: float

    # Population metrics
    population_size: int
    avg_fitness: float
    best_fitness: float
    worst_fitness: float
    median_fitness: float

    # Diversity metrics
    param_diversity: float
    template_diversity: float
    unified_diversity: float

    # Template distribution
    template_distribution: Dict[str, int]  # {template_name: count}
    template_percentages: Dict[str, float]  # {template_name: percentage}

    # Best performers per template
    best_fitness_per_template: Dict[str, float]

    # Champion tracking
    champion_template: str
    champion_fitness: float
    champion_updated: bool

    # Event counts
    mutation_count: int = 0
    crossover_count: int = 0
    template_mutation_count: int = 0

    # Performance timing
    generation_duration: float = 0.0  # seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class EvolutionAlert:
    """Alert for evolution anomalies."""
    timestamp: float
    generation: int
    alert_type: str  # 'fitness_drop', 'diversity_collapse', 'no_improvement', 'system_error'
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)


class EvolutionMetricsTracker:
    """Real-time metrics tracking for multi-template evolution.

    Features:
    - Per-generation metric collection
    - Template distribution tracking over time
    - Mutation/crossover event logging
    - Automatic anomaly detection and alerting
    - Prometheus and JSON export
    - Rolling window statistics

    Example:
        >>> tracker = EvolutionMetricsTracker()
        >>> tracker.record_generation(
        ...     generation=0,
        ...     population=initial_population,
        ...     diversity_metrics={'param': 0.8, 'template': 0.5, 'unified': 0.7},
        ...     champion=best_individual,
        ...     events={'mutations': 5, 'crossovers': 20, 'template_mutations': 2}
        ... )
        >>> tracker.export_summary()
    """

    def __init__(
        self,
        history_window: int = 100,
        alert_thresholds: Optional[Dict[str, float]] = None
    ):
        """Initialize evolution metrics tracker.

        Args:
            history_window: Number of recent generations to keep in memory
            alert_thresholds: Custom thresholds for alerting (optional)
        """
        self.history_window = history_window
        self.generation_history: deque[GenerationMetrics] = deque(maxlen=history_window)
        self.alerts: List[EvolutionAlert] = []

        # Alert thresholds (can be customized)
        self.alert_thresholds = alert_thresholds or {
            'fitness_drop_percentage': 20.0,  # Alert if fitness drops >20%
            'diversity_floor': 0.1,  # Alert if diversity <0.1
            'no_improvement_generations': 20,  # Alert if no improvement in 20 gens
            'template_collapse_threshold': 0.9,  # Alert if one template >90%
        }

        # Tracking state
        self.start_time = time.time()
        self.last_champion_update_generation = 0
        self.best_fitness_ever = 0.0

        # Event counters
        self.total_mutations = 0
        self.total_crossovers = 0
        self.total_template_mutations = 0

        logger.info(f"EvolutionMetricsTracker initialized with history_window={history_window}")

    def record_generation(
        self,
        generation: int,
        population: List[Any],  # List[Individual]
        diversity_metrics: Dict[str, float],
        champion: Any,  # Individual
        champion_updated: bool,
        events: Dict[str, int],
        duration: float = 0.0
    ) -> GenerationMetrics:
        """Record metrics for a completed generation.

        Args:
            generation: Generation number
            population: List of Individual objects
            diversity_metrics: Dict with keys: 'param', 'template', 'unified'
            champion: Current champion Individual
            champion_updated: Whether champion was updated this generation
            events: Dict with keys: 'mutations', 'crossovers', 'template_mutations'
            duration: Generation execution time in seconds

        Returns:
            GenerationMetrics object for this generation
        """
        # Calculate fitness statistics
        fitnesses = [ind.fitness for ind in population if ind.fitness is not None]
        if not fitnesses:
            logger.warning(f"Generation {generation}: No valid fitness values")
            fitnesses = [0.0]

        avg_fitness = sum(fitnesses) / len(fitnesses)
        best_fitness = max(fitnesses)
        worst_fitness = min(fitnesses)
        median_fitness = sorted(fitnesses)[len(fitnesses) // 2]

        # Calculate template distribution
        template_counts = defaultdict(int)
        for ind in population:
            template_counts[ind.template_type] += 1

        template_percentages = {
            template: (count / len(population)) * 100
            for template, count in template_counts.items()
        }

        # Best fitness per template
        best_per_template = {}
        for template in template_counts.keys():
            template_fitnesses = [
                ind.fitness for ind in population
                if ind.template_type == template and ind.fitness is not None
            ]
            if template_fitnesses:
                best_per_template[template] = max(template_fitnesses)

        # Create generation metrics
        metrics = GenerationMetrics(
            generation=generation,
            timestamp=time.time(),
            population_size=len(population),
            avg_fitness=avg_fitness,
            best_fitness=best_fitness,
            worst_fitness=worst_fitness,
            median_fitness=median_fitness,
            param_diversity=diversity_metrics.get('param', 0.0),
            template_diversity=diversity_metrics.get('template', 0.0),
            unified_diversity=diversity_metrics.get('unified', 0.0),
            template_distribution=dict(template_counts),
            template_percentages=template_percentages,
            best_fitness_per_template=best_per_template,
            champion_template=champion.template_type,
            champion_fitness=champion.fitness or 0.0,
            champion_updated=champion_updated,
            mutation_count=events.get('mutations', 0),
            crossover_count=events.get('crossovers', 0),
            template_mutation_count=events.get('template_mutations', 0),
            generation_duration=duration
        )

        # Store in history
        self.generation_history.append(metrics)

        # Update event counters
        self.total_mutations += metrics.mutation_count
        self.total_crossovers += metrics.crossover_count
        self.total_template_mutations += metrics.template_mutation_count

        # Update champion tracking
        if champion_updated:
            self.last_champion_update_generation = generation

        if metrics.best_fitness > self.best_fitness_ever:
            self.best_fitness_ever = metrics.best_fitness

        # Check for anomalies and generate alerts
        self._check_anomalies(metrics)

        # Log summary
        logger.info(
            f"Gen {generation}: avg_fitness={avg_fitness:.4f}, "
            f"best={best_fitness:.4f}, diversity={metrics.unified_diversity:.4f}, "
            f"champion={champion.template_type}"
        )

        return metrics

    def _check_anomalies(self, metrics: GenerationMetrics) -> None:
        """Check for anomalies and generate alerts.

        Args:
            metrics: Current generation metrics
        """
        generation = metrics.generation

        # Check for fitness drop
        if len(self.generation_history) >= 2:
            prev_metrics = self.generation_history[-2]
            fitness_change = ((metrics.avg_fitness - prev_metrics.avg_fitness) /
                            prev_metrics.avg_fitness * 100) if prev_metrics.avg_fitness > 0 else 0

            if fitness_change < -self.alert_thresholds['fitness_drop_percentage']:
                self._create_alert(
                    generation=generation,
                    alert_type='fitness_drop',
                    severity='medium',
                    message=f"Average fitness dropped {abs(fitness_change):.1f}%",
                    details={'prev_fitness': prev_metrics.avg_fitness, 'current_fitness': metrics.avg_fitness}
                )

        # Check for diversity collapse
        if metrics.unified_diversity < self.alert_thresholds['diversity_floor']:
            self._create_alert(
                generation=generation,
                alert_type='diversity_collapse',
                severity='high',
                message=f"Diversity collapsed to {metrics.unified_diversity:.4f}",
                details={'diversity': metrics.unified_diversity, 'threshold': self.alert_thresholds['diversity_floor']}
            )

        # Check for no improvement
        gens_since_improvement = generation - self.last_champion_update_generation
        if gens_since_improvement >= self.alert_thresholds['no_improvement_generations']:
            self._create_alert(
                generation=generation,
                alert_type='no_improvement',
                severity='low',
                message=f"No champion update in {gens_since_improvement} generations",
                details={'last_update_generation': self.last_champion_update_generation}
            )

        # Check for template collapse (one template dominates)
        for template, percentage in metrics.template_percentages.items():
            if percentage > self.alert_thresholds['template_collapse_threshold'] * 100:
                self._create_alert(
                    generation=generation,
                    alert_type='template_collapse',
                    severity='medium',
                    message=f"Template '{template}' dominates at {percentage:.1f}%",
                    details={'template': template, 'percentage': percentage}
                )

    def _create_alert(
        self,
        generation: int,
        alert_type: str,
        severity: str,
        message: str,
        details: Dict[str, Any]
    ) -> None:
        """Create and store an alert.

        Args:
            generation: Generation number
            alert_type: Type of alert
            severity: Severity level
            message: Alert message
            details: Additional details
        """
        alert = EvolutionAlert(
            timestamp=time.time(),
            generation=generation,
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details
        )

        self.alerts.append(alert)

        # Log based on severity
        log_msg = f"ALERT [{severity.upper()}] Gen {generation}: {message}"
        if severity == 'critical':
            logger.error(log_msg)
        elif severity == 'high':
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    def get_summary(self) -> Dict[str, Any]:
        """Get high-level summary of evolution progress.

        Returns:
            Dictionary with evolution summary statistics
        """
        if not self.generation_history:
            return {"error": "No generation data recorded"}

        latest = self.generation_history[-1]
        first = self.generation_history[0]

        # Calculate improvement
        fitness_improvement = ((latest.avg_fitness - first.avg_fitness) /
                              first.avg_fitness * 100) if first.avg_fitness > 0 else 0

        # Recent alerts (last 10)
        recent_alerts = [alert.to_dict() for alert in self.alerts[-10:]]

        return {
            "evolution_progress": {
                "generations_completed": latest.generation + 1,
                "runtime_hours": (time.time() - self.start_time) / 3600,
                "current_generation": latest.generation,
            },
            "performance": {
                "current_avg_fitness": latest.avg_fitness,
                "current_best_fitness": latest.best_fitness,
                "best_fitness_ever": self.best_fitness_ever,
                "fitness_improvement_percent": fitness_improvement,
                "last_champion_update_gen": self.last_champion_update_generation,
                "generations_since_improvement": latest.generation - self.last_champion_update_generation,
            },
            "diversity": {
                "current_unified": latest.unified_diversity,
                "current_param": latest.param_diversity,
                "current_template": latest.template_diversity,
            },
            "templates": {
                "distribution": latest.template_distribution,
                "percentages": latest.template_percentages,
                "champion_template": latest.champion_template,
                "best_per_template": latest.best_fitness_per_template,
            },
            "events": {
                "total_mutations": self.total_mutations,
                "total_crossovers": self.total_crossovers,
                "total_template_mutations": self.total_template_mutations,
                "avg_mutations_per_gen": self.total_mutations / (latest.generation + 1),
                "template_mutation_rate": (self.total_template_mutations / self.total_mutations * 100)
                    if self.total_mutations > 0 else 0,
            },
            "alerts": {
                "total_count": len(self.alerts),
                "recent": recent_alerts,
            }
        }

    def export_json(self, filepath: Optional[Path] = None, include_full_history: bool = False) -> str:
        """Export metrics to JSON format.

        Args:
            filepath: Optional file path to save JSON (if None, returns string)
            include_full_history: If True, include all generation history

        Returns:
            JSON string
        """
        data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "evolution_start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "runtime_hours": (time.time() - self.start_time) / 3600,
            },
            "summary": self.get_summary(),
        }

        if include_full_history:
            data["generation_history"] = [
                metrics.to_dict() for metrics in self.generation_history
            ]
            data["alert_history"] = [
                alert.to_dict() for alert in self.alerts
            ]

        json_str = json.dumps(data, indent=2)

        if filepath:
            filepath = Path(filepath)
            filepath.write_text(json_str)
            logger.info(f"Metrics exported to {filepath}")

        return json_str

    def export_prometheus(self) -> str:
        """Export current metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics string
        """
        if not self.generation_history:
            return "# No metrics available\n"

        latest = self.generation_history[-1]
        lines = []

        # Helper to add metric
        def add_metric(name: str, value: float, help_text: str, metric_type: str = "gauge"):
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} {metric_type}")
            lines.append(f"{name} {value}")
            lines.append("")

        # Evolution progress
        add_metric("evolution_generation", latest.generation, "Current generation number", "counter")
        add_metric("evolution_runtime_hours", (time.time() - self.start_time) / 3600,
                  "Evolution runtime in hours")

        # Fitness metrics
        add_metric("evolution_avg_fitness", latest.avg_fitness, "Current average fitness")
        add_metric("evolution_best_fitness", latest.best_fitness, "Current best fitness")
        add_metric("evolution_best_fitness_ever", self.best_fitness_ever, "Best fitness ever achieved")
        add_metric("evolution_champion_fitness", latest.champion_fitness, "Current champion fitness")

        # Diversity metrics
        add_metric("evolution_diversity_unified", latest.unified_diversity, "Unified diversity score")
        add_metric("evolution_diversity_param", latest.param_diversity, "Parameter diversity score")
        add_metric("evolution_diversity_template", latest.template_diversity, "Template diversity score")

        # Event counts
        add_metric("evolution_mutations_total", self.total_mutations, "Total mutations", "counter")
        add_metric("evolution_crossovers_total", self.total_crossovers, "Total crossovers", "counter")
        add_metric("evolution_template_mutations_total", self.total_template_mutations,
                  "Total template mutations", "counter")

        # Alert count
        add_metric("evolution_alerts_total", len(self.alerts), "Total alerts generated", "counter")

        # Template distribution (as separate labeled metrics)
        for template, count in latest.template_distribution.items():
            lines.append(f"# HELP evolution_template_count Population count per template")
            lines.append(f"# TYPE evolution_template_count gauge")
            lines.append(f'evolution_template_count{{template="{template}"}} {count}')
            lines.append("")

        return "\n".join(lines)

    def get_convergence_analysis(self) -> Dict[str, Any]:
        """Analyze convergence trends over evolution history.

        Returns:
            Dictionary with convergence analysis
        """
        if len(self.generation_history) < 5:
            return {"error": "Insufficient data for convergence analysis (need ≥5 generations)"}

        # Analyze fitness trend
        recent_gens = list(self.generation_history)[-20:]  # Last 20 generations
        fitness_trend = [g.avg_fitness for g in recent_gens]

        # Simple linear regression for trend
        n = len(fitness_trend)
        x_mean = (n - 1) / 2
        y_mean = sum(fitness_trend) / n

        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(fitness_trend))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0

        # Analyze diversity trend
        diversity_trend = [g.unified_diversity for g in recent_gens]
        avg_diversity = sum(diversity_trend) / len(diversity_trend)

        # Template distribution evolution
        initial_dist = self.generation_history[0].template_distribution
        final_dist = self.generation_history[-1].template_distribution

        return {
            "fitness_trend": {
                "slope": slope,
                "direction": "improving" if slope > 0.001 else "plateaued" if slope > -0.001 else "declining",
                "recent_avg": sum(fitness_trend) / len(fitness_trend),
                "volatility": max(fitness_trend) - min(fitness_trend),
            },
            "diversity_trend": {
                "current": diversity_trend[-1],
                "average_recent": avg_diversity,
                "stable": max(diversity_trend) - min(diversity_trend) < 0.1,
            },
            "template_evolution": {
                "initial_distribution": initial_dist,
                "final_distribution": final_dist,
                "dominant_template": max(final_dist.items(), key=lambda x: x[1])[0],
            },
            "convergence_status": self._assess_convergence(slope, avg_diversity),
        }

    def _assess_convergence(self, fitness_slope: float, avg_diversity: float) -> str:
        """Assess overall convergence status.

        Args:
            fitness_slope: Fitness trend slope
            avg_diversity: Average recent diversity

        Returns:
            Convergence status string
        """
        if fitness_slope > 0.01 and avg_diversity > 0.3:
            return "healthy_evolution"  # Improving and diverse
        elif fitness_slope > 0.001 and avg_diversity > 0.2:
            return "slow_improvement"  # Gradual improvement
        elif abs(fitness_slope) < 0.001 and avg_diversity > 0.2:
            return "plateau_diverse"  # Stable but diverse
        elif abs(fitness_slope) < 0.001 and avg_diversity < 0.2:
            return "converged"  # Converged to solution
        elif fitness_slope < -0.001:
            return "degrading"  # Performance declining
        else:
            return "uncertain"  # Unclear status
