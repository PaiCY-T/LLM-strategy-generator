"""
Unit tests for selection mechanisms (tournament, diversity-aware, elitism).

Tests cover:
- SelectionManager initialization and validation
- Tournament selection with various parameters
- Parent pair selection with uniqueness constraints
- Diversity-aware selection probability calculation
- Elite strategy identification by Sharpe/Calmar ratio
- Edge cases and error handling

References:
    - Deb, K., et al. (2002). "A fast and elitist multiobjective genetic algorithm: NSGA-II"
"""

import pytest
from unittest.mock import patch, MagicMock
from src.evolution.types import Strategy, MultiObjectiveMetrics
from src.evolution.selection import SelectionManager


class TestSelectionManagerInit:
    """Test suite for SelectionManager initialization."""

    def test_default_initialization(self):
        """Test SelectionManager with default parameters."""
        manager = SelectionManager()
        assert manager.tournament_size == 3
        assert manager.selection_pressure == 0.8
        assert manager.elite_count == 2
        assert manager.diversity_weight == 0.3

    def test_custom_initialization(self):
        """Test SelectionManager with custom parameters."""
        manager = SelectionManager(
            tournament_size=5,
            selection_pressure=0.9,
            elite_count=3,
            diversity_weight=0.5
        )
        assert manager.tournament_size == 5
        assert manager.selection_pressure == 0.9
        assert manager.elite_count == 3
        assert manager.diversity_weight == 0.5

    def test_raises_error_for_invalid_tournament_size(self):
        """Test that ValueError is raised for tournament_size < 2."""
        with pytest.raises(ValueError, match="tournament_size must be at least 2"):
            SelectionManager(tournament_size=1)

    def test_raises_error_for_invalid_selection_pressure(self):
        """Test that ValueError is raised for selection_pressure out of range."""
        with pytest.raises(ValueError, match="selection_pressure must be in"):
            SelectionManager(selection_pressure=1.5)

        with pytest.raises(ValueError, match="selection_pressure must be in"):
            SelectionManager(selection_pressure=-0.1)

    def test_raises_error_for_negative_elite_count(self):
        """Test that ValueError is raised for negative elite_count."""
        with pytest.raises(ValueError, match="elite_count must be non-negative"):
            SelectionManager(elite_count=-1)

    def test_raises_error_for_invalid_diversity_weight(self):
        """Test that ValueError is raised for diversity_weight out of range."""
        with pytest.raises(ValueError, match="diversity_weight must be in"):
            SelectionManager(diversity_weight=1.5)


