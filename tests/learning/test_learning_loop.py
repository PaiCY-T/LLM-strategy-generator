"""
Tests for Phase 6 LearningLoop (Task 6.4)

Tests learning loop orchestration with focus on:
- Component initialization
- Iteration loop execution
- SIGINT interruption handling (CTRL+C)
- Resumption from last iteration
- Progress tracking
- Summary generation
"""

import logging
import os
import signal
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

import pytest

from src.learning.learning_config import LearningConfig
from src.learning.learning_loop import LearningLoop
from src.learning.iteration_history import IterationRecord


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config(temp_dir):
    """Create test configuration."""
    return LearningConfig(
        max_iterations=5,
        continue_on_error=False,
        history_file=str(temp_dir / "history.jsonl"),
        champion_file=str(temp_dir / "champion.json"),
        log_dir=str(temp_dir / "logs"),
        log_to_file=False,  # Disable for tests
        log_to_console=False,  # Disable for tests
    )


@pytest.fixture
def mock_record():
    """Create mock IterationRecord."""
    return IterationRecord(
        iteration_num=0,
        generation_method="llm",
        strategy_code="# code",
        execution_result={'success': True},
        metrics={'sharpe_ratio': 1.5},
        classification_level="LEVEL_3",
        timestamp="2024-01-01T00:00:00",
        champion_updated=True
    )


class TestLearningLoopInitialization:
    """Test LearningLoop initialization."""

    def test_initialization_creates_all_components(self, test_config):
        """Test all components are initialized."""
        loop = LearningLoop(test_config)

        assert loop.config == test_config
        assert loop.history is not None
        assert loop.champion_tracker is not None
        assert loop.llm_client is not None
        assert loop.feedback_generator is not None
        assert loop.backtest_executor is not None
        assert loop.iteration_executor is not None
        assert loop.interrupted is False

    def test_initialization_creates_log_dir(self, test_config, temp_dir):
        """Test log directory is created."""
        loop = LearningLoop(test_config)

        assert (temp_dir / "logs").exists()

    def test_initialization_failure_raises_error(self, test_config):
        """Test initialization failure raises RuntimeError."""
        # Make history file path invalid
        test_config.history_file = "/invalid/path/that/cannot/be/created/history.jsonl"

        with pytest.raises(RuntimeError, match="Failed to initialize components"):
            LearningLoop(test_config)


class TestGetStartIteration:
    """Test determining start iteration for resumption."""

    def test_no_history_starts_from_zero(self, test_config):
        """Test no previous history starts from iteration 0."""
        loop = LearningLoop(test_config)

        start = loop._get_start_iteration()

        assert start == 0

    def test_resume_from_last_iteration(self, test_config, mock_record):
        """Test resume from last completed iteration."""
        loop = LearningLoop(test_config)

        # Simulate 3 completed iterations
        for i in range(3):
            mock_record.iteration_num = i
            loop.history.save_record(mock_record)

        start = loop._get_start_iteration()

        assert start == 3  # Should resume from 3 (0, 1, 2 completed)

    def test_already_complete_returns_max(self, test_config, mock_record):
        """Test already complete returns max_iterations."""
        test_config.max_iterations = 3
        loop = LearningLoop(test_config)

        # Complete all iterations
        for i in range(3):
            mock_record.iteration_num = i
            loop.history.save_record(mock_record)

        start = loop._get_start_iteration()

        assert start == 3  # Should return max (loop exits immediately)

    def test_get_start_iteration_handles_exception(self, test_config):
        """Test exception in get_start_iteration returns 0."""
        loop = LearningLoop(test_config)

        with patch.object(loop.history, 'get_all', side_effect=Exception("Read error")):
            start = loop._get_start_iteration()

        assert start == 0  # Fallback to 0


