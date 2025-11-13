"""
Unit tests for PopulationManager class.

Tests population initialization, selection, elitism, diversity, and convergence.
"""

import unittest
from unittest.mock import MagicMock
from src.population.population_manager import PopulationManager
from src.population.individual import Individual


class TestPopulationManager(unittest.TestCase):
    """Test cases for PopulationManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = PopulationManager(
            population_size=10,
            elite_size=2,
            tournament_size=2,
            diversity_threshold=0.5,
            convergence_window=3
        )

        self.param_grid = {
            'n_stocks': [5, 10, 15, 20],
            'stop_loss': [0.05, 0.10, 0.15],
            'take_profit': [0.10, 0.15, 0.20]
        }

    def test_initialization_creates_unique_population(self):
        """Test that initialization creates 100% unique individuals."""
        population = self.manager.initialize_population(self.param_grid)

        # Check population size
        self.assertEqual(len(population), self.manager.population_size)

        # Check all individuals are unique
        unique_ids = set(ind.id for ind in population)
        self.assertEqual(len(unique_ids), len(population))

        # Check diversity is 1.0 (100%)
        diversity = self.manager.calculate_diversity(population)
        self.assertAlmostEqual(diversity, 1.0, places=2)

    def test_initialization_with_seed_preserves_champion(self):
        """Test that seed parameters are included in population."""
        seed_params = [
            {'n_stocks': 10, 'stop_loss': 0.10, 'take_profit': 0.15}
        ]

        population = self.manager.initialize_population(
            self.param_grid,
            seed_parameters=seed_params
        )

        # Check that seed individual is in population
        seed_id = Individual(parameters=seed_params[0]).id
        population_ids = [ind.id for ind in population]

        self.assertIn(seed_id, population_ids)
        self.assertEqual(len(population), self.manager.population_size)

    def test_initialization_with_multiple_seeds(self):
        """Test initialization with multiple seed parameters."""
        seed_params = [
            {'n_stocks': 10, 'stop_loss': 0.10, 'take_profit': 0.15},
            {'n_stocks': 20, 'stop_loss': 0.15, 'take_profit': 0.20}
        ]

        population = self.manager.initialize_population(
            self.param_grid,
            seed_parameters=seed_params
        )

        # Check both seeds are in population
        seed_ids = [Individual(parameters=p).id for p in seed_params]
        population_ids = [ind.id for ind in population]

        for seed_id in seed_ids:
            self.assertIn(seed_id, population_ids)

    def test_initialization_validates_template_distribution_sum(self):
        """Test that initialization validates template distribution sums to 1.0."""
        invalid_distribution = {
            'Momentum': 0.4,
            'Turtle': 0.3,
            'Factor': 0.2
            # Sum = 0.9, not 1.0 - should fail
        }

        manager = PopulationManager(population_size=10)

        with self.assertRaises(ValueError) as context:
            manager.initialize_population(template_distribution=invalid_distribution)

        self.assertIn("must sum to 1.0", str(context.exception))

    def test_tournament_selection_returns_best(self):
        """Test that tournament selection returns best individual."""
        # Create evaluated population
        population = [
            Individual(parameters={'n_stocks': i}, fitness=float(i))
            for i in range(10)
        ]

        # Run tournament selection multiple times
        for _ in range(10):
            parent = self.manager.select_parent(population)
            # With tournament_size=2, should select better of two random individuals
            self.assertTrue(parent.is_evaluated())
            self.assertIn(parent, population)

    def test_tournament_selection_raises_on_empty_population(self):
        """Test that selection raises error on empty population."""
        with self.assertRaises(ValueError):
            self.manager.select_parent([])

    def test_tournament_selection_raises_on_unevaluated(self):
        """Test that selection raises error on unevaluated individuals."""
        population = [
            Individual(parameters={'n_stocks': i})
            for i in range(5)
        ]

        with self.assertRaises(ValueError):
            self.manager.select_parent(population)

    def test_elitism_combines_elites_and_offspring(self):
        """Test that elitism combines top elites with top offspring."""
        # Create current population (fitness 1-10)
        current_pop = [
            Individual(parameters={'n_stocks': i}, fitness=float(i))
            for i in range(1, 11)
        ]

        # Create offspring (fitness 5-14)
        offspring = [
            Individual(parameters={'n_stocks': i+100}, fitness=float(i))
            for i in range(5, 15)
        ]

        # Apply elitism
        next_gen = self.manager.apply_elitism(current_pop, offspring)

        # Check size
        self.assertEqual(len(next_gen), self.manager.population_size)

        # Check that top 2 elites are preserved (fitness 10, 9)
        elite_fitness = sorted([ind.fitness for ind in next_gen], reverse=True)[:2]
        self.assertEqual(elite_fitness, [14.0, 13.0])

    def test_elitism_raises_on_empty_current_population(self):
        """Test that elitism raises error on empty current population."""
        offspring = [
            Individual(parameters={'n_stocks': i}, fitness=float(i))
            for i in range(5)
        ]

        with self.assertRaises(ValueError):
            self.manager.apply_elitism([], offspring)

    def test_elitism_raises_on_unevaluated_current(self):
        """Test that elitism raises error on unevaluated current population."""
        current_pop = [
            Individual(parameters={'n_stocks': i})
            for i in range(5)
        ]
        offspring = [
            Individual(parameters={'n_stocks': i}, fitness=float(i))
            for i in range(5)
        ]

        with self.assertRaises(ValueError):
            self.manager.apply_elitism(current_pop, offspring)

    def test_elitism_raises_on_unevaluated_offspring(self):
        """Test that elitism raises error on unevaluated offspring."""
        current_pop = [
            Individual(parameters={'n_stocks': i}, fitness=float(i))
            for i in range(5)
        ]
        offspring = [
            Individual(parameters={'n_stocks': i})
            for i in range(5)
        ]

        with self.assertRaises(ValueError):
            self.manager.apply_elitism(current_pop, offspring)

    def test_calculate_diversity_all_unique(self):
        """Test diversity calculation with all unique individuals."""
        population = [
            Individual(parameters={'n_stocks': i})
            for i in range(10)
        ]

        diversity = self.manager.calculate_diversity(population)

        self.assertEqual(diversity, 1.0)

    def test_calculate_diversity_all_identical(self):
        """Test diversity calculation with identical individuals."""
        params = {'n_stocks': 10}
        population = [
            Individual(parameters=params.copy())
            for _ in range(10)
        ]

        diversity = self.manager.calculate_diversity(population)

        self.assertEqual(diversity, 0.1)  # 1 unique out of 10

    def test_calculate_diversity_half_unique(self):
        """Test diversity calculation with 50% unique individuals."""
        population = [
            Individual(parameters={'n_stocks': 1}),
            Individual(parameters={'n_stocks': 1}),
            Individual(parameters={'n_stocks': 2}),
            Individual(parameters={'n_stocks': 2}),
            Individual(parameters={'n_stocks': 3}),
            Individual(parameters={'n_stocks': 3}),
            Individual(parameters={'n_stocks': 4}),
            Individual(parameters={'n_stocks': 4}),
            Individual(parameters={'n_stocks': 5}),
            Individual(parameters={'n_stocks': 5})
        ]

        diversity = self.manager.calculate_diversity(population)

        self.assertEqual(diversity, 0.5)  # 5 unique out of 10

    def test_calculate_diversity_raises_on_empty(self):
        """Test that diversity calculation raises error on empty population."""
        with self.assertRaises(ValueError):
            self.manager.calculate_diversity([])

    def test_convergence_not_met_initially(self):
        """Test that convergence is not met initially."""
        population = [
            Individual(parameters={'n_stocks': i}, fitness=1.0)
            for i in range(10)
        ]

        converged = self.manager.check_convergence(population)

        self.assertFalse(converged)

    def test_convergence_dual_criteria_low_diversity_and_plateau(self):
        """Test convergence requires both low diversity and fitness plateau."""
        # Create population with low diversity
        params = {'n_stocks': 10}
        population = [
            Individual(parameters=params.copy(), fitness=2.0)
            for _ in range(10)
        ]

        # Simulate convergence_window generations with low diversity + plateau
        for _ in range(self.manager.convergence_window * 2):
            self.manager.check_convergence(population)

        # Now should be converged
        converged = self.manager.check_convergence(population)

        self.assertTrue(converged)

    def test_convergence_not_met_with_high_diversity(self):
        """Test convergence not met with high diversity despite plateau."""
        # Create population with high diversity
        population = [
            Individual(parameters={'n_stocks': i}, fitness=2.0)
            for i in range(10)
        ]

        # Simulate multiple generations
        for _ in range(self.manager.convergence_window * 2):
            self.manager.check_convergence(population)

        # Should NOT converge (diversity too high)
        converged = self.manager.check_convergence(population)

        self.assertFalse(converged)

    def test_convergence_not_met_with_changing_fitness(self):
        """Test convergence not met with changing fitness despite low diversity."""
        # Create population with low diversity
        params = {'n_stocks': 10}
        population_low_div = [
            Individual(parameters=params.copy(), fitness=2.0)
            for _ in range(10)
        ]

        # Simulate generations with changing fitness
        for i in range(self.manager.convergence_window * 2):
            # Change fitness each generation
            for ind in population_low_div:
                ind.fitness = 2.0 + i * 0.1
            self.manager.check_convergence(population_low_div)

        # Should NOT converge (fitness not plateaued)
        converged = self.manager.check_convergence(population_low_div)

        self.assertFalse(converged)

    def test_convergence_reset(self):
        """Test that convergence tracking can be reset."""
        population = [
            Individual(parameters={'n_stocks': i}, fitness=1.0)
            for i in range(10)
        ]

        # Build up history
        for _ in range(5):
            self.manager.check_convergence(population)

        # Reset
        self.manager.reset_convergence_tracking()

        # Check that history is cleared
        self.assertEqual(len(self.manager._diversity_history), 0)
        self.assertEqual(len(self.manager._best_fitness_history), 0)

    def test_convergence_status_empty_initially(self):
        """Test convergence status when no history."""
        status = self.manager.get_convergence_status()

        self.assertIsNone(status['current_diversity'])
        self.assertIsNone(status['current_best_fitness'])
        self.assertEqual(status['diversity_history_length'], 0)

    def test_convergence_status_with_history(self):
        """Test convergence status with history."""
        population = [
            Individual(parameters={'n_stocks': i}, fitness=float(i))
            for i in range(10)
        ]

        # Build history
        for _ in range(5):
            self.manager.check_convergence(population)

        status = self.manager.get_convergence_status()

        self.assertIsNotNone(status['current_diversity'])
        self.assertIsNotNone(status['current_best_fitness'])
        self.assertEqual(status['diversity_history_length'], 5)
        self.assertEqual(status['current_best_fitness'], 9.0)

    def test_check_convergence_raises_on_empty_population(self):
        """Test that convergence check raises error on empty population."""
        with self.assertRaises(ValueError):
            self.manager.check_convergence([])

    def test_check_convergence_raises_on_unevaluated(self):
        """Test that convergence check raises error on unevaluated population."""
        population = [
            Individual(parameters={'n_stocks': i})
            for i in range(5)
        ]

        with self.assertRaises(ValueError):
            self.manager.check_convergence(population)


class TestPopulationManagerTemplateDistribution(unittest.TestCase):
    """Test cases for PopulationManager template distribution (Task 34)."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = PopulationManager(population_size=100)

    def test_equal_distribution_default(self):
        """Test equal distribution (25% each) when template_distribution=None."""
        population = self.manager.initialize_population()

        # Count individuals per template
        template_counts = {}
        for ind in population:
            template_counts[ind.template_type] = template_counts.get(ind.template_type, 0) + 1

        # Should have 4 templates
        self.assertEqual(len(template_counts), 4)

        # Each template should have ~25 individuals (allowing for rounding)
        for template, count in template_counts.items():
            self.assertGreaterEqual(count, 24)  # At least 24
            self.assertLessEqual(count, 26)     # At most 26

        # Total should be exactly 100
        self.assertEqual(sum(template_counts.values()), 100)

    def test_weighted_distribution(self):
        """Test weighted distribution with custom proportions."""
        distribution = {
            'Momentum': 0.5,   # 50 individuals
            'Turtle': 0.3,     # 30 individuals
            'Factor': 0.2      # 20 individuals
        }

        population = self.manager.initialize_population(template_distribution=distribution)

        # Count individuals per template
        template_counts = {}
        for ind in population:
            template_counts[ind.template_type] = template_counts.get(ind.template_type, 0) + 1

        # Should have exactly 3 templates
        self.assertEqual(len(template_counts), 3)

        # Check expected counts (allowing for rounding)
        self.assertEqual(template_counts.get('Momentum', 0), 50)
        self.assertEqual(template_counts.get('Turtle', 0), 30)
        self.assertEqual(template_counts.get('Factor', 0), 20)

        # Total should be exactly 100
        self.assertEqual(sum(template_counts.values()), 100)

    def test_distribution_validation_rejects_invalid_sum(self):
        """Test that distribution validation rejects sum != 1.0."""
        invalid_distributions = [
            {'Momentum': 0.4, 'Turtle': 0.3, 'Factor': 0.2},  # Sum = 0.9
            {'Momentum': 0.6, 'Turtle': 0.6},                 # Sum = 1.2
            {'Momentum': 1.1},                                # Sum = 1.1
        ]

        for distribution in invalid_distributions:
            with self.assertRaises(ValueError) as context:
                self.manager.initialize_population(template_distribution=distribution)
            self.assertIn("must sum to 1.0", str(context.exception))

    def test_distribution_validation_accepts_valid_sum(self):
        """Test that distribution validation accepts sum = 1.0 within tolerance."""
        # Exact 1.0
        distribution1 = {'Momentum': 0.5, 'Turtle': 0.5}
        population1 = self.manager.initialize_population(template_distribution=distribution1)
        self.assertEqual(len(population1), 100)

        # Within tolerance (1.0 + 1e-7)
        distribution2 = {'Momentum': 0.5, 'Turtle': 0.5 + 1e-7}
        population2 = self.manager.initialize_population(template_distribution=distribution2)
        self.assertEqual(len(population2), 100)

    def test_invalid_template_names_rejected(self):
        """Test that invalid template names are rejected."""
        invalid_distribution = {
            'Momentum': 0.5,
            'InvalidTemplate': 0.5  # Not a valid template
        }

        with self.assertRaises(ValueError) as context:
            self.manager.initialize_population(template_distribution=invalid_distribution)

        self.assertIn("Invalid template name", str(context.exception))
        self.assertIn("InvalidTemplate", str(context.exception))

    def test_rounding_assigns_remainder_to_first_alphabetically(self):
        """Test that rounding remainder is assigned to first template alphabetically."""
        # Use population_size=101 with 4 templates
        # 101 / 4 = 25.25 → 25 each = 100, remainder 1
        # Remainder should go to first alphabetically (Factor)
        manager = PopulationManager(population_size=101)

        population = manager.initialize_population()

        # Count individuals per template
        template_counts = {}
        for ind in population:
            template_counts[ind.template_type] = template_counts.get(ind.template_type, 0) + 1

        # Sort templates alphabetically
        sorted_templates = sorted(template_counts.keys())

        # First template alphabetically should have 26 (25 + 1 remainder)
        first_template = sorted_templates[0]
        self.assertEqual(template_counts[first_template], 26)

        # Others should have 25
        for template in sorted_templates[1:]:
            self.assertEqual(template_counts[template], 25)

        # Total should be exactly 101
        self.assertEqual(sum(template_counts.values()), 101)

    def test_all_individuals_have_unique_parameters(self):
        """Test that all individuals have unique parameter combinations."""
        population = self.manager.initialize_population()

        # Extract unique IDs
        unique_ids = set(ind.id for ind in population)

        # Should be 100% unique
        self.assertEqual(len(unique_ids), 100)

        # Verify diversity is 1.0
        diversity = self.manager.calculate_diversity(population)
        self.assertGreaterEqual(diversity, 0.99)

    def test_per_template_parameter_grids_used(self):
        """Test that each template uses its own parameter grid."""
        population = self.manager.initialize_population()

        # Group by template
        by_template = {}
        for ind in population:
            if ind.template_type not in by_template:
                by_template[ind.template_type] = []
            by_template[ind.template_type].append(ind)

        # Each template should have individuals
        self.assertGreater(len(by_template), 0)

        # Verify all individuals in each template group have valid parameters
        for template_type, individuals in by_template.items():
            self.assertGreater(len(individuals), 0)
            for ind in individuals:
                self.assertEqual(ind.template_type, template_type)
                self.assertIsNotNone(ind.parameters)
                self.assertGreater(len(ind.parameters), 0)


if __name__ == '__main__':
    unittest.main()
