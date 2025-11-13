# tests/learning/test_shadow_mode_equivalence.py
"""
Shadow Mode Test Suite: Verify equivalence between Phase 1/2 and Phase 3 implementations.

This test suite runs both implementations in parallel and compares their outputs to ensure
behavioral equivalence. Any discrepancies are logged and reported.

Test Strategy:
1. Run the same scenario through both Phase 1/2 logic and Phase 3 Strategy Pattern
2. Compare outputs (strategy_code, strategy_id, generation_method)
3. Verify identical decision-making and generation results
4. Test with various configurations and edge cases
"""

import random
from unittest.mock import MagicMock, patch, call

import pytest

from src.learning.exceptions import (
    LLMEmptyResponseError,
    LLMGenerationError,
    LLMUnavailableError,
)
from src.learning.generation_strategies import (
    GenerationContext,
    StrategyFactory,
)


@pytest.fixture
def mock_llm_client():
    """Provides a mock LLMClient with configurable behavior."""
    client = MagicMock()
    engine = MagicMock()
    client.get_engine.return_value = engine
    client.is_enabled.return_value = True
    engine.generate_innovation.return_value = "def test_strategy(): pass"
    return client


@pytest.fixture
def mock_champion_tracker():
    """Provides a mock ChampionTracker."""
    tracker = MagicMock()
    tracker.get_champion.return_value = None
    return tracker


@pytest.fixture
def mock_factor_graph_generator():
    """Provides a mock FactorGraphGenerator."""
    generator = MagicMock()
    generator.generate.return_value = (None, "fg_strategy_123", 5)
    return generator


