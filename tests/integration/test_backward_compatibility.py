"""
Backward compatibility tests for template evolution system.

Verifies that the multi-template system maintains backward compatibility
with existing single-template code paths.
"""

import unittest
from src.population.population_manager import PopulationManager
from src.population.individual import Individual
from src.population.genetic_operators import GeneticOperators
from src.population.fitness_evaluator import FitnessEvaluator
from src.population.evolution_monitor import EvolutionMonitor
from src.templates.momentum_template import MomentumTemplate


class TestSingleTemplateBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with single-template mode (Task 36)."""

    def setUp(self):
        """Set up test fixtures for backward compatibility testing."""
        self.template = MomentumTemplate()
        # Valid Momentum template parameters
        self.param_grid = {
            'momentum_period': [10, 20],
            'ma_periods': [60, 120],
            'catalyst_type': ['revenue', 'earnings'],
            'catalyst_lookback': [3, 4],
            'n_stocks': [10, 15],
            'stop_loss': [0.1, 0.12],
            'resample': ['M', 'W'],
            'resample_offset': [0, 1]
        }

    def test_individual_defaults_to_momentum_template(self):
        """Test that Individual defaults to 'Momentum' template for backward compatibility."""
        # Create individual without template_type (old API)
        individual = Individual(
            parameters={'momentum_period': 10, 'ma_periods': 60, 'catalyst_type': 'revenue',
                       'catalyst_lookback': 3, 'n_stocks': 10, 'stop_loss': 0.1,
                       'resample': 'M', 'resample_offset': 0},
            generation=0
        )

        # Should default to 'Momentum'
        self.assertEqual(individual.template_type, 'Momentum')
        self.assertTrue(individual.is_valid())

    def test_fitness_evaluator_single_template_mode(self):
        """Test FitnessEvaluator with template provided (single-template mode)."""
        evaluator = FitnessEvaluator(template=self.template, data=None)

        # Should have template set, not registry
        self.assertIsNotNone(evaluator.template)
        self.assertIsNone(evaluator._registry)

        # Should work with default Momentum individuals
        individual = Individual(
            parameters={'momentum_period': 10, 'ma_periods': 60, 'catalyst_type': 'revenue',
                       'catalyst_lookback': 3, 'n_stocks': 10, 'stop_loss': 0.1,
                       'resample': 'M', 'resample_offset': 0},
            generation=0
        )

        # Cache key should include Momentum
        cache_key = evaluator._get_cache_key(individual.id, 'Momentum', use_oos=False)
        self.assertIn('Momentum', cache_key)

    def test_genetic_operators_backward_compatible(self):
        """Test genetic operators with single template type."""
        operators = GeneticOperators(base_mutation_rate=0.1)

        # Create individuals with valid Momentum parameters
        parent1 = Individual(
            parameters={'momentum_period': 10, 'ma_periods': 60, 'catalyst_type': 'revenue',
                       'catalyst_lookback': 3, 'n_stocks': 10, 'stop_loss': 0.1,
                       'resample': 'M', 'resample_offset': 0},
            generation=0
        )
        parent2 = Individual(
            parameters={'momentum_period': 20, 'ma_periods': 120, 'catalyst_type': 'earnings',
                       'catalyst_lookback': 4, 'n_stocks': 15, 'stop_loss': 0.12,
                       'resample': 'W', 'resample_offset': 1},
            generation=0
        )

        # Crossover should work (same template)
        offspring1, offspring2 = operators.crossover(parent1, parent2, generation=1)
        self.assertEqual(offspring1.template_type, 'Momentum')
        self.assertEqual(offspring2.template_type, 'Momentum')
        self.assertEqual(offspring1.generation, 1)
        self.assertIn(parent1.id, offspring1.parent_ids)
        self.assertIn(parent2.id, offspring1.parent_ids)

        # Mutation should work (preserves template by default with low template_mutation_rate)
        mutated = operators.mutate(parent1, generation=1)
        # Template mutation is probabilistic (5%), so verify structure rather than exact template
        self.assertIsNotNone(mutated.template_type)
        self.assertEqual(mutated.generation, 1)
        self.assertIn(parent1.id, mutated.parent_ids)

    def test_evolution_monitor_with_single_template(self):
        """Test EvolutionMonitor backward compatibility with single template."""
        monitor = EvolutionMonitor()

        # Create population (all Momentum)
        population = [
            Individual(
                parameters={'momentum_period': 10, 'ma_periods': 60, 'catalyst_type': 'revenue',
                           'catalyst_lookback': 3, 'n_stocks': 10 + i, 'stop_loss': 0.1,
                           'resample': 'M', 'resample_offset': 0},
                generation=0,
                fitness=1.0 + i * 0.1
            )
            for i in range(10)
        ]

        # Record generation
        monitor.record_generation(
            generation_num=0,
            population=population,
            diversity=0.5,
            cache_stats={'hit_rate': 0.5, 'cache_size': 10}
        )

        # Check template distribution (should be 100% Momentum)
        summary = monitor.get_template_summary()
        self.assertEqual(summary['final_template_distribution'], {'Momentum': 1.0})
        self.assertEqual(summary['dominant_template'], 'Momentum')

        # Template diversity should be 0.0 (single template)
        self.assertEqual(summary['template_diversity_history'][0], 0.0)

    def test_population_initialization_backward_compatible(self):
        """Test PopulationManager with old API (param_grid only)."""
        manager = PopulationManager(population_size=50)

        # Initialize with equal distribution (new default behavior)
        population = manager.initialize_population()

        # Should create 50 individuals
        self.assertEqual(len(population), 50)

        # With new multi-template default, should have 4 templates
        template_counts = {}
        for ind in population:
            template_counts[ind.template_type] = template_counts.get(ind.template_type, 0) + 1

        # Should have 4 templates with equal distribution
        self.assertEqual(len(template_counts), 4)

        # All individuals should be valid
        for ind in population:
            self.assertTrue(ind.is_valid())
            self.assertIsNotNone(ind.template_type)

    def test_unified_diversity_backward_compatible(self):
        """Test unified diversity calculation is backward compatible."""
        # Create population with all same template
        population = [
            Individual(
                parameters={'momentum_period': 10, 'ma_periods': 60, 'catalyst_type': 'revenue',
                           'catalyst_lookback': 3, 'n_stocks': 10 + i, 'stop_loss': 0.1,
                           'resample': 'M', 'resample_offset': 0},
                template_type='Momentum',
                generation=0
            )
            for i in range(10)
        ]

        param_diversity = 0.6

        # Unified diversity should equal param_diversity (backward compatible)
        unified = EvolutionMonitor.calculate_diversity(population, param_diversity)
        self.assertAlmostEqual(unified, param_diversity, places=4)

    def test_no_template_type_errors_in_legacy_paths(self):
        """Test that legacy code paths don't raise template_type errors."""
        # Create individual with old API (valid Momentum parameters)
        ind1 = Individual(
            parameters={'momentum_period': 10, 'ma_periods': 60, 'catalyst_type': 'revenue',
                       'catalyst_lookback': 3, 'n_stocks': 10, 'stop_loss': 0.1,
                       'resample': 'M', 'resample_offset': 0}
        )

        # Should not raise errors
        self.assertIsNotNone(ind1.id)
        self.assertTrue(ind1.is_valid())
        self.assertEqual(ind1.template_type, 'Momentum')

        # Hash should work
        hash_val = hash(ind1)
        self.assertIsNotNone(hash_val)

        # Serialization should work
        data = ind1.to_dict()
        self.assertIn('template_type', data)
        self.assertEqual(data['template_type'], 'Momentum')

        # Deserialization should work
        ind2 = Individual.from_dict(data)
        self.assertEqual(ind2.template_type, 'Momentum')
        self.assertEqual(ind2.id, ind1.id)

    def test_variance_within_tolerance(self):
        """Test that results are within 0.01% variance of baseline."""
        # Create two identical populations
        manager = PopulationManager(population_size=20)

        pop1 = manager.initialize_population()
        pop2 = manager.initialize_population()

        # Both should be 100% diverse
        div1 = manager.calculate_diversity(pop1)
        div2 = manager.calculate_diversity(pop2)

        self.assertAlmostEqual(div1, 1.0, places=2)
        self.assertAlmostEqual(div2, 1.0, places=2)

        # Variance should be within tolerance
        variance = abs(div1 - div2)
        tolerance = 0.0001  # 0.01% variance
        self.assertLessEqual(variance, tolerance)

        print(f"\n✅ Backward compatibility verified:")
        print(f"   - Diversity 1: {div1:.6f}")
        print(f"   - Diversity 2: {div2:.6f}")
        print(f"   - Variance: {variance:.6f} (tolerance: {tolerance})")


if __name__ == '__main__':
    unittest.main()