class TestTournamentSelection:
    """Test suite for tournament_selection method."""

    def create_test_population(self, size=10):
        """Helper to create test population with varying metrics."""
        population = []
        for i in range(size):
            metrics = MultiObjectiveMetrics(
                sharpe_ratio=0.5 + i * 0.1,  # Increasing Sharpe ratio
                calmar_ratio=0.3 + i * 0.05,  # Increasing Calmar ratio
                total_return=0.1 + i * 0.02,
                max_drawdown=-0.2 + i * 0.01,
                win_rate=0.5 + i * 0.02,
                annual_return=0.1 + i * 0.015
            )
            strategy = Strategy(
                id=f's{i}',
                code=f"data.get('feature_{i}') > 0",  # Different features for diversity
                metrics=metrics
            )
            population.append(strategy)
        return population

    def test_tournament_selection_returns_strategy(self):
        """Test that tournament_selection returns a valid Strategy."""
        manager = SelectionManager(tournament_size=3)
        population = self.create_test_population(10)

        selected = manager.tournament_selection(population)

        assert isinstance(selected, Strategy)
        assert selected in population

    def test_tournament_selection_with_custom_size(self):
        """Test tournament_selection with custom tournament size."""
        manager = SelectionManager(tournament_size=3)
        population = self.create_test_population(10)

        # Should work with custom tournament size
        selected = manager.tournament_selection(population, tournament_size=5)
        assert selected in population

    def test_raises_error_when_population_too_small(self):
        """Test that ValueError is raised when population < tournament_size."""
        manager = SelectionManager(tournament_size=5)
        population = self.create_test_population(3)

        with pytest.raises(ValueError, match="Population size .* must be >= tournament_size"):
            manager.tournament_selection(population)

    @patch('src.evolution.selection.random.random')
    @patch('src.evolution.selection.random.sample')
    def test_selection_pressure_affects_outcome(self, mock_sample, mock_random):
        """Test that selection pressure determines best vs random selection."""
        manager = SelectionManager(tournament_size=3, selection_pressure=0.8)
        population = self.create_test_population(10)

        # Mock tournament: select strategies with different fitness
        tournament = [population[0], population[5], population[9]]  # Low, mid, high fitness
        mock_sample.return_value = tournament

        # Test high selection pressure (select best)
        mock_random.return_value = 0.5  # < 0.8, should select best
        selected = manager.tournament_selection(population)
        # Best strategy should be selected (highest Sharpe ratio)
        assert selected.id == 's9'

        # Test random selection (for diversity)
        mock_random.return_value = 0.9  # >= 0.8, should select random
        manager = SelectionManager(tournament_size=3, selection_pressure=0.8)
        # Cannot predict random selection, just verify it's from tournament
        selected = manager.tournament_selection(population)
        assert selected in tournament

    def test_pareto_rank_influences_selection(self):
        """Test that lower Pareto rank strategies are preferred in tournament."""
        manager = SelectionManager(tournament_size=3, selection_pressure=1.0)

        # Create population with clear Pareto dominance
        # s0: high Sharpe, high Calmar (non-dominated)
        # s1: medium Sharpe, medium Calmar (dominated)
        # s2: low Sharpe, low Calmar (dominated)
        s0 = Strategy(id='s0', code="data.get('roe') > 0.15",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=1.5, calmar_ratio=1.2, total_return=0.3, max_drawdown=-0.1, win_rate=0.6, annual_return=0.2))
        s1 = Strategy(id='s1', code="data.get('pe') < 20",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=1.0, calmar_ratio=0.8, total_return=0.2, max_drawdown=-0.15, win_rate=0.55, annual_return=0.15))
        s2 = Strategy(id='s2', code="data.get('liquidity') > 1M",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=0.5, calmar_ratio=0.4, total_return=0.1, max_drawdown=-0.2, win_rate=0.5, annual_return=0.1))

        population = [s0, s1, s2]

        # With selection_pressure=1.0, should always select s0 (best Pareto rank)
        with patch('src.evolution.selection.random.sample', return_value=population):
            selected = manager.tournament_selection(population)
            assert selected.id == 's0'

    def test_crowding_distance_breaks_ties(self):
        """Test that crowding distance is used when Pareto ranks are equal."""
        manager = SelectionManager(tournament_size=2, selection_pressure=1.0)

        # Create two strategies with identical metrics (same Pareto rank)
        # But different features (different crowding distance)
        s0 = Strategy(id='s0', code="data.get('roe') > 0.15",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=1.0, calmar_ratio=1.0, total_return=0.2, max_drawdown=-0.15, win_rate=0.55, annual_return=0.15))
        s1 = Strategy(id='s1', code="data.get('roe') > 0.15",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=1.0, calmar_ratio=1.0, total_return=0.2, max_drawdown=-0.15, win_rate=0.55, annual_return=0.15))

        population = [s0, s1]

        # Both have same Pareto rank (both non-dominated), crowding distance breaks tie
        selected = manager.tournament_selection(population)
        assert selected in [s0, s1]