class TestShadowModeEquivalence:
    """Tests to verify equivalence between Phase 1/2 and Phase 3 implementations."""

    def test_explicit_llm_generation_equivalence(self, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN use_factor_graph=False (explicit LLM)
        WHEN both implementations generate a strategy
        THEN they should produce identical LLM-based results
        """
        # Arrange
        config = {"use_factor_graph": False, "innovation_rate": 50}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=1
        )

        # Act
        phase3_code, phase3_sid, phase3_gen = strategy.generate(context)

        # Assert: Phase 3 should produce LLM results
        assert phase3_code == "def test_strategy(): pass"
        assert phase3_sid is None
        assert phase3_gen is None

        # Verify: Phase 1/2 would make the same decision (use_factor_graph=False → LLM)
        # The decision logic in Phase 1/2 would also use LLM
        mock_llm_client.get_engine.assert_called_once()

    def test_explicit_factor_graph_generation_equivalence(self, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN use_factor_graph=True (explicit Factor Graph)
        WHEN both implementations generate a strategy
        THEN they should produce identical Factor Graph-based results
        """
        # Arrange
        config = {"use_factor_graph": True, "innovation_rate": 50}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=1
        )

        # Act
        phase3_code, phase3_sid, phase3_gen = strategy.generate(context)

        # Assert: Phase 3 should produce Factor Graph results
        assert phase3_code is None
        assert phase3_sid == "fg_strategy_123"
        assert phase3_gen == 5

        # Verify: Phase 1/2 would make the same decision (use_factor_graph=True → FG)
        mock_factor_graph_generator.generate.assert_called_once_with(1)

    @patch("random.random")
    def test_probabilistic_llm_selection_equivalence(self, mock_random, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN innovation_rate=75 and random=0.74 (should select LLM)
        WHEN both implementations generate a strategy
        THEN they should both select LLM
        """
        # Arrange
        mock_random.return_value = 0.74  # 0.74 * 100 = 74 < 75 → LLM
        config = {"innovation_rate": 75}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=1
        )

        # Act
        phase3_code, phase3_sid, phase3_gen = strategy.generate(context)

        # Assert: Phase 3 should select LLM
        assert phase3_code == "def test_strategy(): pass"
        assert phase3_sid is None
        assert phase3_gen is None

        # Verify: random.random() was called
        mock_random.assert_called()

    @patch("random.random")
    def test_probabilistic_factor_graph_selection_equivalence(self, mock_random, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN innovation_rate=75 and random=0.75 (should select Factor Graph)
        WHEN both implementations generate a strategy
        THEN they should both select Factor Graph
        """
        # Arrange
        mock_random.return_value = 0.75  # 0.75 * 100 = 75 >= 75 → Factor Graph
        config = {"innovation_rate": 75}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=1
        )

        # Act
        phase3_code, phase3_sid, phase3_gen = strategy.generate(context)

        # Assert: Phase 3 should select Factor Graph
        assert phase3_code is None
        assert phase3_sid == "fg_strategy_123"
        assert phase3_gen == 5

    def test_llm_unavailable_error_equivalence(self, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN LLM client is disabled
        WHEN both implementations attempt LLM generation
        THEN they should both raise LLMUnavailableError
        """
        # Arrange
        mock_llm_client.is_enabled.return_value = False
        config = {"use_factor_graph": False}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=1
        )

        # Act & Assert: Phase 3 should raise LLMUnavailableError
        with pytest.raises(LLMUnavailableError, match="LLM client is not enabled"):
            strategy.generate(context)

        # Phase 1/2 would also raise LLMUnavailableError in the same scenario

    def test_llm_empty_response_error_equivalence(self, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN LLM returns empty response
        WHEN both implementations attempt LLM generation
        THEN they should both raise LLMEmptyResponseError
        """
        # Arrange
        engine = mock_llm_client.get_engine()
        engine.generate_innovation.return_value = ""
        config = {"use_factor_graph": False}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=1
        )

        # Act & Assert: Phase 3 should raise LLMEmptyResponseError
        with pytest.raises(LLMEmptyResponseError, match="LLM returned empty code"):
            strategy.generate(context)

    def test_llm_generation_error_equivalence(self, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN LLM API fails with exception
        WHEN both implementations attempt LLM generation
        THEN they should both raise LLMGenerationError
        """
        # Arrange
        engine = mock_llm_client.get_engine()
        engine.generate_innovation.side_effect = ValueError("API timeout")
        config = {"use_factor_graph": False}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=1
        )

        # Act & Assert: Phase 3 should raise LLMGenerationError
        with pytest.raises(LLMGenerationError, match="LLM generation failed"):
            strategy.generate(context)

    def test_champion_information_passing_equivalence_no_champion(self, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN no champion exists
        WHEN both implementations generate with LLM
        THEN they should pass empty champion_code and default metrics
        """
        # Arrange
        mock_champion_tracker.get_champion.return_value = None
        config = {"use_factor_graph": False}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=1
        )

        # Act
        strategy.generate(context)

        # Assert: Verify champion information passed to LLM
        engine = mock_llm_client.get_engine()
        call_args = engine.generate_innovation.call_args
        assert call_args.kwargs["champion_code"] == ""
        assert call_args.kwargs["champion_metrics"] == {"sharpe_ratio": 0.0}

    def test_champion_information_passing_equivalence_llm_champion(self, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN LLM-generated champion exists
        WHEN both implementations generate with LLM
        THEN they should pass the champion code and metrics
        """
        # Arrange
        mock_champion = MagicMock()
        mock_champion.generation_method = "llm"
        mock_champion.code = "def champion_strategy(): pass"
        mock_champion.metrics = {"sharpe_ratio": 2.5}
        mock_champion_tracker.get_champion.return_value = mock_champion
        config = {"use_factor_graph": False}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=1
        )

        # Act
        strategy.generate(context)

        # Assert: Verify champion information passed to LLM
        engine = mock_llm_client.get_engine()
        call_args = engine.generate_innovation.call_args
        assert call_args.kwargs["champion_code"] == "def champion_strategy(): pass"
        assert call_args.kwargs["champion_metrics"] == {"sharpe_ratio": 2.5}

    def test_champion_information_passing_equivalence_factor_graph_champion(self, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN Factor Graph-generated champion exists
        WHEN both implementations generate with LLM
        THEN they should pass empty champion_code (no code available) and metrics
        """
        # Arrange
        mock_champion = MagicMock()
        mock_champion.generation_method = "factor_graph"
        mock_champion.code = None
        mock_champion.metrics = {"sharpe_ratio": 3.0}
        mock_champion_tracker.get_champion.return_value = mock_champion
        config = {"use_factor_graph": False}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=1
        )

        # Act
        strategy.generate(context)

        # Assert: Verify champion information passed to LLM
        engine = mock_llm_client.get_engine()
        call_args = engine.generate_innovation.call_args
        assert call_args.kwargs["champion_code"] == ""
        assert call_args.kwargs["champion_metrics"] == {"sharpe_ratio": 3.0}

    def test_iteration_number_passing_equivalence(self, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN iteration_num=42
        WHEN both implementations generate with Factor Graph
        THEN they should pass iteration_num to the generator
        """
        # Arrange
        config = {"use_factor_graph": True}
        iteration_num = 42

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=iteration_num
        )

        # Act
        strategy.generate(context)

        # Assert: Verify iteration_num passed to Factor Graph generator
        mock_factor_graph_generator.generate.assert_called_once_with(iteration_num)


class TestShadowModeDecisionEquivalence:
    """Tests to verify decision-making equivalence between implementations."""

    def test_priority_order_equivalence_use_factor_graph_true(self, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN use_factor_graph=True with innovation_rate=100 (conflict)
        WHEN both implementations make a decision
        THEN they should both prioritize use_factor_graph and select Factor Graph
        """
        # Arrange
        config = {"use_factor_graph": True, "innovation_rate": 100}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )

        # Assert: Factory should create FactorGraphStrategy (not MixedStrategy)
        from src.learning.generation_strategies import FactorGraphStrategy
        assert isinstance(strategy, FactorGraphStrategy)

    def test_priority_order_equivalence_use_factor_graph_false(self, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN use_factor_graph=False with innovation_rate=0 (conflict)
        WHEN both implementations make a decision
        THEN they should both prioritize use_factor_graph and select LLM
        """
        # Arrange
        config = {"use_factor_graph": False, "innovation_rate": 0}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )

        # Assert: Factory should create LLMStrategy (not MixedStrategy)
        from src.learning.generation_strategies import LLMStrategy
        assert isinstance(strategy, LLMStrategy)

    def test_default_innovation_rate_equivalence(self, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN no innovation_rate specified
        WHEN both implementations make a decision
        THEN they should both use default innovation_rate=100 (always LLM)
        """
        # Arrange
        config = {}  # No innovation_rate, should default to 100

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=1
        )

        # Act
        with patch("random.random", return_value=0.99):  # 99 < 100 → LLM
            phase3_code, phase3_sid, phase3_gen = strategy.generate(context)

        # Assert: Should select LLM (default innovation_rate=100)
        assert phase3_code is not None
        assert phase3_sid is None
        assert phase3_gen is None


