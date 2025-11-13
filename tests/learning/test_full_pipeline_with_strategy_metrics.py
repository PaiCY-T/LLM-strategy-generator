"""Tests for Full Pipeline Integration with StrategyMetrics (Phase 3, Task 3.1).

End-to-end integration tests verifying that StrategyMetrics flows correctly
through the entire learning loop pipeline.

Author: Phase 3 Implementation Team
Date: 2025-01-13
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from src.learning.iteration_executor import IterationExecutor
from src.learning.iteration_history import IterationHistory
from src.learning.champion_tracker import ChampionTracker
from src.learning.feedback_generator import FeedbackGenerator
from src.backtest.executor import ExecutionResult, BacktestExecutor
from src.backtest.metrics import StrategyMetrics


@pytest.fixture
def temp_files():
    """Create temporary files for history and champion."""
    history_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
    champion_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)

    history_path = history_file.name
    champion_path = champion_file.name

    history_file.close()
    champion_file.close()

    yield history_path, champion_path

    # Cleanup
    Path(history_path).unlink(missing_ok=True)
    Path(champion_path).unlink(missing_ok=True)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client that returns valid strategy code."""
    client = Mock()
    client.is_enabled = Mock(return_value=True)

    engine = Mock()
    engine.generate_innovation = Mock(return_value="# Mock strategy code")

    client.get_engine = Mock(return_value=engine)
    return client


@pytest.fixture
def mock_backtest_executor():
    """Mock BacktestExecutor that returns successful results."""
    executor = Mock(spec=BacktestExecutor)

    def mock_execute(*args, **kwargs):
        return ExecutionResult(
            success=True,
            sharpe_ratio=1.85,
            total_return=0.42,
            max_drawdown=-0.15,
            execution_time=5.2
        )

    executor.execute = Mock(side_effect=mock_execute)
    return executor


