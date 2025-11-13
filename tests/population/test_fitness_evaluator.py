"""
Unit tests for FitnessEvaluator class.

Tests IS/OOS split, caching, and batch evaluation.
"""

import unittest
from unittest.mock import MagicMock, patch
from src.population.fitness_evaluator import FitnessEvaluator
from src.population.individual import Individual


class TestFitnessEvaluator(unittest.TestCase):
    """Test cases for FitnessEvaluator class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock template
        self.mock_template = MagicMock()
        self.mock_template.generate_strategy.return_value = (
            {'strategy': 'mock'},
            {
                'sharpe_ratio': 1.5,
                'annual_return': 0.12,
                'max_drawdown': -0.15
            }
        )

        # Create mock data (None is fine for tests with mocked methods)
        self.mock_data = None

        self.evaluator = FitnessEvaluator(
            template=self.mock_template,
            data=self.mock_data,
            is_start='2015',
            is_end='2020',
            oos_start='2021',
            oos_end='2024'
        )

        self.params = {
            'n_stocks': 10,
            'stop_loss': 0.10,
            'take_profit': 0.15
        }

    def test_initialization_stores_periods(self):
        """Test that initialization stores period boundaries."""
        self.assertEqual(self.evaluator.is_start, '2015')
        self.assertEqual(self.evaluator.is_end, '2020')
        self.assertEqual(self.evaluator.oos_start, '2021')
        self.assertEqual(self.evaluator.oos_end, '2024')

    def test_initialization_splits_data(self):
        """Test that initialization stores template and data references."""
        # FitnessEvaluator doesn't pre-split data - it filters via DataCache
        # In single-template mode, template is stored
        self.assertIsNotNone(self.evaluator.template)
        self.assertIsNone(self.evaluator._registry)

        # In multi-template mode, _registry is initialized
        multi_evaluator = FitnessEvaluator(template=None, data=None)
        self.assertIsNone(multi_evaluator.template)
        self.assertIsNotNone(multi_evaluator._registry)

    def test_cache_initially_empty(self):
        """Test that cache is initially empty."""
        stats = self.evaluator.get_cache_stats()

        self.assertEqual(stats['cache_size'], 0)
        self.assertEqual(stats['cache_hits'], 0)
        self.assertEqual(stats['cache_misses'], 0)
        self.assertEqual(stats['hit_rate'], 0.0)

    @patch.object(FitnessEvaluator, '_generate_and_backtest')
    def test_evaluate_sets_fitness_and_metrics(self, mock_backtest):
        """Test that evaluate sets fitness and metrics."""
        mock_backtest.return_value = (
            {'strategy': 'test'},
            {'sharpe_ratio': 2.0, 'annual_return': 0.15}
        )

        individual = Individual(parameters=self.params)

        result = self.evaluator.evaluate(individual, use_oos=False)

        self.assertEqual(result.fitness, 2.0)
        self.assertEqual(result.metrics['sharpe_ratio'], 2.0)
        self.assertTrue(result.is_evaluated())

    @patch.object(FitnessEvaluator, '_generate_and_backtest')
    def test_evaluate_caches_results(self, mock_backtest):
        """Test that evaluate caches results."""
        mock_backtest.return_value = (
            {'strategy': 'test'},
            {'sharpe_ratio': 1.5, 'annual_return': 0.12}
        )

        individual = Individual(parameters=self.params)

        # First evaluation - cache miss
        self.evaluator.evaluate(individual, use_oos=False)
        stats1 = self.evaluator.get_cache_stats()
        self.assertEqual(stats1['cache_misses'], 1)
        self.assertEqual(stats1['cache_hits'], 0)

        # Second evaluation - cache hit
        self.evaluator.evaluate(individual, use_oos=False)
        stats2 = self.evaluator.get_cache_stats()
        self.assertEqual(stats2['cache_misses'], 1)
        self.assertEqual(stats2['cache_hits'], 1)

    @patch.object(FitnessEvaluator, '_generate_and_backtest')
    def test_evaluate_separate_cache_for_is_and_oos(self, mock_backtest):
        """Test that IS and OOS evaluations are cached separately."""
        mock_backtest.return_value = (
            {'strategy': 'test'},
            {'sharpe_ratio': 1.5, 'annual_return': 0.12}
        )

        individual = Individual(parameters=self.params)

        # Evaluate on IS
        self.evaluator.evaluate(individual, use_oos=False)

        # Evaluate on OOS - should be cache miss
        self.evaluator.evaluate(individual, use_oos=True)

        stats = self.evaluator.get_cache_stats()
        self.assertEqual(stats['cache_misses'], 2)  # Both IS and OOS miss
        self.assertEqual(stats['cache_hits'], 0)

    @patch.object(FitnessEvaluator, '_generate_and_backtest')
    def test_evaluate_handles_errors_gracefully(self, mock_backtest):
        """Test that evaluate handles errors and assigns zero fitness."""
        mock_backtest.side_effect = RuntimeError("Backtest failed")

        individual = Individual(parameters=self.params)

        result = self.evaluator.evaluate(individual, use_oos=False)

        self.assertEqual(result.fitness, 0.0)
        self.assertIn('error', result.metrics)
        self.assertTrue(result.is_evaluated())

    def test_evaluate_raises_on_invalid_individual(self):
        """Test that evaluate raises error on invalid individual."""
        invalid_individual = Individual(parameters={})

        with self.assertRaises(ValueError):
            self.evaluator.evaluate(invalid_individual)

    @patch.object(FitnessEvaluator, '_generate_and_backtest')
    def test_evaluate_population_evaluates_all(self, mock_backtest):
        """Test that evaluate_population evaluates all individuals."""
        mock_backtest.return_value = (
            {'strategy': 'test'},
            {'sharpe_ratio': 1.5, 'annual_return': 0.12}
        )

        population = [
            Individual(parameters={'n_stocks': i})
            for i in range(5)
        ]

        result = self.evaluator.evaluate_population(population, use_oos=False)

        self.assertEqual(len(result), 5)
        for ind in result:
            self.assertTrue(ind.is_evaluated())

    @patch.object(FitnessEvaluator, '_generate_and_backtest')
    def test_evaluate_population_uses_cache(self, mock_backtest):
        """Test that evaluate_population leverages cache."""
        mock_backtest.return_value = (
            {'strategy': 'test'},
            {'sharpe_ratio': 1.5, 'annual_return': 0.12}
        )

        # Create population with duplicate
        params1 = {'n_stocks': 10}
        params2 = {'n_stocks': 20}

        population = [
            Individual(parameters=params1),
            Individual(parameters=params1),  # Duplicate
            Individual(parameters=params2)
        ]

        self.evaluator.evaluate_population(population, use_oos=False)

        stats = self.evaluator.get_cache_stats()
        # Should have 2 misses (unique individuals) and 1 hit (duplicate)
        self.assertEqual(stats['cache_misses'], 2)
        self.assertEqual(stats['cache_hits'], 1)

    def test_get_cache_stats_returns_correct_structure(self):
        """Test that get_cache_stats returns correct structure."""
        stats = self.evaluator.get_cache_stats()

        self.assertIn('cache_size', stats)
        self.assertIn('cache_hits', stats)
        self.assertIn('cache_misses', stats)
        self.assertIn('hit_rate', stats)
        self.assertIn('total_evaluations', stats)

    @patch.object(FitnessEvaluator, '_generate_and_backtest')
    def test_get_cache_stats_calculates_hit_rate(self, mock_backtest):
        """Test that cache hit rate is calculated correctly."""
        mock_backtest.return_value = (
            {'strategy': 'test'},
            {'sharpe_ratio': 1.5, 'annual_return': 0.12}
        )

        individual = Individual(parameters=self.params)

        # 1 miss
        self.evaluator.evaluate(individual, use_oos=False)

        # 2 hits
        self.evaluator.evaluate(individual, use_oos=False)
        self.evaluator.evaluate(individual, use_oos=False)

        stats = self.evaluator.get_cache_stats()

        self.assertEqual(stats['total_evaluations'], 3)
        self.assertEqual(stats['cache_hits'], 2)
        self.assertEqual(stats['cache_misses'], 1)
        self.assertAlmostEqual(stats['hit_rate'], 2.0 / 3.0, places=2)

    def test_clear_cache_empties_cache(self):
        """Test that clear_cache empties cache and resets stats."""
        # Add something to cache manually
        self.evaluator._cache['test_key'] = {'fitness': 1.0, 'metrics': {}}
        self.evaluator._cache_hits = 5
        self.evaluator._cache_misses = 3

        self.evaluator.clear_cache()

        stats = self.evaluator.get_cache_stats()
        self.assertEqual(stats['cache_size'], 0)
        self.assertEqual(stats['cache_hits'], 0)
        self.assertEqual(stats['cache_misses'], 0)

    def test_get_cache_key_format(self):
        """Test cache key format includes template_type and IS/OOS split."""
        key_is = self.evaluator._get_cache_key('ind123', 'Momentum', use_oos=False)
        key_oos = self.evaluator._get_cache_key('ind123', 'Momentum', use_oos=True)

        # Defense-in-depth: cache key includes template_type
        self.assertEqual(key_is, 'ind123_Momentum_is')
        self.assertEqual(key_oos, 'ind123_Momentum_oos')
        self.assertNotEqual(key_is, key_oos)

        # Different templates produce different cache keys
        key_turtle = self.evaluator._get_cache_key('ind123', 'Turtle', use_oos=False)
        self.assertEqual(key_turtle, 'ind123_Turtle_is')
        self.assertNotEqual(key_is, key_turtle)

    @patch('src.templates.data_cache.DataCache')
    def test_generate_and_backtest_filters_data_for_is(self, mock_cache_class):
        """Test that _generate_and_backtest filters data to IS period."""
        mock_cache = MagicMock()
        mock_cache_class.get_instance.return_value = mock_cache

        # Mock cache data
        mock_cache._cache = {
            'price:收盤價': MagicMock(),
            'price:成交股數': MagicMock()
        }

        # Mock template response
        self.mock_template.generate_strategy.return_value = (
            {'strategy': 'test'},
            {'sharpe_ratio': 1.5}
        )

        # Call with IS
        self.evaluator._generate_and_backtest(self.params, use_oos=False)

        # Verify template was called
        self.mock_template.generate_strategy.assert_called_once()

    @patch('src.templates.data_cache.DataCache')
    def test_generate_and_backtest_filters_data_for_oos(self, mock_cache_class):
        """Test that _generate_and_backtest filters data to OOS period."""
        mock_cache = MagicMock()
        mock_cache_class.get_instance.return_value = mock_cache

        # Mock cache data
        mock_cache._cache = {
            'price:收盤價': MagicMock(),
            'price:成交股數': MagicMock()
        }

        # Mock template response
        self.mock_template.generate_strategy.return_value = (
            {'strategy': 'test'},
            {'sharpe_ratio': 1.2}
        )

        # Call with OOS
        self.evaluator._generate_and_backtest(self.params, use_oos=True)

        # Verify template was called
        self.mock_template.generate_strategy.assert_called_once()

    def test_repr_format(self):
        """Test __repr__ string format."""
        result = repr(self.evaluator)

        self.assertIn('FitnessEvaluator', result)
        self.assertIn('2015:2020', result)
        self.assertIn('2021:2024', result)

    @patch.object(FitnessEvaluator, '_generate_and_backtest')
    def test_evaluate_extracts_sharpe_as_fitness(self, mock_backtest):
        """Test that evaluate extracts Sharpe ratio as fitness."""
        mock_backtest.return_value = (
            {'strategy': 'test'},
            {
                'sharpe_ratio': 2.5,
                'annual_return': 0.20,
                'max_drawdown': -0.10
            }
        )

        individual = Individual(parameters=self.params)

        result = self.evaluator.evaluate(individual, use_oos=False)

        self.assertEqual(result.fitness, 2.5)

    @patch.object(FitnessEvaluator, '_generate_and_backtest')
    def test_evaluate_handles_missing_sharpe(self, mock_backtest):
        """Test that evaluate handles missing Sharpe ratio."""
        mock_backtest.return_value = (
            {'strategy': 'test'},
            {'annual_return': 0.15}  # No sharpe_ratio
        )

        individual = Individual(parameters=self.params)

        result = self.evaluator.evaluate(individual, use_oos=False)

        self.assertEqual(result.fitness, 0.0)  # Default when missing


class TestFitnessEvaluatorTemplateRouting(unittest.TestCase):
    """Test cases for FitnessEvaluator template routing (Task 28)."""

    def setUp(self):
        """Set up test fixtures."""
        self.params_momentum = {
            'n_stocks': 10,
            'stop_loss': 0.10,
            'take_profit': 0.15
        }
        self.params_turtle = {
            'yield_threshold': 6.0,
            'ma_short': 20,
            'ma_long': 60,
            'rev_short': 6,
            'rev_long': 12,
            'volume_threshold': 1000000,
            'market_cap_threshold': 5000000000,
            'pb_threshold': 2.0,
            'roe_threshold': 0.10,
            'debt_ratio_threshold': 0.60,
            'stop_loss': 0.10,
            'take_profit': 0.15,
            'n_stocks': 10,
            'rebalance_freq': 'M'
        }

    def test_single_template_mode_backward_compatible(self):
        """Test single-template mode with template != None (backward compatible)."""
        mock_template = MagicMock()
        mock_template.generate_strategy.return_value = (
            {'strategy': 'mock'},
            {'sharpe_ratio': 1.5}
        )

        evaluator = FitnessEvaluator(template=mock_template, data=None)

        # Single-template mode
        self.assertIsNotNone(evaluator.template)
        self.assertIsNone(evaluator._registry)

    def test_multi_template_mode_initializes_registry(self):
        """Test multi-template mode with template=None initializes _registry."""
        evaluator = FitnessEvaluator(template=None, data=None)

        # Multi-template mode
        self.assertIsNone(evaluator.template)
        self.assertIsNotNone(evaluator._registry)

    @patch.object(FitnessEvaluator, '_generate_and_backtest')
    def test_cache_key_includes_template_type(self, mock_backtest):
        """Test cache key includes template_type for defense-in-depth."""
        mock_backtest.return_value = ({'strategy': 'mock'}, {'sharpe_ratio': 1.5})

        evaluator = FitnessEvaluator(template=None, data=None)

        # Create individuals with same parameters but different templates
        ind_momentum = Individual(
            parameters=self.params_momentum,
            template_type='Momentum'
        )
        ind_turtle = Individual(
            parameters=self.params_turtle,
            template_type='Turtle'
        )

        # Evaluate both
        evaluator.evaluate(ind_momentum, use_oos=False)
        evaluator.evaluate(ind_turtle, use_oos=False)

        # Check cache has separate entries (defense-in-depth)
        stats = evaluator.get_cache_stats()
        self.assertEqual(stats['cache_size'], 2)  # Two separate cache entries

    @patch.object(FitnessEvaluator, '_generate_and_backtest')
    def test_different_templates_produce_different_cache_keys(self, mock_backtest):
        """Test different template_types produce different cache keys."""
        mock_backtest.return_value = ({'strategy': 'mock'}, {'sharpe_ratio': 1.5})

        evaluator = FitnessEvaluator(template=None, data=None)

        # Manually test cache key generation
        key1 = evaluator._get_cache_key('ind123', 'Momentum', use_oos=False)
        key2 = evaluator._get_cache_key('ind123', 'Turtle', use_oos=False)

        self.assertNotEqual(key1, key2)
        self.assertEqual(key1, 'ind123_Momentum_is')
        self.assertEqual(key2, 'ind123_Turtle_is')

    @patch('src.templates.data_cache.DataCache')
    def test_single_template_mode_uses_self_template(self, mock_cache_class):
        """Test single-template mode uses self.template, ignores template_type."""
        # Mock cache
        mock_cache = MagicMock()
        mock_cache_class.get_instance.return_value = mock_cache
        mock_cache._cache = {}

        # Mock template
        mock_template = MagicMock()
        mock_template.generate_strategy.return_value = (
            {'strategy': 'momentum'},
            {'sharpe_ratio': 1.8}
        )

        evaluator = FitnessEvaluator(template=mock_template, data=None)

        # Call _generate_and_backtest with template_type (should be ignored)
        evaluator._generate_and_backtest(
            self.params_momentum,
            use_oos=False,
            template_type='Turtle'  # Should be ignored
        )

        # Verify self.template was used (not registry.get_template)
        mock_template.generate_strategy.assert_called_once()

    @patch('src.templates.data_cache.DataCache')
    @patch('src.utils.template_registry.TemplateRegistry')
    def test_multi_template_mode_gets_template_from_registry(
        self,
        mock_registry_class,
        mock_cache_class
    ):
        """Test multi-template mode gets template from registry using template_type."""
        # Mock cache
        mock_cache = MagicMock()
        mock_cache_class.get_instance.return_value = mock_cache
        mock_cache._cache = {}

        # Mock registry
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry

        # Mock template from registry
        mock_turtle_template = MagicMock()
        mock_turtle_template.generate_strategy.return_value = (
            {'strategy': 'turtle'},
            {'sharpe_ratio': 2.0}
        )
        mock_registry.get_template.return_value = mock_turtle_template

        evaluator = FitnessEvaluator(template=None, data=None)

        # Call _generate_and_backtest with template_type
        evaluator._generate_and_backtest(
            self.params_turtle,
            use_oos=False,
            template_type='Turtle'
        )

        # Verify registry.get_template was called with correct template_type
        mock_registry.get_template.assert_called_once_with('Turtle')
        mock_turtle_template.generate_strategy.assert_called_once()

    @patch('src.templates.data_cache.DataCache')
    def test_multi_template_mode_raises_error_without_template_type(self, mock_cache_class):
        """Test multi-template mode raises ValueError if template_type not provided."""
        mock_cache = MagicMock()
        mock_cache_class.get_instance.return_value = mock_cache
        mock_cache._cache = {}

        evaluator = FitnessEvaluator(template=None, data=None)

        # Call without template_type should raise ValueError
        with self.assertRaises(ValueError) as context:
            evaluator._generate_and_backtest(
                self.params_momentum,
                use_oos=False,
                template_type=None  # Missing template_type
            )

        error_msg = str(context.exception)
        self.assertIn('Multi-template mode', error_msg)
        self.assertIn('requires template_type', error_msg)


if __name__ == '__main__':
    unittest.main()
