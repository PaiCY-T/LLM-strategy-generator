# tests/learning/test_generation_strategies.py
"""
Phase 3 TDD Test Suite: Strategy Pattern Implementation

Tests for the new components in `src.learning.generation_strategies.py`:
- GenerationContext: Immutable data container.
- LLMStrategy: LLM-based generation with explicit error handling.
- FactorGraphStrategy: Factor Graph-based generation wrapper.
- MixedStrategy: Probabilistic selection between LLM and Factor Graph.
- StrategyFactory: Creation of strategies based on configuration.

These tests are written against the design specification for Phase 3 and will
drive the implementation of the Strategy Pattern.
"""

import random
from unittest.mock import MagicMock, patch

import pytest

# Assuming the new strategies and exceptions will be in these locations
# These imports will fail until the files are created
from src.learning.exceptions import (
    LLMEmptyResponseError,
    LLMGenerationError,
    LLMUnavailableError,
)
from src.learning.generation_strategies import (
    GenerationContext,
    LLMStrategy,
    FactorGraphStrategy,
    MixedStrategy,
    StrategyFactory,
)


@pytest.fixture
def mock_llm_client():
    """Provides a mock LLMClient with a configurable engine."""
    client = MagicMock()
    engine = MagicMock()
    client.get_engine.return_value = engine
    client.is_enabled.return_value = True
    return client


@pytest.fixture
def mock_champion_tracker():
    """Provides a mock ChampionTracker."""
    return MagicMock()


@pytest.fixture
def mock_factor_graph_generator():
    """Provides a mock FactorGraphGenerator."""
    generator = MagicMock()
    generator.generate.return_value = ("fg_code_placeholder", "fg_id_123", 1)
    return generator


@pytest.fixture
def generation_context(mock_llm_client, mock_champion_tracker):
    """Provides a default GenerationContext for strategies."""
    return GenerationContext(
        config={"innovation_rate": 75},
        llm_client=mock_llm_client,
        champion_tracker=mock_champion_tracker,
        feedback="Test feedback",
        iteration_num=5,
    )


class TestGenerationContext:
    """Tests the GenerationContext data container."""

    def test_is_immutable(self, generation_context):
        """
        WHEN attempting to modify an attribute of a frozen dataclass
        THEN a FrozenInstanceError should be raised.
        """
        with pytest.raises(AttributeError): # dataclasses.FrozenInstanceError in 3.7+, but AttributeError in mock contexts
            generation_context.iteration_num = 10


class TestLLMStrategy:
    """Tests the LLMStrategy for code generation."""

    def test_generate_success(self, generation_context):
        """
        WHEN generate is called with a valid context and the LLM returns code
        THEN it should return the strategy code from the LLM engine.
        """
        # Arrange
        strategy = LLMStrategy()
        engine = generation_context.llm_client.get_engine()
        engine.generate_innovation.return_value = "def new_strategy(): pass"
        generation_context.champion_tracker.get_champion.return_value = None

        # Act
        code, sid, sgen = strategy.generate(generation_context)

        # Assert
        assert code == "def new_strategy(): pass"
        assert sid is None
        assert sgen is None
        engine.generate_innovation.assert_called_once()

    def test_raises_unavailable_when_client_disabled(self, generation_context):
        """
        WHEN the LLM client is disabled
        THEN LLMUnavailableError is raised.
        """
        # Arrange
        strategy = LLMStrategy()
        generation_context.llm_client.is_enabled.return_value = False

        # Act & Assert
        with pytest.raises(LLMUnavailableError, match="LLM client is not enabled"):
            strategy.generate(generation_context)

    def test_raises_unavailable_when_engine_is_none(self, generation_context):
        """
        WHEN the LLM client has no engine
        THEN LLMUnavailableError is raised.
        """
        # Arrange
        strategy = LLMStrategy()
        generation_context.llm_client.get_engine.return_value = None

        # Act & Assert
        with pytest.raises(LLMUnavailableError, match="LLM engine not available"):
            strategy.generate(generation_context)

    @pytest.mark.parametrize("empty_response", ["", "   \n\t  ", None])
    def test_raises_empty_response_error(self, generation_context, empty_response):
        """
        WHEN the LLM engine returns an empty or whitespace-only response
        THEN LLMEmptyResponseError is raised.
        """
        # Arrange
        strategy = LLMStrategy()
        engine = generation_context.llm_client.get_engine()
        engine.generate_innovation.return_value = empty_response

        # Act & Assert
        with pytest.raises(LLMEmptyResponseError, match="LLM returned empty code"):
            strategy.generate(generation_context)

    def test_raises_generation_error_on_api_failure(self, generation_context):
        """
        WHEN the LLM engine raises an exception
        THEN it is wrapped in LLMGenerationError and re-raised.
        """
        # Arrange
        strategy = LLMStrategy()
        original_exception = ValueError("API timeout")
        engine = generation_context.llm_client.get_engine()
        engine.generate_innovation.side_effect = original_exception

        # Act & Assert
        with pytest.raises(LLMGenerationError, match="LLM generation failed") as excinfo:
            strategy.generate(generation_context)

        assert excinfo.value.__cause__ is original_exception