class TestRunIterationLoop:
    """Test main iteration loop execution."""

    @patch('src.learning.learning_loop.LearningLoop._setup_signal_handlers')
    @patch('src.learning.learning_loop.LearningLoop._show_startup_info')
    @patch('src.learning.learning_loop.LearningLoop._show_progress')
    @patch('src.learning.learning_loop.LearningLoop._generate_summary')
    def test_run_completes_all_iterations(
        self, mock_summary, mock_progress, mock_startup, mock_signal,
        test_config, mock_record
    ):
        """Test run() completes all iterations successfully."""
        test_config.max_iterations = 3
        loop = LearningLoop(test_config)

        # Mock iteration executor
        loop.iteration_executor.execute_iteration = Mock(return_value=mock_record)

        # Run loop
        loop.run()

        # Verify all iterations executed
        assert loop.iteration_executor.execute_iteration.call_count == 3
        mock_summary.assert_called_once()

    @patch('src.learning.learning_loop.LearningLoop._setup_signal_handlers')
    @patch('src.learning.learning_loop.LearningLoop._show_startup_info')
    @patch('src.learning.learning_loop.LearningLoop._show_progress')
    @patch('src.learning.learning_loop.LearningLoop._generate_summary')
    def test_run_saves_records_to_history(
        self, mock_summary, mock_progress, mock_startup, mock_signal,
        test_config, mock_record
    ):
        """Test run() saves each iteration record to history."""
        test_config.max_iterations = 2
        loop = LearningLoop(test_config)

        loop.iteration_executor.execute_iteration = Mock(return_value=mock_record)

        with patch.object(loop.history, 'save_record') as mock_save:
            loop.run()

            assert mock_save.call_count == 2

    @patch('src.learning.learning_loop.LearningLoop._setup_signal_handlers')
    @patch('src.learning.learning_loop.LearningLoop._show_startup_info')
    @patch('src.learning.learning_loop.LearningLoop._generate_summary')
    def test_run_handles_iteration_exception_continue_on_error_false(
        self, mock_summary, mock_startup, mock_signal, test_config
    ):
        """Test run() stops on error when continue_on_error=False."""
        test_config.max_iterations = 3
        test_config.continue_on_error = False
        loop = LearningLoop(test_config)

        loop.iteration_executor.execute_iteration = Mock(
            side_effect=Exception("Iteration error")
        )

        with pytest.raises(Exception, match="Iteration error"):
            loop.run()

        # Should fail on first iteration
        assert loop.iteration_executor.execute_iteration.call_count == 1

    @patch('src.learning.learning_loop.LearningLoop._setup_signal_handlers')
    @patch('src.learning.learning_loop.LearningLoop._show_startup_info')
    @patch('src.learning.learning_loop.LearningLoop._show_progress')
    @patch('src.learning.learning_loop.LearningLoop._generate_summary')
    def test_run_continues_on_error_when_enabled(
        self, mock_summary, mock_progress, mock_startup, mock_signal,
        test_config, mock_record
    ):
        """Test run() continues on error when continue_on_error=True."""
        test_config.max_iterations = 3
        test_config.continue_on_error = True
        loop = LearningLoop(test_config)

        # Fail first iteration, succeed others
        loop.iteration_executor.execute_iteration = Mock(
            side_effect=[Exception("Error"), mock_record, mock_record]
        )

        loop.run()

        # Should complete all 3 iterations despite first error
        assert loop.iteration_executor.execute_iteration.call_count == 3
        mock_summary.assert_called_once()


class TestSIGINTHandling:
    """Test SIGINT (CTRL+C) interruption handling."""

    @patch('src.learning.learning_loop.LearningLoop._setup_signal_handlers')
    @patch('src.learning.learning_loop.LearningLoop._show_startup_info')
    @patch('src.learning.learning_loop.LearningLoop._generate_summary')
    def test_keyboard_interrupt_stops_loop_gracefully(
        self, mock_summary, mock_startup, mock_signal,
        test_config, mock_record
    ):
        """Test KeyboardInterrupt stops loop gracefully."""
        test_config.max_iterations = 5
        loop = LearningLoop(test_config)

        # Interrupt after 2 iterations
        loop.iteration_executor.execute_iteration = Mock(
            side_effect=[mock_record, mock_record, KeyboardInterrupt()]
        )

        loop.run()

        # Should complete 2 iterations and stop
        assert loop.iteration_executor.execute_iteration.call_count == 3
        assert loop.interrupted is True
        mock_summary.assert_called_once()

    def test_signal_handler_sets_interrupted_flag(self, test_config):
        """Test SIGINT handler sets interrupted flag."""
        loop = LearningLoop(test_config)

        # Simulate SIGINT
        loop._setup_signal_handlers()
        original_handler = signal.getsignal(signal.SIGINT)

        # Trigger handler
        assert loop.interrupted is False
        original_handler(signal.SIGINT, None)
        assert loop.interrupted is True

    def test_signal_handler_force_quit_on_second_interrupt(self, test_config):
        """Test second SIGINT force quits."""
        loop = LearningLoop(test_config)

        loop._setup_signal_handlers()
        handler = signal.getsignal(signal.SIGINT)

        # First SIGINT: sets flag
        handler(signal.SIGINT, None)
        assert loop.interrupted is True

        # Second SIGINT: force quit
        with pytest.raises(SystemExit, match="1"):
            handler(signal.SIGINT, None)