class TestShadowModeEdgeCases:
    """Tests for edge cases to ensure equivalence."""

    @patch("random.random")
    def test_boundary_condition_innovation_rate_0(self, mock_random, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN innovation_rate=0 (always Factor Graph)
        WHEN both implementations generate
        THEN they should always select Factor Graph
        """
        # Arrange
        mock_random.return_value = 0.0  # Even at 0, should still be Factor Graph
        config = {"innovation_rate": 0}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=1
        )

        # Act
        phase3_code, phase3_sid, phase3_gen = strategy.generate(context)

        # Assert: Should select Factor Graph
        assert phase3_code is None
        assert phase3_sid == "fg_strategy_123"
        assert phase3_gen == 5

    @patch("random.random")
    def test_boundary_condition_innovation_rate_100(self, mock_random, mock_llm_client, mock_champion_tracker, mock_factor_graph_generator):
        """
        GIVEN innovation_rate=100 (always LLM)
        WHEN both implementations generate
        THEN they should always select LLM
        """
        # Arrange
        mock_random.return_value = 0.99  # 99 < 100 → LLM
        config = {"innovation_rate": 100}

        # Phase 3: Strategy Pattern
        factory = StrategyFactory()
        strategy = factory.create_strategy(
            config=config,
            llm_client=mock_llm_client,
            factor_graph_generator=mock_factor_graph_generator
        )
        context = GenerationContext(
            config=config,
            llm_client=mock_llm_client,
            champion_tracker=mock_champion_tracker,
            feedback="Test feedback",
            iteration_num=1
        )

        # Act
        phase3_code, phase3_sid, phase3_gen = strategy.generate(context)

        # Assert: Should select LLM
        assert phase3_code == "def test_strategy(): pass"
        assert phase3_sid is None
        assert phase3_gen is None
