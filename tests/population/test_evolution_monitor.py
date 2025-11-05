"""
Unit tests for EvolutionMonitor class.

Tests generation statistics, champion tracking, and summary generation.
"""

import unittest
from src.population.evolution_monitor import EvolutionMonitor
from src.population.individual import Individual


class TestEvolutionMonitor(unittest.TestCase):
    """Test cases for EvolutionMonitor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = EvolutionMonitor()

    def test_initialization_empty_state(self):
        """Test that monitor initializes with empty state."""
        self.assertEqual(len(self.monitor.generation_stats), 0)
        self.assertEqual(len(self.monitor.champion_history), 0)
        self.assertIsNone(self.monitor.current_champion)

    def test_record_generation_stores_statistics(self):
        """Test that record_generation stores generation statistics."""
        population = [
            Individual(parameters={'n_stocks': i}, fitness=float(i))
            for i in range(10)
        ]

        cache_stats = {'hit_rate': 0.5, 'cache_size': 100}

        self.monitor.record_generation(
            generation_num=1,
            population=population,
            diversity=0.8,
            cache_stats=cache_stats
        )

        self.assertEqual(len(self.monitor.generation_stats), 1)
        stats = self.monitor.generation_stats[0]

        self.assertEqual(stats['generation'], 1)
        self.assertEqual(stats['diversity'], 0.8)
        self.assertEqual(stats['cache_hit_rate'], 0.5)
        self.assertEqual(stats['cache_size'], 100)
        self.assertIn('best_fitness', stats)
        self.assertIn('avg_fitness', stats)

    def test_record_generation_calculates_fitness_stats(self):
        """Test that record_generation calculates fitness statistics."""
        population = [
            Individual(parameters={'n_stocks': i}, fitness=float(i))
            for i in range(1, 6)  # Fitness: 1, 2, 3, 4, 5
        ]

        self.monitor.record_generation(
            generation_num=0,
            population=population,
            diversity=1.0,
            cache_stats={'hit_rate': 0.0, 'cache_size': 0}
        )

        stats = self.monitor.generation_stats[0]

        self.assertEqual(stats['best_fitness'], 5.0)
        self.assertEqual(stats['min_fitness'], 1.0)
        self.assertEqual(stats['avg_fitness'], 3.0)
        self.assertGreater(stats['std_fitness'], 0)

    def test_record_generation_raises_on_empty_population(self):
        """Test that record_generation raises error on empty population."""
        with self.assertRaises(ValueError):
            self.monitor.record_generation(
                generation_num=0,
                population=[],
                diversity=0.0,
                cache_stats={}
            )

    def test_record_generation_raises_on_unevaluated_population(self):
        """Test that record_generation raises error if no evaluated individuals."""
        population = [
            Individual(parameters={'n_stocks': i})
            for i in range(5)
        ]

        with self.assertRaises(ValueError):
            self.monitor.record_generation(
                generation_num=0,
                population=population,
                diversity=1.0,
                cache_stats={}
            )

    def test_update_champion_first_individual(self):
        """Test that first individual becomes champion."""
        individual = Individual(parameters={'n_stocks': 10}, fitness=1.5)

        updated = self.monitor.update_champion(individual)

        self.assertTrue(updated)
        self.assertEqual(self.monitor.current_champion, individual)
        self.assertEqual(len(self.monitor.champion_history), 1)

    def test_update_champion_better_individual(self):
        """Test that better individual updates champion."""
        ind1 = Individual(parameters={'n_stocks': 10}, fitness=1.5)
        ind2 = Individual(parameters={'n_stocks': 20}, fitness=2.0)

        self.monitor.update_champion(ind1)
        updated = self.monitor.update_champion(ind2)

        self.assertTrue(updated)
        self.assertEqual(self.monitor.current_champion, ind2)
        self.assertEqual(len(self.monitor.champion_history), 2)

    def test_update_champion_worse_individual(self):
        """Test that worse individual doesn't update champion."""
        ind1 = Individual(parameters={'n_stocks': 10}, fitness=2.0)
        ind2 = Individual(parameters={'n_stocks': 20}, fitness=1.5)

        self.monitor.update_champion(ind1)
        updated = self.monitor.update_champion(ind2)

        self.assertFalse(updated)
        self.assertEqual(self.monitor.current_champion, ind1)
        self.assertEqual(len(self.monitor.champion_history), 1)

    def test_update_champion_equal_fitness(self):
        """Test that equal fitness doesn't update champion."""
        ind1 = Individual(parameters={'n_stocks': 10}, fitness=1.5)
        ind2 = Individual(parameters={'n_stocks': 20}, fitness=1.5)

        self.monitor.update_champion(ind1)
        updated = self.monitor.update_champion(ind2)

        self.assertFalse(updated)
        self.assertEqual(self.monitor.current_champion, ind1)
        self.assertEqual(len(self.monitor.champion_history), 1)

    def test_update_champion_raises_on_unevaluated(self):
        """Test that update_champion raises error on unevaluated individual."""
        individual = Individual(parameters={'n_stocks': 10})

        with self.assertRaises(ValueError):
            self.monitor.update_champion(individual)

    def test_get_champion_returns_current(self):
        """Test that get_champion returns current champion."""
        individual = Individual(parameters={'n_stocks': 10}, fitness=1.5)

        self.monitor.update_champion(individual)

        self.assertEqual(self.monitor.get_champion(), individual)

    def test_get_champion_returns_none_initially(self):
        """Test that get_champion returns None when no champion."""
        self.assertIsNone(self.monitor.get_champion())

    def test_get_champion_update_rate_zero_initially(self):
        """Test that update rate is zero initially."""
        rate = self.monitor.get_champion_update_rate()

        self.assertEqual(rate, 0.0)

    def test_get_champion_update_rate_calculation(self):
        """Test champion update rate calculation."""
        # Record 5 generations
        for gen in range(5):
            population = [
                Individual(parameters={'n_stocks': i}, fitness=float(i))
                for i in range(10)
            ]
            self.monitor.record_generation(
                generation_num=gen,
                population=population,
                diversity=0.8,
                cache_stats={'hit_rate': 0.5, 'cache_size': 100}
            )

        # Update champion 2 times
        self.monitor.update_champion(
            Individual(parameters={'n_stocks': 1}, fitness=1.0)
        )
        self.monitor.update_champion(
            Individual(parameters={'n_stocks': 2}, fitness=2.0)
        )

        rate = self.monitor.get_champion_update_rate()

        # 2 updates / 5 generations = 0.4
        self.assertAlmostEqual(rate, 0.4, places=2)

    def test_get_summary_empty_state(self):
        """Test that get_summary handles empty state."""
        summary = self.monitor.get_summary()

        self.assertEqual(summary['total_generations'], 0)
        self.assertEqual(summary['champion_updates_count'], 0)
        self.assertEqual(summary['champion_update_rate'], 0.0)
        self.assertIsNone(summary['best_fitness'])
        self.assertEqual(summary['avg_fitness_progression'], [])
        self.assertEqual(summary['diversity_progression'], [])
        self.assertIsNone(summary['final_champion'])

    def test_get_summary_with_history(self):
        """Test that get_summary generates comprehensive report."""
        # Record multiple generations
        for gen in range(3):
            population = [
                Individual(parameters={'n_stocks': i}, fitness=float(i + gen))
                for i in range(5)
            ]
            self.monitor.record_generation(
                generation_num=gen,
                population=population,
                diversity=0.8 - gen * 0.1,
                cache_stats={'hit_rate': 0.5 + gen * 0.1, 'cache_size': 100 + gen * 10}
            )

            # Update champion each generation
            best = max(population, key=lambda x: x.fitness)
            self.monitor.update_champion(best)

        summary = self.monitor.get_summary()

        self.assertEqual(summary['total_generations'], 3)
        self.assertEqual(summary['champion_updates_count'], 3)
        self.assertEqual(summary['champion_update_rate'], 1.0)
        self.assertEqual(summary['best_fitness'], 6.0)  # 4 + 2
        self.assertEqual(len(summary['avg_fitness_progression']), 3)
        self.assertEqual(len(summary['diversity_progression']), 3)
        self.assertIsNotNone(summary['final_champion'])

    def test_get_summary_includes_cache_performance(self):
        """Test that summary includes cache performance metrics."""
        # Record generations with varying cache stats
        for gen in range(3):
            population = [
                Individual(parameters={'n_stocks': i}, fitness=float(i))
                for i in range(5)
            ]
            self.monitor.record_generation(
                generation_num=gen,
                population=population,
                diversity=0.8,
                cache_stats={'hit_rate': 0.5 + gen * 0.1, 'cache_size': 100 + gen * 50}
            )

        summary = self.monitor.get_summary()

        self.assertIn('cache_performance', summary)
        self.assertIn('avg_hit_rate', summary['cache_performance'])
        self.assertIn('final_cache_size', summary['cache_performance'])

        # Average hit rate: (0.5 + 0.6 + 0.7) / 3 = 0.6
        self.assertAlmostEqual(
            summary['cache_performance']['avg_hit_rate'],
            0.6,
            places=2
        )
        # Final cache size: 100 + 2*50 = 200
        self.assertEqual(summary['cache_performance']['final_cache_size'], 200)

    def test_get_summary_includes_champion_lineage(self):
        """Test that summary includes champion lineage."""
        # Create champions with parent tracking
        champ1 = Individual(
            parameters={'n_stocks': 10},
            fitness=1.0,
            parent_ids=[]
        )
        champ2 = Individual(
            parameters={'n_stocks': 20},
            fitness=2.0,
            parent_ids=[champ1.id]
        )

        # Record generation first
        population = [champ1, champ2]
        self.monitor.record_generation(
            generation_num=0,
            population=population,
            diversity=1.0,
            cache_stats={'hit_rate': 0.0, 'cache_size': 0}
        )

        self.monitor.update_champion(champ1)
        self.monitor.update_champion(champ2)

        summary = self.monitor.get_summary()

        self.assertEqual(len(summary['champion_lineage']), 2)
        self.assertEqual(summary['champion_lineage'][0], [])
        self.assertEqual(summary['champion_lineage'][1], [champ1.id])

    def test_get_generation_stats_retrieves_specific_generation(self):
        """Test that get_generation_stats retrieves specific generation."""
        # Record multiple generations
        for gen in range(3):
            population = [
                Individual(parameters={'n_stocks': i}, fitness=float(i))
                for i in range(5)
            ]
            self.monitor.record_generation(
                generation_num=gen,
                population=population,
                diversity=0.8,
                cache_stats={'hit_rate': 0.5, 'cache_size': 100}
            )

        # Retrieve generation 1
        stats = self.monitor.get_generation_stats(1)

        self.assertIsNotNone(stats)
        self.assertEqual(stats['generation'], 1)

    def test_get_generation_stats_returns_none_if_not_found(self):
        """Test that get_generation_stats returns None if not found."""
        stats = self.monitor.get_generation_stats(999)

        self.assertIsNone(stats)

    def test_get_champion_history_returns_copy(self):
        """Test that get_champion_history returns copy of history."""
        champ1 = Individual(parameters={'n_stocks': 10}, fitness=1.0)
        champ2 = Individual(parameters={'n_stocks': 20}, fitness=2.0)

        self.monitor.update_champion(champ1)
        self.monitor.update_champion(champ2)

        history = self.monitor.get_champion_history()

        # Modify returned list
        history.append(Individual(parameters={'n_stocks': 30}, fitness=3.0))

        # Original should be unchanged
        self.assertEqual(len(self.monitor.champion_history), 2)

    def test_repr_format(self):
        """Test __repr__ string format."""
        # Add some data
        population = [
            Individual(parameters={'n_stocks': i}, fitness=float(i))
            for i in range(5)
        ]
        self.monitor.record_generation(
            generation_num=0,
            population=population,
            diversity=0.8,
            cache_stats={'hit_rate': 0.5, 'cache_size': 100}
        )
        self.monitor.update_champion(population[-1])

        result = repr(self.monitor)

        self.assertIn('EvolutionMonitor', result)
        self.assertIn('generations=1', result)
        self.assertIn('champion_updates=1', result)

    def test_multiple_generations_progression(self):
        """Test tracking progression across multiple generations."""
        # Simulate 5 generations with improving fitness
        for gen in range(5):
            population = [
                Individual(
                    parameters={'n_stocks': i},
                    fitness=float(i + gen * 2)
                )
                for i in range(10)
            ]

            self.monitor.record_generation(
                generation_num=gen,
                population=population,
                diversity=0.9 - gen * 0.1,
                cache_stats={'hit_rate': 0.3 + gen * 0.1, 'cache_size': 50 + gen * 25}
            )

            # Update champion
            best = max(population, key=lambda x: x.fitness)
            self.monitor.update_champion(best)

        summary = self.monitor.get_summary()

        # Verify progression tracking
        self.assertEqual(len(summary['avg_fitness_progression']), 5)
        self.assertEqual(len(summary['diversity_progression']), 5)

        # Check diversity is decreasing
        diversity_prog = summary['diversity_progression']
        self.assertGreater(diversity_prog[0], diversity_prog[-1])

        # Check fitness is improving
        avg_fitness_prog = summary['avg_fitness_progression']
        self.assertLess(avg_fitness_prog[0], avg_fitness_prog[-1])


