"""Tests for IterationExecutor Metrics Extraction (Phase 3, Task 3.1).

Tests TC-1.5: IterationExecutor._extract_metrics() returns StrategyMetrics

This module verifies that IterationExecutor returns StrategyMetrics dataclass
from _extract_metrics() instead of Dict[str, float].

Author: Phase 3 Implementation Team
Date: 2025-01-13
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.learning.iteration_executor import IterationExecutor
from src.backtest.executor import ExecutionResult
from src.backtest.metrics import StrategyMetrics


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = Mock()
    client.is_enabled = Mock(return_value=True)
    return client


@pytest.fixture
def mock_feedback_generator():
    """Mock FeedbackGenerator."""
    generator = Mock()
    generator.generate_feedback = Mock(return_value="Test feedback")
    return generator


@pytest.fixture
def mock_backtest_executor():
    """Mock BacktestExecutor."""
    executor = Mock()
    return executor


@pytest.fixture
def mock_champion_tracker():
    """Mock ChampionTracker."""
    tracker = Mock()
    tracker.champion = None
    tracker.update_champion = Mock(return_value=False)
    return tracker


@pytest.fixture
def mock_history():
    """Mock IterationHistory."""
    history = Mock()
    history.get_all = Mock(return_value=[])
    return history


@pytest.fixture
def iteration_executor(
    mock_llm_client,
    mock_feedback_generator,
    mock_backtest_executor,
    mock_champion_tracker,
    mock_history
):
    """Create IterationExecutor with mocked dependencies."""
    config = {
        'innovation_rate': 100,
        'history_window': 5,
        'timeout_seconds': 420,
        'start_date': '2018-01-01',
        'end_date': '2024-12-31'
    }

    executor = IterationExecutor(
        llm_client=mock_llm_client,
        feedback_generator=mock_feedback_generator,
        backtest_executor=mock_backtest_executor,
        champion_tracker=mock_champion_tracker,
        history=mock_history,
        config=config,
        data=Mock(),
        sim=Mock()
    )

    return executor


class TestIterationExecutorMetricsExtraction:
    """Test IterationExecutor._extract_metrics() returns StrategyMetrics (TC-1.5)."""

    def test_extract_metrics_returns_strategy_metrics_object(
        self, iteration_executor
    ):
        """TC-1.5: _extract_metrics() returns StrategyMetrics instance.

        WHEN: Call _extract_metrics() with successful ExecutionResult
        THEN: Returns StrategyMetrics dataclass instance
        """
        # Arrange
        execution_result = ExecutionResult(
            success=True,
            sharpe_ratio=1.85,
            total_return=0.42,
            max_drawdown=-0.15,
            execution_time=5.2
        )

        # Act
        metrics = iteration_executor._extract_metrics(execution_result)

        # Assert
        assert isinstance(metrics, StrategyMetrics)
        assert metrics.sharpe_ratio == 1.85
        assert metrics.total_return == 0.42
        assert metrics.max_drawdown == -0.15
        assert metrics.execution_success is True

    def test_extract_metrics_returns_empty_strategy_metrics_on_failure(
        self, iteration_executor
    ):
        """TC-1.5: _extract_metrics() returns empty StrategyMetrics on failure.

        WHEN: Call _extract_metrics() with failed ExecutionResult
        THEN: Returns StrategyMetrics with execution_success=False
        """
        # Arrange
        execution_result = ExecutionResult(
            success=False,
            error_type="TimeoutError",
            error_message="Execution timeout",
            execution_time=420.0
        )

        # Act
        metrics = iteration_executor._extract_metrics(execution_result)

        # Assert
        assert isinstance(metrics, StrategyMetrics)
        assert metrics.sharpe_ratio is None
        assert metrics.total_return is None
        assert metrics.max_drawdown is None
        assert metrics.execution_success is False

    def test_extract_metrics_handles_partial_execution_result(
        self, iteration_executor
    ):
        """TC-1.5: _extract_metrics() handles ExecutionResult with missing metrics.

        WHEN: ExecutionResult has success=True but some metrics are None
        THEN: Returns StrategyMetrics with available metrics
        """
        # Arrange
        execution_result = ExecutionResult(
            success=True,
            sharpe_ratio=1.2,
            total_return=None,  # Missing
            max_drawdown=-0.08,
            execution_time=3.5
        )

        # Act
        metrics = iteration_executor._extract_metrics(execution_result)

        # Assert
        assert isinstance(metrics, StrategyMetrics)
        assert metrics.sharpe_ratio == 1.2
        assert metrics.total_return is None
        assert metrics.max_drawdown == -0.08
        assert metrics.execution_success is True

    @patch('src.learning.iteration_executor.IterationExecutor._initialize_finlab')
    @patch('src.learning.iteration_executor.IterationExecutor._generate_with_llm')
    @patch('src.learning.iteration_executor.IterationExecutor._execute_strategy')
    def test_execute_iteration_creates_record_with_strategy_metrics(
        self,
        mock_execute,
        mock_generate,
        mock_init_finlab,
        iteration_executor,
        mock_history
    ):
        """TC-1.5: execute_iteration() creates IterationRecord with StrategyMetrics.

        WHEN: execute_iteration() completes successfully
        THEN: IterationRecord.metrics contains StrategyMetrics
        """
        # Arrange
        mock_init_finlab.return_value = True
        mock_generate.return_value = ("# Test code", None, None)

        execution_result = ExecutionResult(
            success=True,
            sharpe_ratio=1.95,
            total_return=0.35,
            max_drawdown=-0.12,
            execution_time=4.8
        )
        mock_execute.return_value = execution_result

        # Act
        record = iteration_executor.execute_iteration(iteration_num=5)

        # Assert
        assert record is not None
        assert isinstance(record.metrics, StrategyMetrics)
        assert record.metrics.sharpe_ratio == 1.95
        assert record.metrics.total_return == 0.35
        assert record.metrics.execution_success is True
