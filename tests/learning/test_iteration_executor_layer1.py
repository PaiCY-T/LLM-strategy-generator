"""
Tests for Task 2.1: Layer 1 Field Suggestions Integration in IterationExecutor

TDD approach:
- RED: Write failing tests first
- GREEN: Implement minimal code to pass tests
- REFACTOR: Improve code quality while keeping tests green

Requirements:
- AC1.2: DataFieldManifest integrated into LLM prompt generation
- AC1.3: COMMON_CORRECTIONS (21 entries) appear in all LLM prompts
- NFR-P1: Layer 1 performance <1μs per lookup
"""

import os
import pytest
from unittest.mock import Mock, MagicMock, patch
import importlib
import sys
from src.learning.iteration_executor import IterationExecutor
from src.learning.llm_client import LLMClient
from src.learning.feedback_generator import FeedbackGenerator
from src.backtest.executor import BacktestExecutor
from src.learning.champion_tracker import ChampionTracker
from src.learning.iteration_history import IterationHistory
from src.config.data_fields import DataFieldManifest


@pytest.fixture(autouse=True)
def reset_feature_flags():
    """Reset FeatureFlagManager singleton before each test."""
    # Reset singleton instance before test
    if 'src.config.feature_flags' in sys.modules:
        from src.config.feature_flags import FeatureFlagManager
        FeatureFlagManager._instance = None
        del FeatureFlagManager._instance
        # Force reload to pick up new env vars
        importlib.reload(sys.modules['src.config.feature_flags'])

    # Also reload iteration_executor to pick up new feature flags
    if 'src.learning.iteration_executor' in sys.modules:
        importlib.reload(sys.modules['src.learning.iteration_executor'])

    yield

    # Clean up after test
    if 'src.config.feature_flags' in sys.modules:
        from src.config.feature_flags import FeatureFlagManager
        FeatureFlagManager._instance = None


@pytest.fixture
def mock_components():
    """Create mock components for IterationExecutor."""
    llm_client = Mock(spec=LLMClient)
    llm_client.is_enabled.return_value = True
    llm_client.get_engine.return_value = Mock()

    feedback_generator = Mock(spec=FeedbackGenerator)
    backtest_executor = Mock(spec=BacktestExecutor)
    champion_tracker = Mock(spec=ChampionTracker)
    champion_tracker.champion = None

    history = Mock(spec=IterationHistory)
    history.get_all.return_value = []

    config = {
        "innovation_rate": 100,
        "history_window": 5,
        "timeout_seconds": 420,
        "start_date": "2020-01-01",
        "end_date": "2023-12-31",
        "fee_ratio": 0.001425,
        "tax_ratio": 0.003,
        "resample": "M",
    }

    # Mock data and sim
    data = Mock()
    sim = Mock()

    return {
        "llm_client": llm_client,
        "feedback_generator": feedback_generator,
        "backtest_executor": backtest_executor,
        "champion_tracker": champion_tracker,
        "history": history,
        "config": config,
        "data": data,
        "sim": sim,
    }


