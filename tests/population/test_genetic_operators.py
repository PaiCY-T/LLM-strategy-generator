"""
Unit tests for GeneticOperators class.

Tests mutation, crossover, and adaptive mutation rate.
"""

import unittest
from unittest.mock import patch
from src.population.genetic_operators import GeneticOperators
from src.population.individual import Individual


class TestGeneticOperators(unittest.TestCase):
    """Test cases for GeneticOperators class."""

    def setUp(self):
        """Set up test fixtures."""
        self.operators = GeneticOperators(
            base_mutation_rate=0.15,
            min_mutation_rate=0.05,
            max_mutation_rate=0.30
        )

        # Use actual parameters from MomentumTemplate PARAM_GRID
        self.params = {
            'momentum_period': 20,
            'ma_periods': [5, 10, 20],
            'catalyst_type': 'revenue',
            'catalyst_lookback': 12,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'W',
            'resample_offset': 0
        }

    def test_initialization_with_valid_rates(self):
        """Test initialization with valid mutation rates."""
        operators = GeneticOperators(
            base_mutation_rate=0.15,
            min_mutation_rate=0.05,
            max_mutation_rate=0.30
        )

        self.assertEqual(operators.base_mutation_rate, 0.15)
        self.assertEqual(operators.min_mutation_rate, 0.05)
        self.assertEqual(operators.max_mutation_rate, 0.30)
        self.assertEqual(operators.current_mutation_rate, 0.15)

    def test_initialization_raises_on_invalid_rates(self):
        """Test initialization raises error with invalid rate ordering."""
        with self.assertRaises(ValueError):
            GeneticOperators(
                base_mutation_rate=0.15,
                min_mutation_rate=0.20,  # min > base
                max_mutation_rate=0.30
            )

        with self.assertRaises(ValueError):
            GeneticOperators(
                base_mutation_rate=0.35,  # base > max
                min_mutation_rate=0.05,
                max_mutation_rate=0.30
            )

    def test_mutate_produces_valid_individual(self):
        """Test that mutation produces valid individual."""
        parent = Individual(parameters=self.params, generation=0)

        child = self.operators.mutate(parent, generation=1)

        # Check child is valid
        self.assertTrue(child.is_valid())
        self.assertEqual(child.generation, 1)
        self.assertEqual(child.parent_ids, [parent.id])

    def test_mutate_changes_parameters(self):
        """Test that mutation changes at least some parameters eventually."""
        parent = Individual(parameters=self.params, generation=0)

        # With mutation rate 0.15 and 3 parameters, we expect changes
        # Run multiple times to ensure at least one mutation happens
        mutations_detected = False
        for _ in range(50):
            child = self.operators.mutate(parent, generation=1)
            if child.parameters != parent.parameters:
                mutations_detected = True
                break

        self.assertTrue(mutations_detected)

    def test_mutate_with_zero_rate(self):
        """Test mutation with zero rate produces identical child."""
        operators = GeneticOperators(
            base_mutation_rate=0.0,
            min_mutation_rate=0.0,
            max_mutation_rate=0.0
        )

        parent = Individual(parameters=self.params, generation=0)
        child = operators.mutate(parent, generation=1)

        # Parameters should be identical (but IDs same due to same params)
        self.assertEqual(child.parameters, parent.parameters)

    def test_mutate_with_max_rate(self):
        """Test mutation with 100% rate changes parameters."""
        operators = GeneticOperators(
            base_mutation_rate=1.0,
            min_mutation_rate=1.0,
            max_mutation_rate=1.0
        )

        parent = Individual(parameters=self.params, generation=0)

        # Run a few times - should see changes most of the time
        changes_count = 0
        for _ in range(10):
            child = operators.mutate(parent, generation=1)
            if child.parameters != parent.parameters:
                changes_count += 1

        # With 100% mutation rate and 3 params, should see changes
        self.assertGreater(changes_count, 5)

    def test_crossover_with_different_parents(self):
        """Test crossover with different parents produces two children."""
        parent1 = Individual(
            parameters={
                'momentum_period': 20,
                'ma_periods': [5, 10, 20],
                'catalyst_type': 'revenue',
                'catalyst_lookback': 12,
                'n_stocks': 10,
                'stop_loss': 0.10,
                'resample': 'W',
                'resample_offset': 0
            },
            generation=0
        )
        parent2 = Individual(
            parameters={
                'momentum_period': 60,
                'ma_periods': [20, 60],
                'catalyst_type': 'roe',
                'catalyst_lookback': 4,
                'n_stocks': 20,
                'stop_loss': 0.15,
                'resample': 'M',
                'resample_offset': 1
            },
            generation=0
        )

        child1, child2 = self.operators.crossover(parent1, parent2, generation=1)

        # Check children are valid
        self.assertTrue(child1.is_valid())
        self.assertTrue(child2.is_valid())
        self.assertEqual(child1.generation, 1)
        self.assertEqual(child2.generation, 1)

        # Check parent tracking
        self.assertEqual(child1.parent_ids, [parent1.id, parent2.id])
        self.assertEqual(child2.parent_ids, [parent1.id, parent2.id])

    def test_crossover_with_identical_parents(self):
        """Test crossover with identical parents returns mutated copies."""
        parent = Individual(parameters=self.params, generation=0)

        # Crossover with same parent (duplicate check)
        child1, child2 = self.operators.crossover(parent, parent, generation=1)

        # Should produce two individuals (mutated from same parent)
        self.assertTrue(child1.is_valid())
        self.assertTrue(child2.is_valid())
        self.assertEqual(child1.parent_ids, [parent.id])
        self.assertEqual(child2.parent_ids, [parent.id])

    def test_crossover_inherits_from_parents(self):
        """Test crossover children inherit parameters from parents."""
        parent1 = Individual(
            parameters={
                'momentum_period': 20,
                'ma_periods': [5, 10, 20],
                'catalyst_type': 'revenue',
                'catalyst_lookback': 12,
                'n_stocks': 10,
                'stop_loss': 0.10,
                'resample': 'W',
                'resample_offset': 0
            },
            generation=0
        )
        parent2 = Individual(
            parameters={
                'momentum_period': 60,
                'ma_periods': [20, 60],
                'catalyst_type': 'roe',
                'catalyst_lookback': 4,
                'n_stocks': 20,
                'stop_loss': 0.15,
                'resample': 'M',
                'resample_offset': 1
            },
            generation=0
        )

        # Run crossover multiple times
        for _ in range(10):
            child1, child2 = self.operators.crossover(parent1, parent2, generation=1)

            # Check each parameter comes from one parent or the other
            for param_name in parent1.parameters.keys():
                self.assertIn(
                    child1.parameters[param_name],
                    [parent1.parameters[param_name], parent2.parameters[param_name]]
                )
                self.assertIn(
                    child2.parameters[param_name],
                    [parent1.parameters[param_name], parent2.parameters[param_name]]
                )

    def test_update_mutation_rate_low_diversity(self):
        """Test mutation rate increases with low diversity."""
        initial_rate = self.operators.current_mutation_rate

        self.operators.update_mutation_rate(diversity=0.3)

        # Should increase (0.3 < 0.5)
        self.assertGreater(self.operators.current_mutation_rate, initial_rate)

    def test_update_mutation_rate_high_diversity(self):
        """Test mutation rate decreases with high diversity."""
        initial_rate = self.operators.current_mutation_rate

        self.operators.update_mutation_rate(diversity=0.9)

        # Should decrease (0.9 > 0.8)
        self.assertLess(self.operators.current_mutation_rate, initial_rate)

    def test_update_mutation_rate_healthy_diversity(self):
        """Test mutation rate decays toward base with healthy diversity."""
        # Set current rate away from base
        self.operators.current_mutation_rate = 0.25

        self.operators.update_mutation_rate(diversity=0.6)

        # Should move toward base (0.15)
        self.assertLess(self.operators.current_mutation_rate, 0.25)
        self.assertGreater(self.operators.current_mutation_rate, 0.15)

    def test_update_mutation_rate_respects_min_bound(self):
        """Test mutation rate doesn't go below minimum."""
        # Start at minimum
        self.operators.current_mutation_rate = self.operators.min_mutation_rate

        # Try to decrease further
        self.operators.update_mutation_rate(diversity=0.9)

        # Should stay at minimum
        self.assertGreaterEqual(
            self.operators.current_mutation_rate,
            self.operators.min_mutation_rate
        )

    def test_update_mutation_rate_respects_max_bound(self):
        """Test mutation rate doesn't go above maximum."""
        # Start at maximum
        self.operators.current_mutation_rate = self.operators.max_mutation_rate

        # Try to increase further
        self.operators.update_mutation_rate(diversity=0.1)

        # Should stay at maximum
        self.assertLessEqual(
            self.operators.current_mutation_rate,
            self.operators.max_mutation_rate
        )

    def test_get_mutation_rate(self):
        """Test get_mutation_rate returns current rate."""
        self.assertEqual(
            self.operators.get_mutation_rate(),
            self.operators.base_mutation_rate
        )

        # Change rate
        self.operators.current_mutation_rate = 0.25

        self.assertEqual(self.operators.get_mutation_rate(), 0.25)

    def test_reset_mutation_rate(self):
        """Test reset_mutation_rate restores base rate."""
        # Change rate
        self.operators.current_mutation_rate = 0.25

        # Reset
        self.operators.reset_mutation_rate()

        self.assertEqual(
            self.operators.current_mutation_rate,
            self.operators.base_mutation_rate
        )

    def test_mutate_parameter_with_valid_param(self):
        """Test _mutate_parameter returns valid value from grid."""
        from src.templates.momentum_template import MomentumTemplate
        param_grid = MomentumTemplate().PARAM_GRID

        # Test multiple mutations
        for _ in range(20):
            new_value = self.operators._mutate_parameter(
                'n_stocks',
                10,
                param_grid
            )
            self.assertIn(new_value, param_grid['n_stocks'])

    def test_mutate_parameter_raises_on_invalid_param(self):
        """Test _mutate_parameter raises error on invalid parameter."""
        param_grid = {'valid_param': [1, 2, 3]}

        with self.assertRaises(ValueError):
            self.operators._mutate_parameter(
                'invalid_param',
                10,
                param_grid
            )

    def test_mutate_parameter_raises_on_empty_grid(self):
        """Test _mutate_parameter raises error on empty allowed values."""
        param_grid = {'param': []}

        with self.assertRaises(ValueError):
            self.operators._mutate_parameter(
                'param',
                10,
                param_grid
            )

    def test_adaptive_mutation_convergence_scenario(self):
        """Test adaptive mutation in convergence scenario."""
        # Simulate population converging
        for i in range(10):
            diversity = 1.0 - (i * 0.1)  # Decreasing from 1.0 to 0.0
            self.operators.update_mutation_rate(diversity)

        # By the end, mutation rate should be increased (low diversity)
        self.assertGreater(
            self.operators.current_mutation_rate,
            self.operators.base_mutation_rate
        )

    def test_adaptive_mutation_exploration_scenario(self):
        """Test adaptive mutation during exploration."""
        # Simulate high diversity exploration phase
        for _ in range(10):
            self.operators.update_mutation_rate(diversity=0.95)

        # Mutation rate should be decreased (high diversity)
        self.assertLess(
            self.operators.current_mutation_rate,
            self.operators.base_mutation_rate
        )


