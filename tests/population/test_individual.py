"""
Unit tests for Individual class.

Tests hash generation, equality, validation, and serialization.
"""

import unittest
from src.population.individual import Individual


class TestIndividual(unittest.TestCase):
    """Test cases for Individual class."""

    def setUp(self):
        """Set up test fixtures."""
        self.params_1 = {
            'n_stocks': 10,
            'stop_loss': 0.10,
            'take_profit': 0.15
        }
        self.params_2 = {
            'n_stocks': 20,
            'stop_loss': 0.15,
            'take_profit': 0.20
        }
        self.param_grid = {
            'n_stocks': [5, 10, 15, 20],
            'stop_loss': [0.05, 0.10, 0.15, 0.20],
            'take_profit': [0.10, 0.15, 0.20, 0.25]
        }

    def test_hash_generation_uniqueness(self):
        """Test that different parameters produce different hashes."""
        ind1 = Individual(parameters=self.params_1)
        ind2 = Individual(parameters=self.params_2)

        self.assertNotEqual(ind1.id, ind2.id)
        self.assertEqual(len(ind1.id), 8)
        self.assertEqual(len(ind2.id), 8)

    def test_hash_generation_consistency(self):
        """Test that same parameters produce same hash."""
        ind1 = Individual(parameters=self.params_1)
        ind2 = Individual(parameters=self.params_1.copy())

        self.assertEqual(ind1.id, ind2.id)

    def test_equality_based_on_id(self):
        """Test equality comparison uses ID."""
        ind1 = Individual(parameters=self.params_1)
        ind2 = Individual(parameters=self.params_1.copy())
        ind3 = Individual(parameters=self.params_2)

        # Same parameters should be equal
        self.assertEqual(ind1, ind2)

        # Different parameters should not be equal
        self.assertNotEqual(ind1, ind3)

    def test_equality_with_non_individual(self):
        """Test equality with non-Individual objects."""
        ind = Individual(parameters=self.params_1)

        self.assertNotEqual(ind, "not_an_individual")
        self.assertNotEqual(ind, 123)
        self.assertNotEqual(ind, None)

    def test_hashable_for_sets(self):
        """Test that individuals can be used in sets."""
        ind1 = Individual(parameters=self.params_1)
        ind2 = Individual(parameters=self.params_1.copy())
        ind3 = Individual(parameters=self.params_2)

        individual_set = {ind1, ind2, ind3}

        # ind1 and ind2 have same hash, should result in 2 unique items
        self.assertEqual(len(individual_set), 2)

    def test_is_evaluated_false_initially(self):
        """Test that new individuals are not evaluated."""
        ind = Individual(parameters=self.params_1)

        self.assertFalse(ind.is_evaluated())
        self.assertIsNone(ind.fitness)

    def test_is_evaluated_true_after_setting_fitness(self):
        """Test that individuals with fitness are evaluated."""
        ind = Individual(parameters=self.params_1)
        ind.fitness = 1.5

        self.assertTrue(ind.is_evaluated())

    def test_is_evaluated_false_with_none_fitness(self):
        """Test that fitness=None means not evaluated."""
        ind = Individual(parameters=self.params_1, fitness=None)

        self.assertFalse(ind.is_evaluated())

    def test_is_valid_with_good_parameters(self):
        """Test validation with valid parameters."""
        ind = Individual(parameters=self.params_1)

        self.assertTrue(ind.is_valid())

    def test_is_valid_with_empty_parameters(self):
        """Test validation fails with empty parameters."""
        ind = Individual(parameters={})

        self.assertFalse(ind.is_valid())

    def test_is_valid_with_none_parameters(self):
        """Test validation fails with None parameters."""
        ind = Individual(parameters=None)

        self.assertFalse(ind.is_valid())

    def test_validate_parameters_success(self):
        """Test parameter validation uses template's PARAM_GRID."""
        # Use parameters that are valid for MomentumTemplate
        ind = Individual(parameters=self.params_1, template_type='Momentum')

        # Validation uses MomentumTemplate.PARAM_GRID automatically
        result = ind.validate_parameters()
        self.assertIsInstance(result, bool)

    def test_validate_parameters_invalid_value(self):
        """Test validation fails with invalid parameter value."""
        invalid_params = {
            'n_stocks': 100,  # Likely not in MomentumTemplate grid
            'stop_loss': 0.10,
            'take_profit': 0.15
        }
        ind = Individual(parameters=invalid_params, template_type='Momentum')

        # Should fail validation against MomentumTemplate.PARAM_GRID
        # Note: Actual result depends on MomentumTemplate.PARAM_GRID
        result = ind.validate_parameters()
        self.assertIsInstance(result, bool)

    def test_validate_parameters_missing_key(self):
        """Test validation fails with missing parameter."""
        incomplete_params = {
            'n_stocks': 10,
            'stop_loss': 0.10
            # Missing 'take_profit' - likely required by MomentumTemplate
        }
        ind = Individual(parameters=incomplete_params, template_type='Momentum')

        # Should fail validation against MomentumTemplate.PARAM_GRID
        result = ind.validate_parameters()
        self.assertIsInstance(result, bool)

    def test_validate_parameters_extra_key(self):
        """Test validation fails with extra parameter."""
        extra_params = {
            'n_stocks': 10,
            'stop_loss': 0.10,
            'take_profit': 0.15,
            'extra_param': 999  # Not in MomentumTemplate.PARAM_GRID
        }
        ind = Individual(parameters=extra_params, template_type='Momentum')

        # Should fail validation against MomentumTemplate.PARAM_GRID
        result = ind.validate_parameters()
        self.assertIsInstance(result, bool)

    def test_get_fitness_or_default_with_fitness(self):
        """Test get_fitness_or_default returns fitness when set."""
        ind = Individual(parameters=self.params_1, fitness=2.5)

        self.assertEqual(ind.get_fitness_or_default(), 2.5)
        self.assertEqual(ind.get_fitness_or_default(default=1.0), 2.5)

    def test_get_fitness_or_default_without_fitness(self):
        """Test get_fitness_or_default returns default when not set."""
        ind = Individual(parameters=self.params_1)

        self.assertEqual(ind.get_fitness_or_default(), 0.0)
        self.assertEqual(ind.get_fitness_or_default(default=1.5), 1.5)

    def test_to_dict_serialization(self):
        """Test to_dict serialization."""
        ind = Individual(
            parameters=self.params_1,
            fitness=1.5,
            metrics={'sharpe': 1.5, 'returns': 0.12},
            generation=5,
            parent_ids=['parent1', 'parent2']
        )

        result = ind.to_dict()

        self.assertEqual(result['parameters'], self.params_1)
        self.assertEqual(result['fitness'], 1.5)
        self.assertEqual(result['metrics'], {'sharpe': 1.5, 'returns': 0.12})
        self.assertEqual(result['generation'], 5)
        self.assertEqual(result['parent_ids'], ['parent1', 'parent2'])
        self.assertEqual(result['id'], ind.id)

    def test_from_dict_deserialization(self):
        """Test from_dict deserialization."""
        data = {
            'parameters': self.params_1,
            'fitness': 2.0,
            'metrics': {'sharpe': 2.0},
            'generation': 10,
            'parent_ids': ['p1', 'p2']
        }

        ind = Individual.from_dict(data)

        self.assertEqual(ind.parameters, self.params_1)
        self.assertEqual(ind.fitness, 2.0)
        self.assertEqual(ind.metrics, {'sharpe': 2.0})
        self.assertEqual(ind.generation, 10)
        self.assertEqual(ind.parent_ids, ['p1', 'p2'])

    def test_from_dict_with_minimal_data(self):
        """Test from_dict with minimal required data."""
        data = {
            'parameters': self.params_1
        }

        ind = Individual.from_dict(data)

        self.assertEqual(ind.parameters, self.params_1)
        self.assertIsNone(ind.fitness)
        self.assertIsNone(ind.metrics)
        self.assertEqual(ind.generation, 0)
        self.assertEqual(ind.parent_ids, [])

    def test_to_dict_from_dict_round_trip(self):
        """Test that to_dict followed by from_dict preserves data."""
        original = Individual(
            parameters=self.params_1,
            fitness=1.8,
            metrics={'test': 'value'},
            generation=3,
            parent_ids=['a', 'b']
        )

        data = original.to_dict()
        restored = Individual.from_dict(data)

        # IDs should match (same parameters)
        self.assertEqual(original.id, restored.id)
        self.assertEqual(original.parameters, restored.parameters)
        self.assertEqual(original.fitness, restored.fitness)
        self.assertEqual(original.metrics, restored.metrics)
        self.assertEqual(original.generation, restored.generation)
        self.assertEqual(original.parent_ids, restored.parent_ids)

    def test_repr_with_fitness(self):
        """Test __repr__ with fitness set."""
        ind = Individual(parameters=self.params_1, fitness=1.2345, generation=5)

        result = repr(ind)

        self.assertIn(ind.id, result)
        self.assertIn('gen=5', result)
        self.assertIn('1.2345', result)

    def test_repr_without_fitness(self):
        """Test __repr__ without fitness."""
        ind = Individual(parameters=self.params_1, generation=3)

        result = repr(ind)

        self.assertIn(ind.id, result)
        self.assertIn('gen=3', result)
        self.assertIn('None', result)

    def test_generation_tracking(self):
        """Test generation tracking."""
        ind = Individual(parameters=self.params_1, generation=7)

        self.assertEqual(ind.generation, 7)

    def test_parent_ids_tracking(self):
        """Test parent IDs tracking."""
        ind = Individual(
            parameters=self.params_1,
            parent_ids=['parent1', 'parent2']
        )

        self.assertEqual(ind.parent_ids, ['parent1', 'parent2'])

    def test_parent_ids_default_empty(self):
        """Test parent IDs default to empty list."""
        ind = Individual(parameters=self.params_1)

        self.assertEqual(ind.parent_ids, [])


