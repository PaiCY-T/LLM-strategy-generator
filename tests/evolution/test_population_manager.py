"""
Integration tests for PopulationManager.

Tests cover:
- Population initialization (size, template diversity)
- Population evaluation (Pareto ranking, crowding distance, novelty)
- Generation evolution (workflow, population size, state updates)
- Elitism replacement (elite preservation, size maintenance)
- Checkpoint save/load (state persistence, round-trip)
- Diversity monitoring (adaptive mutation rate)
- Integration with selection, crossover, mutation managers
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import List

from src.evolution.population_manager import PopulationManager
from src.evolution.types import Strategy, MultiObjectiveMetrics, EvolutionResult


class TestPopulationManagerInit:
    """Test PopulationManager initialization."""

    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        autonomous_loop = Mock()
        prompt_builder = Mock()
        code_validator = Mock()

        manager = PopulationManager(
            autonomous_loop=autonomous_loop,
            prompt_builder=prompt_builder,
            code_validator=code_validator
        )

        assert manager.autonomous_loop is autonomous_loop
        assert manager.prompt_builder is prompt_builder
        assert manager.code_validator is code_validator
        assert manager.population_size == 20
        assert manager.elite_count == 2
        assert manager.tournament_size == 3
        assert manager.mutation_rate == 0.1
        assert manager.current_generation == 0
        assert len(manager.current_population) == 0
        assert len(manager.generation_history) == 0

    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters."""
        manager = PopulationManager(
            autonomous_loop=Mock(),
            prompt_builder=Mock(),
            code_validator=Mock(),
            population_size=50,
            elite_count=5,
            tournament_size=5,
            mutation_rate=0.2,
            mutation_strength=0.15,
            crossover_rate=0.8
        )

        assert manager.population_size == 50
        assert manager.elite_count == 5
        assert manager.tournament_size == 5
        assert manager.mutation_rate == 0.2
        assert manager.mutation_strength == 0.15
        assert manager.crossover_rate == 0.8

    def test_components_initialized(self):
        """Test that all evolution components are initialized."""
        manager = PopulationManager(
            autonomous_loop=Mock(),
            prompt_builder=Mock(),
            code_validator=Mock()
        )

        assert manager.selection_manager is not None
        assert manager.crossover_manager is not None
        assert manager.mutation_manager is not None


class TestInitializePopulation:
    """Test population initialization."""

    @pytest.fixture
    def manager(self):
        """Create PopulationManager instance for testing."""
        return PopulationManager(
            autonomous_loop=Mock(),
            prompt_builder=Mock(),
            code_validator=Mock(),
            population_size=20
        )

    def test_creates_correct_population_size(self, manager):
        """Test that initialize_population creates correct number of strategies."""
        population = manager.initialize_population()

        assert len(population) == 20
        assert len(manager.current_population) == 20

    def test_uses_template_diversity(self, manager):
        """Test that different templates are used for diversity."""
        population = manager.initialize_population(
            template_types=['Momentum', 'Value', 'Quality']
        )

        # Check that different templates are used
        templates = [s.template_type for s in population]
        assert 'Momentum' in templates
        assert 'Value' in templates
        assert 'Quality' in templates

    def test_strategies_have_generation_zero(self, manager):
        """Test that initial strategies have generation=0."""
        population = manager.initialize_population()

        for strategy in population:
            assert strategy.generation == 0
            assert len(strategy.parent_ids) == 0

    def test_evaluation_assigns_metrics(self, manager):
        """Test that initialize_population evaluates strategies."""
        population = manager.initialize_population()

        for strategy in population:
            assert strategy.metrics is not None
            assert strategy.pareto_rank is not None
            assert strategy.crowding_distance is not None

    def test_current_generation_set_to_zero(self, manager):
        """Test that current_generation is set to 0."""
        manager.initialize_population()

        assert manager.current_generation == 0


