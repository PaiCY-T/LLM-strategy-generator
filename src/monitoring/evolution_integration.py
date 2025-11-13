"""Evolution Monitoring Integration for Multi-Template Evolution.

This module provides integration wrapper for EvolutionMetricsTracker with
PopulationManager and EvolutionMonitor for seamless runtime monitoring.

Usage Example:
    >>> from src.monitoring.evolution_integration import MonitoredEvolution
    >>>
    >>> # Initialize monitored evolution
    >>> evolution = MonitoredEvolution(
    ...     population_size=100,
    ...     alert_file="alerts.json",
    ...     metrics_export_interval=10
    ... )
    >>>
    >>> # Run monitored evolution
    >>> results = evolution.run_evolution(
    ...     generations=50,
    ...     template_distribution={'Momentum': 0.25, 'Turtle': 0.25, 'Factor': 0.25, 'Mastiff': 0.25}
    ... )
    >>>
    >>> # Export metrics
    >>> evolution.export_prometheus("metrics.txt")
    >>> evolution.export_json("metrics.json")
"""

import time
import json
import logging
import random
import copy
import math
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import asdict

from src.population.population_manager import PopulationManager
from src.population.evolution_monitor import EvolutionMonitor
from src.population.genetic_operators import GeneticOperators
from src.population.fitness_evaluator import FitnessEvaluator
from src.monitoring.evolution_metrics import EvolutionMetricsTracker, GenerationMetrics
from src.monitoring.alerts import (
    AlertManager,
    AlertSeverity,
    create_fitness_drop_alert,
    create_diversity_collapse_alert,
    create_no_improvement_alert,
    create_system_error_alert
)

logger = logging.getLogger(__name__)


