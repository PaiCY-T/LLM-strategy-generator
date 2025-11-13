"""
Strategy Pattern implementation for strategy generation.

This module implements the Strategy design pattern to decouple the decision logic
from the generation methods. It supports three generation strategies:
- LLMStrategy: LLM-based code generation with explicit error handling
- FactorGraphStrategy: Factor Graph-based strategy generation
- MixedStrategy: Probabilistic selection between LLM and Factor Graph

Phase 3 of the architecture refactoring (REQ-4.1, REQ-4.2).
"""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, Tuple, Dict

from src.learning.exceptions import (
    LLMEmptyResponseError,
    LLMGenerationError,
    LLMUnavailableError,
)


@dataclass(frozen=True)
class GenerationContext:
    """Immutable context for strategy generation.

    This dataclass encapsulates all data needed by generation strategies,
    ensuring immutability and type safety.

    Attributes:
        config: Configuration dictionary (use_factor_graph, innovation_rate, etc.)
        llm_client: LLM client for code generation
        champion_tracker: Champion tracker for accessing best strategies
        feedback: Iteration feedback string for LLM
        iteration_num: Current iteration number

    Example:
        >>> context = GenerationContext(
        ...     config={"innovation_rate": 75},
        ...     llm_client=llm_client,
        ...     champion_tracker=champion_tracker,
        ...     feedback="Previous iteration failed",
        ...     iteration_num=5
        ... )
    """
    config: Dict[str, Any]
    llm_client: Any
    champion_tracker: Any
    feedback: str
    iteration_num: int


class GenerationStrategy(ABC):
    """Abstract base class for strategy generation methods.

    All generation strategies must implement the generate() method, which
    takes a GenerationContext and returns a tuple of (code, strategy_id, generation).

    Return format:
        - LLM: (code_string, None, None)
        - Factor Graph: (None, strategy_id, generation_num)
    """

    @abstractmethod
    def generate(self, context: GenerationContext) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """Generate a new strategy using this method.

        Args:
            context: Immutable context containing all necessary data

        Returns:
            Tuple of (code, strategy_id, generation):
            - code: Python code string (LLM) or None (Factor Graph)
            - strategy_id: Unique strategy ID (Factor Graph) or None (LLM)
            - generation: Generation number (Factor Graph) or None (LLM)

        Raises:
            LLMUnavailableError: When LLM client/engine is not available
            LLMEmptyResponseError: When LLM returns empty response
            LLMGenerationError: When LLM generation fails
        """
        pass


class LLMStrategy(GenerationStrategy):
    """LLM-based strategy generation with explicit error handling.

    This strategy encapsulates the logic from iteration_executor._generate_with_llm(),
    replacing silent fallbacks with explicit exceptions (Phase 1 requirement).

    Error Handling:
        - Client disabled → LLMUnavailableError
        - Engine unavailable → LLMUnavailableError
        - Empty response → LLMEmptyResponseError
        - API exceptions → LLMGenerationError (with exception chaining)

    Example:
        >>> strategy = LLMStrategy()
        >>> context = GenerationContext(...)
        >>> code, sid, gen = strategy.generate(context)
        >>> assert code is not None and sid is None and gen is None
    """

    def generate(self, context: GenerationContext) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """Generate strategy using LLM.

        Args:
            context: Generation context with llm_client, champion_tracker, feedback

        Returns:
            (strategy_code, None, None)

        Raises:
            LLMUnavailableError: When LLM is disabled or engine is None
            LLMEmptyResponseError: When LLM returns empty/whitespace response
            LLMGenerationError: When LLM API fails (wraps original exception)
        """
        try:
            # Check if LLM is enabled
            if not context.llm_client.is_enabled():
                raise LLMUnavailableError("LLM client is not enabled")

            # Get LLM engine
            engine = context.llm_client.get_engine()
            if not engine:
                raise LLMUnavailableError("LLM engine not available")

            # Get champion information for InnovationEngine
            champion = context.champion_tracker.champion

            # Extract champion_code and champion_metrics
            if champion:
                # For LLM champions, use code directly
                if champion.generation_method == "llm":
                    champion_code = champion.code or ""
                    champion_metrics = champion.metrics
                # For Factor Graph champions, we don't have code
                # Use empty string and let InnovationEngine handle it
                else:
                    champion_code = ""
                    champion_metrics = champion.metrics
            else:
                # No champion yet, use defaults
                champion_code = ""
                champion_metrics = {"sharpe_ratio": 0.0}

            # Generate strategy using InnovationEngine API
            strategy_code = engine.generate_innovation(
                champion_code=champion_code,
                champion_metrics=champion_metrics,
                failure_history=None,  # TODO: Extract from history in future iteration
                target_metric="sharpe_ratio"
            )

            # Check for empty, None, or whitespace-only responses
            if not strategy_code or (isinstance(strategy_code, str) and not strategy_code.strip()):
                raise LLMEmptyResponseError("LLM returned empty code")

            return (strategy_code, None, None)

        except (LLMUnavailableError, LLMEmptyResponseError):
            # Re-raise our specific exceptions without wrapping
            raise
        except Exception as e:
            # Wrap any other exceptions in LLMGenerationError with exception chain
            raise LLMGenerationError(f"LLM generation failed: {e}") from e