class TestEvaluatePopulation:
    """Test population evaluation."""

    @pytest.fixture
    def manager(self):
        """Create PopulationManager instance for testing."""
        return PopulationManager(
            autonomous_loop=Mock(),
            prompt_builder=Mock(),
            code_validator=Mock()
        )

    @pytest.fixture
    def unevaluated_population(self):
        """Create population without metrics."""
        return [
            Strategy(
                id=f'strategy_{i}',
                generation=0,
                parent_ids=[],
                code=f'# Strategy {i}',
                parameters={'index': i}
            )
            for i in range(10)
        ]

    def test_assigns_metrics_to_all_strategies(self, manager, unevaluated_population):
        """Test that all strategies get metrics assigned."""
        evaluated = manager.evaluate_population(unevaluated_population)

        for strategy in evaluated:
            assert strategy.metrics is not None
            assert isinstance(strategy.metrics, MultiObjectiveMetrics)

    def test_assigns_pareto_ranks(self, manager, unevaluated_population):
        """Test that Pareto ranks are assigned."""
        evaluated = manager.evaluate_population(unevaluated_population)

        for strategy in evaluated:
            assert strategy.pareto_rank is not None
            assert strategy.pareto_rank >= 1

    def test_assigns_crowding_distances(self, manager, unevaluated_population):
        """Test that crowding distances are assigned."""
        evaluated = manager.evaluate_population(unevaluated_population)

        for strategy in evaluated:
            assert strategy.crowding_distance is not None
            assert strategy.crowding_distance >= 0.0

    def test_assigns_novelty_scores(self, manager, unevaluated_population):
        """Test that novelty scores are assigned."""
        evaluated = manager.evaluate_population(unevaluated_population)

        for strategy in evaluated:
            assert strategy.novelty_score is not None
            assert strategy.novelty_score >= 0.0

    def test_pareto_front_has_rank_one(self, manager, unevaluated_population):
        """Test that Pareto front strategies have rank=1."""
        evaluated = manager.evaluate_population(unevaluated_population)

        pareto_front = [s for s in evaluated if s.pareto_rank == 1]
        assert len(pareto_front) > 0


class TestEvolveGeneration:
    """Test generation evolution."""

    @pytest.fixture
    def manager(self):
        """Create PopulationManager with initialized population."""
        mgr = PopulationManager(
            autonomous_loop=Mock(),
            prompt_builder=Mock(),
            code_validator=Mock(),
            population_size=20,
            elite_count=2
        )
        mgr.initialize_population()
        return mgr

    def test_maintains_population_size(self, manager):
        """Test that evolve_generation maintains population size."""
        initial_size = len(manager.current_population)

        result = manager.evolve_generation()

        assert len(manager.current_population) == initial_size
        assert len(result.population.strategies) == initial_size

    def test_increments_generation_number(self, manager):
        """Test that generation number increases."""
        assert manager.current_generation == 0

        result = manager.evolve_generation()

        assert manager.current_generation == 1
        assert result.generation == 1

    def test_returns_evolution_result(self, manager):
        """Test that evolve_generation returns EvolutionResult."""
        result = manager.evolve_generation()

        assert isinstance(result, EvolutionResult)
        assert result.generation == 1
        assert result.population is not None
        assert result.diversity_score is not None
        assert result.pareto_front_size >= 0

    def test_timing_metrics_included(self, manager):
        """Test that timing metrics are captured."""
        result = manager.evolve_generation()

        assert result.evaluation_time >= 0
        assert result.selection_time >= 0
        assert result.crossover_time >= 0
        assert result.mutation_time >= 0
        assert result.total_time > 0

    def test_updates_generation_history(self, manager):
        """Test that generation history is updated."""
        assert len(manager.generation_history) == 0

        # Test single generation update
        with patch('src.evolution.population_manager.calculate_novelty_score', return_value=0.5):
            manager.evolve_generation()

        assert len(manager.generation_history) == 1

        # Test second generation update
        with patch('src.evolution.population_manager.calculate_novelty_score', return_value=0.5):
            manager.evolve_generation()

        assert len(manager.generation_history) == 2

    def test_pareto_front_extracted(self, manager):
        """Test that Pareto front is extracted in result."""
        result = manager.evolve_generation()

        pareto_front = result.population.pareto_front
        assert len(pareto_front) > 0
        for strategy in pareto_front:
            assert strategy.pareto_rank == 1

    def test_best_strategy_identified(self, manager):
        """Test that best strategy is identified."""
        result = manager.evolve_generation()

        # Check that population has a best_sharpe strategy
        best = result.population.best_sharpe
        assert best is not None
        assert best.metrics is not None


