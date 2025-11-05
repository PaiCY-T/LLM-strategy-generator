"""Unit tests for EvolutionMetricsTracker.

Tests real-time metrics tracking, anomaly detection, and export functionality
for multi-template evolution monitoring (Phase 6, Task 42).
"""

import pytest
import time
import json
from collections import defaultdict
from src.monitoring.evolution_metrics import (
    EvolutionMetricsTracker,
    GenerationMetrics,
    EvolutionAlert
)
from src.population.individual import Individual


class MockIndividual:
    """Mock individual for testing."""
    def __init__(self, fitness, template_type):
        self.fitness = fitness
        self.template_type = template_type
        self.parameters = {'param1': 1.0}


@pytest.fixture
def tracker():
    """Create metrics tracker with custom thresholds."""
    return EvolutionMetricsTracker(
        history_window=100,
        alert_thresholds={
            'fitness_drop_percentage': 20.0,
            'diversity_floor': 0.1,
            'no_improvement_generations': 20,
            'template_collapse_threshold': 0.9
        }
    )


@pytest.fixture
def sample_population():
    """Create sample population for testing."""
    return [
        MockIndividual(fitness=1.5, template_type='Momentum'),
        MockIndividual(fitness=1.3, template_type='Momentum'),
        MockIndividual(fitness=1.8, template_type='Turtle'),
        MockIndividual(fitness=1.2, template_type='Turtle'),
        MockIndividual(fitness=2.0, template_type='Factor'),
        MockIndividual(fitness=1.1, template_type='Factor'),
        MockIndividual(fitness=1.6, template_type='Mastiff'),
        MockIndividual(fitness=1.4, template_type='Mastiff'),
    ]


@pytest.fixture
def sample_diversity():
    """Sample diversity metrics."""
    return {
        'param': 0.85,  # Implementation expects 'param' not 'param_diversity'
        'template': 0.90,  # Implementation expects 'template' not 'template_diversity'
        'unified': 0.875  # Implementation expects 'unified' not 'unified_diversity'
    }


class TestGenerationMetricsRecording:
    """Test generation metrics recording functionality."""

    def test_record_first_generation(self, tracker, sample_population, sample_diversity):
        """Test recording first generation metrics."""
        champion = max(sample_population, key=lambda x: x.fitness)
        events = {'mutations': 5, 'crossovers': 3, 'template_mutations': 1}  # Implementation expects these keys

        metrics = tracker.record_generation(
            generation=0,
            population=sample_population,
            diversity_metrics=sample_diversity,
            champion=champion,
            champion_updated=True,
            events=events,
            duration=1.5
        )

        assert metrics.generation == 0
        assert metrics.population_size == 8
        assert metrics.avg_fitness == pytest.approx(1.4875, abs=0.01)
        assert metrics.best_fitness == 2.0
        assert metrics.worst_fitness == 1.1
        assert metrics.median_fitness == pytest.approx(1.5, abs=0.01)  # Median of [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0] is 1.5
        assert metrics.param_diversity == 0.85
        assert metrics.template_diversity == 0.90
        assert metrics.unified_diversity == 0.875
        assert metrics.champion_template == 'Factor'
        assert metrics.champion_fitness == 2.0
        assert metrics.champion_updated is True
        assert metrics.mutation_count == 5
        assert metrics.crossover_count == 3
        assert metrics.template_mutation_count == 1
        assert metrics.generation_duration == 1.5

    def test_template_distribution_tracking(self, tracker, sample_population, sample_diversity):
        """Test template distribution is correctly tracked."""
        champion = max(sample_population, key=lambda x: x.fitness)
        events = {'mutations': 0, 'crossovers': 0, 'template_mutations': 0}

        metrics = tracker.record_generation(
            generation=0,
            population=sample_population,
            diversity_metrics=sample_diversity,
            champion=champion,
            champion_updated=True,
            events=events
        )

        # Check template counts
        assert metrics.template_distribution['Momentum'] == 2
        assert metrics.template_distribution['Turtle'] == 2
        assert metrics.template_distribution['Factor'] == 2
        assert metrics.template_distribution['Mastiff'] == 2

        # Check percentages
        assert metrics.template_percentages['Momentum'] == 25.0
        assert metrics.template_percentages['Turtle'] == 25.0
        assert metrics.template_percentages['Factor'] == 25.0
        assert metrics.template_percentages['Mastiff'] == 25.0

    def test_best_fitness_per_template(self, tracker, sample_population, sample_diversity):
        """Test best fitness per template tracking."""
        champion = max(sample_population, key=lambda x: x.fitness)
        events = {'mutations': 0, 'crossovers': 0, 'template_mutations': 0}

        metrics = tracker.record_generation(
            generation=0,
            population=sample_population,
            diversity_metrics=sample_diversity,
            champion=champion,
            champion_updated=True,
            events=events
        )

        assert metrics.best_fitness_per_template['Momentum'] == 1.5
        assert metrics.best_fitness_per_template['Turtle'] == 1.8
        assert metrics.best_fitness_per_template['Factor'] == 2.0
        assert metrics.best_fitness_per_template['Mastiff'] == 1.6

    def test_history_window_limit(self, tracker, sample_population, sample_diversity):
        """Test history window limiting."""
        champion = max(sample_population, key=lambda x: x.fitness)
        events = {'mutations': 0, 'crossovers': 0, 'template_mutations': 0}

        # Record 150 generations (window is 100)
        for gen in range(150):
            tracker.record_generation(
                generation=gen,
                population=sample_population,
                diversity_metrics=sample_diversity,
                champion=champion,
                champion_updated=False,
                events=events
            )

        # Should only keep last 100
        assert len(tracker.generation_history) == 100
        assert tracker.generation_history[0].generation == 50
        assert tracker.generation_history[-1].generation == 149