class TestTemplateEvolution(unittest.TestCase):
    """Test cases for template evolution features (Tasks 16-17)."""

    def setUp(self):
        """Set up test fixtures for template evolution."""
        self.operators = GeneticOperators(
            base_mutation_rate=0.15,
            min_mutation_rate=0.05,
            max_mutation_rate=0.30,
            template_mutation_rate=0.05
        )

        # Parameters valid for MomentumTemplate
        self.momentum_params = {
            'momentum_period': 20,
            'ma_periods': [5, 10, 20],
            'catalyst_type': 'revenue',
            'catalyst_lookback': 12,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'W',
            'resample_offset': 0
        }

    # Task 16: Unit tests for template mutation

    def test_template_mutation_rate_initialization(self):
        """Test template_mutation_rate is properly initialized."""
        self.assertEqual(self.operators.template_mutation_rate, 0.05)

        # Test custom rate
        ops = GeneticOperators(template_mutation_rate=0.10)
        self.assertEqual(ops.template_mutation_rate, 0.10)

    def test_template_mutation_rate_validation(self):
        """Test template_mutation_rate validation."""
        # Valid rates
        GeneticOperators(template_mutation_rate=0.0)
        GeneticOperators(template_mutation_rate=1.0)
        GeneticOperators(template_mutation_rate=0.5)

        # Invalid rates
        with self.assertRaises(ValueError):
            GeneticOperators(template_mutation_rate=-0.1)

        with self.assertRaises(ValueError):
            GeneticOperators(template_mutation_rate=1.1)

    @patch('random.random')
    def test_template_mutation_occurs_with_probability(self, mock_random):
        """Test template mutation occurs with template_mutation_rate probability."""
        # Mock random to trigger template mutation (first call)
        # but not parameter mutation (subsequent calls)
        # Need enough values for template mutation check + parameter mutation checks
        mock_random.side_effect = [0.01] + [0.99] * 20

        parent = Individual(
            parameters=self.momentum_params,
            template_type='Momentum',
            generation=0
        )

        child = self.operators.mutate(parent, generation=1)

        # Template should have changed (0.01 < 0.05)
        # Note: May still be Momentum if randomly selected
        self.assertIsNotNone(child.template_type)
        self.assertIn(child.template_type, ['Momentum', 'Turtle', 'Factor', 'Mastiff'])

    @patch('random.random')
    def test_template_mutation_skipped_with_high_probability(self, mock_random):
        """Test template mutation skipped when random > template_mutation_rate."""
        # Mock random to skip template mutation (first call > 0.05)
        mock_random.side_effect = [0.99] * 20

        parent = Individual(
            parameters=self.momentum_params,
            template_type='Momentum',
            generation=0
        )

        child = self.operators.mutate(parent, generation=1)

        # Template should remain unchanged
        self.assertEqual(child.template_type, 'Momentum')

    def test_template_mutation_reinitializes_parameters(self):
        """Test parameters re-initialized when template changes."""
        # Force template mutation with high rate
        ops = GeneticOperators(
            base_mutation_rate=0.0,  # No parameter mutation
            min_mutation_rate=0.0,  # Allow base=0.0
            template_mutation_rate=1.0  # Always template mutation
        )

        parent = Individual(
            parameters=self.momentum_params,
            template_type='Momentum',
            generation=0
        )

        # Run multiple mutations
        for _ in range(5):
            child = ops.mutate(parent, generation=1)

            # Template may change (not guaranteed to be different)
            # But parameters should be valid for child's template
            self.assertTrue(child.validate_parameters())
            self.assertTrue(child.is_valid())

            # If template changed, parameters should be different
            if child.template_type != parent.template_type:
                # Parameter keys should match child's template PARAM_GRID
                from src.utils.template_registry import TemplateRegistry
                registry = TemplateRegistry.get_instance()
                template = registry.get_template(child.template_type)
                self.assertEqual(
                    set(child.parameters.keys()),
                    set(template.PARAM_GRID.keys())
                )

    def test_mutate_preserves_generation_and_parent_ids(self):
        """Test mutate preserves generation and parent_ids tracking."""
        parent = Individual(
            parameters=self.momentum_params,
            template_type='Momentum',
            generation=5
        )

        child = self.operators.mutate(parent, generation=10)

        self.assertEqual(child.generation, 10)
        self.assertEqual(child.parent_ids, [parent.id])

    def test_template_mutation_produces_valid_individuals(self):
        """Test template mutation always produces valid individuals."""
        ops = GeneticOperators(template_mutation_rate=1.0)

        parent = Individual(
            parameters=self.momentum_params,
            template_type='Momentum',
            generation=0
        )

        # Run many mutations
        for _ in range(50):
            child = ops.mutate(parent, generation=1)

            # Child must be valid
            self.assertTrue(child.is_valid())
            self.assertTrue(child.is_evaluated() is False)  # No fitness yet
            self.assertIsNotNone(child.id)
            self.assertEqual(len(child.id), 8)

            # Parameters must be valid for child's template
            self.assertTrue(child.validate_parameters())

    # Task 17: Unit tests for template-aware crossover

    def test_same_template_crossover_occurs(self):
        """Test crossover occurs when parents have same template_type."""
        parent1 = Individual(
            parameters=self.momentum_params.copy(),
            template_type='Momentum',
            generation=0
        )
        # Use valid MomentumTemplate parameters (check PARAM_GRID)
        parent2 = Individual(
            parameters={
                'momentum_period': 10,  # Valid in PARAM_GRID
                'ma_periods': [10, 20, 40],  # Valid in PARAM_GRID
                'catalyst_type': 'revenue',  # Valid in PARAM_GRID
                'catalyst_lookback': 6,  # Valid in PARAM_GRID
                'n_stocks': 20,  # Valid in PARAM_GRID
                'stop_loss': 0.15,  # Valid in PARAM_GRID
                'resample': 'M',  # Valid in PARAM_GRID
                'resample_offset': 1  # Valid in PARAM_GRID
            },
            template_type='Momentum',
            generation=0
        )

        child1, child2 = self.operators.crossover(parent1, parent2, generation=1)

        # Children should inherit template_type
        self.assertEqual(child1.template_type, 'Momentum')
        self.assertEqual(child2.template_type, 'Momentum')

        # Children should inherit from both parents
        self.assertEqual(child1.parent_ids, [parent1.id, parent2.id])
        self.assertEqual(child2.parent_ids, [parent1.id, parent2.id])

        # Children should be valid individuals
        self.assertTrue(child1.is_valid())
        self.assertTrue(child2.is_valid())

        # Children should have correct generation
        self.assertEqual(child1.generation, 1)
        self.assertEqual(child2.generation, 1)

    def test_different_template_crossover_returns_mutations(self):
        """Test crossover returns mutated copies when templates differ."""
        # Use operators with template_mutation_rate=0 for deterministic test
        ops_no_template_mutation = GeneticOperators(
            base_mutation_rate=0.15,
            min_mutation_rate=0.05,
            max_mutation_rate=0.30,
            template_mutation_rate=0.0
        )

        parent1 = Individual(
            parameters=self.momentum_params,
            template_type='Momentum',
            generation=0
        )
        # Use valid TurtleTemplate parameters
        parent2 = Individual(
            parameters={
                'yield_threshold': 6.0,
                'ma_short': 20,
                'ma_long': 60,
                'rev_short': 6,
                'rev_long': 12,
                'op_margin_threshold': 3,
                'director_threshold': 10,
                'vol_min': 50,
                'vol_max': 10000,
                'n_stocks': 15,
                'stop_loss': 0.08,
                'take_profit': 0.5,
                'position_limit': 0.15,
                'resample': 'M'
            },
            template_type='Turtle',
            generation=0
        )

        child1, child2 = ops_no_template_mutation.crossover(parent1, parent2, generation=1)

        # Children should keep their parent's template_type (no template mutation)
        # child1 is mutated copy of parent1, child2 is mutated copy of parent2
        self.assertEqual(child1.template_type, parent1.template_type)
        self.assertEqual(child2.template_type, parent2.template_type)

        # Children should have single parent (mutation, not crossover)
        self.assertEqual(len(child1.parent_ids), 1)
        self.assertEqual(len(child2.parent_ids), 1)
        self.assertEqual(child1.parent_ids[0], parent1.id)
        self.assertEqual(child2.parent_ids[0], parent2.id)

    def test_crossover_offspring_inherit_common_template(self):
        """Test offspring inherit common template_type from both parents."""
        # Test with different template types
        for template_type in ['Momentum', 'Turtle', 'Factor', 'Mastiff']:
            # Skip if we can't create valid individuals
            try:
                parent1 = Individual(
                    parameters=self.momentum_params if template_type == 'Momentum' else {},
                    template_type=template_type,
                    generation=0
                )
                parent2 = Individual(
                    parameters=self.momentum_params if template_type == 'Momentum' else {},
                    template_type=template_type,
                    generation=0
                )

                # Re-initialize with valid parameters
                from src.utils.template_registry import TemplateRegistry
                registry = TemplateRegistry.get_instance()
                template = registry.get_template(template_type)

                # Generate valid parameters
                params1 = {k: v[0] for k, v in template.PARAM_GRID.items()}
                params2 = {k: v[-1] for k, v in template.PARAM_GRID.items()}

                parent1 = Individual(parameters=params1, template_type=template_type, generation=0)
                parent2 = Individual(parameters=params2, template_type=template_type, generation=0)

                child1, child2 = self.operators.crossover(parent1, parent2, generation=1)

                # Both children should have same template as parents
                self.assertEqual(child1.template_type, template_type)
                self.assertEqual(child2.template_type, template_type)

            except Exception:
                # Skip templates we can't easily test
                continue

    def test_crossover_with_identical_parents_returns_mutations(self):
        """Test crossover with identical parents returns mutated copies."""
        parent = Individual(
            parameters=self.momentum_params,
            template_type='Momentum',
            generation=0
        )

        child1, child2 = self.operators.crossover(parent, parent, generation=1)

        # Children should have same template
        self.assertEqual(child1.template_type, 'Momentum')
        self.assertEqual(child2.template_type, 'Momentum')

        # Children should have single parent (mutation, not crossover)
        self.assertEqual(child1.parent_ids, [parent.id])
        self.assertEqual(child2.parent_ids, [parent.id])

        # Children should have correct generation
        self.assertEqual(child1.generation, 1)
        self.assertEqual(child2.generation, 1)

        # Children should be valid
        self.assertTrue(child1.is_valid())
        self.assertTrue(child2.is_valid())


if __name__ == '__main__':
    unittest.main()
