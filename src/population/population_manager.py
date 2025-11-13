"""
Population management for evolutionary learning.

Handles population initialization, selection, elitism, diversity tracking,
and convergence detection.
"""

import random
from typing import List, Dict, Any, Optional
from src.population.individual import Individual
from src.utils.template_registry import TemplateRegistry


class PopulationManager:
    """
    Manage population lifecycle in evolutionary algorithm.

    Responsibilities:
        - Population initialization with diversity guarantee
        - Parent selection via tournament selection
        - Elitism strategy implementation
        - Diversity calculation and monitoring
        - Convergence detection with dual criteria
    """

    def __init__(
        self,
        population_size: int = 50,
        elite_size: int = 5,
        tournament_size: int = 2,
        diversity_threshold: float = 0.5,
        convergence_window: int = 10
    ):
        """
        Initialize population manager.

        Args:
            population_size: Number of individuals in population (default: 50)
            elite_size: Number of elites to preserve (default: 5, 10% of population)
            tournament_size: Tournament size for selection (default: 2)
            diversity_threshold: Minimum diversity to avoid convergence (default: 0.5)
            convergence_window: Generations to check for convergence (default: 10)
        """
        self.population_size = population_size
        self.elite_size = elite_size
        self.tournament_size = tournament_size
        self.diversity_threshold = diversity_threshold
        self.convergence_window = convergence_window

        # Convergence tracking state
        self._diversity_history: List[float] = []
        self._best_fitness_history: List[float] = []

    def initialize_population(
        self,
        param_grid: Optional[Dict[str, List[Any]]] = None,
        seed_parameters: Optional[List[Dict[str, Any]]] = None,
        template_distribution: Optional[Dict[str, float]] = None
    ) -> List[Individual]:
        """
        Initialize population with template distribution support.

        Modes:
            - Single-template (backward compatible): param_grid provided, template_distribution=None
              All individuals use default template_type='Momentum'

            - Multi-template (new): param_grid=None, template_distribution configures proportions
              Equal distribution: template_distribution=None → 25% each (4 templates)
              Weighted distribution: template_distribution={'Momentum': 0.4, 'Turtle': 0.6, ...}

        Strategy:
            1. Determine template distribution (equal or weighted)
            2. Calculate individual counts per template
            3. Add seed parameters if provided (preserve champions)
            4. Generate random unique individuals per template
            5. Guarantee all individuals have unique parameter sets

        Args:
            param_grid: (DEPRECATED) Single-template mode parameter grid
                       Use template_distribution instead for multi-template
            seed_parameters: Optional list of parameter dictionaries to include
                           (useful for preserving champion during restarts)
            template_distribution: Optional template distribution configuration
                - None: Equal distribution (25% each for 4 templates)
                - Dict: Custom proportions (must sum to 1.0 within 1e-6 tolerance)
                Example: {'Momentum': 0.4, 'Turtle': 0.3, 'Factor': 0.2, 'Mastiff': 0.1}

        Returns:
            List[Individual]: Population with exactly population_size individuals,
                            all with unique parameter combinations (diversity = 1.0)

        Raises:
            ValueError: If distribution validation fails or template names invalid
            RuntimeError: If failed to generate unique population

        Example:
            >>> # Equal distribution (25% each template)
            >>> manager = PopulationManager(population_size=100)
            >>> population = manager.initialize_population()

            >>> # Weighted distribution
            >>> distribution = {'Momentum': 0.5, 'Turtle': 0.3, 'Factor': 0.2}
            >>> population = manager.initialize_population(template_distribution=distribution)
        """
        registry = TemplateRegistry.get_instance()

        # Task 32: Template distribution logic
        if template_distribution is None:
            # Equal distribution: 25% each for 4 templates
            available_templates = registry.get_available_templates()
            template_distribution = {
                template: 1.0 / len(available_templates)
                for template in available_templates
            }
        else:
            # Validate custom distribution
            total = sum(template_distribution.values())
            if abs(total - 1.0) > 1e-6:
                raise ValueError(
                    f"Template distribution must sum to 1.0, got {total:.10f}"
                )

            # Validate all template names
            for template_name in template_distribution.keys():
                if not registry.validate_template_type(template_name):
                    available = registry.get_available_templates()
                    raise ValueError(
                        f"Invalid template name '{template_name}'. "
                        f"Available templates: {available}"
                    )

        # Calculate individual counts per template
        template_counts = {}
        assigned_total = 0

        # Sort templates alphabetically for deterministic rounding
        sorted_templates = sorted(template_distribution.keys())

        for template in sorted_templates:
            proportion = template_distribution[template]
            count = int(self.population_size * proportion)
            template_counts[template] = count
            assigned_total += count

        # Handle rounding: assign remainder to first template alphabetically
        remainder = self.population_size - assigned_total
        if remainder > 0:
            template_counts[sorted_templates[0]] += remainder

        # Task 33: Per-template individual creation
        population: List[Individual] = []
        seen_ids: set[str] = set()

        # Add seed parameters first (if provided)
        if seed_parameters:
            for params in seed_parameters:
                # Infer template_type from params or default to Momentum
                template_type = params.get('template_type', 'Momentum')
                individual = Individual(
                    parameters=params,
                    template_type=template_type,
                    generation=0
                )
                if individual.id not in seen_ids:
                    population.append(individual)
                    seen_ids.add(individual.id)

        # Generate individuals per template
        for template_type, count in template_counts.items():
            # Get template-specific parameter grid
            param_grid_for_template = registry.get_param_grid(template_type)

            # Calculate how many individuals already created for this template
            existing_count = sum(
                1 for ind in population if ind.template_type == template_type
            )
            target_count = count
            remaining_count = target_count - existing_count

            # Generate remaining individuals for this template
            max_attempts = remaining_count * 100  # Prevent infinite loops
            attempts = 0
            created = 0

            while created < remaining_count and attempts < max_attempts:
                # Generate random parameter combination from template's grid
                params = {
                    param_name: random.choice(param_values)
                    for param_name, param_values in param_grid_for_template.items()
                }

                individual = Individual(
                    parameters=params,
                    template_type=template_type,
                    generation=0
                )

                # Only add if unique
                if individual.id not in seen_ids:
                    population.append(individual)
                    seen_ids.add(individual.id)
                    created += 1

                attempts += 1

            # Verify we created enough individuals for this template
            if created < remaining_count:
                raise RuntimeError(
                    f"Failed to generate {remaining_count} unique individuals for template '{template_type}'. "
                    f"Only generated {created} unique combinations. "
                    f"Consider expanding parameter grid or reducing population size."
                )

        # Verify total population size
        if len(population) != self.population_size:
            raise RuntimeError(
                f"Population size mismatch. Expected {self.population_size}, got {len(population)}"
            )

        # Final validation: diversity should be 1.0 (100% unique)
        diversity = self.calculate_diversity(population)
        if diversity < 0.99:  # Allow small floating point tolerance
            raise RuntimeError(
                f"Population initialization failed diversity guarantee. "
                f"Expected 1.0, got {diversity:.4f}"
            )

        return population

    def select_parent(self, population: List[Individual]) -> Individual:
        """
        Select parent using tournament selection.

        Strategy:
            1. Randomly select tournament_size individuals from population
            2. Return the individual with highest fitness

        Args:
            population: List of evaluated individuals (must have fitness values)

        Returns:
            Individual: Selected parent with highest fitness in tournament

        Raises:
            ValueError: If population is empty or individuals not evaluated
        """
        if not population:
            raise ValueError("Cannot select parent from empty population")

        # Verify all individuals are evaluated
        if not all(ind.is_evaluated() for ind in population):
            raise ValueError("Cannot select parent: some individuals not evaluated")

        # Select random tournament
        tournament = random.sample(population, min(self.tournament_size, len(population)))

        # Return individual with highest fitness
        return max(tournament, key=lambda ind: ind.fitness)

    def apply_elitism(
        self,
        current_population: List[Individual],
        offspring: List[Individual]
    ) -> List[Individual]:
        """
        Combine elites from current generation with top offspring.

        Strategy:
            1. Sort current_population by fitness (descending)
            2. Take top elite_size individuals as elites
            3. Sort offspring by fitness (descending)
            4. Take top (population_size - elite_size) offspring
            5. Combine elites + selected offspring = next generation

        Note: This method assumes both current_population and offspring are
              fully evaluated (have fitness values).

        Args:
            current_population: Current generation (all evaluated)
            offspring: New offspring (all evaluated)

        Returns:
            List[Individual]: Next generation with exactly population_size individuals

        Raises:
            ValueError: If populations not evaluated or wrong size
        """
        # Validate inputs
        if not current_population:
            raise ValueError("Current population cannot be empty")

        if not all(ind.is_evaluated() for ind in current_population):
            raise ValueError("Current population must be fully evaluated")

        if not all(ind.is_evaluated() for ind in offspring):
            raise ValueError("Offspring must be fully evaluated")

        # Sort current population by fitness (descending)
        sorted_current = sorted(
            current_population,
            key=lambda ind: ind.fitness,
            reverse=True
        )

        # Select top elite_size individuals as elites
        elites = sorted_current[:self.elite_size]

        # Sort offspring by fitness (descending)
        sorted_offspring = sorted(
            offspring,
            key=lambda ind: ind.fitness,
            reverse=True
        )

        # Calculate how many offspring to select
        remaining_slots = self.population_size - self.elite_size
        selected_offspring = sorted_offspring[:remaining_slots]

        # Combine elites + selected offspring
        next_generation = elites + selected_offspring

        # Validate output size
        if len(next_generation) != self.population_size:
            raise RuntimeError(
                f"Elitism produced wrong population size. "
                f"Expected {self.population_size}, got {len(next_generation)}"
            )

        return next_generation

    def calculate_diversity(self, population: List[Individual]) -> float:
        """
        Calculate population diversity as proportion of unique individuals.

        Diversity = (number of unique parameter combinations) / population_size

        Args:
            population: List of individuals

        Returns:
            float: Diversity score in range [0.0, 1.0]
                  1.0 = all individuals unique (100% diversity)
                  0.0 = all individuals identical (0% diversity)

        Raises:
            ValueError: If population is empty
        """
        if not population:
            raise ValueError("Cannot calculate diversity of empty population")

        # Count unique parameter combinations using Individual IDs
        unique_ids = len(set(ind.id for ind in population))

        # Calculate diversity ratio
        diversity = unique_ids / len(population)

        return diversity

    def check_convergence(self, population: List[Individual]) -> bool:
        """
        Check if population has converged using dual criteria.

        Convergence requires BOTH criteria to be met:
            1. Diversity < diversity_threshold for convergence_window consecutive generations
            2. Best fitness unchanged for (2 * convergence_window) consecutive generations

        This dual-criteria approach prevents false convergence from temporary plateaus.

        Args:
            population: Current population (must be evaluated)

        Returns:
            bool: True if converged (both criteria met), False otherwise

        Raises:
            ValueError: If population empty or not evaluated
        """
        if not population:
            raise ValueError("Cannot check convergence on empty population")

        if not all(ind.is_evaluated() for ind in population):
            raise ValueError("Cannot check convergence: population not evaluated")

        # Calculate current diversity
        current_diversity = self.calculate_diversity(population)
        self._diversity_history.append(current_diversity)

        # Get best fitness in current generation
        best_fitness = max(ind.fitness for ind in population)
        self._best_fitness_history.append(best_fitness)

        # Need enough history to check convergence
        if len(self._diversity_history) < self.convergence_window:
            return False

        if len(self._best_fitness_history) < 2 * self.convergence_window:
            return False

        # Criterion 1: Diversity < threshold for convergence_window generations
        recent_diversity = self._diversity_history[-self.convergence_window:]
        diversity_converged = all(d < self.diversity_threshold for d in recent_diversity)

        # Criterion 2: Best fitness unchanged for 2 * convergence_window generations
        recent_fitness = self._best_fitness_history[-2 * self.convergence_window:]
        fitness_plateau = len(set(recent_fitness)) == 1  # All values identical

        # Convergence requires BOTH criteria
        converged = diversity_converged and fitness_plateau

        return converged

    def reset_convergence_tracking(self) -> None:
        """
        Reset convergence tracking state.

        Call this method after a convergence restart to begin tracking from scratch.
        """
        self._diversity_history = []
        self._best_fitness_history = []

    def get_convergence_status(self) -> Dict[str, Any]:
        """
        Get current convergence tracking status (useful for debugging/monitoring).

        Returns:
            Dict: Convergence status including:
                - current_diversity: Latest diversity value
                - current_best_fitness: Latest best fitness
                - diversity_history_length: Number of generations tracked
                - diversity_below_threshold_count: Consecutive gens with low diversity
                - fitness_plateau_count: Consecutive gens with unchanged best fitness
        """
        if not self._diversity_history:
            return {
                'current_diversity': None,
                'current_best_fitness': None,
                'diversity_history_length': 0,
                'diversity_below_threshold_count': 0,
                'fitness_plateau_count': 0
            }

        # Count consecutive generations with diversity below threshold
        diversity_below_count = 0
        for d in reversed(self._diversity_history):
            if d < self.diversity_threshold:
                diversity_below_count += 1
            else:
                break

        # Count consecutive generations with unchanged fitness
        fitness_plateau_count = 0
        if len(self._best_fitness_history) >= 2:
            last_fitness = self._best_fitness_history[-1]
            for fitness in reversed(self._best_fitness_history[:-1]):
                if fitness == last_fitness:
                    fitness_plateau_count += 1
                else:
                    break

        return {
            'current_diversity': self._diversity_history[-1],
            'current_best_fitness': self._best_fitness_history[-1],
            'diversity_history_length': len(self._diversity_history),
            'diversity_below_threshold_count': diversity_below_count,
            'fitness_plateau_count': fitness_plateau_count
        }