class TestAnomalyDetection:
    """Test anomaly detection and alerting."""

    def test_fitness_drop_alert(self, tracker, sample_population, sample_diversity):
        """Test alert on significant fitness drop."""
        champion = max(sample_population, key=lambda x: x.fitness)
        events = {'mutations': 0, 'crossovers': 0, 'template_mutations': 0}

        # Record generation 0
        tracker.record_generation(
            generation=0,
            population=sample_population,
            diversity_metrics=sample_diversity,
            champion=champion,
            champion_updated=True,
            events=events
        )

        # Create population with 30% fitness drop
        low_fitness_pop = [MockIndividual(fitness=1.0, template_type='Momentum') for _ in range(8)]

        # Record generation 1 with fitness drop
        tracker.record_generation(
            generation=1,
            population=low_fitness_pop,
            diversity_metrics=sample_diversity,
            champion=champion,
            champion_updated=False,
            events=events
        )

        # Should have fitness drop alert
        fitness_drop_alerts = [a for a in tracker.alerts if a.alert_type == 'fitness_drop']
        assert len(fitness_drop_alerts) > 0
        assert fitness_drop_alerts[0].generation == 1

    def test_diversity_collapse_alert(self, tracker, sample_population):
        """Test alert on diversity collapse."""
        champion = max(sample_population, key=lambda x: x.fitness)
        events = {'mutations': 0, 'crossovers': 0, 'template_mutations': 0}

        # Low diversity metrics
        low_diversity = {
            'param_diversity': 0.05,
            'template_diversity': 0.05,
            'unified_diversity': 0.05
        }

        tracker.record_generation(
            generation=0,
            population=sample_population,
            diversity_metrics=low_diversity,
            champion=champion,
            champion_updated=True,
            events=events
        )

        # Should have diversity collapse alert
        diversity_alerts = [a for a in tracker.alerts if a.alert_type == 'diversity_collapse']
        assert len(diversity_alerts) > 0

    def test_no_improvement_alert(self, tracker, sample_population, sample_diversity):
        """Test alert on prolonged no improvement."""
        champion = max(sample_population, key=lambda x: x.fitness)
        events = {'mutations': 0, 'crossovers': 0, 'template_mutations': 0}

        # Record 25 generations without improvement (threshold is 20)
        for gen in range(25):
            tracker.record_generation(
                generation=gen,
                population=sample_population,
                diversity_metrics=sample_diversity,
                champion=champion,
                champion_updated=False,  # No improvement
                events=events
            )

        # Should have no improvement alert
        no_improvement_alerts = [a for a in tracker.alerts if a.alert_type == 'no_improvement']
        assert len(no_improvement_alerts) > 0

    def test_template_dominance_tracked(self, tracker, sample_diversity):
        """Test template dominance is tracked in metrics."""
        # Create population with 95% Mastiff dominance
        dominant_pop = (
            [MockIndividual(fitness=1.5, template_type='Mastiff') for _ in range(19)] +
            [MockIndividual(fitness=1.5, template_type='Momentum')]
        )

        champion = max(dominant_pop, key=lambda x: x.fitness)
        events = {'mutations': 0, 'crossovers': 0, 'template_mutations': 0}

        metrics = tracker.record_generation(
            generation=0,
            population=dominant_pop,
            diversity_metrics=sample_diversity,
            champion=champion,
            champion_updated=True,
            events=events
        )

        # Check template distribution shows dominance
        assert metrics.template_distribution['Mastiff'] == 19
        assert metrics.template_distribution['Momentum'] == 1
        assert metrics.template_percentages['Mastiff'] == 95.0
        assert metrics.template_percentages['Momentum'] == 5.0