class MonitoredEvolution:
    """Wrapper for evolution with integrated runtime monitoring.

    Combines PopulationManager, EvolutionMonitor, GeneticOperators, and
    EvolutionMetricsTracker for comprehensive monitored evolution.

    Features:
    - Automatic per-generation metrics collection
    - Real-time anomaly detection and alerting
    - Prometheus and JSON metrics export
    - Template distribution tracking
    - Convergence analysis
    - System health monitoring

    Example:
        >>> evolution = MonitoredEvolution(population_size=100)
        >>> results = evolution.run_evolution(generations=50)
        >>> evolution.export_prometheus("metrics.txt")
    """

    def __init__(
        self,
        population_size: int = 50,
        elite_size: int = 3,
        tournament_size: int = 2,
        diversity_threshold: float = 0.5,
        convergence_window: int = 10,
        base_mutation_rate: float = 0.20,
        template_mutation_rate: float = 0.10,
        alert_file: Optional[str] = None,
        metrics_export_interval: int = 10,
        alert_thresholds: Optional[Dict[str, float]] = None
    ):
        """Initialize monitored evolution.

        Args:
            population_size: Number of individuals in population
            elite_size: Number of elites to preserve
            tournament_size: Tournament size for selection
            diversity_threshold: Minimum diversity to avoid convergence
            convergence_window: Generations to check for convergence
            base_mutation_rate: Base probability of mutation per individual
            template_mutation_rate: Probability of template mutation
            alert_file: Path to alert log file (optional)
            metrics_export_interval: Export metrics every N generations
            alert_thresholds: Custom alert thresholds (optional)
        """
        # Core evolution components
        self.population_manager = PopulationManager(
            population_size=population_size,
            elite_size=elite_size,
            tournament_size=tournament_size,
            diversity_threshold=diversity_threshold,
            convergence_window=convergence_window
        )

        self.evolution_monitor = EvolutionMonitor()

        self.genetic_operators = GeneticOperators(
            base_mutation_rate=base_mutation_rate,
            template_mutation_rate=template_mutation_rate
        )

        self.fitness_evaluator = FitnessEvaluator()

        # Monitoring components
        self.metrics_tracker = EvolutionMetricsTracker(
            history_window=100,
            alert_thresholds=alert_thresholds
        )

        self.alert_manager = AlertManager(
            alert_file=Path(alert_file) if alert_file else None,
            min_severity=AlertSeverity.LOW
        )

        # Configuration
        self.metrics_export_interval = metrics_export_interval

        # Integrate alert manager with metrics tracker
        self.metrics_tracker.alert_callback = self.alert_manager.send_alert

        logger.info(f"MonitoredEvolution initialized: pop_size={population_size}, "
                   f"monitoring_interval={metrics_export_interval}")

    def run_evolution(
        self,
        generations: int,
        template_distribution: Optional[Dict[str, float]] = None,
        fitness_function: Optional[Callable] = None,
        early_stopping: bool = True,
        export_final_metrics: bool = True
    ) -> Dict[str, Any]:
        """Run monitored multi-template evolution.

        Args:
            generations: Number of generations to evolve
            template_distribution: Template distribution configuration
                None = equal distribution (25% each)
                Dict = weighted distribution
            fitness_function: Custom fitness evaluation function (optional)
                Signature: fitness_function(individual) -> float
            early_stopping: Stop if converged before max generations
            export_final_metrics: Export metrics at end of evolution

        Returns:
            Dict containing:
                - champion: Best individual found
                - final_population: Final population state
                - metrics_history: All generation metrics
                - convergence_analysis: Convergence analysis results
                - alert_summary: Alert summary statistics
        """
        logger.info(f"Starting monitored evolution: {generations} generations")

        # Initialize population
        try:
            population = self.population_manager.initialize_population(
                template_distribution=template_distribution
            )
            logger.info(f"Population initialized: {len(population)} individuals")
        except Exception as e:
            create_system_error_alert(
                self.alert_manager,
                generation=0,
                error_type="InitializationError",
                error_message=str(e)
            )
            raise

        # Evaluate initial population
        if fitness_function:
            for ind in population:
                ind.fitness = fitness_function(ind)
        else:
            self.fitness_evaluator.evaluate_population(population)

        # Track champion
        champion = max(population, key=lambda x: x.fitness if x.fitness is not None else float('-inf'))

        # Evolution loop
        for generation in range(generations):
            gen_start_time = time.time()

            # Track events for this generation
            events = {
                'mutations': 0,
                'crossovers': 0,
                'template_mutations': 0
            }

            # Selection and genetic operations
            offspring = []
            while len(offspring) < self.population_manager.population_size - self.population_manager.elite_size:
                # Tournament selection
                parent1 = self.population_manager.select_parent(population)
                parent2 = self.population_manager.select_parent(population)

                # Crossover (always performed in this simplified version)
                child1, child2 = self.genetic_operators.crossover(parent1, parent2, generation)
                events['crossovers'] += 1
                # Track template mutations (children with different template than parents)
                if child1.template_type != parent1.template_type or child1.template_type != parent2.template_type:
                    events['template_mutations'] += 1
                offspring.extend([child1, child2])

                # Mutation (probabilistic on each child)
                for child in offspring[-2:]:
                    if random.random() < self.genetic_operators.current_mutation_rate:
                        mutated = self.genetic_operators.mutate(child, generation)
                        # Replace child with mutated version
                        offspring[-2 if child == offspring[-2] else -1] = mutated
                        events['mutations'] += 1

            # Trim to exact size
            offspring = offspring[:self.population_manager.population_size - self.population_manager.elite_size]

            # Elitism
            elites = sorted(population, key=lambda x: x.fitness if x.fitness is not None else float('-inf'))[-self.population_manager.elite_size:]

            # Create next generation
            population = elites + offspring

            # Evaluate fitness
            if fitness_function:
                for ind in offspring:
                    ind.fitness = fitness_function(ind)
            else:
                self.fitness_evaluator.evaluate_population(offspring)

            # Update champion
            current_best = max(population, key=lambda x: x.fitness if x.fitness is not None else float('-inf'))
            champion_updated = False
            if current_best.fitness > champion.fitness:
                champion = copy.deepcopy(current_best)
                champion_updated = True

            # Calculate diversity metrics
            param_diversity = self.population_manager.calculate_diversity(population)

            # Calculate template diversity using Shannon entropy
            template_counts = Counter(ind.template_type for ind in population)
            total = len(population)
            entropy = 0.0
            for count in template_counts.values():
                if count > 0:
                    prob = count / total
                    entropy -= prob * math.log2(prob)
            max_entropy = math.log2(len(template_counts)) if len(template_counts) > 1 else 0.0
            template_diversity = entropy / max_entropy if max_entropy > 0 else 0.0

            # Calculate unified diversity
            unified_diversity = self.evolution_monitor.calculate_diversity(population, param_diversity)

            # Build diversity metrics dictionary
            diversity_metrics = {
                'param_diversity': param_diversity,
                'template_diversity': template_diversity,
                'unified_diversity': unified_diversity
            }

            # Record generation metrics
            gen_duration = time.time() - gen_start_time
            metrics = self.metrics_tracker.record_generation(
                generation=generation,
                population=population,
                diversity_metrics=diversity_metrics,
                champion=champion,
                champion_updated=champion_updated,
                events=events,
                duration=gen_duration
            )

            # Update evolution monitor
            cache_stats = {'hit_rate': 0.0, 'cache_size': 0}  # Placeholder for now
            self.evolution_monitor.record_generation(
                generation_num=generation,
                population=population,
                diversity=unified_diversity,
                cache_stats=cache_stats
            )

            # Periodic metrics export
            if (generation + 1) % self.metrics_export_interval == 0:
                logger.info(
                    f"Gen {generation}: "
                    f"avg_fitness={metrics.avg_fitness:.4f}, "
                    f"best={metrics.best_fitness:.4f}, "
                    f"diversity={metrics.unified_diversity:.4f}, "
                    f"champion_template={metrics.champion_template}"
                )

            # Check convergence
            if early_stopping and self.population_manager.has_converged():
                logger.info(f"Evolution converged at generation {generation}")
                break

        # Final metrics export
        if export_final_metrics:
            logger.info("Exporting final metrics...")
            convergence_analysis = self.metrics_tracker.get_convergence_analysis()
            alert_summary = self.alert_manager.get_alert_summary()

            logger.info(f"Evolution complete: {len(self.metrics_tracker.generation_history)} generations")
            logger.info(f"Champion: template={champion.template_type}, fitness={champion.fitness:.4f}")
            logger.info(f"Total alerts: {alert_summary['total_alerts']}")

        return {
            'champion': champion,
            'final_population': population,
            'metrics_history': list(self.metrics_tracker.generation_history),
            'convergence_analysis': convergence_analysis if export_final_metrics else None,
            'alert_summary': alert_summary if export_final_metrics else None
        }

    def export_prometheus(self, output_file: str) -> None:
        """Export current metrics in Prometheus text format.

        Args:
            output_file: Path to output file
        """
        metrics_text = self.metrics_tracker.export_prometheus()
        Path(output_file).write_text(metrics_text)
        logger.info(f"Prometheus metrics exported to {output_file}")

    def export_json(self, output_file: str) -> None:
        """Export metrics history as JSON.

        Args:
            output_file: Path to output JSON file
        """
        metrics_data = {
            'generation_history': [
                {
                    **asdict(m),
                    'timestamp': m.timestamp,
                    'datetime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(m.timestamp))
                }
                for m in self.metrics_tracker.generation_history
            ],
            'convergence_analysis': self.metrics_tracker.get_convergence_analysis(),
            'alert_summary': self.alert_manager.get_alert_summary()
        }

        Path(output_file).write_text(json.dumps(metrics_data, indent=2))
        logger.info(f"JSON metrics exported to {output_file}")

    def get_recent_metrics(self, count: int = 10) -> List[GenerationMetrics]:
        """Get recent generation metrics.

        Args:
            count: Number of recent generations to retrieve

        Returns:
            List of recent GenerationMetrics
        """
        return list(self.metrics_tracker.generation_history)[-count:]

    def get_template_evolution(self) -> Dict[str, Any]:
        """Get template distribution evolution over time.

        Returns:
            Dict with template distribution history and trends
        """
        return self.evolution_monitor.get_template_distribution_history()


# Convenience function for quick monitored evolution
def run_monitored_evolution(
    generations: int = 50,
    population_size: int = 50,
    template_distribution: Optional[Dict[str, float]] = None,
    fitness_function: Optional[Callable] = None,
    alert_file: Optional[str] = "alerts.json",
    metrics_file: Optional[str] = "metrics.json"
) -> Dict[str, Any]:
    """Run monitored evolution with default settings.

    Convenience function for quick setup and execution.

    Args:
        generations: Number of generations
        population_size: Population size
        template_distribution: Template distribution config
        fitness_function: Custom fitness function (optional)
        alert_file: Alert log file path
        metrics_file: Metrics export file path

    Returns:
        Dict with evolution results and metrics
    """
    evolution = MonitoredEvolution(
        population_size=population_size,
        alert_file=alert_file
    )

    results = evolution.run_evolution(
        generations=generations,
        template_distribution=template_distribution,
        fitness_function=fitness_function
    )

    if metrics_file:
        evolution.export_json(metrics_file)

    return results
