"""
Smart Mutation Engine - Intelligent operator selection and scheduling.

Orchestrates mutation operator selection based on context, success rates,
and adaptive probability adjustment. Enables the evolution system to:
- Choose appropriate mutation operators based on strategy state
- Select compatible factors by category
- Adjust mutation rates based on generation and diversity
- Track operator success rates and adapt probabilities

Architecture: Phase 2.0+ Factor Graph System
Task: C.5 - Smart Mutation Operators and Scheduling
"""

import random
from typing import Dict, Any, Tuple, Optional, Protocol
from collections import defaultdict
from dataclasses import dataclass, field
import numpy as np
import copy


class MutationOperator(Protocol):
    """
    Protocol defining mutation operator interface.

    All mutation operators must implement the mutate() method
    with this signature. This enables polymorphic usage in the
    SmartMutationEngine.
    """

    def mutate(self, strategy: Any, config: Dict[str, Any]) -> Any:
        """Apply mutation to strategy."""
        ...


@dataclass
class OperatorStats:
    """
    Track mutation operator statistics.

    Maintains counts of attempts, successes, and failures for each
    mutation operator to enable adaptive probability adjustment.

    Statistics are tracked per operator name and can be used to
    calculate success rates and adjust selection probabilities.

    Attributes:
        attempts: Total attempts per operator
        successes: Successful mutations per operator
        failures: Failed mutations per operator

    Example:
        >>> stats = OperatorStats()
        >>> stats.record("add_factor", success=True)
        >>> stats.record("add_factor", success=False)
        >>> rate = stats.get_success_rate("add_factor")
        >>> assert rate == 0.5  # 1 success / 2 attempts
    """

    attempts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    successes: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    failures: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record(self, operator: str, success: bool) -> None:
        """
        Record mutation attempt result.

        Args:
            operator: Name of mutation operator
            success: Whether mutation succeeded

        Example:
            >>> stats = OperatorStats()
            >>> stats.record("add_factor", True)
            >>> assert stats.successes["add_factor"] == 1
        """
        self.attempts[operator] += 1
        if success:
            self.successes[operator] += 1
        else:
            self.failures[operator] += 1

    def get_success_rate(self, operator: str) -> float:
        """
        Get success rate for operator (0-1).

        Args:
            operator: Name of mutation operator

        Returns:
            Success rate as fraction (0.0-1.0), or 0.0 if no attempts

        Example:
            >>> stats = OperatorStats()
            >>> stats.record("add_factor", True)
            >>> stats.record("add_factor", True)
            >>> stats.record("add_factor", False)
            >>> rate = stats.get_success_rate("add_factor")
            >>> assert abs(rate - 0.667) < 0.01
        """
        attempts = self.attempts[operator]
        if attempts == 0:
            return 0.0

        successes = self.successes[operator]
        return successes / attempts

    def get_all_rates(self) -> Dict[str, float]:
        """
        Get success rates for all operators.

        Returns:
            Dict mapping operator names to success rates (0-1)

        Example:
            >>> stats = OperatorStats()
            >>> stats.record("add_factor", True)
            >>> stats.record("mutate_parameters", False)
            >>> rates = stats.get_all_rates()
            >>> assert rates["add_factor"] == 1.0
            >>> assert rates["mutate_parameters"] == 0.0
        """
        return {
            operator: self.get_success_rate(operator)
            for operator in self.attempts.keys()
        }