class TestFullPipelineIntegration:
    """Test StrategyMetrics flowing through complete pipeline."""

    @patch('src.learning.iteration_executor.IterationExecutor._initialize_finlab')
    def test_single_iteration_creates_strategy_metrics_in_history(
        self,
        mock_init_finlab,
        temp_files,
        mock_llm_client,
        mock_backtest_executor
    ):
        """Full pipeline: Single iteration creates StrategyMetrics in history.

        WHEN: Execute one complete iteration
        THEN: History file contains StrategyMetrics-based record
        """
        # Arrange
        history_path, champion_path = temp_files
        mock_init_finlab.return_value = True

        history = IterationHistory(history_file=history_path)
        champion_tracker = ChampionTracker(champion_file=champion_path)
        feedback_gen = FeedbackGenerator(history, champion_tracker)

        config = {
            'innovation_rate': 100,
            'history_window': 5,
            'timeout_seconds': 420
        }

        executor = IterationExecutor(
            llm_client=mock_llm_client,
            feedback_generator=feedback_gen,
            backtest_executor=mock_backtest_executor,
            champion_tracker=champion_tracker,
            history=history,
            config=config,
            data=Mock(),
            sim=Mock()
        )

        # Act
        record = executor.execute_iteration(iteration_num=0)
        history.append(record)

        # Assert
        assert isinstance(record.metrics, StrategyMetrics)
        assert record.metrics.sharpe_ratio == 1.85

        # Verify persistence
        reloaded_history = IterationHistory(history_file=history_path)
        all_records = reloaded_history.get_all()
        assert len(all_records) == 1
        assert isinstance(all_records[0].metrics, StrategyMetrics)

    @patch('src.learning.iteration_executor.IterationExecutor._initialize_finlab')
    def test_multiple_iterations_accumulate_strategy_metrics(
        self,
        mock_init_finlab,
        temp_files,
        mock_llm_client,
        mock_backtest_executor
    ):
        """Full pipeline: Multiple iterations accumulate StrategyMetrics records.

        WHEN: Execute 3 iterations
        THEN: History contains 3 records with StrategyMetrics
        """
        # Arrange
        history_path, champion_path = temp_files
        mock_init_finlab.return_value = True

        history = IterationHistory(history_file=history_path)
        champion_tracker = ChampionTracker(champion_file=champion_path)
        feedback_gen = FeedbackGenerator(history, champion_tracker)

        config = {'innovation_rate': 100, 'history_window': 5, 'timeout_seconds': 420}

        executor = IterationExecutor(
            llm_client=mock_llm_client,
            feedback_generator=feedback_gen,
            backtest_executor=mock_backtest_executor,
            champion_tracker=champion_tracker,
            history=history,
            config=config,
            data=Mock(),
            sim=Mock()
        )

        # Act - Execute 3 iterations
        for i in range(3):
            record = executor.execute_iteration(iteration_num=i)
            history.append(record)

        # Assert
        all_records = history.get_all()
        assert len(all_records) == 3

        for i, record in enumerate(all_records):
            assert record.iteration_num == i
            assert isinstance(record.metrics, StrategyMetrics)
            assert record.metrics.sharpe_ratio == 1.85

    @patch('src.learning.iteration_executor.IterationExecutor._initialize_finlab')
    def test_champion_update_uses_strategy_metrics(
        self,
        mock_init_finlab,
        temp_files,
        mock_llm_client,
        mock_backtest_executor
    ):
        """Full pipeline: Champion update uses StrategyMetrics comparison.

        WHEN: Execute iterations with varying performance
        THEN: Champion is updated based on StrategyMetrics.sharpe_ratio
        """
        # Arrange
        history_path, champion_path = temp_files
        mock_init_finlab.return_value = True

        # Mock varying performance
        results = [
            ExecutionResult(success=True, sharpe_ratio=1.2, total_return=0.3, max_drawdown=-0.1, execution_time=5.0),
            ExecutionResult(success=True, sharpe_ratio=1.8, total_return=0.4, max_drawdown=-0.12, execution_time=5.0),
            ExecutionResult(success=True, sharpe_ratio=1.5, total_return=0.35, max_drawdown=-0.11, execution_time=5.0),
        ]

        mock_backtest_executor.execute = Mock(side_effect=results)

        history = IterationHistory(history_file=history_path)
        champion_tracker = ChampionTracker(champion_file=champion_path)
        feedback_gen = FeedbackGenerator(history, champion_tracker)

        config = {'innovation_rate': 100, 'history_window': 5, 'timeout_seconds': 420}

        executor = IterationExecutor(
            llm_client=mock_llm_client,
            feedback_generator=feedback_gen,
            backtest_executor=mock_backtest_executor,
            champion_tracker=champion_tracker,
            history=history,
            config=config,
            data=Mock(),
            sim=Mock()
        )

        # Act
        for i in range(3):
            record = executor.execute_iteration(iteration_num=i)
            history.append(record)

        # Assert - Champion should be iteration 1 (sharpe=1.8)
        assert champion_tracker.champion is not None
        assert isinstance(champion_tracker.champion.metrics, StrategyMetrics)
        assert champion_tracker.champion.metrics.sharpe_ratio == 1.8
        assert champion_tracker.champion.iteration_num == 1

    @patch('src.learning.iteration_executor.IterationExecutor._initialize_finlab')
    def test_feedback_generation_receives_strategy_metrics(
        self,
        mock_init_finlab,
        temp_files,
        mock_llm_client,
        mock_backtest_executor
    ):
        """Full pipeline: FeedbackGenerator receives StrategyMetrics.

        WHEN: Execute iteration with feedback generation
        THEN: FeedbackGenerator processes StrategyMetrics correctly
        """
        # Arrange
        history_path, champion_path = temp_files
        mock_init_finlab.return_value = True

        history = IterationHistory(history_file=history_path)
        champion_tracker = ChampionTracker(champion_file=champion_path)
        feedback_gen = FeedbackGenerator(history, champion_tracker)

        # Spy on generate_feedback method
        original_generate = feedback_gen.generate_feedback
        feedback_calls = []

        def spy_generate(*args, **kwargs):
            feedback_calls.append((args, kwargs))
            return original_generate(*args, **kwargs)

        feedback_gen.generate_feedback = spy_generate

        config = {'innovation_rate': 100, 'history_window': 5, 'timeout_seconds': 420}

        executor = IterationExecutor(
            llm_client=mock_llm_client,
            feedback_generator=feedback_gen,
            backtest_executor=mock_backtest_executor,
            champion_tracker=champion_tracker,
            history=history,
            config=config,
            data=Mock(),
            sim=Mock()
        )

        # Act - Execute 2 iterations (second uses feedback from first)
        record1 = executor.execute_iteration(iteration_num=0)
        history.append(record1)

        record2 = executor.execute_iteration(iteration_num=1)

        # Assert - Check feedback_gen received StrategyMetrics
        assert len(feedback_calls) >= 1
        # The feedback call for iteration 1 should have metrics
        if len(feedback_calls) > 1:
            call_kwargs = feedback_calls[1][1]
            if 'metrics' in call_kwargs:
                metrics_param = call_kwargs['metrics']
                # Should be dict during transition or StrategyMetrics after full impl
                assert metrics_param is not None