class TestElitismReplacement:
    """Test elitism replacement."""

    @pytest.fixture
    def manager(self):
        """Create PopulationManager instance."""
        return PopulationManager(
            autonomous_loop=Mock(),
            prompt_builder=Mock(),
            code_validator=Mock(),
            population_size=20,
            elite_count=2
        )

    @pytest.fixture
    def current_population(self):
        """Create current population with varying metrics."""
        population = []
        for i in range(20):  # Full population_size
            metrics = MultiObjectiveMetrics(
                sharpe_ratio=1.0 + i * 0.1,
                calmar_ratio=1.0 + i * 0.1,
                max_drawdown=-0.2,
                total_return=0.3,
                win_rate=0.6,
                annual_return=0.2
            )
            strategy = Strategy(
                id=f'current_{i}',
                generation=1,
                parent_ids=[],
                code=f'# Current {i}',
                parameters={'index': i},
                metrics=metrics,
                pareto_rank=1 if i < 5 else 2,
                crowding_distance=1.0 - i * 0.02
            )
            population.append(strategy)
        return population

    @pytest.fixture
    def offspring(self):
        """Create offspring population."""
        population = []
        for i in range(18):  # population_size - elite_count
            metrics = MultiObjectiveMetrics(
                sharpe_ratio=1.5 + i * 0.05,
                calmar_ratio=1.5 + i * 0.05,
                max_drawdown=-0.15,
                total_return=0.35,
                win_rate=0.65,
                annual_return=0.25
            )
            strategy = Strategy(
                id=f'offspring_{i}',
                generation=2,
                parent_ids=[f'current_{i}', f'current_{i+1}'],
                code=f'# Offspring {i}',
                parameters={'index': 100 + i},
                metrics=metrics,
                pareto_rank=1,
                crowding_distance=0.8 - i * 0.01
            )
            population.append(strategy)
        return population

    def test_preserves_elites(self, manager, current_population, offspring):
        """Test that top elites are preserved."""
        elite_count = 2
        new_population = manager.elitism_replacement(
            current_population, offspring, elite_count
        )

        # Check that top 2 strategies by Sharpe ratio are preserved
        top_sharpe = sorted(
            current_population,
            key=lambda s: (s.metrics.sharpe_ratio if s.metrics else 0),
            reverse=True
        )[:elite_count]

        top_ids = {s.id for s in top_sharpe}
        new_ids = {s.id for s in new_population}

        # At least one elite should be preserved
        assert len(top_ids & new_ids) >= 1

    def test_maintains_population_size(self, manager, current_population, offspring):
        """Test that population size is maintained."""
        new_population = manager.elitism_replacement(
            current_population, offspring, elite_count=2
        )

        assert len(new_population) == manager.population_size

    def test_selects_best_when_too_many(self, manager):
        """Test selection when elites + offspring exceed population size."""
        # Create population and offspring with mix of ranks
        large_population = [
            Strategy(
                id=f'strategy_{i}',
                generation=2,
                parent_ids=[],
                code=f'# Strategy {i}',
                parameters={'index': i},
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0 + i * 0.1,
                    calmar_ratio=1.0,
                    max_drawdown=-0.2,
                    total_return=0.3,
                    win_rate=0.6,
                    annual_return=0.2
                ),
                pareto_rank=1 if i < 15 else 2,  # 15 rank=1, 15 rank=2
                crowding_distance=1.0 - i * 0.02
            )
            for i in range(30)
        ]

        # Current pop has 15 rank=1 and 5 rank=2
        current_pop = large_population[:20]
        # Offspring has 5 rank=1 and 5 rank=2
        offspring = large_population[10:20]

        new_population = manager.elitism_replacement(current_pop, offspring, elite_count=2)

        # Should be trimmed to population_size
        assert len(new_population) == manager.population_size

        # Should prefer lower Pareto rank (should have more rank=1 than rank=2)
        ranks = [s.pareto_rank for s in new_population]
        assert ranks.count(1) > ranks.count(2)


