"""
Integration tests for multi-template evolution system.

Tests end-to-end functionality of template evolution across
multiple templates (Momentum, Turtle, Factor, Mastiff).
"""

import unittest
import time
from src.population.population_manager import PopulationManager
from src.population.individual import Individual


class TestMultiTemplatePopulationInitialization(unittest.TestCase):
    """Integration test for multi-template population initialization (Task 35)."""

    def test_equal_distribution_initialization(self):
        """Test multi-template initialization with equal distribution."""
        # Create population manager
        manager = PopulationManager(population_size=100)

        # Measure initialization time
        start_time = time.time()
        population = manager.initialize_population()
        elapsed_time = time.time() - start_time

        # Verify population size
        self.assertEqual(len(population), 100)

        # Count individuals per template
        template_counts = {}
        for ind in population:
            template_counts[ind.template_type] = template_counts.get(ind.template_type, 0) + 1

        # Verify 4 templates present
        self.assertEqual(len(template_counts), 4)
        expected_templates = {'Momentum', 'Turtle', 'Factor', 'Mastiff'}
        self.assertEqual(set(template_counts.keys()), expected_templates)

        # Verify 25 individuals per template (±1 for rounding)
        for template, count in template_counts.items():
            self.assertGreaterEqual(count, 24, f"{template} has {count} individuals, expected 24-26")
            self.assertLessEqual(count, 26, f"{template} has {count} individuals, expected 24-26")

        # Verify all individuals have valid parameters for their template
        for ind in population:
            # Check template_type is set
            self.assertIsNotNone(ind.template_type)
            self.assertIn(ind.template_type, expected_templates)

            # Check parameters exist and are non-empty
            self.assertIsNotNone(ind.parameters)
            self.assertIsInstance(ind.parameters, dict)
            self.assertGreater(len(ind.parameters), 0)

            # Check generation is 0
            self.assertEqual(ind.generation, 0)

        # Verify all individuals are unique
        unique_ids = set(ind.id for ind in population)
        self.assertEqual(len(unique_ids), 100, "All individuals should be unique")

        # Verify population initialization time <2 seconds
        self.assertLess(elapsed_time, 2.0, f"Initialization took {elapsed_time:.3f}s, expected <2s")

        # Print summary for verification
        print(f"\n✅ Multi-template population initialized successfully:")
        print(f"   - Total individuals: {len(population)}")
        print(f"   - Template distribution:")
        for template in sorted(template_counts.keys()):
            count = template_counts[template]
            percentage = (count / len(population)) * 100
            print(f"     • {template}: {count} ({percentage:.1f}%)")
        print(f"   - Unique individuals: {len(unique_ids)}")
        print(f"   - Initialization time: {elapsed_time:.3f}s")

    def test_weighted_distribution_initialization(self):
        """Test multi-template initialization with weighted distribution."""
        manager = PopulationManager(population_size=100)

        # Custom distribution
        distribution = {
            'Momentum': 0.4,   # 40 individuals
            'Turtle': 0.3,     # 30 individuals
            'Factor': 0.2,     # 20 individuals
            'Mastiff': 0.1     # 10 individuals
        }

        # Measure initialization time
        start_time = time.time()
        population = manager.initialize_population(template_distribution=distribution)
        elapsed_time = time.time() - start_time

        # Verify population size
        self.assertEqual(len(population), 100)

        # Count individuals per template
        template_counts = {}
        for ind in population:
            template_counts[ind.template_type] = template_counts.get(ind.template_type, 0) + 1

        # Verify expected counts
        self.assertEqual(template_counts.get('Momentum', 0), 40)
        self.assertEqual(template_counts.get('Turtle', 0), 30)
        self.assertEqual(template_counts.get('Factor', 0), 20)
        self.assertEqual(template_counts.get('Mastiff', 0), 10)

        # Verify all individuals have valid parameters
        for ind in population:
            self.assertIsNotNone(ind.template_type)
            self.assertIsNotNone(ind.parameters)
            self.assertIsInstance(ind.parameters, dict)
            self.assertGreater(len(ind.parameters), 0)

        # Verify performance
        self.assertLess(elapsed_time, 2.0, f"Initialization took {elapsed_time:.3f}s, expected <2s")

        # Print summary
        print(f"\n✅ Weighted distribution initialized successfully:")
        print(f"   - Momentum: {template_counts.get('Momentum', 0)} (target 40)")
        print(f"   - Turtle: {template_counts.get('Turtle', 0)} (target 30)")
        print(f"   - Factor: {template_counts.get('Factor', 0)} (target 20)")
        print(f"   - Mastiff: {template_counts.get('Mastiff', 0)} (target 10)")
        print(f"   - Initialization time: {elapsed_time:.3f}s")

    def test_template_specific_parameters(self):
        """Test that each template uses its own parameter grid."""
        manager = PopulationManager(population_size=100)
        population = manager.initialize_population()

        # Group by template
        by_template = {}
        for ind in population:
            if ind.template_type not in by_template:
                by_template[ind.template_type] = []
            by_template[ind.template_type].append(ind)

        # Verify each template has individuals with unique parameter combinations
        for template_type, individuals in by_template.items():
            # Extract unique parameter sets
            param_sets = set()
            for ind in individuals:
                # Convert params dict to frozenset for hashing
                param_tuple = frozenset(ind.parameters.items())
                param_sets.add(param_tuple)

            # Should have high diversity within each template
            diversity_ratio = len(param_sets) / len(individuals)
            self.assertGreater(
                diversity_ratio,
                0.8,
                f"{template_type} has low diversity: {diversity_ratio:.2f}"
            )

            print(f"\n✅ {template_type} template:")
            print(f"   - Individuals: {len(individuals)}")
            print(f"   - Unique parameter sets: {len(param_sets)}")
            print(f"   - Diversity ratio: {diversity_ratio:.2%}")


