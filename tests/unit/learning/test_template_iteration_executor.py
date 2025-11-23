"""Unit tests for TemplateIterationExecutor.

Tests template-based iteration execution with feedback integration.

Test Coverage:
    - Initialization
    - execute_iteration() full flow
    - Parameter generation
    - Code generation
    - Error handling
    - Feedback integration
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from src.learning.template_iteration_executor import TemplateIterationExecutor
from src.learning.iteration_history import IterationRecord
from src.backtest.metrics import StrategyMetrics


class TestTemplateIterationExecutorInitialization:
    """Test TemplateIterationExecutor initialization."""

    def test_initialization_success(self):
        """Test successful initialization."""
        # Setup mocks
        mock_llm_client = Mock()
        mock_feedback_gen = Mock()
        mock_backtest_exec = Mock()
        mock_champion_tracker = Mock()
        mock_history = Mock()

        # Initialize
        executor = TemplateIterationExecutor(
            llm_client=mock_llm_client,
            feedback_generator=mock_feedback_gen,
            backtest_executor=mock_backtest_exec,
            champion_tracker=mock_champion_tracker,
            history=mock_history,
            template_name="Momentum",
            use_json_mode=True,
            config={"llm_model": "gemini-2.5-flash", "history_window": 10}
        )

        # Verify initialization
        assert executor.template_name == "Momentum"
        assert executor.use_json_mode is True
        assert executor.template_param_generator is not None

    def test_initialization_with_invalid_template(self):
        """Test initialization with invalid template name."""
        mock_llm_client = Mock()
        mock_feedback_gen = Mock()
        mock_backtest_exec = Mock()
        mock_champion_tracker = Mock()
        mock_history = Mock()

        # Invalid template should raise during initialization
        with pytest.raises(Exception):
            executor = TemplateIterationExecutor(
                llm_client=mock_llm_client,
                feedback_generator=mock_feedback_gen,
                backtest_executor=mock_backtest_exec,
                champion_tracker=mock_champion_tracker,
                history=mock_history,
                template_name="InvalidTemplate",  # Invalid
                use_json_mode=False,
                config={}
            )


class TestTemplateIterationExecutorExecution:
    """Test execute_iteration() method."""

    def setup_method(self):
        """Setup common mocks for each test."""
        self.mock_llm_client = Mock()
        self.mock_feedback_gen = Mock()
        self.mock_backtest_exec = Mock()
        self.mock_champion_tracker = Mock()
        self.mock_history = Mock()

        self.executor = TemplateIterationExecutor(
            llm_client=self.mock_llm_client,
            feedback_generator=self.mock_feedback_gen,
            backtest_executor=self.mock_backtest_exec,
            champion_tracker=self.mock_champion_tracker,
            history=self.mock_history,
            template_name="Momentum",
            use_json_mode=False,
            config={"llm_model": "gemini-2.5-flash", "history_window": 10}
        )

    def test_execute_first_iteration_no_feedback(self):
        """Test first iteration doesn't generate feedback."""
        # Setup mocks
        self.mock_history.load_recent = Mock(return_value=[])
        self.executor.template_param_generator.generate_parameters = Mock(
            return_value={"momentum_period": 20, "n_stocks": 10}
        )
        self.executor.template_param_generator.template.generate_code = Mock(
            return_value="def strategy(): pass"
        )
        self.mock_backtest_exec.execute = Mock(
            return_value={"status": "success", "execution_time": 5.0}
        )
        self.executor.metrics_extractor.extract = Mock(
            return_value=StrategyMetrics(sharpe_ratio=1.5, total_return=0.2, max_drawdown=-0.1)
        )
        self.executor.success_classifier.classify = Mock(return_value="LEVEL_3")
        self.mock_champion_tracker.update_if_better = Mock(return_value=False)

        # Execute iteration 0 (first iteration)
        record = self.executor.execute_iteration(0)

        # Verify feedback generator was NOT called for first iteration
        self.mock_feedback_gen.generate_feedback.assert_not_called()

        # Verify record
        assert record.iteration_num == 0
        assert record.generation_method == "template"
        assert record.template_name == "Momentum"
        assert record.json_mode is False

    def test_execute_with_feedback(self):
        """Test second iteration generates and uses feedback."""
        # Setup mocks
        mock_last_record = Mock()
        mock_last_record.metrics = StrategyMetrics(sharpe_ratio=1.0, total_return=0.1, max_drawdown=-0.15)
        mock_last_record.execution_result = {"status": "success"}
        mock_last_record.classification_level = "LEVEL_3"
        mock_last_record.error_msg = None

        self.mock_history.load_recent = Mock(return_value=[mock_last_record])
        self.mock_feedback_gen.generate_feedback = Mock(
            return_value="Previous strategy had Sharpe 1.0. Try improving..."
        )
        self.executor.template_param_generator.generate_parameters = Mock(
            return_value={"momentum_period": 20, "n_stocks": 10}
        )
        self.executor.template_param_generator.template.generate_code = Mock(
            return_value="def strategy(): pass"
        )
        self.mock_backtest_exec.execute = Mock(
            return_value={"status": "success", "execution_time": 5.0}
        )
        self.executor.metrics_extractor.extract = Mock(
            return_value=StrategyMetrics(sharpe_ratio=1.5, total_return=0.2, max_drawdown=-0.1)
        )
        self.executor.success_classifier.classify = Mock(return_value="LEVEL_3")
        self.mock_champion_tracker.update_if_better = Mock(return_value=False)

        # Execute iteration 1 (second iteration)
        record = self.executor.execute_iteration(1)

        # Verify feedback was generated
        self.mock_feedback_gen.generate_feedback.assert_called_once()

        # Verify record has feedback
        assert record.feedback_used is not None
        assert "Sharpe 1.0" in record.feedback_used

    def test_execute_with_champion_update(self):
        """Test iteration that updates champion."""
        # Setup mocks
        self.mock_history.load_recent = Mock(return_value=[])
        self.executor.template_param_generator.generate_parameters = Mock(
            return_value={"momentum_period": 20, "n_stocks": 10}
        )
        self.executor.template_param_generator.template.generate_code = Mock(
            return_value="def strategy(): pass"
        )
        self.mock_backtest_exec.execute = Mock(
            return_value={"status": "success", "execution_time": 5.0}
        )
        self.executor.metrics_extractor.extract = Mock(
            return_value=StrategyMetrics(sharpe_ratio=2.0, total_return=0.3, max_drawdown=-0.08)
        )
        self.executor.success_classifier.classify = Mock(return_value="LEVEL_3")
        self.mock_champion_tracker.update_if_better = Mock(return_value=True)  # Champion updated!

        # Execute iteration
        record = self.executor.execute_iteration(0)

        # Verify champion was updated
        assert record.champion_updated is True
        self.mock_champion_tracker.update_if_better.assert_called_once()