class FactorGraphStrategy(GenerationStrategy):
    """Factor Graph-based strategy generation.

    This strategy wraps the factor_graph_generator, delegating all generation
    logic to the existing implementation. It acts as an adapter to the Strategy interface.

    Example:
        >>> generator = factor_graph_generator  # Existing generator
        >>> strategy = FactorGraphStrategy(generator)
        >>> context = GenerationContext(...)
        >>> code, sid, gen = strategy.generate(context)
        >>> assert code is None and sid is not None and gen is not None
    """

    def __init__(self, factor_graph_generator: Any):
        """Initialize with a factor graph generator.

        Args:
            factor_graph_generator: Existing generator with generate(iteration_num) method
        """
        self.generator = factor_graph_generator

    def generate(self, context: GenerationContext) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """Generate strategy using Factor Graph.

        Args:
            context: Generation context with iteration_num

        Returns:
            (None, strategy_id, generation_num) from factor_graph_generator
        """
        return self.generator.generate(context.iteration_num)


class MixedStrategy(GenerationStrategy):
    """Probabilistic strategy selection based on innovation_rate.

    This strategy implements the original probabilistic behavior: randomly
    choose between LLM and Factor Graph based on the innovation_rate percentage.

    Decision Logic:
        if random.random() * 100 < innovation_rate:
            use LLM
        else:
            use Factor Graph

    Example:
        >>> llm = LLMStrategy()
        >>> fg = FactorGraphStrategy(generator)
        >>> mixed = MixedStrategy(llm, fg)
        >>> context = GenerationContext(config={"innovation_rate": 75}, ...)
        >>> # 75% chance of using LLM, 25% chance of using Factor Graph
        >>> result = mixed.generate(context)
    """

    def __init__(self, llm_strategy: LLMStrategy, fg_strategy: FactorGraphStrategy):
        """Initialize with LLM and Factor Graph strategies.

        Args:
            llm_strategy: LLM strategy instance
            fg_strategy: Factor Graph strategy instance
        """
        self.llm = llm_strategy
        self.fg = fg_strategy

    def generate(self, context: GenerationContext) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """Generate strategy using probabilistic selection.

        Args:
            context: Generation context with config["innovation_rate"]

        Returns:
            Result from either LLMStrategy or FactorGraphStrategy
        """
        innovation_rate = context.config.get("innovation_rate", 100)

        # Probabilistic decision
        if random.random() * 100 < innovation_rate:
            return self.llm.generate(context)
        else:
            return self.fg.generate(context)


class StrategyFactory:
    """Factory for creating generation strategies based on configuration.

    This factory implements the decision logic that was previously in
    iteration_executor._decide_generation_method(), with the same priority:
        1. use_factor_graph (if set) takes priority
        2. Falls back to innovation_rate for probabilistic selection

    Priority Rules:
        - use_factor_graph=True → FactorGraphStrategy
        - use_factor_graph=False → LLMStrategy
        - use_factor_graph=None → MixedStrategy (probabilistic)

    Example:
        >>> factory = StrategyFactory()
        >>>
        >>> # Explicit Factor Graph
        >>> strategy = factory.create_strategy(
        ...     config={"use_factor_graph": True},
        ...     llm_client=client,
        ...     factor_graph_generator=generator
        ... )
        >>> assert isinstance(strategy, FactorGraphStrategy)
        >>>
        >>> # Explicit LLM
        >>> strategy = factory.create_strategy(
        ...     config={"use_factor_graph": False},
        ...     llm_client=client,
        ...     factor_graph_generator=generator
        ... )
        >>> assert isinstance(strategy, LLMStrategy)
        >>>
        >>> # Probabilistic (innovation_rate-based)
        >>> strategy = factory.create_strategy(
        ...     config={"innovation_rate": 75},
        ...     llm_client=client,
        ...     factor_graph_generator=generator
        ... )
        >>> assert isinstance(strategy, MixedStrategy)
    """

    def create_strategy(
        self,
        config: Dict[str, Any],
        llm_client: Any,
        factor_graph_generator: Any
    ) -> GenerationStrategy:
        """Create the appropriate strategy based on configuration.

        Args:
            config: Configuration dictionary with use_factor_graph and/or innovation_rate
            llm_client: LLM client for LLMStrategy
            factor_graph_generator: Generator for FactorGraphStrategy

        Returns:
            Strategy instance (LLMStrategy, FactorGraphStrategy, or MixedStrategy)
        """
        use_factor_graph = config.get("use_factor_graph")

        # Priority 1: Explicit use_factor_graph setting
        if use_factor_graph is True:
            return FactorGraphStrategy(factor_graph_generator)
        elif use_factor_graph is False:
            return LLMStrategy()

        # Priority 2: Probabilistic (MixedStrategy)
        # When use_factor_graph is None, use innovation_rate for probabilistic selection
        llm_strategy = LLMStrategy()
        fg_strategy = FactorGraphStrategy(factor_graph_generator)
        return MixedStrategy(llm_strategy, fg_strategy)