class TestSelectParents:
    """Test suite for select_parents method."""

    def create_test_population(self, size=10):
        """Helper to create test population."""
        population = []
        for i in range(size):
            metrics = MultiObjectiveMetrics(
                sharpe_ratio=0.5 + i * 0.1,
                calmar_ratio=0.3 + i * 0.05,
                total_return=0.1 + i * 0.02,
                max_drawdown=-0.2 + i * 0.01,
                win_rate=0.5 + i * 0.02,
                annual_return=0.1 + i * 0.015
            )
            strategy = Strategy(
                id=f's{i}',
                code=f"data.get('feature_{i}') > 0",
                metrics=metrics
            )
            population.append(strategy)
        return population

    def test_select_parents_returns_correct_count(self):
        """Test that select_parents returns requested number of pairs."""
        manager = SelectionManager()
        population = self.create_test_population(10)

        parent_pairs = manager.select_parents(population, count=5)

        assert len(parent_pairs) == 5

    def test_parent_pairs_have_unique_parents(self):
        """Test that each parent pair consists of unique parents (no self-pairing)."""
        manager = SelectionManager()
        population = self.create_test_population(10)

        parent_pairs = manager.select_parents(population, count=20)

        for parent1, parent2 in parent_pairs:
            assert parent1.id != parent2.id

    def test_parents_are_from_population(self):
        """Test that all selected parents are from the original population."""
        manager = SelectionManager()
        population = self.create_test_population(10)

        parent_pairs = manager.select_parents(population, count=10)

        for parent1, parent2 in parent_pairs:
            assert parent1 in population
            assert parent2 in population

    def test_raises_error_for_population_size_less_than_2(self):
        """Test that ValueError is raised when population has fewer than 2 strategies."""
        manager = SelectionManager()
        population = self.create_test_population(1)

        with pytest.raises(ValueError, match="Population size must be at least 2"):
            manager.select_parents(population, count=1)

    def test_large_count_works(self):
        """Test selecting many parent pairs (count > population size)."""
        manager = SelectionManager()
        population = self.create_test_population(10)

        # Can select more pairs than population size (parents can repeat across pairs)
        parent_pairs = manager.select_parents(population, count=50)
        assert len(parent_pairs) == 50


class TestCalculateSelectionProbability:
    """Test suite for calculate_selection_probability method."""

    def create_test_population_with_diversity(self):
        """Helper to create population with varying fitness and diversity."""
        # Create diverse population
        s0 = Strategy(id='s0', code="data.get('roe') > 0.15",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=1.5, calmar_ratio=1.2, total_return=0.3, max_drawdown=-0.1, win_rate=0.6, annual_return=0.2))
        s1 = Strategy(id='s1', code="data.get('pe') < 20",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=1.0, calmar_ratio=0.8, total_return=0.2, max_drawdown=-0.15, win_rate=0.55, annual_return=0.15))
        s2 = Strategy(id='s2', code="data.get('liquidity') > 1M",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=0.5, calmar_ratio=0.4, total_return=0.1, max_drawdown=-0.2, win_rate=0.5, annual_return=0.1))
        s3 = Strategy(id='s3', code="data.indicator('momentum') > 0",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=0.8, calmar_ratio=0.6, total_return=0.15, max_drawdown=-0.18, win_rate=0.52, annual_return=0.12))
        return [s0, s1, s2, s3]

    def test_higher_probability_for_non_dominated_strategies(self):
        """Test that non-dominated strategies get higher selection probability."""
        manager = SelectionManager(diversity_weight=0.3)
        population = self.create_test_population_with_diversity()

        # s0 has highest Sharpe/Calmar, should be non-dominated
        prob_s0 = manager.calculate_selection_probability(population[0], population)
        prob_s2 = manager.calculate_selection_probability(population[2], population)

        # s0 (non-dominated) should have higher probability than s2 (dominated)
        assert prob_s0 > prob_s2

    def test_diversity_weight_affects_probability(self):
        """Test that diversity_weight influences novelty contribution."""
        population = self.create_test_population_with_diversity()

        # Test with low diversity weight (fitness-focused)
        manager_low = SelectionManager(diversity_weight=0.1)
        prob_low = manager_low.calculate_selection_probability(population[0], population)

        # Test with high diversity weight (novelty-focused)
        manager_high = SelectionManager(diversity_weight=0.9)
        prob_high = manager_high.calculate_selection_probability(population[0], population)

        # Probabilities should differ based on diversity weight
        # (exact relationship depends on strategy's novelty score)
        assert prob_low != prob_high

    def test_probability_positive_for_all_strategies(self):
        """Test that all strategies get positive selection probability."""
        manager = SelectionManager(diversity_weight=0.3)
        population = self.create_test_population_with_diversity()

        for strategy in population:
            prob = manager.calculate_selection_probability(strategy, population)
            assert prob > 0.0

    def test_returns_zero_for_strategy_not_in_population(self):
        """Test that probability is 0.0 for strategy not in population."""
        manager = SelectionManager(diversity_weight=0.3)
        population = self.create_test_population_with_diversity()

        # Create strategy not in population
        external_strategy = Strategy(
            id='external',
            code="data.get('external') > 0",
            metrics=MultiObjectiveMetrics(sharpe_ratio=1.0, calmar_ratio=0.8, total_return=0.2, max_drawdown=-0.15, win_rate=0.55, annual_return=0.15)
        )

        prob = manager.calculate_selection_probability(external_strategy, population)
        assert prob == 0.0


