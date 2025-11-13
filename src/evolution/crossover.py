"""
Crossover mechanism for evolutionary strategy generation.

This module implements genetic crossover operations for combining parent strategies
to create offspring. It includes parameter-level crossover, code generation via LLM,
semantic preservation, and compatibility checking.

Key Components:
- CrossoverManager: Orchestrates crossover operations
- parameter_crossover: Uniform crossover for strategy parameters
- generate_offspring_code: LLM-based code generation from crossover parameters
- check_compatibility: Validates parent compatibility for crossover

Design Principles:
- Semantic Preservation: Offspring should be semantically valid and executable
- Feature Combination: Blend strengths from both parents
- Robustness: Retry logic with fallback to mutation
- Validation: All generated code must pass validation checks
"""

import logging
import random
from typing import Any, Dict, List, Optional, Tuple

from src.evolution.types import Strategy

logger: logging.Logger = logging.getLogger(__name__)


class CrossoverManager:
    """
    Manages genetic crossover operations for evolutionary strategy generation.

    The CrossoverManager orchestrates the process of combining two parent strategies
    to create offspring through:
    1. Parameter-level uniform crossover (50/50 probability per parameter)
    2. Factor weight renormalization (maintain sum=1.0 constraint)
    3. LLM-based code generation from crossover parameters
    4. Code validation with retry logic
    5. Compatibility checking to prevent invalid combinations

    Attributes:
        prompt_builder: PromptBuilder instance for generating crossover prompts
        code_validator: CodeValidator instance for validating generated code
        crossover_rate: Probability of performing crossover (default: 0.7)
        max_retries: Maximum retry attempts for code generation (default: 3)

    Example:
        >>> prompt_builder = PromptBuilder()
        >>> code_validator = CodeValidator()
        >>> crossover_mgr = CrossoverManager(prompt_builder, code_validator)
        >>> parent1, parent2 = population[0], population[1]
        >>> offspring = crossover_mgr.crossover(parent1, parent2)
    """

    def __init__(
        self,
        prompt_builder: Any,  # Type hint as Any to avoid circular import
        code_validator: Any,
        crossover_rate: float = 0.7,
        max_retries: int = 3
    ):
        """
        Initialize CrossoverManager with dependencies and configuration.

        Args:
            prompt_builder: PromptBuilder instance for generating crossover prompts
            code_validator: CodeValidator instance for validating generated code
            crossover_rate: Probability of performing crossover vs mutation (default: 0.7)
            max_retries: Maximum retry attempts for code generation (default: 3)

        Raises:
            ValueError: If crossover_rate not in [0.0, 1.0] or max_retries < 1
        """
        if not 0.0 <= crossover_rate <= 1.0:
            raise ValueError(
                f"crossover_rate must be in [0.0, 1.0], got {crossover_rate}"
            )
        if max_retries < 1:
            raise ValueError(
                f"max_retries must be at least 1, got {max_retries}"
            )

        self.prompt_builder = prompt_builder
        self.code_validator = code_validator
        self.crossover_rate = crossover_rate
        self.max_retries = max_retries

        logger.info(
            f"CrossoverManager initialized: crossover_rate={crossover_rate}, "
            f"max_retries={max_retries}"
        )

    def parameter_crossover(
        self,
        params1: Dict[str, Any],
        params2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform uniform crossover on strategy parameters.

        For each parameter, randomly select from parent1 or parent2 with 50/50
        probability. Handles missing keys by using None if key not in both parents.
        Factor weights are renormalized to sum=1.0 after crossover.

        Args:
            params1: Parameters from parent1 strategy
            params2: Parameters from parent2 strategy

        Returns:
            Dict containing crossover parameters with factor weights renormalized

        Example:
            >>> params1 = {'lookback': 20, 'threshold': 0.5, 'factor_weights': {'roe': 0.6, 'momentum': 0.4}}
            >>> params2 = {'lookback': 30, 'threshold': 0.3, 'factor_weights': {'roe': 0.3, 'pe': 0.7}}
            >>> crossover_params = mgr.parameter_crossover(params1, params2)
            >>> # Result might be: {'lookback': 30, 'threshold': 0.5, 'factor_weights': {'roe': 0.45, 'momentum': 0.2, 'pe': 0.35}}
            >>> sum(crossover_params['factor_weights'].values())  # Always 1.0
            1.0
        """
        # Get all unique keys from both parents
        all_keys = set(params1.keys()) | set(params2.keys())

        crossover_params = {}

        for key in all_keys:
            # Get values from both parents (None if missing)
            val1 = params1.get(key)
            val2 = params2.get(key)

            # If only one parent has this key, use that value
            if val1 is None:
                crossover_params[key] = val2
            elif val2 is None:
                crossover_params[key] = val1
            else:
                # Both parents have this key - uniform crossover (50/50)
                crossover_params[key] = random.choice([val1, val2])

        # Renormalize factor_weights if present
        if 'factor_weights' in crossover_params:
            crossover_params['factor_weights'] = self._renormalize_weights(
                crossover_params['factor_weights']
            )

        logger.debug(
            f"Parameter crossover: {len(params1)} + {len(params2)} keys "
            f"→ {len(crossover_params)} crossover keys"
        )

        return crossover_params

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

    def generate_offspring_code(
        self,
        parent1: Strategy,
        parent2: Strategy,
        crossover_params: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate offspring code via LLM from crossover parameters.

        Uses prompt_builder to create crossover prompt, calls LLM API to generate
        code, and validates the generated code. Returns None if validation fails.

        Args:
            parent1: First parent strategy
            parent2: Second parent strategy
            crossover_params: Parameters from parameter_crossover

        Returns:
            Generated code string if valid, None if validation fails

        Note:
            This method makes an LLM API call and may be slow (~5-10 seconds)
        """
        logger.debug(
            f"Generating offspring code from parents {parent1.id[:8]} + "
            f"{parent2.id[:8]}"
        )

        try:
            # Build crossover prompt
            prompt = self.prompt_builder.build_crossover_prompt(
                parent1=parent1,
                parent2=parent2,
                target_params=crossover_params
            )

            # Call LLM API to generate code
            # TODO: Integrate with actual LLM API (placeholder for now)
            generated_code = self._call_llm_api(prompt)

            # Validate generated code
            is_valid = self.code_validator.validate(generated_code)

            if is_valid:
                logger.debug("Generated code passed validation")
                return generated_code
            else:
                logger.warning("Generated code failed validation")
                return None

        except Exception as e:
            logger.error(f"Error generating offspring code: {e}", exc_info=True)
            return None

    def _call_llm_api(self, prompt: str) -> str:
        """
        Call LLM API to generate code (placeholder).

        Args:
            prompt: Crossover prompt from prompt_builder

        Returns:
            Generated code string

        Note:
            This is a placeholder - actual implementation should integrate with
            LLM API (OpenAI, Anthropic, etc.)
        """
        # TODO: Integrate with actual LLM API
        # For now, return placeholder
        logger.warning("_call_llm_api is a placeholder - implement LLM integration")
        return "# Placeholder code from LLM API"

    def crossover(
        self,
        parent1: Strategy,
        parent2: Strategy,
        crossover_rate: Optional[float] = None,
        max_retries: Optional[int] = None
    ) -> Optional[Strategy]:
        """
        Perform complete crossover operation with retry logic.

        Attempts to generate offspring through crossover up to max_retries times.
        Falls back to single-parent mutation if all retries fail.

        Args:
            parent1: First parent strategy
            parent2: Second parent strategy
            crossover_rate: Override instance crossover_rate (optional)
            max_retries: Override instance max_retries (optional)

        Returns:
            Offspring strategy if successful, None if all attempts fail

        Note:
            Logs crossover failures and fallback attempts
        """
        if crossover_rate is None:
            crossover_rate = self.crossover_rate
        if max_retries is None:
            max_retries = self.max_retries

        # Check if crossover should be performed
        if random.random() >= crossover_rate:
            logger.debug(
                f"Skipping crossover (rate={crossover_rate}), "
                f"fallback to mutation"
            )
            return None

        # Check compatibility
        if not self.check_compatibility(parent1, parent2):
            logger.warning(
                f"Parents {parent1.id[:8]} and {parent2.id[:8]} incompatible, "
                f"skipping crossover"
            )
            return None

        # Attempt crossover with retry logic
        for attempt in range(max_retries):
            logger.debug(
                f"Crossover attempt {attempt + 1}/{max_retries} for "
                f"{parent1.id[:8]} + {parent2.id[:8]}"
            )

            # Step 1: Parameter crossover
            crossover_params = self.parameter_crossover(
                parent1.parameters,
                parent2.parameters
            )

            # Step 2: Generate offspring code
            offspring_code = self.generate_offspring_code(
                parent1,
                parent2,
                crossover_params
            )

            if offspring_code is not None:
                # Success - create offspring strategy
                # TODO: Create Strategy object with generated code
                logger.info(
                    f"Crossover succeeded on attempt {attempt + 1}: "
                    f"{parent1.id[:8]} + {parent2.id[:8]}"
                )
                return None  # Placeholder - return Strategy object

            logger.debug(f"Crossover attempt {attempt + 1} failed, retrying...")

        # All retries failed
        logger.warning(
            f"All {max_retries} crossover attempts failed for "
            f"{parent1.id[:8]} + {parent2.id[:8]}, fallback to mutation"
        )
        return None

    def check_compatibility(
        self,
        parent1: Strategy,
        parent2: Strategy
    ) -> bool:
        """
        Check if two parent strategies are compatible for crossover.

        Verifies that:
        1. Both parents use the same factor types (momentum, value, quality, etc.)
        2. Both have similar parameter structures

        Args:
            parent1: First parent strategy
            parent2: Second parent strategy

        Returns:
            True if parents are compatible, False otherwise

        Note:
            Logs warning if parents are incompatible
        """
        # Check factor type compatibility
        factors1 = set(parent1.parameters.get('factor_weights', {}).keys())
        factors2 = set(parent2.parameters.get('factor_weights', {}).keys())

        # If no factors in common, incompatible
        if not factors1 or not factors2:
            logger.debug(
                f"Incompatible: parent1 has {len(factors1)} factors, "
                f"parent2 has {len(factors2)} factors"
            )
            return False

        # Calculate factor overlap
        overlap = factors1 & factors2
        union = factors1 | factors2
        overlap_ratio = len(overlap) / len(union) if union else 0.0

        # Require at least 30% factor overlap
        min_overlap = 0.3
        compatible = overlap_ratio >= min_overlap

        if not compatible:
            logger.warning(
                f"Incompatible parents: {overlap_ratio:.2%} factor overlap "
                f"(minimum {min_overlap:.0%}). Parent1: {factors1}, "
                f"Parent2: {factors2}"
            )
        else:
            logger.debug(
                f"Compatible parents: {overlap_ratio:.2%} factor overlap"
            )

        return compatible
