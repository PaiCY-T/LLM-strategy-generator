# tests/learning/test_iteration_executor_phase1.py
"""
Phase 1 TDD Test Suite: Configuration Priority and Explicit Error Handling

Tests for iteration_executor.py methods:
- _decide_generation_method(): Configuration priority logic (REQ-1.1, REQ-1.2)
- _generate_with_llm(): Silent fallback elimination (REQ-2.1)

These tests are written against the DESIRED behavior after Phase 1 fixes.
They will FAIL with the current implementation, driving the required refactoring.

Key Assertions:
1. `use_factor_graph` flag has absolute priority over `innovation_rate`.
2. Conflicting configurations (e.g., `use_factor_graph=True` and `innovation_rate=100`)
   raise `ConfigurationConflictError`.
3. The four silent fallback points in `_generate_with_llm` are eliminated and
   replaced with specific, descriptive exceptions.
"""

import random
from unittest.mock import MagicMock, patch

import pytest

from src.learning.exceptions import (
    ConfigurationConflictError,
    LLMEmptyResponseError,
    LLMGenerationError,
    LLMUnavailableError,
)
from src.learning.iteration_executor import IterationExecutor


@pytest.fixture
def mock_dependencies():
    """Provides mocked dependencies for IterationExecutor instantiation."""
    return {
        "llm_client": MagicMock(),
        "feedback_generator": MagicMock(),
        "backtest_executor": MagicMock(),
        "champion_tracker": MagicMock(),
        "history": MagicMock(),
        "data": MagicMock(),
        "sim": MagicMock(),
    }


class TestDecideGenerationMethod:
    """
    TDD Tests for `_decide_generation_method` (REQ-1.1, REQ-1.2).

    These tests enforce the new configuration priority rules. They will fail
    until the implementation is updated to respect `use_factor_graph` and
    detect configuration conflicts.
    """

    @pytest.mark.parametrize(
        "config, expected_use_llm",
        [
            # REQ-1.1: `use_factor_graph` has absolute priority (non-conflicting cases)
            # Note: Conflicting cases (use_factor_graph=True + innovation_rate=100 and
            # use_factor_graph=False + innovation_rate=0) are covered by conflict detection tests
            pytest.param({"use_factor_graph": True, "innovation_rate": 50}, False, id="use_factor_graph=True overrides innovation_rate=50"),
            pytest.param({"use_factor_graph": True, "innovation_rate": 0}, False, id="use_factor_graph=True with innovation_rate=0"),
            pytest.param({"use_factor_graph": False, "innovation_rate": 50}, True, id="use_factor_graph=False overrides innovation_rate=50"),
            pytest.param({"use_factor_graph": False, "innovation_rate": 100}, True, id="use_factor_graph=False with innovation_rate=100"),

            # REQ-1.2: Fallback to `innovation_rate` when `use_factor_graph` is not set
            pytest.param({"innovation_rate": 100}, True, id="innovation_rate=100 forces LLM"),
            pytest.param({"innovation_rate": 0}, False, id="innovation_rate=0 forces Factor Graph"),
        ],
    )
    def test_configuration_priority(self, mock_dependencies, config, expected_use_llm):
        """
        WHEN `use_factor_graph` is set
        THEN it must take absolute priority over `innovation_rate`.
        """
        # Arrange
        executor = IterationExecutor(config=config, **mock_dependencies)

        # Act
        use_llm = executor._decide_generation_method()

        # Assert
        assert use_llm is expected_use_llm

    @patch("random.random")
    @pytest.mark.parametrize(
        "random_val, innovation_rate, expected_use_llm",
        [
            # Probabilistic decision when `use_factor_graph` is None
            pytest.param(0.49, 50, True, id="random < innovation_rate -> LLM"),
            pytest.param(0.51, 50, False, id="random > innovation_rate -> Factor Graph"),
            pytest.param(0.50, 50, False, id="random == innovation_rate -> Factor Graph (boundary)"),
        ]
    )
    def test_probabilistic_decision(self, mock_random, mock_dependencies, random_val, innovation_rate, expected_use_llm):
        """
        WHEN `use_factor_graph` is not specified
        THEN the decision should be probabilistic based on `innovation_rate`.
        """
        # Arrange
        mock_random.return_value = random_val
        config = {"innovation_rate": innovation_rate}
        executor = IterationExecutor(config=config, **mock_dependencies)

        # Act
        use_llm = executor._decide_generation_method()

        # Assert
        assert use_llm is expected_use_llm

    @pytest.mark.parametrize(
        "conflicting_config, error_match",
        [
            pytest.param(
                {"use_factor_graph": True, "innovation_rate": 100},
                "Configuration conflict: `use_factor_graph=True` is incompatible with `innovation_rate=100`",
                id="conflict_force_fg_and_force_llm"
            ),
        ]
    )
    def test_raises_on_configuration_conflict(self, mock_dependencies, conflicting_config, error_match):
        """
        WHEN the configuration contains logically incompatible settings
        THEN `ConfigurationConflictError` must be raised.

        Note: Phase 2 validation raises the exception during __init__ (eager validation),
        while Phase 1 validation raises it during _decide_generation_method() (lazy validation).
        This test accommodates both behaviors.
        """
        # Arrange & Act
        # Try to create executor - Phase 2 may raise exception here
        try:
            executor = IterationExecutor(config=conflicting_config, **mock_dependencies)
            # If we get here, Phase 2 validation is not active
            # Phase 1: Exception should be raised during method call
            with pytest.raises(ConfigurationConflictError, match=error_match):
                executor._decide_generation_method()
        except ConfigurationConflictError as e:
            # Phase 2: Exception raised during construction (fail-fast)
            # Verify the error message matches expectations
            assert "Configuration conflict" in str(e)