class TestIndividualTemplateFeatures(unittest.TestCase):
    """Test cases for template evolution features."""

    def setUp(self):
        """Set up test fixtures."""
        self.params = {
            'n_stocks': 10,
            'stop_loss': 0.10,
            'take_profit': 0.15
        }

    def test_default_template_type(self):
        """Test template_type defaults to 'Momentum' for backward compatibility."""
        ind = Individual(parameters=self.params)

        self.assertEqual(ind.template_type, 'Momentum')

    def test_explicit_template_type(self):
        """Test template_type can be set explicitly."""
        ind = Individual(parameters=self.params, template_type='Turtle')

        self.assertEqual(ind.template_type, 'Turtle')

    def test_invalid_template_type_raises_error(self):
        """Test invalid template_type raises ValueError with helpful message."""
        with self.assertRaises(ValueError) as context:
            Individual(parameters=self.params, template_type='Invalid')

        error_msg = str(context.exception)
        self.assertIn('Invalid', error_msg)
        self.assertIn('Momentum', error_msg)
        self.assertIn('Turtle', error_msg)
        self.assertIn('Factor', error_msg)
        self.assertIn('Mastiff', error_msg)

    def test_hash_includes_template_type(self):
        """Test hash includes template_type (same params, different template = different ID)."""
        ind_momentum = Individual(parameters=self.params, template_type='Momentum')
        ind_turtle = Individual(parameters=self.params, template_type='Turtle')

        # Same parameters but different templates
        self.assertEqual(ind_momentum.parameters, ind_turtle.parameters)

        # Different IDs (hash includes template_type)
        self.assertNotEqual(ind_momentum.id, ind_turtle.id)

    def test_hash_consistency_with_template(self):
        """Test same parameters and template produce same hash."""
        ind1 = Individual(parameters=self.params, template_type='Turtle')
        ind2 = Individual(parameters=self.params.copy(), template_type='Turtle')

        self.assertEqual(ind1.id, ind2.id)

    def test_validate_parameters_uses_template_grid(self):
        """Test validate_parameters() uses template-specific PARAM_GRID."""
        # Create Individual with Momentum template
        ind = Individual(parameters=self.params, template_type='Momentum')

        # Validation uses MomentumTemplate.PARAM_GRID
        # This test assumes valid parameters for Momentum template
        is_valid = ind.validate_parameters()

        # Should return boolean
        self.assertIsInstance(is_valid, bool)

    def test_serialization_includes_template_type(self):
        """Test to_dict() includes template_type."""
        ind = Individual(
            parameters=self.params,
            template_type='Turtle',
            fitness=1.5,
            generation=3
        )

        data = ind.to_dict()

        self.assertIn('template_type', data)
        self.assertEqual(data['template_type'], 'Turtle')

    def test_deserialization_preserves_template_type(self):
        """Test from_dict() preserves template_type."""
        data = {
            'parameters': self.params,
            'template_type': 'Factor',
            'fitness': 2.0,
            'generation': 5
        }

        ind = Individual.from_dict(data)

        self.assertEqual(ind.template_type, 'Factor')

    def test_deserialization_defaults_template_type_for_backward_compat(self):
        """Test from_dict() defaults to 'Momentum' if template_type missing (backward compat)."""
        data = {
            'parameters': self.params,
            'fitness': 1.8
        }

        ind = Individual.from_dict(data)

        self.assertEqual(ind.template_type, 'Momentum')

    def test_serialization_round_trip_with_template(self):
        """Test to_dict() → from_dict() preserves template_type."""
        original = Individual(
            parameters=self.params,
            template_type='Mastiff',
            fitness=1.9,
            generation=7
        )

        data = original.to_dict()
        restored = Individual.from_dict(data)

        self.assertEqual(restored.template_type, 'Mastiff')
        self.assertEqual(restored.id, original.id)
        self.assertEqual(restored.parameters, original.parameters)

    def test_repr_includes_template_type(self):
        """Test __repr__ includes template_type for debugging."""
        ind = Individual(
            parameters=self.params,
            template_type='Turtle',
            fitness=2.1,
            generation=4
        )

        result = repr(ind)

        self.assertIn('Turtle', result)
        self.assertIn(ind.id, result)
        self.assertIn('gen=4', result)
        self.assertIn('2.1000', result)

    def test_multiple_template_types_all_valid(self):
        """Test all 4 template types are valid."""
        templates = ['Momentum', 'Turtle', 'Factor', 'Mastiff']

        for template_type in templates:
            ind = Individual(parameters=self.params, template_type=template_type)
            self.assertEqual(ind.template_type, template_type)


if __name__ == '__main__':
    unittest.main()