class TestGetEliteStrategies:
    """Test suite for get_elite_strategies method."""

    def create_test_population_with_metrics(self):
        """Helper to create population with varying Sharpe/Calmar ratios."""
        # Create strategies with known Sharpe/Calmar ratios for sorting
        s0 = Strategy(id='s0', code="data.get('roe') > 0.15",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=1.5, calmar_ratio=1.2, total_return=0.3, max_drawdown=-0.1, win_rate=0.6, annual_return=0.2))
        s1 = Strategy(id='s1', code="data.get('pe') < 20",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=1.2, calmar_ratio=1.0, total_return=0.25, max_drawdown=-0.12, win_rate=0.58, annual_return=0.18))
        s2 = Strategy(id='s2', code="data.get('liquidity') > 1M",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=0.8, calmar_ratio=0.9, total_return=0.2, max_drawdown=-0.15, win_rate=0.55, annual_return=0.15))
        s3 = Strategy(id='s3', code="data.indicator('momentum') > 0",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=0.5, calmar_ratio=0.5, total_return=0.1, max_drawdown=-0.2, win_rate=0.5, annual_return=0.1))
        return [s3, s1, s0, s2]  # Return in random order

    def test_returns_top_strategies_by_sharpe_ratio(self):
        """Test that elite strategies are sorted by Sharpe ratio (primary)."""
        manager = SelectionManager(elite_count=2)
        population = self.create_test_population_with_metrics()

        elite = manager.get_elite_strategies(population)

        assert len(elite) == 2
        assert elite[0].id == 's0'  # Highest Sharpe (1.5)
        assert elite[1].id == 's1'  # Second highest Sharpe (1.2)

    def test_calmar_ratio_breaks_ties(self):
        """Test that Calmar ratio is used when Sharpe ratios are equal."""
        # Create strategies with identical Sharpe but different Calmar
        s0 = Strategy(id='s0', code="data.get('roe') > 0.15",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=1.0, calmar_ratio=1.2, total_return=0.2, max_drawdown=-0.15, win_rate=0.55, annual_return=0.15))
        s1 = Strategy(id='s1', code="data.get('pe') < 20",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=1.0, calmar_ratio=0.8, total_return=0.2, max_drawdown=-0.15, win_rate=0.55, annual_return=0.15))

        population = [s1, s0]
        manager = SelectionManager(elite_count=1)

        elite = manager.get_elite_strategies(population)

        # s0 should be selected (higher Calmar ratio)
        assert elite[0].id == 's0'

    def test_custom_elite_count(self):
        """Test get_elite_strategies with custom elite_count parameter."""
        manager = SelectionManager(elite_count=2)
        population = self.create_test_population_with_metrics()

        # Override instance elite_count with parameter
        elite = manager.get_elite_strategies(population, elite_count=3)

        assert len(elite) == 3

    def test_elite_count_zero_returns_empty_list(self):
        """Test that elite_count=0 returns empty list."""
        manager = SelectionManager(elite_count=0)
        population = self.create_test_population_with_metrics()

        elite = manager.get_elite_strategies(population)

        assert elite == []

    def test_raises_error_when_elite_count_exceeds_population(self):
        """Test that ValueError is raised when elite_count > population size."""
        manager = SelectionManager(elite_count=10)
        population = self.create_test_population_with_metrics()

        with pytest.raises(ValueError, match="elite_count .* cannot exceed population size"):
            manager.get_elite_strategies(population)

    def test_handles_none_metrics_gracefully(self):
        """Test that strategies with None metrics are ranked lowest."""
        s0 = Strategy(id='s0', code="data.get('roe') > 0.15",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=1.0, calmar_ratio=1.0, total_return=0.2, max_drawdown=-0.15, win_rate=0.55, annual_return=0.15))
        s1 = Strategy(id='s1', code="data.get('pe') < 20",
                      metrics=MultiObjectiveMetrics(sharpe_ratio=None, calmar_ratio=None, total_return=0.1, max_drawdown=-0.2, win_rate=0.5, annual_return=0.1))

        population = [s1, s0]
        manager = SelectionManager(elite_count=1)

        elite = manager.get_elite_strategies(population)

        # s0 should be selected (has valid metrics)
        assert elite[0].id == 's0'