class TestMetricsExport:
    """Test metrics export functionality."""

    def test_prometheus_export(self, tracker, sample_population, sample_diversity):
        """Test Prometheus format export."""
        champion = max(sample_population, key=lambda x: x.fitness)
        events = {'mutations': 5, 'crossovers': 3, 'template_mutations': 1}

        tracker.record_generation(
            generation=0,
            population=sample_population,
            diversity_metrics=sample_diversity,
            champion=champion,
            champion_updated=True,
            events=events
        )

        prometheus_text = tracker.export_prometheus()

        # Check metrics are present
        assert 'evolution_avg_fitness' in prometheus_text
        assert 'evolution_best_fitness' in prometheus_text
        assert 'evolution_diversity_unified' in prometheus_text
        assert 'evolution_template_count' in prometheus_text  # Uses evolution_template_count not evolution_template_distribution
        assert 'evolution_mutations_total' in prometheus_text

    def test_json_export(self, tracker, sample_population, sample_diversity):
        """Test JSON metrics serialization."""
        champion = max(sample_population, key=lambda x: x.fitness)
        events = {'mutations': 5, 'crossovers': 3, 'template_mutations': 1}

        metrics = tracker.record_generation(
            generation=0,
            population=sample_population,
            diversity_metrics=sample_diversity,
            champion=champion,
            champion_updated=True,
            events=events
        )

        # Should be JSON serializable
        json_data = json.dumps({
            'generation': metrics.generation,
            'avg_fitness': metrics.avg_fitness,
            'template_distribution': metrics.template_distribution
        })

        assert json_data is not None
        parsed = json.loads(json_data)
        assert parsed['generation'] == 0


class TestConvergenceAnalysis:
    """Test convergence analysis functionality."""

    def test_fitness_trend_analysis(self, tracker, sample_population, sample_diversity):
        """Test fitness trend analysis."""
        champion = max(sample_population, key=lambda x: x.fitness)
        events = {'mutations': 0, 'crossovers': 0, 'template_mutations': 0}

        # Record 20 generations with improving fitness
        for gen in range(20):
            # Gradually increase fitness
            improving_pop = [
                MockIndividual(fitness=1.0 + gen * 0.1, template_type='Momentum')
                for _ in range(8)
            ]
            tracker.record_generation(
                generation=gen,
                population=improving_pop,
                diversity_metrics=sample_diversity,
                champion=max(improving_pop, key=lambda x: x.fitness),
                champion_updated=True,
                events=events
            )

        analysis = tracker.get_convergence_analysis()

        # Check actual structure from implementation
        assert 'fitness_trend' in analysis
        assert analysis['fitness_trend']['slope'] > 0  # Improving trend
        assert analysis['fitness_trend']['direction'] == 'improving'
        assert 'diversity_trend' in analysis
        assert 'template_evolution' in analysis
        assert 'convergence_status' in analysis

    def test_diversity_stability_analysis(self, tracker, sample_population):
        """Test diversity stability analysis."""
        champion = max(sample_population, key=lambda x: x.fitness)
        events = {'mutations': 0, 'crossovers': 0, 'template_mutations': 0}

        # Record generations with stable diversity
        for gen in range(20):
            stable_diversity = {
                'param': 0.85,  # Implementation expects 'param' not 'param_diversity'
                'template': 0.90,
                'unified': 0.875
            }
            tracker.record_generation(
                generation=gen,
                population=sample_population,
                diversity_metrics=stable_diversity,
                champion=champion,
                champion_updated=False,
                events=events
            )

        analysis = tracker.get_convergence_analysis()

        # Check actual structure from implementation
        assert 'diversity_trend' in analysis
        assert analysis['diversity_trend']['current'] == 0.875
        assert analysis['diversity_trend']['average_recent'] == pytest.approx(0.875, abs=0.01)
        assert analysis['diversity_trend']['stable'] is True  # Should be stable (variation < 0.1)


class TestGetRecentMetrics:
    """Test retrieval of recent metrics."""

    def test_get_recent_metrics_via_history(self, tracker, sample_population, sample_diversity):
        """Test accessing recent metrics via generation_history."""
        champion = max(sample_population, key=lambda x: x.fitness)
        events = {'mutations': 0, 'crossovers': 0, 'template_mutations': 0}

        # Record 15 generations
        for gen in range(15):
            tracker.record_generation(
                generation=gen,
                population=sample_population,
                diversity_metrics=sample_diversity,
                champion=champion,
                champion_updated=False,
                events=events
            )

        # Access last 5 via generation_history
        recent = list(tracker.generation_history)[-5:]

        assert len(recent) == 5
        assert recent[0].generation == 10
        assert recent[-1].generation == 14
