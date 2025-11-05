"""
Mutation mechanism for evolutionary strategy optimization.

This module implements genetic mutation operations for introducing variation
into strategy populations. It includes Gaussian mutation for numeric parameters,
type-preserving parameter mutation, and LLM-based code regeneration.

Key Components:
- MutationManager: Orchestrates mutation operations
- gaussian_mutation: Gaussian noise sampling for numeric values
- mutate_parameters: Parameter-level mutation with type preservation
- mutate: Complete mutation workflow with code regeneration

Design Principles:
- Controlled Variation: Mutation strength controls magnitude of changes
- Type Preservation: Integer/float types maintained through mutation
- Robustness: Retry logic with validation checks
- Adaptivity: Mutation rate can be dynamically adjusted based on diversity
"""

import logging
import random
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from src.evolution.types import Strategy

logger: logging.Logger = logging.getLogger(__name__)


class MutationManager:
    """
    Manages genetic mutation operations for evolutionary strategy optimization.

    The MutationManager orchestrates mutation through:
    1. Gaussian mutation for numeric parameter perturbation
    2. Type-preserving parameter mutation (int/float)
    3. Factor weight renormalization (maintain sum=1.0 constraint)
    4. LLM-based code regeneration from mutated parameters
    5. Code validation with retry logic

    Attributes:
        code_validator: CodeValidator instance for validating generated code
        mutation_rate: Probability of mutating each parameter (default: 0.1)
        mutation_strength: Magnitude of Gaussian noise (default: 0.1)
        max_retries: Maximum retry attempts for code generation (default: 3)

    Example:
        >>> code_validator = CodeValidator()
        >>> mutation_mgr = MutationManager(code_validator)
        >>> mutated_strategy = mutation_mgr.mutate(strategy, mutation_rate=0.2)
    """

    def __init__(
        self,
        code_validator: Any,
        mutation_rate: float = 0.1,
        mutation_strength: float = 0.1,
        max_retries: int = 3
    ):
        """
        Initialize MutationManager with configuration.

        Args:
            code_validator: CodeValidator instance for validating generated code
            mutation_rate: Probability of mutating each parameter (default: 0.1)
            mutation_strength: Magnitude of Gaussian noise (default: 0.1)
            max_retries: Maximum retry attempts for code generation (default: 3)

        Raises:
            ValueError: If mutation_rate not in [0.0, 1.0], mutation_strength not positive,
                       or max_retries < 1
        """
        if not 0.0 <= mutation_rate <= 1.0:
            raise ValueError(
                f"mutation_rate must be in [0.0, 1.0], got {mutation_rate}"
            )
        if mutation_strength <= 0.0:
            raise ValueError(
                f"mutation_strength must be positive, got {mutation_strength}"
            )
        if max_retries < 1:
            raise ValueError(
                f"max_retries must be at least 1, got {max_retries}"
            )

        self.code_validator = code_validator
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength
        self.max_retries = max_retries

        logger.info(
            f"MutationManager initialized: mutation_rate={mutation_rate}, "
            f"mutation_strength={mutation_strength}, max_retries={max_retries}"
        )

    def gaussian_mutation(
        self,
        value: float,
        sigma: float,
        bounds: Optional[Tuple[float, float]] = None
    ) -> float:
        """
        Apply Gaussian mutation to a numeric value.

        Samples noise from N(0, sigma) and applies relative mutation:
        mutated = value + noise * value

        Args:
            value: Original numeric value
            sigma: Standard deviation of Gaussian noise (mutation strength)
            bounds: Optional (min, max) bounds for clipping

        Returns:
            Mutated value, clipped to bounds if provided

        Example:
            >>> mgr = MutationManager(validator)
            >>> mgr.gaussian_mutation(10.0, sigma=0.1, bounds=(5.0, 15.0))
            10.5  # Example: 10 + 0.05*10 = 10.5
        """
        # Sample Gaussian noise
        noise = np.random.normal(0, sigma)

        # Apply relative mutation
        mutated = value + noise * value

        # Clip to bounds if provided
        if bounds is not None:
            min_val, max_val = bounds
            mutated = np.clip(mutated, min_val, max_val)

        logger.debug(
            f"Gaussian mutation: {value:.4f} → {mutated:.4f} "
            f"(noise={noise:.4f}, sigma={sigma:.4f})"
        )

        return float(mutated)

    def mutate_parameters(
        self,
        params: Dict[str, Any],
        mutation_rate: Optional[float] = None,
        mutation_strength: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Mutate strategy parameters with type preservation.

        For each parameter, mutate with probability mutation_rate:
        - int: ±10% or ±1 (whichever is larger), rounded to int
        - float: Gaussian mutation with mutation_strength

        Factor weights are renormalized to sum=1.0 after mutation.

        Args:
            params: Original strategy parameters
            mutation_rate: Override instance mutation_rate (optional)
            mutation_strength: Override instance mutation_strength (optional)

        Returns:
            Mutated parameters with types preserved

        Example:
            >>> params = {'lookback': 20, 'threshold': 0.5, 'factor_weights': {'roe': 0.6, 'pe': 0.4}}
            >>> mutated = mgr.mutate_parameters(params, mutation_rate=0.5)
            >>> # lookback might be 22, threshold might be 0.52, weights still sum to 1.0
        """
        if mutation_rate is None:
            mutation_rate = self.mutation_rate
        if mutation_strength is None:
            mutation_strength = self.mutation_strength

        mutated_params = {}

        for key, value in params.items():
            # Skip factor_weights - handle separately
            if key == 'factor_weights':
                mutated_params[key] = value.copy() if isinstance(value, dict) else value
                continue

            # Mutate with probability mutation_rate
            if random.random() < mutation_rate:
                if isinstance(value, int):
                    # Integer mutation: ±10% or ±1
                    delta = max(1, int(abs(value) * 0.1))
                    mutated_value = value + random.choice([-delta, delta])
                    mutated_params[key] = int(mutated_value)
                    logger.debug(f"Mutated int {key}: {value} → {mutated_params[key]}")

                elif isinstance(value, float):
                    # Float mutation: Gaussian
                    mutated_value = self.gaussian_mutation(value, mutation_strength)
                    mutated_params[key] = float(mutated_value)
                    logger.debug(f"Mutated float {key}: {value:.4f} → {mutated_params[key]:.4f}")

                else:
                    # Other types: keep unchanged
                    mutated_params[key] = value
            else:
                # Not mutated
                mutated_params[key] = value

        # Mutate factor_weights if present
        if 'factor_weights' in params and isinstance(params['factor_weights'], dict):
            mutated_weights = {}
            for factor, weight in params['factor_weights'].items():
                if random.random() < mutation_rate:
                    # Gaussian mutation on weight
                    mutated_weight = self.gaussian_mutation(
                        weight, mutation_strength, bounds=(0.0, 1.0)
                    )
                    mutated_weights[factor] = mutated_weight
                    logger.debug(f"Mutated weight {factor}: {weight:.4f} → {mutated_weight:.4f}")
                else:
                    mutated_weights[factor] = weight

            # Renormalize weights
            mutated_params['factor_weights'] = self._renormalize_weights(mutated_weights)

        logger.debug(
            f"Parameter mutation: {len(params)} params, "
            f"mutation_rate={mutation_rate:.2f}"
        )

        return mutated_params

    def _renormalize_weights(
        self,
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Renormalize factor weights to sum=1.0.

        Args:
            weights: Dictionary of factor weights

        Returns:
            Renormalized weights summing to 1.0

        Note:
            If all weights are zero, returns equal weights for all factors
        """
        if not weights:
            return {}

        total = sum(weights.values())

        # Edge case: all weights zero - use equal weights
        if total == 0.0:
            num_factors = len(weights)
            equal_weight = 1.0 / num_factors
            normalized = {k: equal_weight for k in weights.keys()}
            logger.warning(
                f"All weights zero, using equal weights: {equal_weight:.4f} "
                f"for {num_factors} factors"
            )
            return normalized

        # Normalize to sum=1.0
        normalized = {k: v / total for k, v in weights.items()}

        # Verify sum (should be 1.0 within floating point precision)
        normalized_sum = sum(normalized.values())
        logger.debug(f"Weight renormalization: {total:.4f} → {normalized_sum:.4f}")

        return normalized

    def generate_mutated_code(
        self,
        strategy: Strategy,
        mutated_params: Dict[str, Any],
        prompt_builder: Any
    ) -> Optional[str]:
        """
        Generate mutated code via LLM from mutated parameters.

        Uses prompt_builder to create mutation prompt, calls LLM API to generate
        code, and validates the generated code. Returns None if validation fails.

        Args:
            strategy: Original strategy
            mutated_params: Mutated parameters
            prompt_builder: PromptBuilder instance for generating mutation prompts

        Returns:
            Generated code string if valid, None if validation fails

        Note:
            This method makes an LLM API call and may be slow (~5-10 seconds)
        """
        logger.debug(
            f"Generating mutated code for strategy {strategy.id[:8]}"
        )

        try:
            # Build mutation prompt
            prompt = prompt_builder.build_mutation_prompt(
                strategy=strategy,
                mutated_params=mutated_params
            )

            # Call LLM API to generate code
            # TODO: Integrate with actual LLM API (placeholder for now)
            generated_code = self._call_llm_api(prompt)

            # Validate generated code
            is_valid = self.code_validator.validate(generated_code)

            if is_valid:
                logger.debug("Generated mutated code passed validation")
                return generated_code
            else:
                logger.warning("Generated mutated code failed validation")
                return None

        except Exception as e:
            logger.error(f"Error generating mutated code: {e}", exc_info=True)
            return None

    def _call_llm_api(self, prompt: str) -> str:
        """
        Call LLM API to generate code (placeholder).

        Args:
            prompt: Mutation prompt from prompt_builder

        Returns:
            Generated code string

        Note:
            This is a placeholder - actual implementation should integrate with
            LLM API (OpenAI, Anthropic, etc.)
        """
        # TODO: Integrate with actual LLM API
        logger.warning("_call_llm_api is a placeholder - implement LLM integration")
        return "# Placeholder mutated code from LLM API"

    def mutate(
        self,
        strategy: Strategy,
        prompt_builder: Any,
        mutation_rate: Optional[float] = None,
        mutation_strength: Optional[float] = None,
        max_retries: Optional[int] = None
    ) -> Optional[Strategy]:
        """
        Perform complete mutation operation with code regeneration.

        Attempts to generate mutated offspring through:
        1. Parameter mutation via mutate_parameters
        2. Code regeneration via LLM with mutated parameters
        3. Validation with retry logic

        Args:
            strategy: Original strategy to mutate
            prompt_builder: PromptBuilder instance for generating mutation prompts
            mutation_rate: Override instance mutation_rate (optional)
            mutation_strength: Override instance mutation_strength (optional)
            max_retries: Override instance max_retries (optional)

        Returns:
            Mutated strategy if successful, None if all attempts fail

        Note:
            Logs mutation failures and retry attempts
        """
        if mutation_rate is None:
            mutation_rate = self.mutation_rate
        if mutation_strength is None:
            mutation_strength = self.mutation_strength
        if max_retries is None:
            max_retries = self.max_retries

        # Attempt mutation with retry logic
        for attempt in range(max_retries):
            logger.debug(
                f"Mutation attempt {attempt + 1}/{max_retries} for "
                f"strategy {strategy.id[:8]}"
            )

            # Step 1: Mutate parameters
            mutated_params = self.mutate_parameters(
                strategy.parameters,
                mutation_rate,
                mutation_strength
            )

            # Step 2: Generate mutated code
            mutated_code = self.generate_mutated_code(
                strategy,
                mutated_params,
                prompt_builder
            )

            if mutated_code is not None:
                # Success - create mutated strategy
                # TODO: Create Strategy object with mutated code
                logger.info(
                    f"Mutation succeeded on attempt {attempt + 1}: "
                    f"strategy {strategy.id[:8]}"
                )
                return None  # Placeholder - return Strategy object

            logger.debug(f"Mutation attempt {attempt + 1} failed, retrying...")

        # All retries failed
        logger.warning(
            f"All {max_retries} mutation attempts failed for "
            f"strategy {strategy.id[:8]}"
        )
        return None
