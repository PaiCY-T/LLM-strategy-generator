"""
Pydantic configuration models for strategy generation.

This module provides type-safe configuration models with validation
for the strategy generation system. It implements Phase 2 of the
generation refactoring effort.

Key Features:
    - Type safety with Pydantic BaseModel
    - Field validation with constraints
    - Configuration conflict detection
    - Priority-based decision logic

Usage:
    from learning.config_models import GenerationConfig

    # Create configuration with validation
    config = GenerationConfig(
        use_factor_graph=False,
        innovation_rate=75
    )

    # Check if should use LLM
    if config.should_use_llm():
        # Use LLM generation
        pass
    else:
        # Use factor graph
        pass
"""

import random
from typing import Optional, Annotated

from pydantic import BaseModel, Field, model_validator, ConfigDict


class GenerationConfig(BaseModel):
    """Pydantic configuration for strict type validation."""

    model_config = ConfigDict(strict=True, validate_assignment=True)
    """
    Configuration model for strategy generation behavior.

    This model defines how the system should generate new strategies,
    with support for both LLM-based and factor graph-based approaches.

    Attributes:
        use_factor_graph: Optional explicit control over generation method.
            - True: Force factor graph usage (disable LLM)
            - False: Force LLM usage (disable factor graph)
            - None: Use probabilistic decision based on innovation_rate
        innovation_rate: Percentage chance (0-100) of using LLM when
            use_factor_graph is None. Higher values favor LLM innovation.

    Priority Logic:
        1. If use_factor_graph is set (True/False): Use explicit choice
        2. If use_factor_graph is None: Probabilistic based on innovation_rate

    Conflict Detection:
        Raises ValueError when use_factor_graph=True AND innovation_rate=100,
        as this represents conflicting intentions (force factor graph but
        maximum LLM preference).

    Examples:
        >>> # Force LLM usage
        >>> config = GenerationConfig(use_factor_graph=False)
        >>> config.should_use_llm()
        True

        >>> # Force factor graph usage
        >>> config = GenerationConfig(use_factor_graph=True, innovation_rate=50)
        >>> config.should_use_llm()
        False

        >>> # Probabilistic: 75% chance of LLM
        >>> config = GenerationConfig(innovation_rate=75)
        >>> # config.should_use_llm() returns True ~75% of the time

        >>> # Configuration conflict raises error
        >>> config = GenerationConfig(use_factor_graph=True, innovation_rate=100)
        Traceback (most recent call last):
            ...
        ValueError: Configuration conflict: use_factor_graph=True conflicts with...
    """

    use_factor_graph: Optional[bool] = None
    innovation_rate: Annotated[int, Field(ge=0, le=100)] = 100

    @model_validator(mode="after")
    def check_configuration_conflicts(self) -> "GenerationConfig":
        """
        Validate that configuration fields don't conflict.

        This validator checks for the primary logical inconsistency:
        use_factor_graph=True (force factor graph) + innovation_rate=100 (force LLM)

        Note: use_factor_graph=False + innovation_rate=0 is NOT considered a conflict
        because use_factor_graph has priority, so the behavior is well-defined
        (use LLM, ignoring innovation_rate).

        Returns:
            Self if validation passes

        Raises:
            ValueError: When use_factor_graph=True and innovation_rate=100
        """
        if self.use_factor_graph is True and self.innovation_rate == 100:
            raise ValueError(
                "Configuration conflict: use_factor_graph=True conflicts with "
                "innovation_rate=100. Suggestion: Set innovation_rate < 100 or "
                "use_factor_graph=False"
            )

        return self

    def should_use_llm(self) -> bool:
        """
        Determine whether to use LLM for strategy generation.

        Decision Logic:
            1. Priority 1: Explicit use_factor_graph setting
               - If True: Return False (use factor graph, not LLM)
               - If False: Return True (use LLM)
            2. Priority 2: Probabilistic based on innovation_rate
               - Generate random value in [0, 100)
               - Return True if random < innovation_rate

        Returns:
            True if LLM should be used, False if factor graph should be used

        Examples:
            >>> config = GenerationConfig(use_factor_graph=False)
            >>> config.should_use_llm()
            True

            >>> config = GenerationConfig(use_factor_graph=True)
            >>> config.should_use_llm()
            False

            >>> config = GenerationConfig(innovation_rate=100)
            >>> config.should_use_llm()  # Always True when rate=100
            True

            >>> config = GenerationConfig(innovation_rate=0)
            >>> config.should_use_llm()  # Always False when rate=0
            False
        """
        # Priority 1: Explicit use_factor_graph setting
        if self.use_factor_graph is not None:
            # If use_factor_graph=True, we DON'T use LLM (use factor graph)
            # If use_factor_graph=False, we DO use LLM
            return not self.use_factor_graph

        # Priority 2: Probabilistic decision based on innovation_rate
        # Generate random value in [0, 100) and compare with innovation_rate
        use_llm = random.random() * 100 < self.innovation_rate
        return use_llm
