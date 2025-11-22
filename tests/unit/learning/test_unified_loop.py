"""Unit tests for UnifiedLoop.

Tests UnifiedLoop initialization, configuration, and backward compatibility API.

Test Coverage:
    - Initialization (standard mode and template mode)
    - Configuration building
    - Template executor injection
    - Backward compatible API (champion, history properties)
    - Error handling
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.learning.unified_loop import UnifiedLoop
from src.learning.unified_config import ConfigurationError


class TestUnifiedLoopInitialization:
    """Test UnifiedLoop initialization."""

    @patch('src.learning.unified_loop.LearningLoop')
    def test_initialization_standard_mode(self, mock_learning_loop_class):
        """Test initialization in standard mode (template_mode=False)."""
        # Setup mock
        mock_learning_loop = Mock()
        mock_learning_loop_class.return_value = mock_learning_loop

        # Create UnifiedLoop
        loop = UnifiedLoop(
            max_iterations=10,
            template_mode=False
        )

        # Verify initialization
        assert loop.template_mode is False
        assert loop.use_json_mode is False
        assert loop.learning_loop is not None
        assert mock_learning_loop_class.called

    @patch('src.learning.unified_loop.LearningLoop')
    @patch('src.learning.template_iteration_executor.TemplateIterationExecutor')
    def test_initialization_template_mode(self, mock_template_executor_class, mock_learning_loop_class):
        """Test initialization in template mode (template_mode=True)."""
        # Setup mocks
        mock_learning_loop = Mock()
        mock_learning_loop.llm_client = Mock()
        mock_learning_loop.feedback_generator = Mock()
        mock_learning_loop.backtest_executor = Mock()
        mock_learning_loop.champion_tracker = Mock()
        mock_learning_loop.history = Mock()
        mock_learning_loop_class.return_value = mock_learning_loop

        mock_template_executor = Mock()
        mock_template_executor_class.return_value = mock_template_executor

        # Create UnifiedLoop with template mode
        loop = UnifiedLoop(
            max_iterations=10,
            template_mode=True,
            template_name="Momentum",
            use_json_mode=True
        )

        # Verify template mode settings
        assert loop.template_mode is True
        assert loop.use_json_mode is True
        assert loop.config.template_name == "Momentum"

        # Verify TemplateIterationExecutor was injected
        assert mock_template_executor_class.called

    def test_initialization_invalid_config(self):
        """Test initialization with invalid configuration."""
        with pytest.raises(ConfigurationError):
            # template_mode=True requires template_name
            UnifiedLoop(
                max_iterations=10,
                template_mode=True,
                template_name=""  # Invalid
            )


class TestUnifiedLoopConfigurationBuilding:
    """Test configuration building."""

    @patch('src.learning.unified_loop.LearningLoop')
    def test_build_unified_config(self, mock_learning_loop_class):
        """Test _build_unified_config creates valid UnifiedConfig."""
        mock_learning_loop_class.return_value = Mock()

        loop = UnifiedLoop(
            model="gpt-4",
            max_iterations=50,
            template_mode=True,
            template_name="Factor",
            use_json_mode=False,
            timeout_seconds=600
        )

        # Verify config was built correctly
        assert loop.config.llm_model == "gpt-4"
        assert loop.config.max_iterations == 50
        assert loop.config.template_mode is True
        assert loop.config.template_name == "Factor"
        assert loop.config.use_json_mode is False
        assert loop.config.timeout_seconds == 600


class TestUnifiedLoopTemplateExecutorInjection:
    """Test template executor injection."""

    @patch('src.learning.unified_loop.LearningLoop')
    @patch('src.learning.template_iteration_executor.TemplateIterationExecutor')
    def test_inject_template_executor_success(self, mock_template_executor_class, mock_learning_loop_class):
        """Test successful template executor injection."""
        # Setup mocks
        mock_learning_loop = Mock()
        mock_learning_loop.llm_client = Mock()
        mock_learning_loop.feedback_generator = Mock()
        mock_learning_loop.backtest_executor = Mock()
        mock_learning_loop.champion_tracker = Mock()
        mock_learning_loop.history = Mock()
        mock_learning_loop_class.return_value = mock_learning_loop

        mock_template_executor = Mock()
        mock_template_executor_class.return_value = mock_template_executor

        # Create loop with template mode
        loop = UnifiedLoop(
            template_mode=True,
            template_name="Momentum",
            use_json_mode=True
        )

        # Verify injection
        mock_template_executor_class.assert_called_once()
        call_kwargs = mock_template_executor_class.call_args[1]
        assert call_kwargs['template_name'] == "Momentum"
        assert call_kwargs['use_json_mode'] is True

    @patch('src.learning.unified_loop.LearningLoop')
    def test_inject_template_executor_import_error(self, mock_learning_loop_class):
        """Test graceful handling when TemplateIterationExecutor not available."""
        # Setup mock
        mock_learning_loop = Mock()
        mock_learning_loop_class.return_value = mock_learning_loop

        # This should not raise even if TemplateIterationExecutor doesn't exist yet
        # (logs warning instead)
        loop = UnifiedLoop(
            template_mode=True,
            template_name="Momentum"
        )

        # Loop should still be created
        assert loop.template_mode is True


class TestUnifiedLoopBackwardCompatibility:
    """Test backward compatibility API."""

    @patch('src.learning.unified_loop.LearningLoop')
    def test_champion_property(self, mock_learning_loop_class):
        """Test champion property provides backward compatible access."""
        # Setup mock
        mock_champion = Mock()
        mock_champion.metrics = {"sharpe_ratio": 1.5}
        mock_champion_tracker = Mock()
        mock_champion_tracker.champion = mock_champion

        mock_learning_loop = Mock()
        mock_learning_loop.champion_tracker = mock_champion_tracker
        mock_learning_loop_class.return_value = mock_learning_loop

        # Create loop and access champion
        loop = UnifiedLoop()
        champion = loop.champion

        # Verify backward compatible access
        assert champion is mock_champion
        assert champion.metrics["sharpe_ratio"] == 1.5

    @patch('src.learning.unified_loop.LearningLoop')
    def test_history_property(self, mock_learning_loop_class):
        """Test history property provides backward compatible access."""
        # Setup mock
        mock_history = Mock()
        mock_history.load_recent = Mock(return_value=[])

        mock_learning_loop = Mock()
        mock_learning_loop.history = mock_history
        mock_learning_loop_class.return_value = mock_learning_loop

        # Create loop and access history
        loop = UnifiedLoop()
        history = loop.history

        # Verify backward compatible access
        assert history is mock_history
        history.load_recent.assert_not_called()  # Just property access


class TestUnifiedLoopRun:
    """Test run() method."""

    @patch('src.learning.unified_loop.LearningLoop')
    def test_run_delegates_to_learning_loop(self, mock_learning_loop_class):
        """Test that run() delegates to LearningLoop."""
        # Setup mocks
        mock_history = Mock()
        mock_history.get_all = Mock(return_value=[])

        mock_champion_tracker = Mock()
        mock_champion_tracker.champion = None

        mock_learning_loop = Mock()
        mock_learning_loop.history = mock_history
        mock_learning_loop.champion_tracker = mock_champion_tracker
        mock_learning_loop.interrupted = False
        mock_learning_loop.run = Mock()
        mock_learning_loop_class.return_value = mock_learning_loop

        # Create loop and run
        loop = UnifiedLoop(max_iterations=10)
        result = loop.run()

        # Verify delegation
        mock_learning_loop.run.assert_called_once()

        # Verify result structure
        assert "iterations_completed" in result
        assert "champion" in result
        assert "interrupted" in result

    @patch('src.learning.unified_loop.LearningLoop')
    def test_run_returns_champion_info(self, mock_learning_loop_class):
        """Test that run() returns champion information."""
        # Setup mocks
        mock_record = Mock()
        mock_history = Mock()
        mock_history.get_all = Mock(return_value=[mock_record])

        mock_champion = Mock()
        mock_champion.metrics = {"sharpe_ratio": 2.0}
        mock_champion_tracker = Mock()
        mock_champion_tracker.champion = mock_champion

        mock_learning_loop = Mock()
        mock_learning_loop.history = mock_history
        mock_learning_loop.champion_tracker = mock_champion_tracker
        mock_learning_loop.interrupted = False
        mock_learning_loop.run = Mock()
        mock_learning_loop_class.return_value = mock_learning_loop

        # Run
        loop = UnifiedLoop()
        result = loop.run()

        # Verify champion info
        assert result["iterations_completed"] == 1
        assert result["champion"] is mock_champion
        assert result["interrupted"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