class MutationScheduler:
    """
    Adaptive mutation rate scheduling.

    Adjusts mutation rate based on:
    - Generation number (higher early, lower late)
    - Population diversity (increase when diversity is low)
    - Performance stagnation (increase when no improvement)

    The scheduler implements a three-phase mutation strategy:
    - Early generations (0-20%): High rate (0.5-0.8) - exploration
    - Mid generations (20-70%): Medium rate (0.3-0.5) - balanced
    - Late generations (70-100%): Low rate (0.1-0.3) - exploitation

    Additionally, the scheduler boosts mutation rates when:
    - Population diversity is low (< 0.3): +0.2 boost
    - Performance stagnates (no improvement): +0.1 per 5 stagnant generations

    Example:
        >>> scheduler = MutationScheduler(config)
        >>> # Early generation, high diversity, no stagnation
        >>> rate = scheduler.get_mutation_rate(5, diversity=0.8, stagnation_count=0)
        >>> assert 0.5 <= rate <= 0.8  # High early rate
        >>>
        >>> # Late generation, low diversity, some stagnation
        >>> rate = scheduler.get_mutation_rate(90, diversity=0.2, stagnation_count=10)
        >>> # Base rate: 0.1-0.3 (late)
        >>> # + 0.2 (low diversity)
        >>> # + 0.2 (10 stagnant / 5 = 2 * 0.1)
        >>> assert 0.4 <= rate <= 0.7
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize mutation scheduler with configuration.

        Args:
            config: Scheduler configuration with schedule and adaptation settings

        Expected config format:
            {
                "schedule": {
                    "max_generations": 100,
                    "early_rate": 0.7,
                    "mid_rate": 0.4,
                    "late_rate": 0.2,
                    "diversity_threshold": 0.3,
                    "diversity_boost": 0.2
                },
                "initial_probabilities": {
                    "add_factor": 0.4,
                    "remove_factor": 0.2,
                    "replace_factor": 0.2,
                    "mutate_parameters": 0.2
                },
                "adaptation": {
                    "enable": True,
                    "success_rate_weight": 0.3,
                    "min_probability": 0.05,
                    "update_interval": 5
                }
            }
        """
        self.config = self._validate_config(config)
        self.schedule = self.config.get("schedule", {})
        self.initial_probabilities = self.config.get("initial_probabilities", {})
        self.adaptation = self.config.get("adaptation", {})

        # Extract schedule parameters with defaults
        self.max_generations = self.schedule.get("max_generations", 100)
        self.early_rate = self.schedule.get("early_rate", 0.7)
        self.mid_rate = self.schedule.get("mid_rate", 0.4)
        self.late_rate = self.schedule.get("late_rate", 0.2)
        self.diversity_threshold = self.schedule.get("diversity_threshold", 0.3)
        self.diversity_boost = self.schedule.get("diversity_boost", 0.2)

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and fill in default configuration values.

        Args:
            config: User-provided configuration

        Returns:
            Validated configuration with defaults filled in

        Raises:
            ValueError: If config contains invalid values
        """
        # Default configuration
        default_config = {
            "schedule": {
                "max_generations": 100,
                "early_rate": 0.7,
                "mid_rate": 0.4,
                "late_rate": 0.2,
                "diversity_threshold": 0.3,
                "diversity_boost": 0.2
            },
            "initial_probabilities": {
                "add_factor": 0.4,
                "remove_factor": 0.2,
                "replace_factor": 0.2,
                "mutate_parameters": 0.2
            },
            "adaptation": {
                "enable": True,
                "success_rate_weight": 0.3,
                "min_probability": 0.05,
                "update_interval": 5
            }
        }

        # Merge with user config
        merged = copy.deepcopy(default_config)
        if "schedule" in config:
            merged["schedule"].update(config["schedule"])

        # For initial_probabilities, if user provides ANY probabilities,
        # replace defaults entirely (don't merge)
        if "initial_probabilities" in config:
            merged["initial_probabilities"] = config["initial_probabilities"]

        if "adaptation" in config:
            merged["adaptation"].update(config["adaptation"])

        # Validate mutation rates are in [0, 1]
        schedule = merged["schedule"]
        for rate_key in ["early_rate", "mid_rate", "late_rate", "diversity_boost"]:
            rate = schedule[rate_key]
            if not (0.0 <= rate <= 1.0):
                raise ValueError(f"{rate_key} must be in [0, 1], got {rate}")

        # Validate diversity threshold
        if not (0.0 <= schedule["diversity_threshold"] <= 1.0):
            raise ValueError(
                f"diversity_threshold must be in [0, 1], got {schedule['diversity_threshold']}"
            )

        # Validate probabilities sum to ~1.0
        probs = merged["initial_probabilities"]
        total = sum(probs.values())
        if not (0.95 <= total <= 1.05):
            raise ValueError(
                f"initial_probabilities must sum to ~1.0, got {total}"
            )

        return merged

    def get_mutation_rate(
        self,
        generation: int,
        diversity: float,
        stagnation_count: int = 0
    ) -> float:
        """
        Calculate adaptive mutation rate.

        Args:
            generation: Current generation number (0-indexed)
            diversity: Population diversity metric (0-1)
            stagnation_count: Generations without improvement

        Returns:
            Mutation rate (0-1)

        Strategy:
        - Early generations (0-20%): High rate (0.5-0.8)
        - Mid generations (20-70%): Medium rate (0.3-0.5)
        - Late generations (70-100%): Low rate (0.1-0.3)
        - Low diversity boost: +0.2 when diversity < 0.3
        - Stagnation boost: +0.1 per 5 stagnant generations

        Example:
            >>> scheduler = MutationScheduler(config)
            >>> # Early generation
            >>> rate = scheduler.get_mutation_rate(5, 0.5, 0)
            >>> assert 0.5 <= rate <= 0.8
            >>>
            >>> # Late generation with low diversity
            >>> rate = scheduler.get_mutation_rate(90, 0.2, 0)
            >>> assert 0.3 <= rate <= 0.5  # late_rate + diversity_boost
        """
        # Calculate generation progress (0-1)
        progress = generation / self.max_generations

        # Base rate based on generation phase
        if progress < 0.2:
            # Early phase: High mutation rate (exploration)
            base_rate = self.early_rate
        elif progress < 0.7:
            # Mid phase: Medium mutation rate (balanced)
            base_rate = self.mid_rate
        else:
            # Late phase: Low mutation rate (exploitation)
            base_rate = self.late_rate

        # Start with base rate
        mutation_rate = base_rate

        # Add diversity boost if diversity is low
        if diversity < self.diversity_threshold:
            mutation_rate += self.diversity_boost

        # Add stagnation boost (0.1 per 5 stagnant generations)
        stagnation_boost = (stagnation_count // 5) * 0.1
        mutation_rate += stagnation_boost

        # Clip to [0, 1]
        mutation_rate = np.clip(mutation_rate, 0.0, 1.0)

        return mutation_rate

    def get_operator_probabilities(
        self,
        generation: int,
        max_generations: int,
        success_rates: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate operator selection probabilities.

        Base probabilities:
        - Early: Favor add_factor (0.5), moderate others (0.2, 0.2, 0.1)
        - Mid: Balanced (0.25 each)
        - Late: Favor mutate_parameters (0.5), moderate others

        Adjust by success rates:
        - Increase probability for successful operators (+20%)
        - Decrease for failing operators (-20%)

        Args:
            generation: Current generation number
            max_generations: Total generations planned
            success_rates: Dict mapping operator names to success rates (0-1)

        Returns:
            Dict mapping operator names to probabilities (sum to 1.0)

        Example:
            >>> scheduler = MutationScheduler(config)
            >>> success_rates = {
            ...     "add_factor": 0.8,
            ...     "remove_factor": 0.5,
            ...     "replace_factor": 0.5,
            ...     "mutate_parameters": 0.3
            ... }
            >>> probs = scheduler.get_operator_probabilities(5, 100, success_rates)
            >>> # Early generation: add_factor favored, boosted by high success rate
            >>> assert probs["add_factor"] > 0.5
        """
        # Calculate generation progress (0-1)
        progress = generation / max_generations

        # Base probabilities based on generation phase
        if progress < 0.2:
            # Early phase: Favor structural changes (add_factor)
            base_probs = {
                "add_factor": 0.5,
                "remove_factor": 0.2,
                "replace_factor": 0.2,
                "mutate_parameters": 0.1
            }
        elif progress < 0.7:
            # Mid phase: Balanced exploration
            base_probs = {
                "add_factor": 0.25,
                "remove_factor": 0.25,
                "replace_factor": 0.25,
                "mutate_parameters": 0.25
            }
        else:
            # Late phase: Favor fine-tuning (mutate_parameters)
            base_probs = {
                "add_factor": 0.15,
                "remove_factor": 0.15,
                "replace_factor": 0.2,
                "mutate_parameters": 0.5
            }

        # Adjust by success rates if adaptation is enabled
        if not self.adaptation.get("enable", True):
            return base_probs

        # Calculate adjustment weight
        weight = self.adaptation.get("success_rate_weight", 0.3)
        min_prob = self.adaptation.get("min_probability", 0.05)

        # Adjust probabilities based on success rates
        adjusted_probs = {}
        for operator, base_prob in base_probs.items():
            success_rate = success_rates.get(operator, 0.5)  # Default to neutral

            # Adjustment: +/- weight based on deviation from 0.5
            adjustment = weight * (success_rate - 0.5)
            adjusted_prob = base_prob + adjustment

            # Ensure minimum probability
            adjusted_prob = max(adjusted_prob, min_prob)
            adjusted_probs[operator] = adjusted_prob

        # Normalize to sum to 1.0
        total = sum(adjusted_probs.values())
        if total > 0:
            adjusted_probs = {k: v / total for k, v in adjusted_probs.items()}

        return adjusted_probs


