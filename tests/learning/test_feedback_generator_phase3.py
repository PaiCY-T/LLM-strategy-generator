"""Tests for FeedbackGenerator StrategyMetrics Integration (Phase 3, Task 3.1).

Tests TC-1.3: FeedbackGenerator.generate_feedback() accepts Optional[StrategyMetrics]

This module verifies that FeedbackGenerator correctly handles StrategyMetrics
instead of Dict[str, float], using attribute access patterns.

Author: Phase 3 Implementation Team
Date: 2025-01-13
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.learning.feedback_generator import FeedbackGenerator
from src.backtest.metrics import StrategyMetrics


@pytest.fixture
def mock_history():
    """Mock IterationHistory for FeedbackGenerator."""
    history = Mock()
    history.load_recent = Mock(return_value=[])
    return history


@pytest.fixture
def mock_champion_tracker():
    """Mock ChampionTracker for FeedbackGenerator."""
    tracker = Mock()
    tracker.champion = None
    return tracker


@pytest.fixture
def feedback_generator(mock_history, mock_champion_tracker):
    """Create FeedbackGenerator with mocked dependencies."""
    return FeedbackGenerator(mock_history, mock_champion_tracker)


class TestFeedbackGeneratorStrategyMetricsIntegration:
    """Test FeedbackGenerator accepts StrategyMetrics parameter (TC-1.3)."""

    def test_generate_feedback_accepts_strategy_metrics_parameter(
        self, feedback_generator, mock_history
    ):
        """TC-1.3: generate_feedback() accepts Optional[StrategyMetrics] parameter.

        WHEN: Call generate_feedback() with StrategyMetrics object
        THEN: Method accepts StrategyMetrics and generates feedback
        """
        # Arrange
        metrics = StrategyMetrics(
            sharpe_ratio=1.85,
            total_return=0.42,
            max_drawdown=-0.15,
            execution_success=True
        )

        # Mock recent records
        mock_record = Mock()
        mock_record.metrics = metrics
        mock_record.classification_level = "LEVEL_3"
        mock_history.load_recent.return_value = [mock_record]

        # Act
        feedback = feedback_generator.generate_feedback(
            iteration_num=1,
            metrics=metrics,
            execution_result={'success': True},
            classification_level='LEVEL_3'
        )

        # Assert
        assert isinstance(feedback, str)
        assert len(feedback) > 0
        assert "Sharpe" in feedback or "sharpe" in feedback

    def test_generate_feedback_uses_attribute_access_for_sharpe_ratio(
        self, feedback_generator, mock_history
    ):
        """TC-1.3: FeedbackGenerator uses metrics.sharpe_ratio (attribute access).

        WHEN: Pass StrategyMetrics to generate_feedback()
        THEN: Internal code uses metrics.sharpe_ratio not metrics.get()
        """
        # Arrange
        metrics = StrategyMetrics(sharpe_ratio=2.15, execution_success=True)

        # Mock recent history with 2 records for trend analysis
        prev_metrics = StrategyMetrics(sharpe_ratio=1.5, execution_success=True)
        mock_prev = Mock()
        mock_prev.metrics = prev_metrics

        current_record = Mock()
        current_record.metrics = metrics

        mock_history.load_recent.return_value = [mock_prev, current_record]

        # Act
        feedback = feedback_generator.generate_feedback(
            iteration_num=5,
            metrics=metrics,
            execution_result={'success': True},
            classification_level='LEVEL_3'
        )

        # Assert
        assert isinstance(feedback, str)
        # Feedback should mention the Sharpe ratio value
        assert "2.15" in feedback or "2.2" in feedback

    def test_generate_feedback_handles_none_strategy_metrics(
        self, feedback_generator, mock_history
    ):
        """TC-1.3: generate_feedback() handles None metrics (execution failure).

        WHEN: Call generate_feedback() with metrics=None
        THEN: Generates appropriate error feedback
        """
        # Arrange
        mock_history.load_recent.return_value = []

        # Act
        feedback = feedback_generator.generate_feedback(
            iteration_num=3,
            metrics=None,
            execution_result={'success': False},
            classification_level=None,
            error_msg="Strategy execution timeout"
        )

        # Assert
        assert isinstance(feedback, str)
        assert "error" in feedback.lower() or "fail" in feedback.lower()

    def test_generate_feedback_handles_partial_strategy_metrics(
        self, feedback_generator, mock_history
    ):
        """TC-1.3: generate_feedback() handles StrategyMetrics with None fields.

        WHEN: StrategyMetrics has some None values
        THEN: Feedback generation handles missing values gracefully
        """
        # Arrange
        metrics = StrategyMetrics(
            sharpe_ratio=1.2,
            total_return=None,  # Missing value
            max_drawdown=None,  # Missing value
            execution_success=True
        )

        mock_record = Mock()
        mock_record.metrics = metrics
        mock_history.load_recent.return_value = [mock_record]

        # Act
        feedback = feedback_generator.generate_feedback(
            iteration_num=2,
            metrics=metrics,
            execution_result={'success': True},
            classification_level='LEVEL_2'
        )

        # Assert
        assert isinstance(feedback, str)
        assert len(feedback) > 0

    def test_champion_comparison_uses_strategy_metrics_attribute_access(
        self, feedback_generator, mock_history, mock_champion_tracker
    ):
        """TC-1.3: Champion comparison uses metrics.sharpe_ratio attribute.

        WHEN: Champion exists with StrategyMetrics
        THEN: Feedback generator accesses champion.metrics.sharpe_ratio
        """
        # Arrange
        current_metrics = StrategyMetrics(sharpe_ratio=2.0, execution_success=True)
        champion_metrics = StrategyMetrics(sharpe_ratio=1.5, execution_success=True)

        mock_champion = Mock()
        mock_champion.metrics = champion_metrics
        mock_champion_tracker.champion = mock_champion

        mock_record = Mock()
        mock_record.metrics = current_metrics
        mock_history.load_recent.return_value = [mock_record]

        # Act
        feedback = feedback_generator.generate_feedback(
            iteration_num=10,
            metrics=current_metrics,
            execution_result={'success': True},
            classification_level='LEVEL_3'
        )

        # Assert
        assert isinstance(feedback, str)
        # Should mention beating champion or gap to champion
        assert ("champion" in feedback.lower() or "Champion" in feedback)


class TestFeedbackGeneratorBackwardCompatibility:
    """Test backward compatibility during transition period."""

    def test_generate_feedback_still_works_with_dict_during_transition(
        self, feedback_generator, mock_history
    ):
        """Transition: generate_feedback() temporarily accepts dict for compatibility.

        WHEN: Pass dict instead of StrategyMetrics (legacy code)
        THEN: Method still works (will be deprecated after full migration)

        Note: This test documents transition behavior and should be removed
        after Task 3.1 implementation is complete and all call sites updated.
        """
        # Arrange
        metrics_dict = {
            'sharpe_ratio': 1.5,
            'total_return': 0.3,
            'max_drawdown': -0.1
        }

        mock_record = Mock()
        mock_record.metrics = metrics_dict
        mock_history.load_recent.return_value = [mock_record]

        # Act - This should work during transition
        feedback = feedback_generator.generate_feedback(
            iteration_num=1,
            metrics=metrics_dict,
            execution_result={'success': True},
            classification_level='LEVEL_3'
        )

        # Assert
        assert isinstance(feedback, str)
        assert len(feedback) > 0

        # TODO: After Task 3.1 complete, this test should be updated to
        # verify that only StrategyMetrics is accepted
