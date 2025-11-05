"""
Genetic operators for evolutionary population learning.

Implements mutation and crossover operations with adaptive parameters.
"""

from typing import Dict, List, Any, Tuple
import random
import copy
from src.population.individual import Individual


class GeneticOperators:
    """
    Genetic operators with adaptive mutation rate and template evolution.

    Implements mutation and crossover operations for evolutionary algorithms:
    - Mutation: Randomly modifies parameter values within allowed grid
    - Template Mutation: Changes template_type with parameter re-initialization
    - Crossover: Combines two parents to create offspring
    - Adaptive mutation: Adjusts mutation rate based on population diversity

    Attributes:
        base_mutation_rate: Baseline mutation probability (0.15 default)
        min_mutation_rate: Minimum allowed mutation rate (0.05 default)
        max_mutation_rate: Maximum allowed mutation rate (0.30 default)
        template_mutation_rate: Template type mutation probability (0.05 default)
        current_mutation_rate: Current adaptive mutation rate (starts at base)
    """

    def __init__(
        self,
        base_mutation_rate: float = 0.15,
        min_mutation_rate: float = 0.05,
        max_mutation_rate: float = 0.30,
        template_mutation_rate: float = 0.05
    ):
        """
        Initialize genetic operators with adaptive mutation configuration.

        Args:
            base_mutation_rate: Baseline mutation probability (default: 0.15)
            min_mutation_rate: Minimum mutation rate (default: 0.05)
            max_mutation_rate: Maximum mutation rate (default: 0.30)
            template_mutation_rate: Template type mutation probability (default: 0.05)
                TUNABLE HYPERPARAMETER: Controls exploration/exploitation balance
                across templates. Higher values (e.g., 0.10) increase template
                diversity but may slow convergence. Lower values (e.g., 0.02)
                focus on parameter optimization within current templates.

        Raises:
            ValueError: If rates are invalid or out of bounds
        """
        # Validate mutation rate bounds
        if not (0.0 <= min_mutation_rate <= base_mutation_rate <= max_mutation_rate <= 1.0):
            raise ValueError(
                f"Invalid mutation rates: min={min_mutation_rate}, "
                f"base={base_mutation_rate}, max={max_mutation_rate}. "
                f"Must satisfy: 0 <= min <= base <= max <= 1"
            )

        # Validate template mutation rate
        if not (0.0 <= template_mutation_rate <= 1.0):
            raise ValueError(
                f"Invalid template_mutation_rate: {template_mutation_rate}. "
                f"Must be in range [0.0, 1.0]"
            )

        self.base_mutation_rate = base_mutation_rate
        self.min_mutation_rate = min_mutation_rate
        self.max_mutation_rate = max_mutation_rate
        self.template_mutation_rate = template_mutation_rate
        self.current_mutation_rate = base_mutation_rate

    def mutate(self, individual: Individual, generation: int) -> Individual:
        """
        Create mutated copy of individual with template and parameter mutation.

        Template Mutation:
        With probability template_mutation_rate, randomly selects a new template_type
        from available templates. When template changes, parameters are re-initialized
        by randomly sampling from the new template's PARAM_GRID to ensure validity.

        Parameter Mutation:
        For each parameter, with probability current_mutation_rate, randomly selects
        a new value from the parameter grid. Parameters are validated to ensure they
        remain within the allowed grid for the individual's template_type.

        Args:
            individual: Individual to mutate
            generation: Current generation number (for offspring tracking)

        Returns:
            Individual: New mutated individual with updated template_type and/or parameters

        Example:
            >>> operators = GeneticOperators(template_mutation_rate=0.05)
            >>> parent = Individual(parameters={'n_stocks': 10, 'stop_loss': 0.10}, template_type='Momentum')
            >>> child = operators.mutate(parent, generation=5)
            >>> # child may have different template_type (5% chance) and/or mutated parameters
        """
        from src.utils.template_registry import TemplateRegistry
        registry = TemplateRegistry.get_instance()

        # Step 1: Template Mutation (with probability template_mutation_rate)
        new_template_type = individual.template_type
        template_changed = False

        if random.random() < self.template_mutation_rate:
            # Select random template_type from available templates
            available_templates = registry.get_available_templates()
            new_template_type = random.choice(available_templates)
            template_changed = True

        # Step 2: Get parameter grid for the (possibly new) template
        template = registry.get_template(new_template_type)
        param_grid = template.PARAM_GRID

        # Step 3: Initialize parameters based on template mutation
        # Template mutation and parameter mutation are mutually exclusive
        if template_changed:
            # Template changed - re-initialize parameters from new template's PARAM_GRID
            # No additional parameter mutation needed - re-initialization provides exploration
            new_params = {}
            for param_name, allowed_values in param_grid.items():
                new_params[param_name] = random.choice(allowed_values)
        else:
            # Template unchanged - copy existing parameters for mutation
            new_params = copy.deepcopy(individual.parameters)

            # Step 4: Parameter Mutation (only if template unchanged)
            # Mutate each parameter independently with probability current_mutation_rate
            for param_name in list(new_params.keys()):
                if random.random() < self.current_mutation_rate:
                    new_params[param_name] = self._mutate_parameter(
                        param_name, new_params[param_name], param_grid
                    )

        # Step 5: Create new individual with mutated template_type and parameters
        mutated = Individual(
            parameters=new_params,
            template_type=new_template_type,
            generation=generation,
            parent_ids=[individual.id]
        )

        return mutated

    def crossover(
        self,
        parent1: Individual,
        parent2: Individual,
        generation: int
    ) -> Tuple[Individual, Individual]:
        """
        Create two offspring using uniform crossover (same-template only).

        Same-Template Crossover Constraint:
        Crossover only occurs between individuals with the same template_type.
        If templates differ, returns two mutated copies of each parent instead.
        This ensures offspring inherit valid parameter combinations from their
        template-specific PARAM_GRID.

        Uniform Crossover:
        For each parameter, randomly inherit from parent1 or parent2 with equal
        probability. Offspring inherit the common template_type from both parents.

        Args:
            parent1: First parent individual
            parent2: Second parent individual
            generation: Current generation number (for offspring tracking)

        Returns:
            Tuple[Individual, Individual]: Two offspring individuals

        Example:
            >>> operators = GeneticOperators()
            >>> p1 = Individual(parameters={'n_stocks': 10}, template_type='Momentum')
            >>> p2 = Individual(parameters={'n_stocks': 20}, template_type='Momentum')
            >>> child1, child2 = operators.crossover(p1, p2, generation=5)
            >>> # child1 and child2 have mixed parameters from p1 and p2
            >>> # Both children have template_type='Momentum'
        """
        # Same-template check - only crossover individuals with same template_type
        if parent1.template_type != parent2.template_type:
            # Different templates - skip crossover, return mutated copies
            child1 = self.mutate(parent1, generation)
            child2 = self.mutate(parent2, generation)
            return (child1, child2)

        # Duplicate parent check - avoid crossover if parents are identical
        if parent1.id == parent2.id:
            # Parents identical - skip crossover, just mutate
            child1 = self.mutate(parent1, generation)
            child2 = self.mutate(parent1, generation)
            return (child1, child2)

        # Normal uniform crossover - each parameter randomly inherited
        # Both parents have same template_type, so offspring inherit it
        common_template_type = parent1.template_type

        child1_params = {}
        child2_params = {}

        for param_name in parent1.parameters.keys():
            # Flip coin for each parameter
            if random.random() < 0.5:
                # Child1 inherits from parent1, child2 from parent2
                child1_params[param_name] = parent1.parameters[param_name]
                child2_params[param_name] = parent2.parameters[param_name]
            else:
                # Child1 inherits from parent2, child2 from parent1
                child1_params[param_name] = parent2.parameters[param_name]
                child2_params[param_name] = parent1.parameters[param_name]

        # Create offspring individuals with inherited template_type
        child1 = Individual(
            parameters=child1_params,
            template_type=common_template_type,
            generation=generation,
            parent_ids=[parent1.id, parent2.id]
        )

        child2 = Individual(
            parameters=child2_params,
            template_type=common_template_type,
            generation=generation,
            parent_ids=[parent1.id, parent2.id]
        )

        return (child1, child2)

    def update_mutation_rate(self, diversity: float) -> None:
        """
        Update mutation rate based on population diversity.

        Adaptive mutation strategy:
        - Low diversity (<0.5): Increase mutation to explore more
        - High diversity (>0.8): Decrease mutation to exploit current region
        - Healthy diversity (0.5-0.8): Slowly decay back to base rate

        Args:
            diversity: Current population diversity (0.0 to 1.0)

        Example:
            >>> operators = GeneticOperators()
            >>> operators.update_mutation_rate(0.3)  # Low diversity
            >>> print(operators.current_mutation_rate)  # Increased
            >>> operators.update_mutation_rate(0.9)  # High diversity
            >>> print(operators.current_mutation_rate)  # Decreased
        """
        if diversity < 0.5:
            # Low diversity - increase mutation to promote exploration
            self.current_mutation_rate = min(
                self.max_mutation_rate,
                self.current_mutation_rate * 1.2
            )
        elif diversity > 0.8:
            # High diversity - decrease mutation to promote exploitation
            self.current_mutation_rate = max(
                self.min_mutation_rate,
                self.current_mutation_rate * 0.8
            )
        else:
            # Healthy diversity - slowly decay back to base rate
            decay_factor = 0.95
            self.current_mutation_rate = (
                self.current_mutation_rate * decay_factor +
                self.base_mutation_rate * (1 - decay_factor)
            )

    def _mutate_parameter(
        self,
        param_name: str,
        param_value: Any,
        param_grid: Dict[str, List[Any]]
    ) -> Any:
        """
        Mutate a single parameter by randomly selecting from grid.

        Randomly selects a new value from the parameter's allowed values
        in the grid. May return the same value if randomly selected.

        Args:
            param_name: Name of parameter to mutate
            param_value: Current parameter value
            param_grid: Grid of allowed parameter values

        Returns:
            Any: New parameter value (randomly selected from grid)

        Raises:
            ValueError: If parameter name not in grid
        """
        if param_name not in param_grid:
            raise ValueError(
                f"Parameter '{param_name}' not found in parameter grid"
            )

        # Get allowed values for this parameter
        allowed_values = param_grid[param_name]

        if not allowed_values:
            raise ValueError(
                f"Parameter '{param_name}' has empty allowed values in grid"
            )

        # Randomly select new value from allowed values
        new_value = random.choice(allowed_values)

        return new_value

    def get_mutation_rate(self) -> float:
        """
        Get current mutation rate.

        Returns:
            float: Current adaptive mutation rate
        """
        return self.current_mutation_rate

    def reset_mutation_rate(self) -> None:
        """
        Reset mutation rate to base value.

        Useful when restarting evolution or after convergence restart.
        """
        self.current_mutation_rate = self.base_mutation_rate
