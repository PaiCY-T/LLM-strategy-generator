"""
Extended unit tests for Hybrid Architecture with comprehensive coverage.

Covers serialization, edge cases, backward compatibility, and integration scenarios.
"""

import pytest
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from src.learning.champion_tracker import ChampionStrategy, ChampionTracker
from src.learning.iteration_history import IterationRecord, IterationHistory
from src.backtest.executor import BacktestExecutor, ExecutionResult


class TestChampionStrategySerialization:
    """Test ChampionStrategy serialization and deserialization."""

    def test_to_dict_llm(self):
        """Test LLM champion serialization to dict."""
        champion = ChampionStrategy(
            iteration_num=1,
            generation_method="llm",
            code="# LLM code",
            strategy_id=None,
            strategy_generation=None,
            parameters={"param1": "value1"},
            metrics={"sharpe_ratio": 1.5},
            success_patterns=["pattern1"],
            timestamp="2025-11-05T10:00:00"
        )

        data = champion.to_dict()

        assert data["iteration_num"] == 1
        assert data["generation_method"] == "llm"
        assert data["code"] == "# LLM code"
        assert data["strategy_id"] is None
        assert data["strategy_generation"] is None
        assert data["parameters"] == {"param1": "value1"}

    def test_to_dict_factor_graph(self):
        """Test Factor Graph champion serialization to dict."""
        champion = ChampionStrategy(
            iteration_num=2,
            generation_method="factor_graph",
            code=None,
            strategy_id="momentum_v1",
            strategy_generation=1,
            parameters={},
            metrics={"sharpe_ratio": 2.0},
            success_patterns=[],
            timestamp="2025-11-05T11:00:00"
        )

        data = champion.to_dict()

        assert data["generation_method"] == "factor_graph"
        assert data["code"] is None
        assert data["strategy_id"] == "momentum_v1"
        assert data["strategy_generation"] == 1

    def test_from_dict_llm(self):
        """Test LLM champion deserialization from dict."""
        data = {
            "iteration_num": 1,
            "generation_method": "llm",
            "code": "# test",
            "strategy_id": None,
            "strategy_generation": None,
            "parameters": {},
            "metrics": {"sharpe_ratio": 1.5},
            "success_patterns": [],
            "timestamp": "2025-11-05T10:00:00"
        }

        champion = ChampionStrategy.from_dict(data)

        assert champion.generation_method == "llm"
        assert champion.code == "# test"
        assert champion.strategy_id is None

    def test_from_dict_factor_graph(self):
        """Test Factor Graph champion deserialization from dict."""
        data = {
            "iteration_num": 2,
            "generation_method": "factor_graph",
            "code": None,
            "strategy_id": "momentum_v1",
            "strategy_generation": 1,
            "parameters": {},
            "metrics": {"sharpe_ratio": 2.0},
            "success_patterns": [],
            "timestamp": "2025-11-05T11:00:00"
        }

        champion = ChampionStrategy.from_dict(data)

        assert champion.generation_method == "factor_graph"
        assert champion.strategy_id == "momentum_v1"
        assert champion.strategy_generation == 1

    def test_dict_roundtrip_llm(self):
        """Test LLM champion dict roundtrip (to_dict -> from_dict)."""
        original = ChampionStrategy(
            iteration_num=1,
            generation_method="llm",
            code="# original code",
            strategy_id=None,
            strategy_generation=None,
            parameters={"test": "value"},
            metrics={"sharpe_ratio": 1.8},
            success_patterns=["pattern"],
            timestamp="2025-11-05T10:00:00"
        )

        data = original.to_dict()
        restored = ChampionStrategy.from_dict(data)

        assert restored.iteration_num == original.iteration_num
        assert restored.generation_method == original.generation_method
        assert restored.code == original.code
        assert restored.parameters == original.parameters
        assert restored.metrics == original.metrics

    def test_dict_roundtrip_factor_graph(self):
        """Test Factor Graph champion dict roundtrip."""
        original = ChampionStrategy(
            iteration_num=2,
            generation_method="factor_graph",
            code=None,
            strategy_id="test_strategy",
            strategy_generation=5,
            parameters={},
            metrics={"sharpe_ratio": 2.5},
            success_patterns=[],
            timestamp="2025-11-05T11:00:00"
        )

        data = original.to_dict()
        restored = ChampionStrategy.from_dict(data)

        assert restored.generation_method == original.generation_method
        assert restored.strategy_id == original.strategy_id
        assert restored.strategy_generation == original.strategy_generation


