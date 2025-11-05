"""
Comprehensive test suite for FeedbackGenerator.

Test Coverage:
1. Basic Functionality
   - Test initialization with IterationHistory and ChampionTracker
   - Test FeedbackContext dataclass creation

2. Template Selection (6 scenarios)
   - Iteration 0 (no history) → uses TEMPLATE_ITERATION_0
   - Success with improving Sharpe → uses TEMPLATE_SUCCESS_IMPROVING
   - Success with declining Sharpe → uses TEMPLATE_SUCCESS_DECLINING
   - Timeout error → uses TEMPLATE_TIMEOUT
   - Execution error → uses TEMPLATE_EXECUTION_ERROR
   - Trend analysis helper

3. Champion Integration
   - Feedback when champion exists (show comparison)
   - Feedback when no champion exists (encourage first milestone)

4. Trend Analysis
   - Improving trend (e.g., "0.5 → 0.8 → 1.2")
   - Declining trend (e.g., "1.5 → 1.2 → 0.9")
   - Flat trend (e.g., "1.0 → 1.0 → 1.0")
   - Edge case: only 1-2 records

5. Length Constraints
   - Verify feedback is <500 words
   - Test truncation if feedback exceeds limit
   - Verify templates are <100 words each

6. Error Handling
   - Handle missing metrics gracefully
   - Handle empty history
   - Handle None values

Task: Week 3 Development - Task 2.3 (FeedbackGenerator Test Suite)
Dependencies: Task 2.1-2.2 COMPLETE (FeedbackGenerator implementation)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, Optional, List

from src.learning.feedback_generator import (
    FeedbackGenerator,
    FeedbackContext,
    TEMPLATE_ITERATION_0,
    TEMPLATE_SUCCESS_SIMPLE,
    TEMPLATE_SUCCESS_IMPROVING,
    TEMPLATE_SUCCESS_DECLINING,
    TEMPLATE_TIMEOUT,
    TEMPLATE_EXECUTION_ERROR,
)


# ==============================================================================
# Test FeedbackContext Dataclass
# ==============================================================================

class TestFeedbackContext:
    """Test FeedbackContext dataclass creation and validation."""

    def test_feedback_context_creation(self):
        """Create FeedbackContext with valid data."""
        context = FeedbackContext(
            iteration_num=5,
            metrics={'sharpe_ratio': 1.5, 'annual_return': 0.25},
            execution_result={'status': 'success', 'execution_time': 5.2},
            classification_level='LEVEL_3',
            error_msg=None
        )

        assert context.iteration_num == 5
        assert context.metrics['sharpe_ratio'] == 1.5
        assert context.execution_result['status'] == 'success'
        assert context.classification_level == 'LEVEL_3'
        assert context.error_msg is None

    def test_feedback_context_with_error(self):
        """Create FeedbackContext with error information."""
        context = FeedbackContext(
            iteration_num=10,
            metrics=None,
            execution_result={'status': 'error'},
            classification_level=None,
            error_msg='data.get() called with invalid key: market_value'
        )

        assert context.iteration_num == 10
        assert context.metrics is None
        assert context.execution_result['status'] == 'error'
        assert context.classification_level is None
        assert 'invalid key' in context.error_msg

    def test_feedback_context_default_error_msg(self):
        """FeedbackContext with default error_msg=None."""
        context = FeedbackContext(
            iteration_num=0,
            metrics={'sharpe_ratio': 1.0},
            execution_result={'status': 'success'},
            classification_level='LEVEL_1'
        )

        assert context.error_msg is None


# ==============================================================================
# Test FeedbackGenerator Initialization
# ==============================================================================

class TestFeedbackGeneratorInitialization:
    """Test FeedbackGenerator initialization and basic functionality."""

    @pytest.fixture
    def mock_history(self):
        """Mock IterationHistory."""
        mock = MagicMock()
        mock.load_recent.return_value = []
        return mock

    @pytest.fixture
    def mock_champion_tracker(self):
        """Mock ChampionTracker."""
        mock = MagicMock()
        mock.champion = None
        return mock

    @pytest.fixture
    def feedback_generator(self, mock_history, mock_champion_tracker):
        """Create FeedbackGenerator with mocked dependencies."""
        return FeedbackGenerator(mock_history, mock_champion_tracker)

    def test_initialization(self, mock_history, mock_champion_tracker):
        """Test FeedbackGenerator initialization."""
        generator = FeedbackGenerator(mock_history, mock_champion_tracker)

        assert generator.history == mock_history
        assert generator.champion_tracker == mock_champion_tracker

    def test_generate_feedback_returns_string(self, feedback_generator):
        """Test that generate_feedback returns a string."""
        result = feedback_generator.generate_feedback(
            iteration_num=0,
            metrics=None,
            execution_result={'status': 'success'},
            classification_level=None
        )

        assert isinstance(result, str)
        assert len(result) > 0


# ==============================================================================
# Test Template Selection
# ==============================================================================

class TestTemplateSelection:
    """Test template selection logic for different scenarios."""

    @pytest.fixture
    def mock_history(self):
        """Mock IterationHistory."""
        mock = MagicMock()
        mock.load_recent.return_value = []
        return mock

    @pytest.fixture
    def mock_champion_tracker(self):
        """Mock ChampionTracker."""
        mock = MagicMock()
        mock.champion = None
        return mock

    @pytest.fixture
    def feedback_generator(self, mock_history, mock_champion_tracker):
        """Create FeedbackGenerator with mocked dependencies."""
        return FeedbackGenerator(mock_history, mock_champion_tracker)

    def test_iteration_0_uses_iteration_0_template(self, feedback_generator):
        """Iteration 0 (no history) uses TEMPLATE_ITERATION_0."""
        feedback = feedback_generator.generate_feedback(
            iteration_num=0,
            metrics=None,
            execution_result={'status': 'success'},
            classification_level=None
        )

        # Verify template content present
        assert "iteration 0" in feedback.lower() or "starting" in feedback.lower()
        assert "goal" in feedback.lower() or "sharpe ratio" in feedback.lower()

    def test_success_improving_uses_improving_template(self, feedback_generator, mock_history):
        """Success with improving Sharpe uses TEMPLATE_SUCCESS_IMPROVING."""
        # Mock history: previous iteration had Sharpe 1.0
        mock_record1 = MagicMock()
        mock_record1.metrics = {'sharpe_ratio': 1.5}  # Current (first in list)
        mock_record1.iteration_num = 5

        mock_record2 = MagicMock()
        mock_record2.metrics = {'sharpe_ratio': 1.0}  # Previous
        mock_record2.iteration_num = 4

        mock_history.load_recent.return_value = [mock_record1, mock_record2]

        feedback = feedback_generator.generate_feedback(
            iteration_num=5,
            metrics={'sharpe_ratio': 1.5},
            execution_result={'status': 'success'},
            classification_level='LEVEL_3'
        )

        # Verify improving template content
        assert "progress" in feedback.lower() or "improvement" in feedback.lower()
        assert "1.000" in feedback or "1.0" in feedback  # Previous Sharpe
        assert "1.500" in feedback or "1.5" in feedback  # Current Sharpe

    def test_success_declining_uses_declining_template(self, feedback_generator, mock_history):
        """Success with declining Sharpe uses TEMPLATE_SUCCESS_DECLINING."""
        # Mock history: previous iteration had Sharpe 1.5
        mock_record1 = MagicMock()
        mock_record1.metrics = {'sharpe_ratio': 1.0}  # Current (declining)
        mock_record1.iteration_num = 5

        mock_record2 = MagicMock()
        mock_record2.metrics = {'sharpe_ratio': 1.5}  # Previous (better)
        mock_record2.iteration_num = 4

        mock_history.load_recent.return_value = [mock_record1, mock_record2]

        feedback = feedback_generator.generate_feedback(
            iteration_num=5,
            metrics={'sharpe_ratio': 1.0},
            execution_result={'status': 'success'},
            classification_level='LEVEL_2'
        )

        # Verify declining template content
        assert "declining" in feedback.lower() or "warning" in feedback.lower()
        assert "1.5" in feedback  # Previous Sharpe
        assert "1.0" in feedback  # Current Sharpe

    def test_timeout_uses_timeout_template(self, feedback_generator):
        """Timeout error uses TEMPLATE_TIMEOUT."""
        feedback = feedback_generator.generate_feedback(
            iteration_num=10,
            metrics=None,
            execution_result={'status': 'timeout'},
            classification_level=None
        )

        # Verify timeout template content
        assert "timeout" in feedback.lower()
        assert "infinite loop" in feedback.lower() or "exceeded time limit" in feedback.lower()

    def test_execution_error_uses_error_template(self, feedback_generator):
        """Execution error uses TEMPLATE_EXECUTION_ERROR."""
        feedback = feedback_generator.generate_feedback(
            iteration_num=10,
            metrics=None,
            execution_result={'status': 'error'},
            classification_level=None,
            error_msg='data.get() called with invalid key: market_value'
        )

        # Verify error template content
        assert "error" in feedback.lower()
        assert "data.get()" in feedback or "market_value" in feedback
        assert "common causes" in feedback.lower() or "debugging" in feedback.lower()

    def test_template_selection_early_iteration_fallback(self, feedback_generator, mock_history):
        """Iteration 1 with insufficient history uses TEMPLATE_SUCCESS_SIMPLE."""
        # Mock history with only 1 record (not enough for trend analysis)
        mock_record = MagicMock()
        mock_record.metrics = {'sharpe_ratio': 0.8}
        mock_record.iteration_num = 0
        mock_history.load_recent.return_value = [mock_record]

        feedback = feedback_generator.generate_feedback(
            iteration_num=1,
            metrics={'sharpe_ratio': 1.2},
            execution_result={'status': 'success'},
            classification_level='LEVEL_3'
        )

        # Verify TEMPLATE_SUCCESS_SIMPLE content
        assert "Iteration 1: SUCCESS" in feedback
        assert "Not enough history for trend analysis yet" in feedback
        assert "No previous history yet" not in feedback  # Should NOT say this


# ==============================================================================
# Test Champion Integration
# ==============================================================================

class TestChampionIntegration:
    """Test champion integration in feedback generation."""

    @pytest.fixture
    def mock_history(self):
        """Mock IterationHistory."""
        mock = MagicMock()
        # Mock history with 2 records for trend analysis
        mock_record1 = MagicMock()
        mock_record1.metrics = {'sharpe_ratio': 1.5}
        mock_record1.iteration_num = 5

        mock_record2 = MagicMock()
        mock_record2.metrics = {'sharpe_ratio': 1.0}
        mock_record2.iteration_num = 4

        mock.load_recent.return_value = [mock_record1, mock_record2]
        return mock

    @pytest.fixture
    def feedback_generator_no_champion(self, mock_history):
        """Create FeedbackGenerator with no champion."""
        mock_champion_tracker = MagicMock()
        mock_champion_tracker.champion = None
        return FeedbackGenerator(mock_history, mock_champion_tracker)

    @pytest.fixture
    def feedback_generator_with_champion(self, mock_history):
        """Create FeedbackGenerator with existing champion."""
        mock_champion_tracker = MagicMock()
        mock_champion = MagicMock()
        mock_champion.metrics = {'sharpe_ratio': 2.0}
        mock_champion_tracker.champion = mock_champion
        return FeedbackGenerator(mock_history, mock_champion_tracker)

    def test_feedback_no_champion_encourages_milestone(self, feedback_generator_no_champion):
        """When no champion exists, feedback encourages first milestone."""
        feedback = feedback_generator_no_champion.generate_feedback(
            iteration_num=5,
            metrics={'sharpe_ratio': 1.5},
            execution_result={'status': 'success'},
            classification_level='LEVEL_3'
        )

        # Should mention no champion or setting baseline
        assert "no champion" in feedback.lower() or "baseline" in feedback.lower() or "setting" in feedback.lower()

    def test_feedback_with_champion_shows_comparison(self, feedback_generator_with_champion):
        """When champion exists, feedback shows comparison."""
        feedback = feedback_generator_with_champion.generate_feedback(
            iteration_num=5,
            metrics={'sharpe_ratio': 1.5},
            execution_result={'status': 'success'},
            classification_level='LEVEL_3'
        )

        # Should mention champion or target
        assert "champion" in feedback.lower() or "target" in feedback.lower()
        # Should show champion Sharpe (2.0)
        assert "2.0" in feedback

    def test_feedback_champion_comparison_above_champion(self, feedback_generator_with_champion):
        """Feedback shows when current strategy is above champion."""
        feedback = feedback_generator_with_champion.generate_feedback(
            iteration_num=5,
            metrics={'sharpe_ratio': 2.5},  # Above champion (2.0)
            execution_result={'status': 'success'},
            classification_level='LEVEL_4'
        )

        # Should indicate above champion
        assert "above" in feedback.lower() or "✅" in feedback or "beat" in feedback.lower()

    def test_feedback_champion_comparison_below_champion(self, feedback_generator_with_champion):
        """Feedback shows when current strategy is below champion."""
        feedback = feedback_generator_with_champion.generate_feedback(
            iteration_num=5,
            metrics={'sharpe_ratio': 1.2},  # Below champion (2.0)
            execution_result={'status': 'success'},
            classification_level='LEVEL_2'
        )

        # Should indicate gap to champion
        assert "gap" in feedback.lower() or "below" in feedback.lower() or "target" in feedback.lower()


# ==============================================================================
# Test Trend Analysis
# ==============================================================================

class TestTrendAnalysis:
    """Test trend analysis functionality."""

    @pytest.fixture
    def mock_champion_tracker(self):
        """Mock ChampionTracker."""
        mock = MagicMock()
        mock.champion = None
        return mock

    @pytest.fixture
    def feedback_generator(self, mock_champion_tracker):
        """Create FeedbackGenerator with mock champion tracker."""
        mock_history = MagicMock()
        return FeedbackGenerator(mock_history, mock_champion_tracker)

    def test_improving_trend(self, feedback_generator):
        """Test improving trend (e.g., 0.5 → 0.8 → 1.2)."""
        # Mock history with improving trend
        mock_records = []
        sharpe_values = [0.5, 0.8, 1.0, 1.2]
        for i, sharpe in enumerate(sharpe_values):
            record = MagicMock()
            record.metrics = {'sharpe_ratio': sharpe}
            record.iteration_num = i
            mock_records.append(record)

        mock_records.reverse()  # Newest first

        trend_summary = feedback_generator._analyze_trend(mock_records)

        assert "improving" in trend_summary.lower()
        assert "0.50" in trend_summary or "0.5" in trend_summary
        assert "1.20" in trend_summary or "1.2" in trend_summary

    def test_declining_trend(self, feedback_generator):
        """Test declining trend (e.g., 1.5 → 1.2 → 0.9)."""
        # Mock history with declining trend
        mock_records = []
        sharpe_values = [1.5, 1.2, 1.0, 0.9]
        for i, sharpe in enumerate(sharpe_values):
            record = MagicMock()
            record.metrics = {'sharpe_ratio': sharpe}
            record.iteration_num = i
            mock_records.append(record)

        mock_records.reverse()  # Newest first

        trend_summary = feedback_generator._analyze_trend(mock_records)

        assert "declining" in trend_summary.lower() or "weakening" in trend_summary.lower()
        assert "1.50" in trend_summary or "1.5" in trend_summary
        assert "0.90" in trend_summary or "0.9" in trend_summary

    def test_flat_trend(self, feedback_generator):
        """Test flat trend (e.g., 1.0 → 1.0 → 1.0)."""
        # Mock history with flat trend
        mock_records = []
        for i in range(5):
            record = MagicMock()
            record.metrics = {'sharpe_ratio': 1.0}
            record.iteration_num = i
            mock_records.append(record)

        mock_records.reverse()  # Newest first

        trend_summary = feedback_generator._analyze_trend(mock_records)

        assert "1.00" in trend_summary or "1.0" in trend_summary
        # Flat trend might be classified as "fluctuating" or similar
        assert len(trend_summary) > 0

    def test_trend_analysis_limited_history_2_records(self, feedback_generator):
        """Test trend analysis with only 2 records."""
        mock_records = []
        for i, sharpe in enumerate([0.8, 1.0]):
            record = MagicMock()
            record.metrics = {'sharpe_ratio': sharpe}
            record.iteration_num = i
            mock_records.append(record)

        mock_records.reverse()  # Newest first

        trend_summary = feedback_generator._analyze_trend(mock_records)

        # Should indicate limited history
        assert "limited" in trend_summary.lower() or "history" in trend_summary.lower()

    def test_trend_analysis_limited_history_1_record(self, feedback_generator):
        """Test trend analysis with only 1 record."""
        record = MagicMock()
        record.metrics = {'sharpe_ratio': 1.5}
        record.iteration_num = 0
        mock_records = [record]

        trend_summary = feedback_generator._analyze_trend(mock_records)

        # Should indicate limited history
        assert "limited" in trend_summary.lower() or "history" in trend_summary.lower()

    def test_analyze_trend_improving_non_monotonic(self, feedback_generator):
        """Non-monotonic upward trend classified as 'improving'."""
        mock_records = []
        sharpe_values = [1.0, 0.8, 1.1]  # Dip then recovery above start
        for i, sharpe in enumerate(sharpe_values):
            record = MagicMock()
            record.metrics = {'sharpe_ratio': sharpe}
            record.iteration_num = i
            mock_records.append(record)

        mock_records.reverse()  # Newest first

        trend = feedback_generator._analyze_trend(mock_records)
        assert "improving" in trend.lower()

    def test_analyze_trend_weakening(self, feedback_generator):
        """Non-monotonic downward trend classified as 'weakening'."""
        mock_records = []
        sharpe_values = [1.0, 1.2, 0.9]  # Peak then drop below start
        for i, sharpe in enumerate(sharpe_values):
            record = MagicMock()
            record.metrics = {'sharpe_ratio': sharpe}
            record.iteration_num = i
            mock_records.append(record)

        mock_records.reverse()  # Newest first

        trend = feedback_generator._analyze_trend(mock_records)
        assert "weakening" in trend.lower()


# ==============================================================================
# Test Length Constraints
# ==============================================================================

class TestLengthConstraints:
    """Test feedback length constraints."""

    @pytest.fixture
    def mock_history(self):
        """Mock IterationHistory."""
        mock = MagicMock()
        mock.load_recent.return_value = []
        return mock

    @pytest.fixture
    def mock_champion_tracker(self):
        """Mock ChampionTracker."""
        mock = MagicMock()
        mock.champion = None
        return mock

    @pytest.fixture
    def feedback_generator(self, mock_history, mock_champion_tracker):
        """Create FeedbackGenerator with mocked dependencies."""
        return FeedbackGenerator(mock_history, mock_champion_tracker)

    def test_feedback_under_500_words(self, feedback_generator):
        """Verify feedback is under 500 words."""
        feedback = feedback_generator.generate_feedback(
            iteration_num=5,
            metrics={'sharpe_ratio': 1.5},
            execution_result={'status': 'success'},
            classification_level='LEVEL_3'
        )

        word_count = len(feedback.split())
        assert word_count <= 500, f"Feedback exceeds 500 words: {word_count} words"

    def test_truncation_with_excessive_feedback(self, feedback_generator):
        """Test truncation if feedback exceeds 500 word limit."""
        # Mock a template that returns excessive content
        with patch.object(feedback_generator, '_select_template_and_variables') as mock_select:
            # Create feedback with >500 words
            long_text = " ".join(["word"] * 600)
            mock_select.return_value = (long_text, {})

            feedback = feedback_generator.generate_feedback(
                iteration_num=5,
                metrics={'sharpe_ratio': 1.5},
                execution_result={'status': 'success'},
                classification_level='LEVEL_3'
            )

            word_count = len(feedback.split())
            assert word_count <= 500, "Feedback should be truncated to 500 words"
            assert feedback.endswith("..."), "Truncated feedback should end with ..."

    def test_template_iteration_0_under_100_words(self):
        """Verify TEMPLATE_ITERATION_0 is under 100 words."""
        word_count = len(TEMPLATE_ITERATION_0.split())
        assert word_count <= 100, f"TEMPLATE_ITERATION_0 exceeds 100 words: {word_count} words"

    def test_template_success_improving_under_100_words(self):
        """Verify TEMPLATE_SUCCESS_IMPROVING is under 100 words."""
        word_count = len(TEMPLATE_SUCCESS_IMPROVING.split())
        assert word_count <= 100, f"TEMPLATE_SUCCESS_IMPROVING exceeds 100 words: {word_count} words"

    def test_template_success_declining_under_100_words(self):
        """Verify TEMPLATE_SUCCESS_DECLINING is under 100 words."""
        word_count = len(TEMPLATE_SUCCESS_DECLINING.split())
        assert word_count <= 100, f"TEMPLATE_SUCCESS_DECLINING exceeds 100 words: {word_count} words"

    def test_template_timeout_under_100_words(self):
        """Verify TEMPLATE_TIMEOUT is under 100 words."""
        word_count = len(TEMPLATE_TIMEOUT.split())
        assert word_count <= 100, f"TEMPLATE_TIMEOUT exceeds 100 words: {word_count} words"

    def test_template_execution_error_under_100_words(self):
        """Verify TEMPLATE_EXECUTION_ERROR is under 100 words."""
        word_count = len(TEMPLATE_EXECUTION_ERROR.split())
        assert word_count <= 100, f"TEMPLATE_EXECUTION_ERROR exceeds 100 words: {word_count} words"


# ==============================================================================
# Test Error Handling
# ==============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def mock_history(self):
        """Mock IterationHistory."""
        mock = MagicMock()
        mock.load_recent.return_value = []
        return mock

    @pytest.fixture
    def mock_champion_tracker(self):
        """Mock ChampionTracker."""
        mock = MagicMock()
        mock.champion = None
        return mock

    @pytest.fixture
    def feedback_generator(self, mock_history, mock_champion_tracker):
        """Create FeedbackGenerator with mocked dependencies."""
        return FeedbackGenerator(mock_history, mock_champion_tracker)

    def test_handle_missing_sharpe_ratio_in_metrics(self, feedback_generator, mock_history):
        """Handle missing sharpe_ratio gracefully."""
        # Mock history with records missing sharpe_ratio
        mock_record1 = MagicMock()
        mock_record1.metrics = {'annual_return': 0.25}  # No sharpe_ratio
        mock_record1.iteration_num = 5

        mock_record2 = MagicMock()
        mock_record2.metrics = {'annual_return': 0.20}  # No sharpe_ratio
        mock_record2.iteration_num = 4

        mock_history.load_recent.return_value = [mock_record1, mock_record2]

        # Should not crash
        feedback = feedback_generator.generate_feedback(
            iteration_num=5,
            metrics={'annual_return': 0.25},  # No sharpe_ratio
            execution_result={'status': 'success'},
            classification_level='LEVEL_1'
        )

        assert isinstance(feedback, str)
        assert len(feedback) > 0

    def test_handle_none_metrics(self, feedback_generator):
        """Handle None metrics gracefully."""
        feedback = feedback_generator.generate_feedback(
            iteration_num=5,
            metrics=None,
            execution_result={'status': 'error'},
            classification_level=None,
            error_msg='Execution failed'
        )

        assert isinstance(feedback, str)
        assert len(feedback) > 0
        assert "error" in feedback.lower()

    def test_handle_empty_history(self, feedback_generator, mock_history):
        """Handle empty iteration history gracefully."""
        mock_history.load_recent.return_value = []

        feedback = feedback_generator.generate_feedback(
            iteration_num=5,
            metrics={'sharpe_ratio': 1.5},
            execution_result={'status': 'success'},
            classification_level='LEVEL_3'
        )

        assert isinstance(feedback, str)
        assert len(feedback) > 0

    def test_handle_none_error_msg(self, feedback_generator):
        """Handle None error_msg gracefully."""
        feedback = feedback_generator.generate_feedback(
            iteration_num=5,
            metrics=None,
            execution_result={'status': 'error'},
            classification_level=None,
            error_msg=None
        )

        assert isinstance(feedback, str)
        assert "unknown error" in feedback.lower()

    def test_handle_none_classification_level(self, feedback_generator, mock_history):
        """Handle None classification_level gracefully."""
        mock_record1 = MagicMock()
        mock_record1.metrics = {'sharpe_ratio': 1.5}
        mock_record1.iteration_num = 5

        mock_record2 = MagicMock()
        mock_record2.metrics = {'sharpe_ratio': 1.0}
        mock_record2.iteration_num = 4

        mock_history.load_recent.return_value = [mock_record1, mock_record2]

        feedback = feedback_generator.generate_feedback(
            iteration_num=5,
            metrics={'sharpe_ratio': 1.5},
            execution_result={'status': 'success'},
            classification_level=None  # None classification
        )

        assert isinstance(feedback, str)
        assert len(feedback) > 0

    def test_find_last_success_with_no_success(self, feedback_generator):
        """Test _find_last_success when no successful iterations exist."""
        mock_records = []
        for i in range(5):
            record = MagicMock()
            record.execution_result = {'status': 'error'}
            record.iteration_num = i
            mock_records.append(record)

        last_success = feedback_generator._find_last_success(mock_records)

        assert last_success is None

    def test_find_last_success_with_success(self, feedback_generator):
        """Test _find_last_success when successful iteration exists."""
        mock_records = []
        # Add error records
        for i in range(3):
            record = MagicMock()
            record.execution_result = {'status': 'error'}
            record.iteration_num = i + 5
            mock_records.append(record)

        # Add successful record
        success_record = MagicMock()
        success_record.execution_result = {'status': 'success'}
        success_record.metrics = {'sharpe_ratio': 1.5}
        success_record.iteration_num = 4
        mock_records.append(success_record)

        last_success = feedback_generator._find_last_success(mock_records)

        assert last_success is not None
        assert last_success.iteration_num == 4

    def test_format_last_success_with_none(self, feedback_generator):
        """Test _format_last_success with None input."""
        formatted = feedback_generator._format_last_success(None)

        assert isinstance(formatted, str)
        assert "no recent successful" in formatted.lower() or "review fundamentals" in formatted.lower()

    def test_format_last_success_with_record(self, feedback_generator):
        """Test _format_last_success with valid record."""
        mock_record = MagicMock()
        mock_record.iteration_num = 10
        mock_record.metrics = {'sharpe_ratio': 2.0}

        formatted = feedback_generator._format_last_success(mock_record)

        assert isinstance(formatted, str)
        assert "iteration 10" in formatted.lower()
        assert "2.0" in formatted

    def test_negative_sharpe_absolute_change(self, feedback_generator, mock_history):
        """Negative Sharpe shows absolute change, not percentage."""
        # Mock history with negative Sharpe improving from -2.0 to -1.0
        mock_record1 = MagicMock()
        mock_record1.metrics = {'sharpe_ratio': -1.0}  # Current (improved but still negative)
        mock_record1.iteration_num = 1

        mock_record2 = MagicMock()
        mock_record2.metrics = {'sharpe_ratio': -2.0}  # Previous (worse)
        mock_record2.iteration_num = 0

        mock_history.load_recent.return_value = [mock_record1, mock_record2]

        feedback = feedback_generator.generate_feedback(
            iteration_num=1,
            metrics={'sharpe_ratio': -1.0},
            execution_result={'status': 'success'},
            classification_level='LEVEL_2'
        )

        # Should show absolute change, not percentage
        assert "absolute" in feedback.lower()
        assert "-1.0" in feedback or "-1.00" in feedback


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestFeedbackGeneratorIntegration:
    """Integration tests for FeedbackGenerator with realistic scenarios."""

    @pytest.fixture
    def mock_history(self):
        """Mock IterationHistory with realistic data."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_champion_tracker(self):
        """Mock ChampionTracker with realistic champion."""
        mock = MagicMock()
        mock_champion = MagicMock()
        mock_champion.metrics = {'sharpe_ratio': 2.5}
        mock.champion = mock_champion
        return mock

    @pytest.fixture
    def feedback_generator(self, mock_history, mock_champion_tracker):
        """Create FeedbackGenerator with realistic dependencies."""
        return FeedbackGenerator(mock_history, mock_champion_tracker)

    def test_realistic_improving_iteration(self, feedback_generator, mock_history):
        """Test realistic improving iteration scenario."""
        # Mock realistic history
        mock_records = []
        sharpe_values = [1.0, 1.2, 1.5, 1.8, 2.0]
        for i, sharpe in enumerate(sharpe_values):
            record = MagicMock()
            record.metrics = {'sharpe_ratio': sharpe, 'annual_return': sharpe * 0.2}
            record.iteration_num = i
            record.execution_result = {'status': 'success'}
            mock_records.append(record)

        mock_records.reverse()  # Newest first
        mock_history.load_recent.return_value = mock_records

        feedback = feedback_generator.generate_feedback(
            iteration_num=4,
            metrics={'sharpe_ratio': 2.0, 'annual_return': 0.40},
            execution_result={'status': 'success'},
            classification_level='LEVEL_4'
        )

        assert "progress" in feedback.lower() or "improving" in feedback.lower()
        assert "2.0" in feedback  # Current Sharpe
        assert "champion" in feedback.lower()  # Champion reference

    def test_realistic_error_recovery(self, feedback_generator, mock_history):
        """Test realistic error recovery scenario."""
        # Mock history: last success was 3 iterations ago
        mock_records = []

        # Recent errors
        for i in range(3):
            record = MagicMock()
            record.execution_result = {'status': 'error'}
            record.iteration_num = 10 + i
            record.metrics = None
            mock_records.append(record)

        # Last success
        success_record = MagicMock()
        success_record.execution_result = {'status': 'success'}
        success_record.metrics = {'sharpe_ratio': 1.5}
        success_record.iteration_num = 9
        mock_records.append(success_record)

        mock_history.load_recent.return_value = mock_records

        feedback = feedback_generator.generate_feedback(
            iteration_num=13,
            metrics=None,
            execution_result={'status': 'error'},
            classification_level=None,
            error_msg='KeyError: close_price'
        )

        assert "error" in feedback.lower()
        assert "KeyError" in feedback or "close_price" in feedback
        assert "iteration 9" in feedback.lower()  # Last success reference