class TestTemplateIterationExecutorErrorHandling:
    """Test error handling."""

    def setup_method(self):
        """Setup common mocks for each test."""
        self.mock_llm_client = Mock()
        self.mock_feedback_gen = Mock()
        self.mock_backtest_exec = Mock()
        self.mock_champion_tracker = Mock()
        self.mock_history = Mock()

        self.executor = TemplateIterationExecutor(
            llm_client=self.mock_llm_client,
            feedback_generator=self.mock_feedback_gen,
            backtest_executor=self.mock_backtest_exec,
            champion_tracker=self.mock_champion_tracker,
            history=self.mock_history,
            template_name="Momentum",
            use_json_mode=False,
            config={"llm_model": "gemini-2.5-flash", "history_window": 10}
        )

    def test_parameter_generation_error(self):
        """Test handling of parameter generation errors."""
        # Setup mocks
        self.mock_history.load_recent = Mock(return_value=[])
        self.executor.template_param_generator.generate_parameters = Mock(
            side_effect=Exception("Parameter generation failed")
        )

        # Execute iteration
        record = self.executor.execute_iteration(0)

        # Verify error record
        assert record.classification_level == "LEVEL_0"
        assert "Parameter generation error" in record.execution_result.get("error", "")
        assert record.champion_updated is False

    def test_code_generation_error(self):
        """Test handling of code generation errors."""
        # Setup mocks
        self.mock_history.load_recent = Mock(return_value=[])
        self.executor.template_param_generator.generate_parameters = Mock(
            return_value={"momentum_period": 20}
        )
        self.executor.template_param_generator.template.generate_code = Mock(
            side_effect=Exception("Code generation failed")
        )

        # Execute iteration
        record = self.executor.execute_iteration(0)

        # Verify error record
        assert record.classification_level == "LEVEL_0"
        assert "Code generation error" in record.execution_result.get("error", "")

    def test_execution_error(self):
        """Test handling of strategy execution errors."""
        # Setup mocks
        self.mock_history.load_recent = Mock(return_value=[])
        self.executor.template_param_generator.generate_parameters = Mock(
            return_value={"momentum_period": 20}
        )
        self.executor.template_param_generator.template.generate_code = Mock(
            return_value="def strategy(): pass"
        )
        self.mock_backtest_exec.execute = Mock(
            side_effect=Exception("Execution failed")
        )

        # Execute iteration
        record = self.executor.execute_iteration(0)

        # Verify error record
        assert record.classification_level == "LEVEL_0"
        assert "Execution error" in record.execution_result.get("error", "")

    def test_feedback_generation_failure_continues(self):
        """Test that feedback generation failure doesn't stop iteration."""
        # Setup mocks
        mock_last_record = Mock()
        mock_last_record.metrics = StrategyMetrics(sharpe_ratio=1.0, total_return=0.1, max_drawdown=-0.15)
        mock_last_record.execution_result = {"status": "success"}
        mock_last_record.classification_level = "LEVEL_3"

        self.mock_history.load_recent = Mock(return_value=[mock_last_record])
        self.mock_feedback_gen.generate_feedback = Mock(
            side_effect=Exception("Feedback generation failed")
        )
        self.executor.template_param_generator.generate_parameters = Mock(
            return_value={"momentum_period": 20}
        )
        self.executor.template_param_generator.template.generate_code = Mock(
            return_value="def strategy(): pass"
        )
        self.mock_backtest_exec.execute = Mock(
            return_value={"status": "success", "execution_time": 5.0}
        )
        self.executor.metrics_extractor.extract = Mock(
            return_value=StrategyMetrics(sharpe_ratio=1.2, total_return=0.15, max_drawdown=-0.12)
        )
        self.executor.success_classifier.classify = Mock(return_value="LEVEL_3")
        self.mock_champion_tracker.update_if_better = Mock(return_value=False)

        # Execute iteration 1 (should continue despite feedback failure)
        record = self.executor.execute_iteration(1)

        # Verify iteration completed successfully
        assert record.classification_level == "LEVEL_3"
        assert record.feedback_used is None  # No feedback due to error