class TestMultiTemplate10GenerationEvolution(unittest.TestCase):
    """E2E test for 10-generation multi-template evolution (Task 37)."""

    def test_10_generation_multi_template_evolution(self):
        """
        Run 10 generations with 40 individuals (10 per template).

        Verifies:
        - All templates represented in final population (≥5% each)
        - Template mutation occurred (lineage tracking)
        - Champion identified with template_type
        - EvolutionMonitor tracks template distribution
        """
        from src.population.genetic_operators import GeneticOperators
        from src.population.fitness_evaluator import FitnessEvaluator
        from src.population.evolution_monitor import EvolutionMonitor
        from unittest.mock import MagicMock

        # Initialize components
        manager = PopulationManager(population_size=40)
        operators = GeneticOperators(
            base_mutation_rate=0.15,
            template_mutation_rate=0.05  # 5% template mutation
        )
        monitor = EvolutionMonitor()

        # Mock FitnessEvaluator for testing (assign random fitness)
        import random
        evaluator = MagicMock()

        def mock_evaluate(individual):
            individual.fitness = random.uniform(0.5, 2.5)
            individual.metrics = {
                'sharpe_ratio': individual.fitness,
                'annual_return': random.uniform(0.1, 0.3),
                'max_drawdown': random.uniform(-0.2, -0.1)
            }
            return individual

        evaluator.evaluate = mock_evaluate
        evaluator.evaluate_population = lambda pop: [mock_evaluate(ind) for ind in pop]

        # Create initial population (10 per template)
        distribution = {
            'Momentum': 0.25,
            'Turtle': 0.25,
            'Factor': 0.25,
            'Mastiff': 0.25
        }
        population = manager.initialize_population(template_distribution=distribution)

        # Verify initial distribution
        initial_counts = {}
        for ind in population:
            initial_counts[ind.template_type] = initial_counts.get(ind.template_type, 0) + 1

        print(f"\n✅ Initial population (gen 0):")
        for template in sorted(initial_counts.keys()):
            print(f"   - {template}: {initial_counts[template]}")

        # Evaluate initial population
        population = evaluator.evaluate_population(population)

        # Track template mutations
        template_mutation_count = 0

        # Run 10 generations
        for generation in range(10):
            # Calculate diversity
            diversity = manager.calculate_diversity(population)

            # Record generation
            monitor.record_generation(
                generation_num=generation,
                population=population,
                diversity=diversity,
                cache_stats={'hit_rate': 0.5, 'cache_size': generation * 10}
            )

            # Update champion
            best_individual = max(population, key=lambda ind: ind.fitness)
            champion_updated = monitor.update_champion(best_individual)

            # Create next generation
            offspring = []
            for _ in range(manager.population_size):
                parent1 = manager.select_parent(population)
                parent2 = manager.select_parent(population)

                # Crossover
                child1, child2 = operators.crossover(parent1, parent2, generation + 1)

                # Mutate
                child1 = operators.mutate(child1, generation + 1)

                # Track template mutations
                if child1.template_type != parent1.template_type:
                    template_mutation_count += 1

                offspring.append(child1)
                if len(offspring) < manager.population_size:
                    offspring.append(child2)

            # Trim to population size
            offspring = offspring[:manager.population_size]

            # Evaluate offspring
            offspring = evaluator.evaluate_population(offspring)

            # Apply elitism
            population = manager.apply_elitism(population, offspring)

        # Record final generation (generation 10)
        final_diversity = manager.calculate_diversity(population)
        monitor.record_generation(
            generation_num=10,
            population=population,
            diversity=final_diversity,
            cache_stats={'hit_rate': 0.5, 'cache_size': 100}
        )

        # Update champion with final population
        final_best = max(population, key=lambda ind: ind.fitness)
        monitor.update_champion(final_best)

        # Final generation stats
        final_counts = {}
        for ind in population:
            final_counts[ind.template_type] = final_counts.get(ind.template_type, 0) + 1

        print(f"\n✅ Final population (gen 10):")
        for template in sorted(final_counts.keys()):
            count = final_counts[template]
            percentage = (count / len(population)) * 100
            print(f"   - {template}: {count} ({percentage:.1f}%)")

        # Verify all templates represented (≥5% each)
        for template in distribution.keys():
            count = final_counts.get(template, 0)
            percentage = (count / len(population)) * 100
            self.assertGreaterEqual(
                percentage,
                5.0,
                f"{template} has {percentage:.1f}%, expected ≥5%"
            )

        # Verify template mutation occurred
        self.assertGreater(
            template_mutation_count,
            0,
            "Expected at least one template mutation across 10 generations"
        )
        print(f"   - Template mutations: {template_mutation_count}")

        # Verify champion identified with template_type
        champion = monitor.get_champion()
        self.assertIsNotNone(champion)
        self.assertIsNotNone(champion.template_type)
        self.assertIn(champion.template_type, distribution.keys())
        print(f"   - Champion template: {champion.template_type}")
        print(f"   - Champion fitness: {champion.fitness:.4f}")

        # Verify EvolutionMonitor tracks template distribution
        template_summary = monitor.get_template_summary()
        self.assertEqual(len(template_summary['template_progression']), 11)  # Generations 0-10
        self.assertIsNotNone(template_summary['dominant_template'])

        # Final template distribution should exist
        final_dist = template_summary['final_template_distribution']
        self.assertEqual(len(final_dist), len(final_counts))

        print(f"   - Dominant template: {template_summary['dominant_template']}")
        print(f"   - Template diversity: {template_summary['template_diversity_history'][-1]:.2f}")

        # Get summary stats
        summary = monitor.get_summary()
        print(f"\n✅ Evolution summary:")
        print(f"   - Total generations: {summary['total_generations']}")
        print(f"   - Champion updates: {summary['champion_updates_count']}")
        print(f"   - Final avg fitness: {summary['avg_fitness']:.4f}")
        print(f"   - Final diversity: {summary['final_diversity']:.4f}")

        # Success criteria verification
        self.assertEqual(summary['total_generations'], 11)  # Generations 0-10
        self.assertGreater(summary['champion_updates_count'], 0)


if __name__ == '__main__':
    unittest.main()