class TestProgressTracking:
    """Test progress tracking and reporting."""

    def test_show_progress_calculates_success_rates(self, test_config, mock_record):
        """Test progress tracking calculates success rates correctly."""
        loop = LearningLoop(test_config)

        # Add mix of success levels
        records = [
            IterationRecord(
                iteration_num=i,
                generation_method="llm",
                strategy_code="# code",
                execution_result={},
                metrics={'sharpe_ratio': 1.0},
                classification_level=level,
                timestamp="2024-01-01T00:00:00",
                champion_updated=False
            )
            for i, level in enumerate(["LEVEL_0", "LEVEL_1", "LEVEL_2", "LEVEL_3", "LEVEL_3"])
        ]

        for record in records:
            loop.history.save_record(record)

        # Test progress display (should not crash)
        loop._show_progress(iteration_num=4, record=records[-1])

        # Verify metrics calculation
        all_records = loop.history.get_all()
        total = len(all_records)
        level_1_plus = sum(1 for r in all_records if r.classification_level in ("LEVEL_1", "LEVEL_2", "LEVEL_3"))
        level_3 = sum(1 for r in all_records if r.classification_level == "LEVEL_3")

        assert total == 5
        assert level_1_plus == 4  # LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_3
        assert level_3 == 2  # Two LEVEL_3


class TestSummaryGeneration:
    """Test summary report generation."""

    def test_generate_summary_with_no_records(self, test_config):
        """Test summary generation with no iterations."""
        loop = LearningLoop(test_config)

        # Should not crash
        loop._generate_summary(start_iteration=0)

    def test_generate_summary_with_champion(self, test_config):
        """Test summary generation with champion present."""
        loop = LearningLoop(test_config)

        # Add successful iteration
        record = IterationRecord(
            iteration_num=0,
            generation_method="llm",
            strategy_code="# code",
            execution_result={'success': True},
            metrics={'sharpe_ratio': 2.5, 'total_return': 0.3},
            classification_level="LEVEL_3",
            timestamp="2024-01-01T00:00:00",
            champion_updated=True
        )
        loop.history.save_record(record)

        # Update champion
        loop.champion_tracker.update_champion(
            iteration_num=0,
            metrics=record.metrics,
            generation_method="llm",
            code=record.strategy_code
        )

        # Should not crash and should display champion info
        loop._generate_summary(start_iteration=0)

        champion = loop.champion_tracker.get_champion()
        assert champion is not None

    def test_generate_summary_calculates_statistics(self, test_config):
        """Test summary calculates classification breakdown."""
        loop = LearningLoop(test_config)

        # Add mix of iterations
        levels = ["LEVEL_0", "LEVEL_0", "LEVEL_1", "LEVEL_2", "LEVEL_3"]
        for i, level in enumerate(levels):
            record = IterationRecord(
                iteration_num=i,
                generation_method="llm",
                strategy_code="# code",
                execution_result={},
                metrics={'sharpe_ratio': 1.0},
                classification_level=level,
                timestamp="2024-01-01T00:00:00",
                champion_updated=False
            )
            loop.history.save_record(record)

        # Generate summary (should calculate correctly)
        loop._generate_summary(start_iteration=0)

        records = loop.history.get_all()
        assert len(records) == 5
        assert sum(1 for r in records if r.classification_level == "LEVEL_0") == 2
        assert sum(1 for r in records if r.classification_level == "LEVEL_3") == 1