class TestTemplateIterationExecutorJSONMode:
    """Test JSON mode functionality."""

    def test_json_mode_enabled(self):
        """Test that json_mode is recorded in IterationRecord."""
        # Setup mocks
        mock_llm_client = Mock()
        mock_feedback_gen = Mock()
        mock_backtest_exec = Mock()
        mock_champion_tracker = Mock()
        mock_history = Mock()

        executor = TemplateIterationExecutor(
            llm_client=mock_llm_client,
            feedback_generator=mock_feedback_gen,
            backtest_executor=mock_backtest_exec,
            champion_tracker=mock_champion_tracker,
            history=mock_history,
            template_name="Momentum",
            use_json_mode=True,  # JSON mode enabled
            config={"llm_model": "gemini-2.5-flash", "history_window": 10}
        )

        mock_history.load_recent = Mock(return_value=[])
        executor.template_param_generator.generate_parameters = Mock(
            return_value={"momentum_period": 20}
        )
        executor.template_param_generator.template.generate_code = Mock(
            return_value="def strategy(): pass"
        )
        mock_backtest_exec.execute = Mock(
            return_value={"status": "success", "execution_time": 5.0}
        )
        executor.metrics_extractor.extract = Mock(
            return_value=StrategyMetrics(sharpe_ratio=1.5, total_return=0.2, max_drawdown=-0.1)
        )
        executor.success_classifier.classify = Mock(return_value="LEVEL_3")
        mock_champion_tracker.update_if_better = Mock(return_value=False)

        # Execute iteration
        record = executor.execute_iteration(0)

        # Verify JSON mode is recorded
        assert record.json_mode is True
        assert record.template_name == "Momentum"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
