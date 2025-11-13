"""Tests for ChampionTracker Type Consistency (Phase 3, Task 3.1).

Tests TC-1.4: ChampionTracker.update_champion() accepts StrategyMetrics

This module verifies that ChampionTracker uses StrategyMetrics dataclass
instead of Dict[str, float] for metrics storage and comparison.

Author: Phase 3 Implementation Team
Date: 2025-01-13
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock
from src.learning.champion_tracker import ChampionTracker, ChampionStrategy
from src.backtest.metrics import StrategyMetrics


@pytest.fixture
def temp_champion_file():
    """Create temporary champion file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def champion_tracker(temp_champion_file):
    """Create ChampionTracker with mocked dependencies."""
    # Create mock dependencies
    mock_hall_of_fame = Mock()
    mock_history = Mock()
    mock_anti_churn = Mock()

    # Configure mocks - use get_current_champion() as used in _load_champion()
    mock_hall_of_fame.get_current_champion.return_value = None  # No initial champion

    tracker = ChampionTracker(
        champion_file=temp_champion_file,
        hall_of_fame=mock_hall_of_fame,
        history=mock_history,
        anti_churn=mock_anti_churn
    )

    return tracker


class TestChampionTrackerStrategyMetricsIntegration:
    """Test ChampionTracker accepts StrategyMetrics (TC-1.4)."""

    def test_update_champion_accepts_strategy_metrics_parameter(
        self, champion_tracker
    ):
        """TC-1.4: update_champion() accepts StrategyMetrics parameter.

        WHEN: Call update_champion() with StrategyMetrics
        THEN: Champion is updated with StrategyMetrics data
        """
        # Arrange
        metrics = StrategyMetrics(
            sharpe_ratio=1.85,
            total_return=0.42,
            max_drawdown=-0.15,
            execution_success=True
        )

        # Act
        result = champion_tracker.update_champion(
            iteration_num=5,
            metrics=metrics,
            generation_method="llm",
            code="# Test strategy code"
        )

        # Assert
        assert result is True
        assert champion_tracker.champion is not None
        assert champion_tracker.champion.metrics.sharpe_ratio == 1.85

    def test_champion_strategy_stores_strategy_metrics_object(
        self, champion_tracker
    ):
        """TC-1.4: ChampionStrategy.metrics stores StrategyMetrics dataclass.

        WHEN: Update champion with StrategyMetrics
        THEN: ChampionStrategy.metrics is StrategyMetrics instance
        """
        # Arrange
        metrics = StrategyMetrics(
            sharpe_ratio=2.1,
            total_return=0.5,
            execution_success=True
        )

        # Act
        champion_tracker.update_champion(
            iteration_num=10,
            code="# Test code",
            metrics=metrics,
            generation_method="llm"
        )

        # Assert
        champion = champion_tracker.champion
        assert isinstance(champion.metrics, StrategyMetrics)
        assert champion.metrics.sharpe_ratio == 2.1
        assert champion.metrics.total_return == 0.5

    def test_champion_comparison_uses_strategy_metrics_attribute(
        self, champion_tracker
    ):
        """TC-1.4: Champion comparison uses metrics.sharpe_ratio attribute.

        WHEN: Update champion multiple times
        THEN: Comparison logic uses metrics.sharpe_ratio attribute access
        """
        # Arrange
        first_metrics = StrategyMetrics(sharpe_ratio=1.5, execution_success=True)
        second_metrics = StrategyMetrics(sharpe_ratio=1.2, execution_success=True)
        third_metrics = StrategyMetrics(sharpe_ratio=1.8, execution_success=True)

        # Act
        result1 = champion_tracker.update_champion(1, "# Code 1", first_metrics, generation_method="llm")
        result2 = champion_tracker.update_champion(2, "# Code 2", second_metrics, generation_method="llm")
        result3 = champion_tracker.update_champion(3, "# Code 3", third_metrics, generation_method="llm")

        # Assert
        assert result1 is True  # First champion
        assert result2 is False  # Lower Sharpe, not updated
        assert result3 is True  # Higher Sharpe, updated
        assert champion_tracker.champion.metrics.sharpe_ratio == 1.8

    def test_champion_serialization_preserves_strategy_metrics(
        self, champion_tracker, temp_champion_file
    ):
        """TC-1.4: Champion file serialization preserves StrategyMetrics data.

        WHEN: Save champion with StrategyMetrics and reload
        THEN: Reloaded champion has correct StrategyMetrics
        """
        # Arrange
        metrics = StrategyMetrics(
            sharpe_ratio=1.95,
            total_return=0.38,
            max_drawdown=-0.12,
            win_rate=0.65,
            execution_success=True
        )

        # Act - Save
        champion_tracker.update_champion(
            iteration_num=15,
            metrics=metrics,
            generation_method="llm",
            code="# Champion strategy"
        )

        # Act - Reload
        # Create dependencies for new tracker instance
        import tempfile
        from src.learning.iteration_history import IterationHistory
        from src.repository.hall_of_fame import HallOfFameRepository
        from src.config.anti_churn_manager import AntiChurnManager

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as hf:
            history_path = hf.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as hof:
            hall_path = hof.name

        new_tracker = ChampionTracker(
            champion_file=temp_champion_file,
            hall_of_fame=HallOfFameRepository(filepath=hall_path),
            history=IterationHistory(filepath=history_path),
            anti_churn=AntiChurnManager()
        )

        # Cleanup
        Path(history_path).unlink(missing_ok=True)
        Path(hall_path).unlink(missing_ok=True)

        # Assert
        assert new_tracker.champion is not None
        assert isinstance(new_tracker.champion.metrics, StrategyMetrics)
        assert new_tracker.champion.metrics.sharpe_ratio == 1.95
        assert new_tracker.champion.metrics.total_return == 0.38
        assert new_tracker.champion.metrics.max_drawdown == -0.12


class TestChampionTrackerBackwardCompatibility:
    """Test backward compatibility with historical champion.json files."""

    def test_load_champion_from_dict_format_file(self, temp_champion_file):
        """TC-1.8: ChampionTracker loads historical dict-format champion files.

        WHEN: Champion file contains dict-format metrics
        THEN: ChampionTracker converts to StrategyMetrics on load
        """
        # Arrange - Create historical dict-format champion file
        historical_champion = {
            "iteration_num": 42,
            "metrics": {
                "sharpe_ratio": 2.15,
                "total_return": 0.48,
                "max_drawdown": -0.10
            },
            "timestamp": "2025-01-10T10:30:00",
            "generation_method": "llm",
            "code": "# Historical champion"
        }

        with open(temp_champion_file, 'w') as f:
            json.dump(historical_champion, f)

        # Act
        # Create dependencies for tracker instance
        import tempfile
        from src.learning.iteration_history import IterationHistory
        from src.repository.hall_of_fame import HallOfFameRepository
        from src.config.anti_churn_manager import AntiChurnManager

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as hf:
            history_path = hf.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as hof:
            hall_path = hof.name

        tracker = ChampionTracker(
            champion_file=temp_champion_file,
            hall_of_fame=HallOfFameRepository(filepath=hall_path),
            history=IterationHistory(filepath=history_path),
            anti_churn=AntiChurnManager()
        )

        # Cleanup
        Path(history_path).unlink(missing_ok=True)
        Path(hall_path).unlink(missing_ok=True)

        # Assert
        assert tracker.champion is not None
        assert isinstance(tracker.champion.metrics, StrategyMetrics)
        assert tracker.champion.metrics.sharpe_ratio == 2.15
        assert tracker.champion.metrics.total_return == 0.48