class TestFactorGraphStrategy:
    """Tests the FactorGraphStrategy for code generation."""

    def test_generate_delegates_to_generator(self, generation_context, mock_factor_graph_generator):
        """
        WHEN generate is called
        THEN it should delegate to the factor_graph_generator and return its result.
        """
        # Arrange
        strategy = FactorGraphStrategy(mock_factor_graph_generator)

        # Act
        result = strategy.generate(generation_context)

        # Assert
        mock_factor_graph_generator.generate.assert_called_once_with(generation_context.iteration_num)
        assert result == ("fg_code_placeholder", "fg_id_123", 1)


class TestMixedStrategy:
    """Tests the MixedStrategy for probabilistic delegation."""

    @patch("random.random")
    def test_delegates_to_llm_strategy(self, mock_random, generation_context):
        """
        WHEN random value is less than innovation_rate
        THEN it delegates to the LLMStrategy.
        """
        # Arrange
        mock_random.return_value = 0.74  # 0.74 * 100 = 74 < 75
        context = generation_context

        llm_strategy = MagicMock(spec=LLMStrategy)
        llm_strategy.generate.return_value = ("llm_code", None, None)
        fg_strategy = MagicMock(spec=FactorGraphStrategy)

        mixed_strategy = MixedStrategy(llm_strategy, fg_strategy)

        # Act
        result = mixed_strategy.generate(context)

        # Assert
        assert result == ("llm_code", None, None)
        llm_strategy.generate.assert_called_once_with(context)
        fg_strategy.generate.assert_not_called()

    @patch("random.random")
    def test_delegates_to_factor_graph_strategy(self, mock_random, generation_context):
        """
        WHEN random value is greater than or equal to innovation_rate
        THEN it delegates to the FactorGraphStrategy.
        """
        # Arrange
        mock_random.return_value = 0.75  # 0.75 * 100 = 75 >= 75
        context = generation_context

        llm_strategy = MagicMock(spec=LLMStrategy)
        fg_strategy = MagicMock(spec=FactorGraphStrategy)
        fg_strategy.generate.return_value = ("fg_code", "fg_id", 1)

        mixed_strategy = MixedStrategy(llm_strategy, fg_strategy)

        # Act
        result = mixed_strategy.generate(context)

        # Assert
        assert result == ("fg_code", "fg_id", 1)
        fg_strategy.generate.assert_called_once_with(context)
        llm_strategy.generate.assert_not_called()


class TestStrategyFactory:
    """Tests the StrategyFactory for creating the correct strategy."""

    @pytest.mark.parametrize(
        "config, expected_strategy_type",
        [
            pytest.param(
                {"use_factor_graph": True, "innovation_rate": 50},
                FactorGraphStrategy,
                id="use_factor_graph_True_returns_FactorGraphStrategy"
            ),
            pytest.param(
                {"use_factor_graph": False, "innovation_rate": 50},
                LLMStrategy,
                id="use_factor_graph_False_returns_LLMStrategy"
            ),
            pytest.param(
                {"innovation_rate": 50},
                MixedStrategy,
                id="use_factor_graph_None_returns_MixedStrategy"
            ),
            pytest.param(
                {}, # Default innovation_rate is 100, use_factor_graph is None
                MixedStrategy,
                id="empty_config_returns_MixedStrategy"
            ),
        ]
    )
    def test_create_strategy(
        self, config, expected_strategy_type, mock_llm_client, mock_factor_graph_generator
    ):
        """
        WHEN create_strategy is called with different configurations
        THEN it returns an instance of the correct strategy class based on priority rules.
        """
        # Arrange
        factory = StrategyFactory()

        # Act
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )

        # Assert
        assert isinstance(strategy, expected_strategy_type)