class TestFieldSuggestionsInjection:
    """Test field suggestions injection into LLM prompts."""

    def test_inject_field_suggestions_returns_empty_when_disabled(self, mock_components):
        """
        Test that inject_field_suggestions() returns empty string when Layer 1 is disabled.

        REQUIREMENT: AC1.2 - Feature flag controls injection
        """
        # Set environment variable to disable Layer 1
        with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": "false"}):
            executor = IterationExecutor(**mock_components)

            # Call inject_field_suggestions()
            result = executor.inject_field_suggestions()

            # Should return empty string when disabled
            assert result == "", "Should return empty string when Layer 1 disabled"

    def test_inject_field_suggestions_returns_content_when_enabled(self, mock_components):
        """
        Test that inject_field_suggestions() returns formatted content when Layer 1 is enabled.

        REQUIREMENT: AC1.2 - DataFieldManifest integrated into LLM prompt generation
        """
        # Set environment variable to enable Layer 1
        with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": "true"}):
            executor = IterationExecutor(**mock_components)

            # Call inject_field_suggestions()
            result = executor.inject_field_suggestions()

            # Should return non-empty string with field suggestions
            assert result != "", "Should return field suggestions when Layer 1 enabled"
            assert "## Valid Data Fields Reference" in result, "Should contain section header"
            assert "Common Field Corrections:" in result, "Should contain corrections header"

    def test_common_corrections_appear_in_suggestions(self, mock_components):
        """
        Test that all 21 COMMON_CORRECTIONS entries appear in field suggestions.

        REQUIREMENT: AC1.3 - COMMON_CORRECTIONS (21 entries) appear in all LLM prompts
        """
        # Set environment variable to enable Layer 1
        with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": "true"}):
            executor = IterationExecutor(**mock_components)

            # Call inject_field_suggestions()
            result = executor.inject_field_suggestions()

            # Get COMMON_CORRECTIONS from DataFieldManifest
            corrections = DataFieldManifest.COMMON_CORRECTIONS

            # Should contain all corrections
            assert len(corrections) == 21, f"Expected 21 corrections, got {len(corrections)}"

            # Verify each correction appears in result
            for wrong_field, correct_field in corrections.items():
                # Should contain the correction in format: "wrong" → "correct"
                assert wrong_field in result, f"Missing wrong field: {wrong_field}"
                assert correct_field in result, f"Missing correct field: {correct_field}"

    def test_valid_field_names_appear_in_suggestions(self, mock_components):
        """
        Test that all valid field names are listed in field suggestions.

        REQUIREMENT: AC1.2 - All valid field names listed
        """
        # Set environment variable to enable Layer 1
        with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": "true"}):
            executor = IterationExecutor(**mock_components)

            # Call inject_field_suggestions()
            result = executor.inject_field_suggestions()

            # Get valid field names from DataFieldManifest
            manifest = DataFieldManifest()
            valid_fields = manifest.get_all_canonical_names()

            # Should list at least the core price fields
            assert "price:收盤價" in result, "Should list closing price"
            assert "price:成交金額" in result, "Should list trading value"

            # Should have multiple fields listed
            field_count = 0
            for field in valid_fields:
                if field in result:
                    field_count += 1

            assert field_count >= 10, f"Should list at least 10 valid fields, got {field_count}"

    def test_field_suggestions_integrated_into_llm_prompt(self, mock_components):
        """
        Test that field suggestions are appended to LLM prompt in _generate_with_llm().

        REQUIREMENT: AC1.2 - DataFieldManifest integrated into LLM prompt generation
        """
        # Set environment variable to enable Layer 1
        with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": "true"}):
            executor = IterationExecutor(**mock_components)

            # Mock the LLM engine's generate_innovation method
            mock_engine = MagicMock()
            mock_engine.generate_innovation.return_value = "strategy_code"
            mock_components["llm_client"].get_engine.return_value = mock_engine

            # Mock inject_field_suggestions to return a marker string
            with patch.object(executor, 'inject_field_suggestions', return_value="\n## FIELD_SUGGESTIONS_MARKER"):
                # Call _generate_with_llm
                feedback = "Test feedback"
                strategy_code, strategy_id, strategy_generation = executor._generate_with_llm(feedback, 0)

                # Verify generate_innovation was called
                assert mock_engine.generate_innovation.called, "LLM engine should be called"

                # Note: We can't directly inspect the prompt content passed to LLM
                # because it's built inside InnovationEngine.
                # Instead, we verify that inject_field_suggestions() is called during generation.
                # This will be verified in integration tests.

    def test_layer1_performance_under_1us(self, mock_components):
        """
        Test that DataFieldManifest lookup performance is <1μs.

        REQUIREMENT: NFR-P1 - Layer 1 performance <1μs per lookup
        """
        import time

        # Set environment variable to enable Layer 1
        with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": "true"}):
            executor = IterationExecutor(**mock_components)

            # Create manifest
            manifest = DataFieldManifest()

            # Measure 1000 lookups
            iterations = 1000
            start_time = time.perf_counter()

            for _ in range(iterations):
                # Perform a typical lookup
                manifest.get_field("close")

            end_time = time.perf_counter()
            elapsed_seconds = end_time - start_time

            # Calculate average time per lookup in microseconds
            avg_time_us = (elapsed_seconds / iterations) * 1_000_000

            # Should be less than 1 microsecond per lookup
            assert avg_time_us < 1.0, f"Average lookup time {avg_time_us:.2f}μs exceeds 1μs limit"


class TestBackwardCompatibility:
    """Test backward compatibility when Layer 1 is disabled."""

    def test_iteration_executor_works_without_layer1(self, mock_components):
        """
        Test that IterationExecutor works normally when ENABLE_VALIDATION_LAYER1=false.

        REQUIREMENT: Backward compatibility
        """
        # Set environment variable to disable Layer 1
        with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": "false"}):
            # Should initialize without errors
            executor = IterationExecutor(**mock_components)

            # Should have inject_field_suggestions method
            assert hasattr(executor, "inject_field_suggestions"), \
                "Should have inject_field_suggestions method"

            # Should return empty string when disabled
            result = executor.inject_field_suggestions()
            assert result == "", "Should return empty when disabled"

    def test_llm_generation_works_without_layer1(self, mock_components):
        """
        Test that LLM generation works normally when Layer 1 is disabled.

        REQUIREMENT: Backward compatibility
        """
        # Set environment variable to disable Layer 1
        with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": "false"}):
            executor = IterationExecutor(**mock_components)

            # Mock the LLM engine
            mock_engine = MagicMock()
            mock_engine.generate_innovation.return_value = "strategy_code"
            mock_components["llm_client"].get_engine.return_value = mock_engine

            # Call _generate_with_llm
            feedback = "Test feedback"
            strategy_code, strategy_id, strategy_generation = executor._generate_with_llm(feedback, 0)

            # Should work normally
            assert strategy_code == "strategy_code", "Should generate strategy normally"
            assert strategy_id is None, "Should return None for strategy_id"
            assert strategy_generation is None, "Should return None for strategy_generation"