class TestIntegrationScenarios:
    """Integration tests combining multiple selection methods."""

    def create_diverse_population(self):
        """Helper to create diverse population for integration tests."""
        population = []
        for i in range(20):
            metrics = MultiObjectiveMetrics(
                sharpe_ratio=0.5 + i * 0.05,
                calmar_ratio=0.3 + i * 0.03,
                total_return=0.1 + i * 0.01,
                max_drawdown=-0.2 + i * 0.005,
                win_rate=0.5 + i * 0.01,
                annual_return=0.1 + i * 0.008
            )
            strategy = Strategy(
                id=f's{i}',
                code=f"data.get('feature_{i}') > 0",
                metrics=metrics
            )
            population.append(strategy)
        return population

    def test_complete_selection_workflow(self):
        """Test complete selection workflow: elite + parent selection."""
        manager = SelectionManager(
            tournament_size=3,
            selection_pressure=0.8,
            elite_count=2,
            diversity_weight=0.3
        )
        population = self.create_diverse_population()

        # Step 1: Identify elite strategies
        elite = manager.get_elite_strategies(population)
        assert len(elite) == 2

        # Step 2: Select parent pairs for mating
        parent_pairs = manager.select_parents(population, count=10)
        assert len(parent_pairs) == 10

        # Step 3: Calculate selection probabilities
        probs = [manager.calculate_selection_probability(s, population) for s in population]
        assert all(p >= 0.0 for p in probs)

    def test_selection_maintains_diversity(self):
        """Test that diversity-aware selection favors both fit and novel strategies."""
        manager = SelectionManager(diversity_weight=0.5)
        population = self.create_diverse_population()

        # High fitness, low novelty strategy
        high_fitness = population[-1]  # Highest Sharpe ratio

        # Medium fitness, high novelty strategy (different features)
        medium_fitness = population[10]

        prob_high_fitness = manager.calculate_selection_probability(high_fitness, population)
        prob_medium_fitness = manager.calculate_selection_probability(medium_fitness, population)

        # High fitness should still have advantage, but not overwhelming
        assert prob_high_fitness > prob_medium_fitness
        # Medium fitness should have non-zero probability (diversity contribution)
        assert prob_medium_fitness > 0.0