class TestCheckpointing:
    """Test checkpoint save/load."""

    @pytest.fixture
    def manager(self):
        """Create PopulationManager with initialized population."""
        mgr = PopulationManager(
            autonomous_loop=Mock(),
            prompt_builder=Mock(),
            code_validator=Mock(),
            population_size=10,
            elite_count=2
        )
        mgr.initialize_population()
        mgr.evolve_generation()
        return mgr

    def test_save_checkpoint_creates_file(self, manager):
        """Test that save_checkpoint creates JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "checkpoint.json"

            manager.save_checkpoint(str(filepath))

            assert filepath.exists()

    def test_checkpoint_contains_required_fields(self, manager):
        """Test that checkpoint contains all required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "checkpoint.json"

            manager.save_checkpoint(str(filepath))

            with open(filepath) as f:
                checkpoint = json.load(f)

            assert 'generation' in checkpoint
            assert 'population' in checkpoint
            assert 'generation_history' in checkpoint
            assert 'config' in checkpoint
            assert 'timestamp' in checkpoint

    def test_load_checkpoint_restores_state(self, manager):
        """Test that load_checkpoint restores manager state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "checkpoint.json"

            # Save state
            original_generation = manager.current_generation
            original_pop_size = len(manager.current_population)

            manager.save_checkpoint(str(filepath))

            # Create new manager and load
            new_manager = PopulationManager(
                autonomous_loop=Mock(),
                prompt_builder=Mock(),
                code_validator=Mock()
            )

            new_manager.load_checkpoint(str(filepath))

            # Verify state restored
            assert new_manager.current_generation == original_generation
            assert len(new_manager.current_population) == original_pop_size

    def test_save_load_round_trip(self, manager):
        """Test that save/load round-trip preserves state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "checkpoint.json"

            # Save current state
            manager.save_checkpoint(str(filepath))

            # Load into new manager
            new_manager = PopulationManager(
                autonomous_loop=Mock(),
                prompt_builder=Mock(),
                code_validator=Mock()
            )
            new_manager.load_checkpoint(str(filepath))

            # Verify critical state matches
            assert new_manager.current_generation == manager.current_generation
            assert len(new_manager.current_population) == len(manager.current_population)
            assert new_manager.population_size == manager.population_size
            assert new_manager.elite_count == manager.elite_count
            assert new_manager.mutation_rate == manager.mutation_rate

    def test_load_nonexistent_file_raises_error(self):
        """Test that loading nonexistent file raises error."""
        manager = PopulationManager(
            autonomous_loop=Mock(),
            prompt_builder=Mock(),
            code_validator=Mock()
        )

        with pytest.raises(FileNotFoundError):
            manager.load_checkpoint("/nonexistent/checkpoint.json")


class TestDiversityMonitoring:
    """Test diversity monitoring and adaptation."""

    @pytest.fixture
    def manager(self):
        """Create PopulationManager instance."""
        return PopulationManager(
            autonomous_loop=Mock(),
            prompt_builder=Mock(),
            code_validator=Mock(),
            mutation_rate=0.1
        )

    def test_low_diversity_increases_mutation_rate(self, manager):
        """Test that low diversity increases mutation rate."""
        # Create low-diversity population (all similar)
        population = [
            Strategy(
                id=f'strategy_{i}',
                generation=1,
                parent_ids=[],
                code='# Similar code',
                parameters={'param': i * 0.01}  # Very similar parameters
            )
            for i in range(10)
        ]

        initial_mutation_rate = manager.mutation_rate

        # Mock diversity calculation to return low diversity
        with patch('src.evolution.population_manager.calculate_population_diversity', return_value=0.25):
            diversity = manager.monitor_and_adapt_diversity(population)

            # Mutation rate should increase by 50%
            assert manager.mutation_rate > initial_mutation_rate
            assert manager.mutation_rate == pytest.approx(initial_mutation_rate * 1.5)

    def test_very_low_diversity_increases_mutation_rate_more(self, manager):
        """Test that very low diversity triggers stronger adaptation."""
        population = [
            Strategy(
                id=f'strategy_{i}',
                generation=1,
                parent_ids=[],
                code='# Identical code',
                parameters={'param': 0.5}
            )
            for i in range(10)
        ]

        initial_mutation_rate = manager.mutation_rate

        # Mock severe diversity collapse
        with patch('src.evolution.population_manager.calculate_population_diversity', return_value=0.15):
            diversity = manager.monitor_and_adapt_diversity(population)

            # Mutation rate should increase
            assert manager.mutation_rate > initial_mutation_rate

    def test_high_diversity_maintains_mutation_rate(self, manager):
        """Test that high diversity maintains mutation rate."""
        population = [
            Strategy(
                id=f'strategy_{i}',
                generation=1,
                parent_ids=[],
                code=f'# Diverse code {i}',
                parameters={'param': i * 0.1}
            )
            for i in range(10)
        ]

        initial_mutation_rate = manager.mutation_rate

        # Mock high diversity
        with patch('src.evolution.population_manager.calculate_population_diversity', return_value=0.8):
            diversity = manager.monitor_and_adapt_diversity(population)

            # Mutation rate should not change
            assert manager.mutation_rate == initial_mutation_rate

    def test_mutation_rate_capped_at_maximum(self, manager):
        """Test that mutation rate is capped at 0.5."""
        manager.mutation_rate = 0.4  # Start high

        population = [Strategy(id=f's_{i}', generation=1, parent_ids=[], code='#', parameters={}) for i in range(10)]

        # Mock low diversity to trigger increase
        with patch('src.evolution.population_manager.calculate_population_diversity', return_value=0.1):
            manager.monitor_and_adapt_diversity(population)

            # Should be capped at 0.5
            assert manager.mutation_rate <= 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
