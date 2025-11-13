"""Tests for Phase 3 Backward Compatibility (Task 3.1).

Tests TC-1.8: Historical JSONL files load successfully

This module verifies that the StrategyMetrics type changes maintain backward
compatibility with existing JSONL history files and champion.json files.

Author: Phase 3 Implementation Team
Date: 2025-01-13
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from src.learning.iteration_history import IterationHistory, IterationRecord
from src.learning.champion_tracker import ChampionTracker
from src.backtest.metrics import StrategyMetrics


@pytest.fixture
def temp_jsonl_file():
    """Create temporary JSONL file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_champion_file():
    """Create temporary champion JSON file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink(missing_ok=True)


class TestHistoricalJSONLLoading:
    """Test loading historical JSONL files with dict-format metrics (TC-1.8)."""

    def test_load_jsonl_with_dict_format_metrics(self, temp_jsonl_file):
        """TC-1.8: IterationHistory loads historical JSONL with dict metrics.

        WHEN: JSONL file contains records with dict-format metrics
        THEN: Records load successfully and metrics converted to StrategyMetrics
        """
        # Arrange - Create historical JSONL file
        historical_records = [
            {
                "iteration_num": 0,
                "generation_method": "llm",
                "strategy_code": "# Strategy 0",
                "execution_result": {"success": True},
                "metrics": {
                    "sharpe_ratio": 1.25,
                    "total_return": 0.35,
                    "max_drawdown": -0.12
                },
                "classification_level": "LEVEL_2",
                "timestamp": "2025-01-01T10:00:00",
                "champion_updated": False
            },
            {
                "iteration_num": 1,
                "generation_method": "llm",
                "strategy_code": "# Strategy 1",
                "execution_result": {"success": True},
                "metrics": {
                    "sharpe_ratio": 1.85,
                    "total_return": 0.42,
                    "max_drawdown": -0.15
                },
                "classification_level": "LEVEL_3",
                "timestamp": "2025-01-01T11:00:00",
                "champion_updated": True
            }
        ]

        with open(temp_jsonl_file, 'w') as f:
            for record in historical_records:
                f.write(json.dumps(record) + '\n')

        # Act
        history = IterationHistory(filepath=temp_jsonl_file)
        all_records = history.get_all()

        # Assert
        assert len(all_records) == 2

        # Verify first record
        assert all_records[0].iteration_num == 0
        assert isinstance(all_records[0].metrics, StrategyMetrics)
        assert all_records[0].metrics.sharpe_ratio == 1.25
        assert all_records[0].metrics.total_return == 0.35

        # Verify second record
        assert all_records[1].iteration_num == 1
        assert isinstance(all_records[1].metrics, StrategyMetrics)
        assert all_records[1].metrics.sharpe_ratio == 1.85

    def test_load_jsonl_with_missing_metric_fields(self, temp_jsonl_file):
        """TC-1.8: Handle historical records with missing metric fields.

        WHEN: Historical JSONL has incomplete metrics dict
        THEN: Loads successfully with None for missing fields
        """
        # Arrange
        historical_record = {
            "iteration_num": 5,
            "generation_method": "llm",
            "strategy_code": "# Historical strategy with partial metrics",
            "execution_result": {"success": True},
            "metrics": {
                "sharpe_ratio": 1.5
                # total_return and max_drawdown missing
            },
            "classification_level": "LEVEL_2",
            "timestamp": "2025-01-05T10:00:00",
            "champion_updated": False
        }

        with open(temp_jsonl_file, 'w') as f:
            f.write(json.dumps(historical_record) + '\n')

        # Act
        history = IterationHistory(filepath=temp_jsonl_file)
        records = history.get_all()

        # Assert
        assert len(records) == 1
        assert isinstance(records[0].metrics, StrategyMetrics)
        assert records[0].metrics.sharpe_ratio == 1.5
        assert records[0].metrics.total_return is None
        assert records[0].metrics.max_drawdown is None

    def test_roundtrip_save_load_preserves_strategy_metrics(self, temp_jsonl_file):
        """TC-1.8: Save and load cycle preserves StrategyMetrics data.

        WHEN: Save StrategyMetrics → load from file
        THEN: Loaded metrics equal original metrics
        """
        # Arrange
        original_metrics = StrategyMetrics(
            sharpe_ratio=2.05,
            total_return=0.48,
            max_drawdown=-0.13,
            win_rate=0.68,
            execution_success=True
        )

        original_record = IterationRecord(
            iteration_num=10,
            generation_method="llm",
            strategy_code="# Test strategy",
            execution_result={"success": True},
            metrics=original_metrics,
            classification_level="LEVEL_3",
            timestamp=datetime.now().isoformat(),
            champion_updated=True
        )

        history = IterationHistory(filepath=temp_jsonl_file)

        # Act - Save
        history.save(original_record)

        # Act - Load
        new_history = IterationHistory(filepath=temp_jsonl_file)
        loaded_records = new_history.get_all()

        # Assert
        assert len(loaded_records) == 1
        loaded_record = loaded_records[0]
        assert isinstance(loaded_record.metrics, StrategyMetrics)
        assert loaded_record.metrics.sharpe_ratio == original_metrics.sharpe_ratio
        assert loaded_record.metrics.total_return == original_metrics.total_return
        assert loaded_record.metrics.max_drawdown == original_metrics.max_drawdown
        assert loaded_record.metrics.win_rate == original_metrics.win_rate


class TestHistoricalChampionLoading:
    """Test loading historical champion.json files (TC-1.8)."""

    def test_load_champion_json_with_dict_metrics(self, temp_champion_file):
        """TC-1.8: ChampionTracker loads historical champion.json with dict metrics.

        WHEN: champion.json contains dict-format metrics
        THEN: Champion loads and metrics converted to StrategyMetrics
        """
        # Arrange - Create historical champion.json
        historical_champion = {
            "iteration_num": 42,
            "metrics": {
                "sharpe_ratio": 2.35,
                "total_return": 0.52,
                "max_drawdown": -0.09,
                "win_rate": 0.72
            },
            "timestamp": "2025-01-10T15:30:00",
            "generation_method": "llm",
            "code": "# Historical champion strategy",
            "strategy_id": None,
            "strategy_generation": None
        }

        with open(temp_champion_file, 'w') as f:
            json.dump(historical_champion, f)

        # Act
        tracker = ChampionTracker(champion_file=temp_champion_file)

        # Assert
        assert tracker.champion is not None
        assert isinstance(tracker.champion.metrics, StrategyMetrics)
        assert tracker.champion.metrics.sharpe_ratio == 2.35
        assert tracker.champion.metrics.total_return == 0.52
        assert tracker.champion.metrics.max_drawdown == -0.09
        assert tracker.champion.iteration_num == 42

    def test_save_and_load_champion_preserves_strategy_metrics(
        self, temp_champion_file
    ):
        """TC-1.8: Champion save/load cycle preserves StrategyMetrics.

        WHEN: Save champion with StrategyMetrics → reload
        THEN: Reloaded champion has identical metrics
        """
        # Arrange
        original_metrics = StrategyMetrics(
            sharpe_ratio=1.95,
            total_return=0.38,
            max_drawdown=-0.14,
            win_rate=0.60,
            execution_success=True
        )

        # Act - Save
        tracker = ChampionTracker(champion_file=temp_champion_file)
        tracker.update_champion(
            iteration_num=25,
            metrics=original_metrics,
            generation_method="llm",
            code="# Champion code"
        )

        # Act - Reload
        new_tracker = ChampionTracker(champion_file=temp_champion_file)

        # Assert
        assert new_tracker.champion is not None
        assert isinstance(new_tracker.champion.metrics, StrategyMetrics)
        assert new_tracker.champion.metrics.sharpe_ratio == 1.95
        assert new_tracker.champion.metrics.total_return == 0.38
        assert new_tracker.champion.metrics.execution_success is True


class TestMixedFormatHandling:
    """Test handling of mixed dict and StrategyMetrics formats."""

    def test_iteration_record_to_dict_from_dict_roundtrip(self):
        """TC-1.8: IterationRecord serialization handles both formats.

        WHEN: Convert IterationRecord with StrategyMetrics to dict and back
        THEN: Roundtrip preserves all data
        """
        # Arrange
        metrics = StrategyMetrics(
            sharpe_ratio=1.65,
            total_return=0.32,
            max_drawdown=-0.11,
            execution_success=True
        )

        record = IterationRecord(
            iteration_num=8,
            generation_method="llm",
            strategy_code="# Code",
            execution_result={"success": True},
            metrics=metrics,
            classification_level="LEVEL_2",
            timestamp=datetime.now().isoformat(),
            champion_updated=False
        )

        # Act
        record_dict = record.to_dict()
        restored_record = IterationRecord.from_dict(record_dict)

        # Assert
        assert isinstance(restored_record.metrics, StrategyMetrics)
        assert restored_record.metrics.sharpe_ratio == metrics.sharpe_ratio
        assert restored_record.metrics.total_return == metrics.total_return
        assert restored_record.iteration_num == 8
