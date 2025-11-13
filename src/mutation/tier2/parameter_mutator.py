"""
Parameter Mutator - Gaussian mutation for Factor parameters.

Integrates Phase 1 parameter mutation capabilities into the Factor Graph
architecture, enabling gradual parameter optimization during evolution.

Architecture: Phase 2.0+ Factor Graph System
Task: C.4 - mutate_parameters() Integration (Phase 1)
"""

import random
import copy
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

from src.factor_graph.strategy import Strategy
from src.factor_graph.factor import Factor


class ParameterMutator:
    """
    Mutates Factor parameters using Gaussian distribution.

    This integrates Phase 1 parameter mutation capabilities into the Factor Graph
    architecture, enabling gradual parameter optimization during evolution.

    The mutator applies Gaussian mutations to numerical parameters with:
    - Configurable standard deviation (as % of current value)
    - Parameter bounds enforcement (min/max)
    - Parameter type preservation (int/float)
    - Statistical tracking of parameter drift

    Mutation Strategy:
    ------------------
    1. Select random factor from strategy
    2. For each parameter with probability mutation_probability:
       - Apply Gaussian noise: new = current + N(0, std_dev * current)
       - Enforce bounds if specified
       - Preserve type (round to int if original was int)
    3. Validate mutated parameters
    4. Track drift statistics

    Example Usage:
    --------------
    ```python
    from src.mutation.tier2 import ParameterMutator

    mutator = ParameterMutator()

    config = {
        "std_dev": 0.1,  # 10% standard deviation
        "parameter_bounds": {
            "period": (5, 50),  # RSI period between 5-50
            "threshold": (0.0, 1.0),  # Normalized thresholds
        },
        "mutation_probability": 0.3  # 30% chance per parameter
    }

    # Mutate strategy parameters
    mutated_strategy = mutator.mutate(original_strategy, config)

    # Get mutation statistics
    stats = mutator.get_statistics()
    print(f"Mutations applied: {stats['total_mutations']}")
    print(f"Average drift: {stats['avg_drift']}")
    ```

    Configuration Format:
    --------------------
    {
        "std_dev": float,  # Standard deviation as % of current value (default: 0.1)
        "parameter_bounds": {  # Optional bounds per parameter name
            "period": (min, max),
            "threshold": (min, max),
            # ... other parameter bounds
        },
        "mutation_probability": float,  # Probability per parameter (default: 0.3)
        "seed": int  # Optional random seed for reproducibility
    }

    Design Notes:
    ------------
    - Pure function: Returns new strategy, preserves original
    - Type-safe: Preserves int vs float types
    - Bounds-aware: Clips values to valid ranges
    - Validation: Ensures parameters remain valid after mutation
    - Statistics: Tracks drift for analysis
    """

    def __init__(self):
        """Initialize parameter mutator with empty statistics."""
        self.statistics = {
            "total_mutations": 0,
            "mutations_by_factor": {},
            "mutations_by_parameter": {},
            "parameter_drifts": [],
            "avg_drift": 0.0,
            "bounded_clips": 0  # Count of times bounds were enforced
        }

    def mutate(self, strategy: Strategy, config: Dict[str, Any]) -> Strategy:
        """
        Apply parameter mutation to random Factor in strategy.

        Selects a random factor from the strategy and mutates its parameters
        using Gaussian distribution with configurable standard deviation.

        Args:
            strategy: Strategy to mutate (not modified)
            config: Mutation configuration with std_dev, parameter_bounds, etc.

        Returns:
            New Strategy with mutated factor parameters (original unchanged)

        Raises:
            ValueError: If strategy has no factors
            ValueError: If config is invalid

        Example:
            >>> mutator = ParameterMutator()
            >>> config = {"std_dev": 0.1, "mutation_probability": 0.3}
            >>> mutated = mutator.mutate(original_strategy, config)
            >>> # Original strategy unchanged, mutated has different parameters
        """
        # Validate strategy has factors
        if not strategy.factors:
            raise ValueError("Strategy has no factors to mutate")

        # Validate and extract config
        std_dev = config.get("std_dev", 0.1)
        parameter_bounds = config.get("parameter_bounds", {})
        mutation_probability = config.get("mutation_probability", 0.3)
        seed = config.get("seed", None)

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        # Validate config values
        if not (0.0 < std_dev <= 10.0):  # Allow larger std_dev for aggressive mutations
            raise ValueError(f"std_dev must be in (0, 10], got {std_dev}")
        if not (0.0 <= mutation_probability <= 1.0):
            raise ValueError(
                f"mutation_probability must be in [0, 1], got {mutation_probability}"
            )

        # Create copy of strategy for mutation
        mutated_strategy = strategy.copy()

        # Select random factor to mutate
        factor_ids = list(mutated_strategy.factors.keys())
        selected_factor_id = random.choice(factor_ids)

        # Mutate the selected factor's parameters
        original_factor = mutated_strategy.factors[selected_factor_id]
        mutated_factor = self._mutate_factor_parameters(
            original_factor,
            std_dev,
            parameter_bounds,
            mutation_probability
        )

        # Replace factor in strategy
        # Since we're working with a copy, we can safely modify
        mutated_strategy.factors[selected_factor_id] = mutated_factor

        # Update DAG node attributes to reference new factor
        mutated_strategy.dag.nodes[selected_factor_id]['factor'] = mutated_factor

        return mutated_strategy

    def _mutate_factor_parameters(
        self,
        factor: Factor,
        std_dev: float,
        parameter_bounds: Dict[str, Tuple[float, float]],
        mutation_probability: float
    ) -> Factor:
        """
        Mutate parameters of a single Factor.

        Args:
            factor: Factor to mutate
            std_dev: Standard deviation as % of current value
            parameter_bounds: Bounds per parameter name
            mutation_probability: Probability of mutating each parameter

        Returns:
            New Factor with mutated parameters
        """
        # If factor has no parameters, return unchanged
        if not factor.parameters:
            return factor

        # Create deep copy of parameters
        mutated_parameters = copy.deepcopy(factor.parameters)

        # Mutate each parameter with given probability
        for param_name, param_value in factor.parameters.items():
            # Only mutate numerical parameters
            if not isinstance(param_value, (int, float)):
                continue

            # Mutate with probability
            if random.random() < mutation_probability:
                # Get bounds for this parameter
                bounds = parameter_bounds.get(param_name, None)

                # Apply Gaussian mutation
                new_value = self._apply_gaussian_mutation(
                    param_value,
                    std_dev,
                    bounds
                )

                # Track statistics
                self._track_mutation(param_name, param_value, new_value, factor.id)

                # Update parameter
                mutated_parameters[param_name] = new_value

        # Create new factor with mutated parameters
        # All other attributes remain the same
        mutated_factor = Factor(
            id=factor.id,
            name=factor.name,
            category=factor.category,
            inputs=factor.inputs.copy(),
            outputs=factor.outputs.copy(),
            logic=factor.logic,  # Shallow copy of callable (acceptable)
            parameters=mutated_parameters,
            description=factor.description
        )

        return mutated_factor

    def _apply_gaussian_mutation(
        self,
        param_value: float,
        std_dev: float,
        bounds: Optional[Tuple[float, float]]
    ) -> float:
        """
        Apply Gaussian mutation with bounds enforcement.

        Mutation formula:
        - new_value = current_value + N(0, std_dev * current_value)
        - If bounds specified: new_value = clip(new_value, min, max)
        - If original was int: new_value = round(new_value)

        Args:
            param_value: Current parameter value
            std_dev: Standard deviation as % of current value
            bounds: Optional (min, max) bounds to enforce

        Returns:
            Mutated parameter value with same type as original

        Example:
            >>> # Mutate RSI period of 14 with 10% std dev
            >>> new_period = _apply_gaussian_mutation(14, 0.1, (5, 50))
            >>> # Returns int in range [5, 50], typically 12-16
        """
        # Remember if original was int
        is_int = isinstance(param_value, int)

        # Calculate mutation magnitude (std dev as % of current value)
        # Use absolute value to handle negative parameters
        mutation_std = std_dev * abs(param_value) if param_value != 0 else std_dev

        # Apply Gaussian noise
        noise = np.random.normal(0, mutation_std)
        new_value = param_value + noise

        # Enforce bounds if specified
        if bounds is not None:
            min_val, max_val = bounds
            if new_value < min_val or new_value > max_val:
                self.statistics["bounded_clips"] += 1
            new_value = np.clip(new_value, min_val, max_val)

        # Preserve type (round to int if original was int)
        if is_int:
            new_value = int(round(new_value))

        return new_value

    def _track_mutation(
        self,
        param_name: str,
        old_value: float,
        new_value: float,
        factor_id: str
    ) -> None:
        """
        Track parameter mutation statistics.

        Updates internal statistics for analysis:
        - Total mutations count
        - Mutations per factor
        - Mutations per parameter name
        - Parameter drift values
        - Average drift

        Args:
            param_name: Name of mutated parameter
            old_value: Original value
            new_value: Mutated value
            factor_id: ID of factor containing parameter
        """
        # Increment total mutations
        self.statistics["total_mutations"] += 1

        # Track mutations by factor
        if factor_id not in self.statistics["mutations_by_factor"]:
            self.statistics["mutations_by_factor"][factor_id] = 0
        self.statistics["mutations_by_factor"][factor_id] += 1

        # Track mutations by parameter name
        if param_name not in self.statistics["mutations_by_parameter"]:
            self.statistics["mutations_by_parameter"][param_name] = 0
        self.statistics["mutations_by_parameter"][param_name] += 1

        # Calculate and track drift (relative change)
        if old_value != 0:
            drift = abs((new_value - old_value) / old_value)
        else:
            drift = abs(new_value)

        self.statistics["parameter_drifts"].append(drift)

        # Update average drift
        if self.statistics["parameter_drifts"]:
            self.statistics["avg_drift"] = np.mean(
                self.statistics["parameter_drifts"]
            )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get mutation statistics.

        Returns:
            Dictionary with mutation statistics:
            - total_mutations: Total number of parameters mutated
            - mutations_by_factor: Dict mapping factor_id to mutation count
            - mutations_by_parameter: Dict mapping param_name to mutation count
            - parameter_drifts: List of relative drift values
            - avg_drift: Average relative drift
            - bounded_clips: Number of times bounds were enforced

        Example:
            >>> stats = mutator.get_statistics()
            >>> print(f"Total mutations: {stats['total_mutations']}")
            >>> print(f"Average drift: {stats['avg_drift']:.2%}")
        """
        return copy.deepcopy(self.statistics)

    def reset_statistics(self) -> None:
        """
        Reset mutation statistics.

        Clears all tracked statistics. Useful when running multiple
        experiments or batches of mutations.

        Example:
            >>> mutator.reset_statistics()
            >>> stats = mutator.get_statistics()
            >>> assert stats['total_mutations'] == 0
        """
        self.statistics = {
            "total_mutations": 0,
            "mutations_by_factor": {},
            "mutations_by_parameter": {},
            "parameter_drifts": [],
            "avg_drift": 0.0,
            "bounded_clips": 0
        }