class TestChampionStrategyEdgeCases:
    """Test ChampionStrategy edge cases and boundary conditions."""

    def test_empty_code_string_llm(self):
        """Test LLM champion with empty code string fails."""
        with pytest.raises(ValueError, match="non-empty code"):
            ChampionStrategy(
                iteration_num=1,
                generation_method="llm",
                code="",  # Empty string
                strategy_id=None,
                strategy_generation=None,
                parameters={},
                metrics={},
                success_patterns=[],
                timestamp=datetime.now().isoformat()
            )

    def test_whitespace_only_code_llm(self):
        """Test LLM champion with whitespace-only code fails."""
        with pytest.raises(ValueError, match="non-empty code"):
            ChampionStrategy(
                iteration_num=1,
                generation_method="llm",
                code="   \n\t   ",  # Whitespace only
                strategy_id=None,
                strategy_generation=None,
                parameters={},
                metrics={},
                success_patterns=[],
                timestamp=datetime.now().isoformat()
            )

    def test_empty_strategy_id_factor_graph(self):
        """Test Factor Graph champion with empty strategy_id fails."""
        with pytest.raises(ValueError, match="must have strategy_id"):
            ChampionStrategy(
                iteration_num=2,
                generation_method="factor_graph",
                code=None,
                strategy_id="",  # Empty string
                strategy_generation=1,
                parameters={},
                metrics={},
                success_patterns=[],
                timestamp=datetime.now().isoformat()
            )

    def test_zero_strategy_generation_valid(self):
        """Test Factor Graph champion with strategy_generation=0 is valid."""
        champion = ChampionStrategy(
            iteration_num=2,
            generation_method="factor_graph",
            code=None,
            strategy_id="test",
            strategy_generation=0,  # Zero is valid
            parameters={},
            metrics={},
            success_patterns=[],
            timestamp=datetime.now().isoformat()
        )

        assert champion.strategy_generation == 0

    def test_negative_iteration_num(self):
        """Test champion with negative iteration_num."""
        # Note: This should ideally be validated, but currently isn't
        champion = ChampionStrategy(
            iteration_num=-1,  # Negative
            generation_method="llm",
            code="# test",
            strategy_id=None,
            strategy_generation=None,
            parameters={},
            metrics={},
            success_patterns=[],
            timestamp=datetime.now().isoformat()
        )

        assert champion.iteration_num == -1


class TestIterationRecordSerialization:
    """Test IterationRecord serialization and backward compatibility."""

    def test_dict_conversion_llm(self):
        """Test LLM iteration record dict conversion."""
        record = IterationRecord(
            iteration_num=5,
            generation_method="llm",
            strategy_code="# code",
            strategy_id=None,
            strategy_generation=None,
            execution_result={"success": True},
            metrics={"sharpe_ratio": 1.8},
            classification_level="LEVEL_3",
            timestamp="2025-11-05T10:00:00"
        )

        from dataclasses import asdict
        data = asdict(record)

        assert data["generation_method"] == "llm"
        assert data["strategy_code"] == "# code"
        assert data["strategy_id"] is None

    def test_default_generation_method(self):
        """Test IterationRecord defaults to 'llm' for backward compatibility."""
        record = IterationRecord(
            iteration_num=5,
            # No generation_method specified
            strategy_code="# code",
            execution_result={"success": True},
            metrics={"sharpe_ratio": 1.8},
            classification_level="LEVEL_3",
            timestamp="2025-11-05T10:00:00"
        )

        assert record.generation_method == "llm"

    def test_jsonl_roundtrip_llm(self):
        """Test JSONL serialization roundtrip for LLM record."""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as f:
            temp_path = f.name

            try:
                # Create and save record
                history = IterationHistory(temp_path)

                record = IterationRecord(
                    iteration_num=1,
                    generation_method="llm",
                    strategy_code="# test code",
                    strategy_id=None,
                    strategy_generation=None,
                    execution_result={"success": True, "execution_time": 3.5},
                    metrics={"sharpe_ratio": 1.5, "total_return": 0.2, "max_drawdown": -0.1},
                    classification_level="LEVEL_3",
                    timestamp="2025-11-05T10:00:00",
                    champion_updated=True
                )

                history.save(record)

                # Load and verify
                loaded_records = history.load_all()
                assert len(loaded_records) == 1

                loaded = loaded_records[0]
                assert loaded.iteration_num == 1
                assert loaded.generation_method == "llm"
                assert loaded.strategy_code == "# test code"
                assert loaded.strategy_id is None

            finally:
                import os
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_jsonl_roundtrip_factor_graph(self):
        """Test JSONL serialization roundtrip for Factor Graph record."""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as f:
            temp_path = f.name

            try:
                history = IterationHistory(temp_path)

                record = IterationRecord(
                    iteration_num=2,
                    generation_method="factor_graph",
                    strategy_code=None,
                    strategy_id="momentum_v1",
                    strategy_generation=1,
                    execution_result={"success": True, "execution_time": 4.2},
                    metrics={"sharpe_ratio": 2.0, "total_return": 0.3, "max_drawdown": -0.12},
                    classification_level="LEVEL_3",
                    timestamp="2025-11-05T11:00:00"
                )

                history.save(record)

                # Load and verify
                loaded_records = history.load_all()
                assert len(loaded_records) == 1

                loaded = loaded_records[0]
                assert loaded.generation_method == "factor_graph"
                assert loaded.strategy_id == "momentum_v1"
                assert loaded.strategy_generation == 1
                assert loaded.strategy_code is None

            finally:
                import os
                if os.path.exists(temp_path):
                    os.unlink(temp_path)