class TestEvolutionMonitorTemplateTracking(unittest.TestCase):
    """Test cases for EvolutionMonitor template tracking (Task 29)."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = EvolutionMonitor()
        self.params = {'n_stocks': 10, 'stop_loss': 0.10, 'take_profit': 0.15}

    def test_calculate_diversity_all_same_template(self):
        """Test unified diversity with all same template (backward compatible)."""
        # All Momentum template
        population = [
            Individual(parameters=self.params, template_type='Momentum', fitness=1.0 + i * 0.1)
            for i in range(10)
        ]

        param_diversity = 0.6
        unified_diversity = EvolutionMonitor.calculate_diversity(population, param_diversity)

        # When all same template, template_diversity = 0
        # Result should equal param_diversity (backward compatible)
        self.assertAlmostEqual(unified_diversity, param_diversity, places=4)

    def test_calculate_diversity_mixed_templates(self):
        """Test unified diversity with mixed templates."""
        # 50% Momentum, 50% Turtle (perfect split)
        population = (
            [Individual(parameters=self.params, template_type='Momentum', fitness=1.0)] * 5 +
            [Individual(parameters=self.params, template_type='Turtle', fitness=1.1)] * 5
        )

        param_diversity = 0.5
        unified_diversity = EvolutionMonitor.calculate_diversity(population, param_diversity)

        # Template diversity should be 1.0 (max for 2 templates perfectly split)
        # Unified = 0.7*0.5 + 0.3*1.0 = 0.35 + 0.3 = 0.65
        expected = 0.7 * param_diversity + 0.3 * 1.0
        self.assertAlmostEqual(unified_diversity, expected, places=4)

    def test_calculate_diversity_four_templates_perfect_split(self):
        """Test unified diversity with 4 templates perfectly distributed."""
        # 25% each template (perfect distribution)
        population = (
            [Individual(parameters=self.params, template_type='Momentum', fitness=1.0)] * 25 +
            [Individual(parameters=self.params, template_type='Turtle', fitness=1.1)] * 25 +
            [Individual(parameters=self.params, template_type='Factor', fitness=1.2)] * 25 +
            [Individual(parameters=self.params, template_type='Mastiff', fitness=1.3)] * 25
        )

        param_diversity = 0.4
        unified_diversity = EvolutionMonitor.calculate_diversity(population, param_diversity)

        # Template diversity should be 1.0 (max for 4 templates perfectly split)
        # Unified = 0.7*0.4 + 0.3*1.0 = 0.28 + 0.3 = 0.58
        expected = 0.7 * param_diversity + 0.3 * 1.0
        self.assertAlmostEqual(unified_diversity, expected, places=4)

    def test_calculate_diversity_empty_population(self):
        """Test unified diversity with empty population."""
        population = []
        param_diversity = 0.5

        unified_diversity = EvolutionMonitor.calculate_diversity(population, param_diversity)
        self.assertEqual(unified_diversity, 0.0)

    def test_record_generation_tracks_template_counts(self):
        """Test record_generation tracks template_counts."""
        population = [
            Individual(parameters=self.params, template_type='Momentum', fitness=1.0),
            Individual(parameters=self.params, template_type='Momentum', fitness=1.1),
            Individual(parameters=self.params, template_type='Turtle', fitness=1.2),
        ]

        self.monitor.record_generation(
            generation_num=0,
            population=population,
            diversity=0.5,
            cache_stats={'hit_rate': 0.8, 'cache_size': 10}
        )

        stats = self.monitor.get_generation_stats(0)
        self.assertIn('template_counts', stats)
        self.assertEqual(stats['template_counts']['Momentum'], 2)
        self.assertEqual(stats['template_counts']['Turtle'], 1)

    def test_record_generation_tracks_template_distribution(self):
        """Test record_generation tracks template_distribution."""
        population = [
            Individual(parameters=self.params, template_type='Momentum', fitness=1.0),
            Individual(parameters=self.params, template_type='Momentum', fitness=1.1),
            Individual(parameters=self.params, template_type='Turtle', fitness=1.2),
            Individual(parameters=self.params, template_type='Turtle', fitness=1.3),
        ]

        self.monitor.record_generation(
            generation_num=0,
            population=population,
            diversity=0.6,
            cache_stats={'hit_rate': 0.7, 'cache_size': 15}
        )

        stats = self.monitor.get_generation_stats(0)
        self.assertIn('template_distribution', stats)
        self.assertAlmostEqual(stats['template_distribution']['Momentum'], 0.5, places=4)
        self.assertAlmostEqual(stats['template_distribution']['Turtle'], 0.5, places=4)

    def test_get_template_summary_empty_state(self):
        """Test get_template_summary with no generations recorded."""
        summary = self.monitor.get_template_summary()

        self.assertEqual(summary['template_progression'], [])
        self.assertEqual(summary['final_template_distribution'], {})
        self.assertEqual(summary['template_diversity_history'], [])
        self.assertIsNone(summary['dominant_template'])
        self.assertEqual(summary['template_stability'], 0.0)

    def test_get_template_summary_single_generation(self):
        """Test get_template_summary with single generation."""
        population = [
            Individual(parameters=self.params, template_type='Momentum', fitness=1.0),
            Individual(parameters=self.params, template_type='Turtle', fitness=1.1),
        ]

        self.monitor.record_generation(
            generation_num=0,
            population=population,
            diversity=0.7,
            cache_stats={'hit_rate': 0.5, 'cache_size': 5}
        )

        summary = self.monitor.get_template_summary()

        # Template progression
        self.assertEqual(len(summary['template_progression']), 1)
        self.assertIn('Momentum', summary['template_progression'][0])
        self.assertIn('Turtle', summary['template_progression'][0])

        # Final distribution
        self.assertAlmostEqual(summary['final_template_distribution']['Momentum'], 0.5)
        self.assertAlmostEqual(summary['final_template_distribution']['Turtle'], 0.5)

        # Diversity history
        self.assertEqual(len(summary['template_diversity_history']), 1)
        self.assertAlmostEqual(summary['template_diversity_history'][0], 1.0, places=4)

        # Dominant template
        self.assertIn(summary['dominant_template'], ['Momentum', 'Turtle'])

        # Stability (single generation = perfect stability)
        self.assertEqual(summary['template_stability'], 1.0)

    def test_get_template_summary_template_evolution(self):
        """Test get_template_summary tracks template evolution over generations."""
        # Gen 0: 100% Momentum
        pop0 = [Individual(parameters=self.params, template_type='Momentum', fitness=1.0 + i * 0.1) for i in range(10)]
        self.monitor.record_generation(0, pop0, 0.5, {'hit_rate': 0.5, 'cache_size': 10})

        # Gen 1: 70% Momentum, 30% Turtle
        pop1 = (
            [Individual(parameters=self.params, template_type='Momentum', fitness=1.0 + i * 0.1) for i in range(7)] +
            [Individual(parameters=self.params, template_type='Turtle', fitness=1.5 + i * 0.1) for i in range(3)]
        )
        self.monitor.record_generation(1, pop1, 0.6, {'hit_rate': 0.6, 'cache_size': 15})

        # Gen 2: 50% Momentum, 50% Turtle
        pop2 = (
            [Individual(parameters=self.params, template_type='Momentum', fitness=1.0 + i * 0.1) for i in range(5)] +
            [Individual(parameters=self.params, template_type='Turtle', fitness=1.5 + i * 0.1) for i in range(5)]
        )
        self.monitor.record_generation(2, pop2, 0.7, {'hit_rate': 0.7, 'cache_size': 20})

        summary = self.monitor.get_template_summary()

        # Verify progression
        self.assertEqual(len(summary['template_progression']), 3)

        # Gen 0 should be 100% Momentum
        self.assertAlmostEqual(summary['template_progression'][0]['Momentum'], 1.0)

        # Gen 2 should be 50% split
        self.assertAlmostEqual(summary['template_progression'][2]['Momentum'], 0.5)
        self.assertAlmostEqual(summary['template_progression'][2]['Turtle'], 0.5)

        # Diversity should increase over generations (0 -> 1.0)
        self.assertAlmostEqual(summary['template_diversity_history'][0], 0.0, places=2)
        self.assertAlmostEqual(summary['template_diversity_history'][2], 1.0, places=2)

        # Template stability should be low (diversity changing)
        self.assertLess(summary['template_stability'], 1.0)

    def test_get_template_summary_dominant_template_identification(self):
        """Test get_template_summary identifies dominant template."""
        # 80% Momentum, 20% Turtle
        population = (
            [Individual(parameters=self.params, template_type='Momentum', fitness=1.0)] * 8 +
            [Individual(parameters=self.params, template_type='Turtle', fitness=1.1)] * 2
        )

        self.monitor.record_generation(0, population, 0.4, {'hit_rate': 0.6, 'cache_size': 12})

        summary = self.monitor.get_template_summary()

        # Dominant template should be Momentum
        self.assertEqual(summary['dominant_template'], 'Momentum')


if __name__ == '__main__':
    unittest.main()