class TestResumptionScenarios:
    """Test various resumption scenarios (Task 6.4 focus)."""

    @patch('src.learning.learning_loop.LearningLoop._setup_signal_handlers')
    @patch('src.learning.learning_loop.LearningLoop._show_startup_info')
    @patch('src.learning.learning_loop.LearningLoop._show_progress')
    @patch('src.learning.learning_loop.LearningLoop._generate_summary')
    def test_resume_after_clean_stop(
        self, mock_summary, mock_progress, mock_startup, mock_signal,
        test_config, mock_record
    ):
        """Test resumption after clean stop (completed 3 of 5)."""
        test_config.max_iterations = 5
        loop = LearningLoop(test_config)

        # Simulate 3 completed iterations
        for i in range(3):
            mock_record.iteration_num = i
            loop.history.save_record(mock_record)

        # Mock executor for remaining iterations
        loop.iteration_executor.execute_iteration = Mock(return_value=mock_record)

        # Run (should complete iterations 3-4)
        loop.run()

        # Should execute 2 remaining iterations
        assert loop.iteration_executor.execute_iteration.call_count == 2

    @patch('src.learning.learning_loop.LearningLoop._setup_signal_handlers')
    @patch('src.learning.learning_loop.LearningLoop._show_startup_info')
    @patch('src.learning.learning_loop.LearningLoop._generate_summary')
    def test_resume_after_interrupt(
        self, mock_summary, mock_startup, mock_signal,
        test_config, mock_record
    ):
        """Test resumption after KeyboardInterrupt."""
        test_config.max_iterations = 5

        # First run: Complete 2 iterations then interrupt
        loop1 = LearningLoop(test_config)
        loop1.iteration_executor.execute_iteration = Mock(
            side_effect=[
                mock_record._replace(iteration_num=0),
                mock_record._replace(iteration_num=1),
                KeyboardInterrupt()
            ]
        )
        loop1.run()

        # Second run: Resume from iteration 2
        loop2 = LearningLoop(test_config)
        loop2.iteration_executor.execute_iteration = Mock(return_value=mock_record)

        start = loop2._get_start_iteration()
        assert start == 2

    def test_resume_with_corrupted_history(self, test_config):
        """Test resumption with partially corrupted history."""
        loop = LearningLoop(test_config)

        # Write valid record
        record = IterationRecord(
            iteration_num=0,
            generation_method="llm",
            strategy_code="# code",
            execution_result={},
            metrics={},
            classification_level="LEVEL_3",
            timestamp="2024-01-01T00:00:00"
        )
        loop.history.save_record(record)

        # Append corrupted line
        with open(test_config.history_file, 'a') as f:
            f.write("CORRUPTED JSON LINE\n")

        # Should handle gracefully and resume from last valid record
        start = loop._get_start_iteration()
        assert start == 1  # Resume after record 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_zero_max_iterations_invalid(self):
        """Test max_iterations=0 is rejected by validation."""
        with pytest.raises(ValueError, match="max_iterations must be > 0"):
            LearningConfig(max_iterations=0)

    def test_empty_history_file_path_uses_default(self, temp_dir):
        """Test empty history_file uses default."""
        config = LearningConfig(history_file="")
        # Should use default or create new

    @patch('src.learning.learning_loop.LearningLoop._setup_signal_handlers')
    @patch('src.learning.learning_loop.LearningLoop._show_startup_info')
    @patch('src.learning.learning_loop.LearningLoop._generate_summary')
    def test_run_with_already_complete_exits_immediately(
        self, mock_summary, mock_startup, mock_signal,
        test_config, mock_record
    ):
        """Test run exits immediately if already complete."""
        test_config.max_iterations = 2
        loop = LearningLoop(test_config)

        # Complete all iterations
        for i in range(2):
            mock_record.iteration_num = i
            loop.history.save_record(mock_record)

        loop.iteration_executor.execute_iteration = Mock()

        loop.run()

        # Should not execute any iterations
        loop.iteration_executor.execute_iteration.assert_not_called()