class SmartMutationEngine:
    """
    Orchestrates intelligent mutation operator selection.

    Maintains operator statistics and adapts selection probabilities
    based on historical success rates. Enables the evolution system
    to learn which operators are most effective and adjust accordingly.

    The engine tracks:
    - Success/failure counts per operator
    - Success rates over time
    - Adaptive probability adjustment

    Selection strategy:
    - Early generations: Favor add_factor (structural exploration)
    - Mid generations: Balanced selection
    - Late generations: Favor mutate_parameters (fine-tuning)
    - Always: Boost successful operators, reduce failing ones

    Example:
        >>> from src.mutation.tier2 import ParameterMutator
        >>>
        >>> # Initialize engine with operators
        >>> operators = {
        ...     "mutate_parameters": ParameterMutator()
        ... }
        >>>
        >>> config = {
        ...     "initial_probabilities": {
        ...         "mutate_parameters": 1.0
        ...     },
        ...     "schedule": {
        ...         "max_generations": 100
        ...     }
        ... }
        >>>
        >>> engine = SmartMutationEngine(operators, config)
        >>>
        >>> # Select operator based on context
        >>> context = {
        ...     "generation": 10,
        ...     "diversity": 0.5,
        ...     "population_size": 20
        ... }
        >>>
        >>> operator_name, operator = engine.select_operator(context)
        >>> assert operator_name == "mutate_parameters"
        >>>
        >>> # Update success statistics
        >>> engine.update_success_rate("mutate_parameters", success=True)
        >>>
        >>> # Get statistics
        >>> stats = engine.get_statistics()
        >>> assert stats["operator_success_rates"]["mutate_parameters"] == 1.0
    """

    def __init__(self, operators: Dict[str, MutationOperator], config: Dict[str, Any]):
        """
        Initialize with mutation operators.

        Args:
            operators: Dict mapping operator names to instances
                {"add_factor": AddFactorMutator(),
                 "remove_factor": RemoveFactorMutator(),
                 "replace_factor": ReplaceFactorMutator(),
                 "mutate_parameters": ParameterMutator()}
            config: Configuration for mutation strategy

        Raises:
            ValueError: If operators dict is empty
            ValueError: If config is invalid
        """
        if not operators:
            raise ValueError("Must provide at least one mutation operator")

        # Validate that all operators in initial_probabilities exist
        # BEFORE creating scheduler (which validates probability sums)
        initial_probs = config.get("initial_probabilities", {})
        for operator_name in initial_probs.keys():
            if operator_name not in operators:
                raise ValueError(
                    f"Operator '{operator_name}' in initial_probabilities "
                    f"not found in operators dict"
                )

        self.operators = operators
        self.config = config
        self.stats = OperatorStats()
        self.scheduler = MutationScheduler(config)

        # Track update interval for adaptive probabilities
        self.adaptation_config = config.get("adaptation", {})
        self.update_interval = self.adaptation_config.get("update_interval", 5)
        self.last_update_generation = 0

    def select_operator(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, MutationOperator]:
        """
        Select mutation operator based on context.

        Args:
            context: Optional context dict with:
                - generation: int (current generation number)
                - diversity: float (population diversity 0-1)
                - population_size: int (current population size)
                - strategy: Strategy (optional - for context-aware selection)

        Returns:
            (operator_name, operator_instance)

        Example:
            >>> engine = SmartMutationEngine(operators, config)
            >>> context = {"generation": 10, "diversity": 0.5}
            >>> name, operator = engine.select_operator(context)
            >>> assert name in operators
        """
        if context is None:
            context = {}

        # Extract context
        generation = context.get("generation", 0)
        max_generations = self.scheduler.max_generations

        # Get success rates
        success_rates = self.stats.get_all_rates()

        # Get operator probabilities (adaptive based on generation and success)
        probabilities = self.scheduler.get_operator_probabilities(
            generation,
            max_generations,
            success_rates
        )

        # Filter to only operators we have
        probabilities = {
            name: prob
            for name, prob in probabilities.items()
            if name in self.operators
        }

        # Normalize in case some operators are missing
        total = sum(probabilities.values())
        if total > 0:
            probabilities = {k: v / total for k, v in probabilities.items()}
        else:
            # Fallback: uniform probabilities
            n = len(self.operators)
            probabilities = {name: 1.0 / n for name in self.operators.keys()}

        # Select operator using weighted random choice
        operator_names = list(probabilities.keys())
        weights = [probabilities[name] for name in operator_names]

        selected_name = np.random.choice(operator_names, p=weights)
        selected_operator = self.operators[selected_name]

        return selected_name, selected_operator

    def update_success_rate(self, operator_name: str, success: bool) -> None:
        """
        Update operator success statistics.

        Args:
            operator_name: Name of operator that was applied
            success: Whether the mutation succeeded

        Example:
            >>> engine = SmartMutationEngine(operators, config)
            >>> engine.update_success_rate("add_factor", True)
            >>> stats = engine.get_statistics()
            >>> assert stats["operator_success_rates"]["add_factor"] == 1.0
        """
        self.stats.record(operator_name, success)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current operator statistics.

        Returns:
            Dictionary with:
                - operator_attempts: Dict[str, int] - Attempts per operator
                - operator_successes: Dict[str, int] - Successes per operator
                - operator_failures: Dict[str, int] - Failures per operator
                - operator_success_rates: Dict[str, float] - Success rates per operator
                - total_attempts: int - Total mutations attempted
                - total_successes: int - Total successful mutations

        Example:
            >>> engine = SmartMutationEngine(operators, config)
            >>> engine.update_success_rate("add_factor", True)
            >>> engine.update_success_rate("add_factor", False)
            >>> stats = engine.get_statistics()
            >>> assert stats["operator_attempts"]["add_factor"] == 2
            >>> assert stats["operator_successes"]["add_factor"] == 1
            >>> assert stats["operator_success_rates"]["add_factor"] == 0.5
        """
        return {
            "operator_attempts": dict(self.stats.attempts),
            "operator_successes": dict(self.stats.successes),
            "operator_failures": dict(self.stats.failures),
            "operator_success_rates": self.stats.get_all_rates(),
            "total_attempts": sum(self.stats.attempts.values()),
            "total_successes": sum(self.stats.successes.values())
        }