class TestGenerateWithLLM:
    """
    TDD Tests for `_generate_with_llm` (REQ-2.1).

    These tests replace the previous "silent fallback" tests. They assert that
    each of the four degradation points now raises a specific, informative exception
    instead of silently falling back to the factor graph.
    """

    @pytest.fixture
    def executor(self, mock_dependencies):
        """Returns a pre-configured IterationExecutor instance."""
        executor = IterationExecutor(config={}, **mock_dependencies)
        # Mock the fallback method to ensure it's NEVER called in these tests
        executor._generate_with_factor_graph = MagicMock()
        return executor

    def test_happy_path_successful_generation(self, executor):
        """
        WHEN all LLM dependencies are healthy and the LLM returns code
        THEN the code is returned and no fallback occurs.
        """
        # Arrange
        mock_engine = MagicMock()
        mock_engine.generate_innovation.return_value = "def strategy(): pass"
        executor.llm_client.is_enabled.return_value = True
        executor.llm_client.get_engine.return_value = mock_engine
        executor.champion_tracker.get_champion.return_value = None

        # Act
        code, sid, sgen = executor._generate_with_llm("feedback", 1)

        # Assert
        assert code == "def strategy(): pass"
        assert sid is None
        assert sgen is None
        executor._generate_with_factor_graph.assert_not_called()
        mock_engine.generate_innovation.assert_called_once()

    def test_raises_LLMUnavailableError_when_client_disabled(self, executor):
        """
        (REQ-2.1, Point 1)
        WHEN the LLM client is disabled
        THEN `LLMUnavailableError` is raised.
        (Original code at line 386-388)
        """
        # Arrange
        executor.llm_client.is_enabled.return_value = False

        # Act & Assert
        with pytest.raises(LLMUnavailableError, match="LLM client is not enabled"):
            executor._generate_with_llm("feedback", 1)
        executor._generate_with_factor_graph.assert_not_called()

    def test_raises_LLMUnavailableError_when_engine_is_none(self, executor):
        """
        (REQ-2.1, Point 2)
        WHEN the LLM engine is not available (get_engine() returns None)
        THEN `LLMUnavailableError` is raised.
        (Original code at line 391-394)
        """
        # Arrange
        executor.llm_client.is_enabled.return_value = True
        executor.llm_client.get_engine.return_value = None

        # Act & Assert
        with pytest.raises(LLMUnavailableError, match="LLM engine is not available"):
            executor._generate_with_llm("feedback", 1)
        executor._generate_with_factor_graph.assert_not_called()

    @pytest.mark.parametrize(
        "empty_response",
        [
            pytest.param("", id="empty_string"),
            pytest.param("   \n\t   ", id="whitespace_only"),
            pytest.param(None, id="none_response"),
        ]
    )
    def test_raises_LLMEmptyResponseError_when_llm_returns_empty_code(self, executor, empty_response):
        """
        (REQ-2.1, Point 3)
        WHEN the LLM returns an empty, whitespace-only, or None response
        THEN `LLMEmptyResponseError` is raised.
        (Original code at line 424-426)
        """
        # Arrange
        mock_engine = MagicMock()
        mock_engine.generate_innovation.return_value = empty_response
        executor.llm_client.is_enabled.return_value = True
        executor.llm_client.get_engine.return_value = mock_engine
        executor.champion_tracker.get_champion.return_value = None

        # Act & Assert
        with pytest.raises(LLMEmptyResponseError, match="LLM returned an empty or whitespace-only response"):
            executor._generate_with_llm("feedback", 1)
        executor._generate_with_factor_graph.assert_not_called()

    def test_raises_LLMGenerationError_on_api_exception(self, executor):
        """
        (REQ-2.1, Point 4)
        WHEN the LLM client's `generate_innovation` method raises an exception
        THEN it is caught and re-raised as `LLMGenerationError`.
        (Original code at line 432-435)
        """
        # Arrange
        original_exception = ValueError("API rate limit exceeded")
        mock_engine = MagicMock()
        mock_engine.generate_innovation.side_effect = original_exception
        executor.llm_client.is_enabled.return_value = True
        executor.llm_client.get_engine.return_value = mock_engine
        executor.champion_tracker.get_champion.return_value = None

        # Act & Assert
        with pytest.raises(LLMGenerationError, match="LLM generation failed") as excinfo:
            executor._generate_with_llm("feedback", 1)

        # Verify that the original exception is chained for better debugging
        assert excinfo.value.__cause__ is original_exception
        executor._generate_with_factor_graph.assert_not_called()

    @pytest.mark.parametrize(
        "champion_obj, expected_code, expected_metrics",
        [
            pytest.param(None, "", {"sharpe_ratio": 0.0}, id="no_champion"),
            pytest.param(
                MagicMock(generation_method="llm", code="llm_code", metrics={"sharpe_ratio": 2.5}),
                "llm_code",
                {"sharpe_ratio": 2.5},
                id="llm_champion"
            ),
            pytest.param(
                MagicMock(generation_method="factor_graph", code=None, metrics={"sharpe_ratio": 1.8}),
                "",
                {"sharpe_ratio": 1.8},
                id="factor_graph_champion"
            ),
        ]
    )
    def test_champion_information_is_passed_correctly(
        self, executor, champion_obj, expected_code, expected_metrics
    ):
        """
        WHEN a champion exists (either LLM or Factor Graph based)
        THEN its information is correctly extracted and passed to the LLM engine.
        """
        # Arrange
        mock_engine = MagicMock()
        mock_engine.generate_innovation.return_value = "new_code"
        executor.llm_client.is_enabled.return_value = True
        executor.llm_client.get_engine.return_value = mock_engine
        executor.champion_tracker.get_champion.return_value = champion_obj

        # Act
        executor._generate_with_llm("feedback", 1)

        # Assert
        mock_engine.generate_innovation.assert_called_once_with(
            champion_code=expected_code,
            champion_metrics=expected_metrics,
            failure_history=None,
            target_metric="sharpe_ratio"
        )