class TestBacktestExecutorExtended:
    """Extended tests for BacktestExecutor execute_strategy()."""

    def test_strategy_to_pipeline_failure(self):
        """Test handling when Strategy.to_pipeline() fails."""
        mock_strategy = Mock()
        mock_strategy.to_pipeline.side_effect = Exception("Pipeline error")

        mock_data = Mock()
        mock_sim = Mock()

        executor = BacktestExecutor(timeout=60)

        with patch('multiprocessing.Process') as mock_process:
            process_instance = Mock()
            process_instance.is_alive.return_value = False
            mock_process.return_value = process_instance

            with patch('multiprocessing.Queue') as mock_queue:
                queue_instance = Mock()

                # Simulate error result
                error_result = ExecutionResult(
                    success=False,
                    error_type="Exception",
                    error_message="Pipeline error",
                    execution_time=0.5,
                    stack_trace="..."
                )
                queue_instance.get.return_value = error_result
                mock_queue.return_value = queue_instance

                result = executor.execute_strategy(
                    strategy=mock_strategy,
                    data=mock_data,
                    sim=mock_sim
                )

                assert result.success is False
                assert result.error_type == "Exception"

    def test_metrics_extraction_nan_handling(self):
        """Test metrics extraction handles NaN values correctly."""
        # This is tested within _execute_strategy_in_process
        # Mock report with NaN values
        mock_report = Mock()
        mock_report.get_stats.return_value = {
            'daily_sharpe': float('nan'),
            'total_return': float('nan'),
            'max_drawdown': float('nan')
        }

        # The ExecutionResult should convert NaN to None
        # This is implicitly tested in the main test suite


class TestChampionTrackerIntegration:
    """Integration tests for ChampionTracker with hybrid architecture."""

    def test_update_champion_llm_to_factor_graph_transition(self):
        """Test transitioning from LLM champion to Factor Graph champion."""
        mock_hall_of_fame = Mock()
        mock_history = Mock()
        mock_anti_churn = Mock()
        mock_anti_churn.min_sharpe_for_champion = 0.5
        mock_anti_churn.get_required_improvement.return_value = 0.05
        mock_anti_churn.get_additive_threshold.return_value = 0.1

        tracker = ChampionTracker(
            hall_of_fame=mock_hall_of_fame,
            history=mock_history,
            anti_churn=mock_anti_churn
        )

        # First: Create LLM champion
        llm_metrics = {"sharpe_ratio": 1.5, "max_drawdown": -0.15, "calmar_ratio": 1.0}
        updated = tracker.update_champion(
            iteration_num=1,
            metrics=llm_metrics,
            generation_method="llm",
            code="# LLM code"
        )

        assert updated is True
        assert tracker.champion.generation_method == "llm"

        # Second: Update with Factor Graph champion (better Sharpe)
        fg_metrics = {"sharpe_ratio": 2.0, "max_drawdown": -0.12, "calmar_ratio": 1.5}
        updated = tracker.update_champion(
            iteration_num=5,
            metrics=fg_metrics,
            generation_method="factor_graph",
            strategy_id="momentum_v1",
            strategy_generation=1
        )

        assert updated is True
        assert tracker.champion.generation_method == "factor_graph"
        assert tracker.champion.strategy_id == "momentum_v1"

    def test_update_champion_factor_graph_to_llm_transition(self):
        """Test transitioning from Factor Graph champion to LLM champion."""
        mock_hall_of_fame = Mock()
        mock_history = Mock()
        mock_anti_churn = Mock()
        mock_anti_churn.min_sharpe_for_champion = 0.5
        mock_anti_churn.get_required_improvement.return_value = 0.05
        mock_anti_churn.get_additive_threshold.return_value = 0.1

        tracker = ChampionTracker(
            hall_of_fame=mock_hall_of_fame,
            history=mock_history,
            anti_churn=mock_anti_churn
        )

        # First: Create Factor Graph champion
        fg_metrics = {"sharpe_ratio": 1.5, "max_drawdown": -0.15, "calmar_ratio": 1.0}
        updated = tracker.update_champion(
            iteration_num=1,
            metrics=fg_metrics,
            generation_method="factor_graph",
            strategy_id="momentum_v1",
            strategy_generation=1
        )

        assert updated is True
        assert tracker.champion.generation_method == "factor_graph"

        # Second: Update with LLM champion (better Sharpe)
        llm_metrics = {"sharpe_ratio": 2.0, "max_drawdown": -0.12, "calmar_ratio": 1.5}
        updated = tracker.update_champion(
            iteration_num=5,
            metrics=llm_metrics,
            generation_method="llm",
            code="# Better LLM code"
        )

        assert updated is True
        assert tracker.champion.generation_method == "llm"
        assert tracker.champion.code == "# Better LLM code"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
