"""
Evolution monitoring and statistics tracking for genetic algorithm.

Tracks generation statistics, champion history, and cache performance.
"""

import statistics
import math
from typing import List, Dict, Optional, Any
from collections import Counter
from src.population.individual import Individual


class EvolutionMonitor:
    """
    Monitor and track evolutionary algorithm progress.

    Tracks:
        - Generation-level statistics (fitness, diversity, cache)
        - Champion history and update rate
        - Summary metrics and insights

    Attributes:
        generation_stats: List of statistics dictionaries per generation
        champion_history: List of all champions throughout evolution
        current_champion: Current best individual
    """

    def __init__(self):
        """Initialize evolution monitor with empty tracking structures."""
        self.generation_stats: List[Dict] = []
        self.champion_history: List[Individual] = []
        self.current_champion: Optional[Individual] = None

    @staticmethod
    def calculate_diversity(
        population: List[Individual],
        param_diversity: float
    ) -> float:
        """
        Calculate unified diversity combining parameter and template diversity.

        Formula: diversity = 0.7 * param_diversity + 0.3 * template_diversity

        Template diversity is measured using Shannon entropy normalized to [0, 1].
        When all individuals use the same template, template_diversity = 0 and
        the result equals param_diversity (backward compatible).

        Args:
            population: List of individuals to calculate diversity for
            param_diversity: Parameter diversity score from genetic operators (0.0-1.0)

        Returns:
            float: Unified diversity score (0.0-1.0)

        Example:
            >>> # All same template (backward compatible)
            >>> pop = [Individual(params={'n': 10}, template_type='Momentum')] * 10
            >>> diversity = EvolutionMonitor.calculate_diversity(pop, param_div=0.6)
            >>> assert diversity == 0.6  # 0.7*0.6 + 0.3*0.0

            >>> # Mixed templates
            >>> pop = [Individual(..., template_type='Momentum')] * 5 + \
            ...       [Individual(..., template_type='Turtle')] * 5
            >>> diversity = EvolutionMonitor.calculate_diversity(pop, param_div=0.5)
            >>> assert diversity > 0.5  # Includes template diversity
        """
        if not population:
            return 0.0

        # Calculate template diversity using Shannon entropy
        template_counts = Counter(ind.template_type for ind in population)
        total = len(population)

        # Shannon entropy calculation
        entropy = 0.0
        for count in template_counts.values():
            if count > 0:
                prob = count / total
                entropy -= prob * math.log2(prob)

        # Normalize entropy to [0, 1]
        # Max entropy = log2(num_templates) when perfectly distributed
        # For 4 templates: max_entropy = log2(4) = 2.0
        max_entropy = math.log2(len(template_counts)) if len(template_counts) > 1 else 0.0
        template_diversity = entropy / max_entropy if max_entropy > 0 else 0.0

        # Backward compatibility: if only 1 template type, return param_diversity directly
        if len(template_counts) == 1:
            return param_diversity

        # Weighted combination: 70% parameter, 30% template
        unified_diversity = 0.7 * param_diversity + 0.3 * template_diversity

        return unified_diversity

    def record_generation(
        self,
        generation_num: int,
        population: List[Individual],
        diversity: float,
        cache_stats: Dict[str, Any]
    ) -> None:
        """
        Record statistics for a generation.

        Args:
            generation_num: Current generation number
            population: Current population of individuals
            diversity: Population diversity score (0.0-1.0)
            cache_stats: Dictionary with 'hit_rate' and 'cache_size'

        Note:
            All individuals in population must be evaluated (fitness not None)
        """
        # Validate inputs
        if not population:
            raise ValueError("Population cannot be empty")

        evaluated_pop = [ind for ind in population if ind.is_evaluated()]
        if not evaluated_pop:
            raise ValueError("No evaluated individuals in population")

        # Calculate generation statistics
        gen_stats = self._calculate_generation_stats(population)

        # Track template distribution (Task 26)
        template_counts = Counter(ind.template_type for ind in population)
        template_distribution = {
            template: count / len(population)
            for template, count in template_counts.items()
        }

        gen_stats.update({
            'generation': generation_num,
            'diversity': diversity,
            'cache_hit_rate': cache_stats.get('hit_rate', 0.0),
            'cache_size': cache_stats.get('cache_size', 0),
            'template_counts': dict(template_counts),
            'template_distribution': template_distribution
        })

        self.generation_stats.append(gen_stats)

    def update_champion(self, individual: Individual) -> bool:
        """
        Update champion if new individual is better.

        Args:
            individual: Individual to compare against current champion

        Returns:
            bool: True if champion was updated, False otherwise

        Raises:
            ValueError: If individual is not evaluated
        """
        if not individual.is_evaluated():
            raise ValueError("Individual must be evaluated before becoming champion")

        # First champion
        if self.current_champion is None:
            self.current_champion = individual
            self.champion_history.append(individual)
            return True

        # Check if new champion
        if individual.fitness > self.current_champion.fitness:
            self.current_champion = individual
            self.champion_history.append(individual)
            return True

        return False

    def get_champion(self) -> Optional[Individual]:
        """
        Get current champion.

        Returns:
            Optional[Individual]: Current champion or None if no champion yet
        """
        return self.current_champion

    def get_champion_update_rate(self) -> float:
        """
        Calculate champion update rate.

        Returns:
            float: Ratio of champion updates to total generations (0.0-1.0)

        Note:
            Returns 0.0 if no generations recorded
        """
        if not self.generation_stats:
            return 0.0

        total_generations = len(self.generation_stats)
        champion_updates = len(self.champion_history)

        return champion_updates / total_generations

    def get_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive summary report.

        Returns:
            Dict containing:
                - total_generations: Number of generations
                - champion_updates_count: Number of champion updates
                - champion_update_rate: Update rate ratio
                - best_fitness: Best fitness achieved
                - avg_fitness_progression: List of avg fitness per generation
                - diversity_progression: List of diversity per generation
                - cache_performance: Dict with avg hit rate and final size
                - champion_lineage: List of champion parent IDs
                - final_champion: Current champion dict representation
        """
        if not self.generation_stats:
            return {
                'total_generations': 0,
                'champion_updates_count': 0,
                'champion_update_rate': 0.0,
                'best_fitness': None,
                'avg_fitness_progression': [],
                'diversity_progression': [],
                'cache_performance': {
                    'avg_hit_rate': 0.0,
                    'final_cache_size': 0
                },
                'champion_lineage': [],
                'final_champion': None
            }

        # Extract progressions
        avg_fitness_progression = [
            stats['avg_fitness'] for stats in self.generation_stats
        ]
        diversity_progression = [
            stats['diversity'] for stats in self.generation_stats
        ]

        # Calculate cache performance
        cache_hit_rates = [
            stats.get('cache_hit_rate', 0.0) for stats in self.generation_stats
        ]
        avg_cache_hit_rate = statistics.mean(cache_hit_rates) if cache_hit_rates else 0.0
        final_cache_size = self.generation_stats[-1].get('cache_size', 0)

        # Extract champion lineage
        champion_lineage = [
            champion.parent_ids for champion in self.champion_history
        ]

        return {
            'total_generations': len(self.generation_stats),
            'champion_updates_count': len(self.champion_history),
            'champion_update_rate': self.get_champion_update_rate(),
            'best_fitness': self.current_champion.fitness if self.current_champion else None,
            'avg_fitness': avg_fitness_progression[-1] if avg_fitness_progression else 0.0,
            'final_diversity': diversity_progression[-1] if diversity_progression else 0.0,
            'avg_cache_hit_rate': avg_cache_hit_rate,
            'avg_fitness_progression': avg_fitness_progression,
            'diversity_progression': diversity_progression,
            'cache_performance': {
                'avg_hit_rate': avg_cache_hit_rate,
                'final_cache_size': final_cache_size
            },
            'champion_lineage': champion_lineage,
            'final_champion': self.current_champion.to_dict() if self.current_champion else None
        }

    def _calculate_generation_stats(self, population: List[Individual]) -> Dict[str, float]:
        """
        Calculate fitness statistics for current generation.

        Args:
            population: List of individuals (must have fitness values)

        Returns:
            Dict with 'best_fitness', 'avg_fitness', 'min_fitness', 'std_fitness'

        Note:
            Only evaluates individuals with fitness values
        """
        evaluated_pop = [ind for ind in population if ind.is_evaluated()]

        if not evaluated_pop:
            return {
                'best_fitness': 0.0,
                'avg_fitness': 0.0,
                'min_fitness': 0.0,
                'std_fitness': 0.0
            }

        fitness_values = [ind.fitness for ind in evaluated_pop]

        return {
            'best_fitness': max(fitness_values),
            'avg_fitness': statistics.mean(fitness_values),
            'min_fitness': min(fitness_values),
            'std_fitness': statistics.stdev(fitness_values) if len(fitness_values) > 1 else 0.0
        }

    def get_generation_stats(self, generation_num: int) -> Optional[Dict]:
        """
        Get statistics for specific generation.

        Args:
            generation_num: Generation number to retrieve

        Returns:
            Optional[Dict]: Generation statistics or None if not found
        """
        for stats in self.generation_stats:
            if stats['generation'] == generation_num:
                return stats
        return None

    def get_champion_history(self) -> List[Individual]:
        """
        Get full champion history.

        Returns:
            List[Individual]: All champions throughout evolution
        """
        return self.champion_history.copy()

    def get_template_summary(self) -> Dict[str, Any]:
        """
        Generate template evolution summary (Task 27).

        Returns:
            Dict containing:
                - template_progression: List of template distributions per generation
                - final_template_distribution: Current template distribution
                - template_diversity_history: List of template diversity scores
                - dominant_template: Most common template in final generation
                - template_stability: How stable template distribution is

        Example:
            >>> summary = monitor.get_template_summary()
            >>> print(summary['final_template_distribution'])
            {'Momentum': 0.4, 'Turtle': 0.3, 'Factor': 0.2, 'Mastiff': 0.1}
        """
        if not self.generation_stats:
            return {
                'template_progression': [],
                'final_template_distribution': {},
                'template_diversity_history': [],
                'dominant_template': None,
                'template_stability': 0.0
            }

        # Extract template distribution progression
        template_progression = [
            stats.get('template_distribution', {})
            for stats in self.generation_stats
        ]

        # Calculate template diversity history using Shannon entropy
        template_diversity_history = []
        for stats in self.generation_stats:
            template_dist = stats.get('template_distribution', {})
            if template_dist:
                # Shannon entropy
                entropy = 0.0
                for prob in template_dist.values():
                    if prob > 0:
                        entropy -= prob * math.log2(prob)

                # Normalize to [0, 1]
                max_entropy = math.log2(len(template_dist)) if len(template_dist) > 1 else 0.0
                diversity = entropy / max_entropy if max_entropy > 0 else 0.0
                template_diversity_history.append(diversity)
            else:
                template_diversity_history.append(0.0)

        # Get final distribution
        final_distribution = self.generation_stats[-1].get('template_distribution', {})

        # Determine dominant template
        dominant_template = None
        if final_distribution:
            dominant_template = max(final_distribution, key=final_distribution.get)

        # Calculate template stability (variance of template distributions)
        # Lower variance = more stable
        if len(template_diversity_history) > 1:
            template_stability = 1.0 - statistics.stdev(template_diversity_history)
        else:
            template_stability = 1.0

        return {
            'template_progression': template_progression,
            'final_template_distribution': final_distribution,
            'template_diversity_history': template_diversity_history,
            'dominant_template': dominant_template,
            'template_stability': max(0.0, template_stability)  # Ensure non-negative
        }

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            str: Human-readable representation
        """
        gen_count = len(self.generation_stats)
        champion_count = len(self.champion_history)
        update_rate = self.get_champion_update_rate()
        best_fitness = self.current_champion.fitness if self.current_champion else None

        return (
            f"EvolutionMonitor("
            f"generations={gen_count}, "
            f"champion_updates={champion_count}, "
            f"update_rate={update_rate:.2%}, "
            f"best_fitness={best_fitness})"
        )
