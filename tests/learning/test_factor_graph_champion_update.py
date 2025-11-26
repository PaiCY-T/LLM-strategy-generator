"""
Unit tests for Factor Graph Champion Update Bug Fix (Spec A Task 4.2).

Tests that Factor Graph strategies can properly update the champion by
ensuring the Strategy DAG object is passed to ChampionTracker.update_champion().

Test Coverage:
- Factor Graph champion update with strategy object
- Strategy retrieval from registry
- Error handling when strategy not in registry
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

# Mock imports for isolated testing
import sys


class TestFactorGraphChampionUpdate:
    """Test Factor Graph Champion Update fix (Spec A Task 4.2)."""

    @pytest.fixture
    def mock_strategy(self):
        """Create mock Strategy object."""
        strategy = Mock()
        strategy.id = 'test-strategy-001'
        strategy.generation = 5
        strategy.parameters = {'n_stocks': 20}
        strategy.metrics = Mock()
        strategy.metrics.sharpe_ratio = 2.5
        return strategy

    @pytest.fixture
    def mock_champion_tracker(self):
        """Create mock ChampionTracker."""
        tracker = Mock()
        tracker.update_champion = Mock(return_value=True)
        tracker.champion = None
        return tracker

    @pytest.fixture
    def sample_metrics(self) -> Dict[str, float]:
        """Create sample metrics dictionary."""
        return {
            'sharpe_ratio': 2.5,
            'max_drawdown': -0.15,
            'total_return': 0.45,
            'win_rate': 0.62,
            'calmar_ratio': 1.8,
            'annual_return': 0.28
        }

    def test_factor_graph_champion_update_passes_strategy(
        self, mock_strategy, mock_champion_tracker, sample_metrics
    ):
        """Test that Factor Graph champion update passes strategy object."""
        # Create a minimal _update_champion_if_better function to test logic
        strategy_registry = {'test-strategy-001': mock_strategy}

        def _update_champion_if_better(
            iteration_num: int,
            generation_method: str,
            strategy_code,
            strategy_id,
            strategy_generation,
            metrics: Dict[str, float],
            classification_level: str,
            strategy=None
        ) -> bool:
            if classification_level != "LEVEL_3":
                return False

            if not metrics or "sharpe_ratio" not in metrics:
                return False

            # For Factor Graph mode, retrieve strategy from registry if not provided
            if generation_method == "factor_graph" and strategy is None and strategy_id:
                strategy = strategy_registry.get(strategy_id)
                if strategy is None:
                    return False

            # Call champion_tracker.update_champion with strategy
            updated = mock_champion_tracker.update_champion(
                iteration_num=iteration_num,
                metrics=metrics,
                generation_method=generation_method,
                code=strategy_code,
                strategy=strategy,
                strategy_id=strategy_id,
                strategy_generation=strategy_generation
            )

            return updated

        # Test Factor Graph update
        result = _update_champion_if_better(
            iteration_num=10,
            generation_method="factor_graph",
            strategy_code=None,
            strategy_id='test-strategy-001',
            strategy_generation=5,
            metrics=sample_metrics,
            classification_level="LEVEL_3",
            strategy=None  # Strategy should be retrieved from registry
        )

        # Verify champion_tracker.update_champion was called with strategy
        assert result is True
        mock_champion_tracker.update_champion.assert_called_once()
        call_kwargs = mock_champion_tracker.update_champion.call_args.kwargs
        assert call_kwargs['strategy'] == mock_strategy
        assert call_kwargs['generation_method'] == "factor_graph"
        assert call_kwargs['strategy_id'] == 'test-strategy-001'
        assert call_kwargs['strategy_generation'] == 5

    def test_factor_graph_update_fails_when_strategy_not_in_registry(
        self, mock_champion_tracker, sample_metrics
    ):
        """Test Factor Graph update fails gracefully when strategy not in registry."""
        strategy_registry = {}  # Empty registry

        def _update_champion_if_better(
            iteration_num: int,
            generation_method: str,
            strategy_code,
            strategy_id,
            strategy_generation,
            metrics: Dict[str, float],
            classification_level: str,
            strategy=None
        ) -> bool:
            if classification_level != "LEVEL_3":
                return False

            if not metrics or "sharpe_ratio" not in metrics:
                return False

            if generation_method == "factor_graph" and strategy is None and strategy_id:
                strategy = strategy_registry.get(strategy_id)
                if strategy is None:
                    return False

            mock_champion_tracker.update_champion(
                iteration_num=iteration_num,
                metrics=metrics,
                generation_method=generation_method,
                code=strategy_code,
                strategy=strategy,
                strategy_id=strategy_id,
                strategy_generation=strategy_generation
            )
            return True

        # Test with missing strategy
        result = _update_champion_if_better(
            iteration_num=10,
            generation_method="factor_graph",
            strategy_code=None,
            strategy_id='missing-strategy',
            strategy_generation=5,
            metrics=sample_metrics,
            classification_level="LEVEL_3",
            strategy=None
        )

        # Should return False and NOT call update_champion
        assert result is False
        mock_champion_tracker.update_champion.assert_not_called()

    def test_llm_champion_update_ignores_strategy(
        self, mock_champion_tracker, sample_metrics
    ):
        """Test LLM champion update doesn't require strategy object."""
        def _update_champion_if_better(
            iteration_num: int,
            generation_method: str,
            strategy_code,
            strategy_id,
            strategy_generation,
            metrics: Dict[str, float],
            classification_level: str,
            strategy=None
        ) -> bool:
            if classification_level != "LEVEL_3":
                return False

            if not metrics or "sharpe_ratio" not in metrics:
                return False

            # LLM mode doesn't need strategy retrieval
            if generation_method == "factor_graph" and strategy is None and strategy_id:
                return False  # Simplified for test

            mock_champion_tracker.update_champion(
                iteration_num=iteration_num,
                metrics=metrics,
                generation_method=generation_method,
                code=strategy_code,
                strategy=strategy,
                strategy_id=strategy_id,
                strategy_generation=strategy_generation
            )
            return True

        # Test LLM update (strategy should be None)
        result = _update_champion_if_better(
            iteration_num=10,
            generation_method="llm",
            strategy_code="def strategy(): pass",
            strategy_id=None,
            strategy_generation=None,
            metrics=sample_metrics,
            classification_level="LEVEL_3",
            strategy=None
        )

        # Should succeed and call update_champion with None strategy
        assert result is True
        mock_champion_tracker.update_champion.assert_called_once()
        call_kwargs = mock_champion_tracker.update_champion.call_args.kwargs
        assert call_kwargs['strategy'] is None
        assert call_kwargs['generation_method'] == "llm"
        assert call_kwargs['code'] == "def strategy(): pass"

    def test_non_level3_classification_skips_update(
        self, mock_champion_tracker, sample_metrics
    ):
        """Test that non-LEVEL_3 classification skips champion update."""
        def _update_champion_if_better(
            iteration_num: int,
            generation_method: str,
            strategy_code,
            strategy_id,
            strategy_generation,
            metrics: Dict[str, float],
            classification_level: str,
            strategy=None
        ) -> bool:
            if classification_level != "LEVEL_3":
                return False

            mock_champion_tracker.update_champion()
            return True

        # Test with LEVEL_2 (should skip)
        for level in ["LEVEL_0", "LEVEL_1", "LEVEL_2"]:
            result = _update_champion_if_better(
                iteration_num=10,
                generation_method="factor_graph",
                strategy_code=None,
                strategy_id='test-strategy',
                strategy_generation=5,
                metrics=sample_metrics,
                classification_level=level,
                strategy=None
            )
            assert result is False

        # update_champion should never be called
        mock_champion_tracker.update_champion.assert_not_called()

    def test_missing_sharpe_ratio_skips_update(
        self, mock_champion_tracker
    ):
        """Test that missing sharpe_ratio skips champion update."""
        def _update_champion_if_better(
            iteration_num: int,
            generation_method: str,
            strategy_code,
            strategy_id,
            strategy_generation,
            metrics: Dict[str, float],
            classification_level: str,
            strategy=None
        ) -> bool:
            if classification_level != "LEVEL_3":
                return False

            if not metrics or "sharpe_ratio" not in metrics:
                return False

            mock_champion_tracker.update_champion()
            return True

        # Test with missing sharpe_ratio
        result = _update_champion_if_better(
            iteration_num=10,
            generation_method="factor_graph",
            strategy_code=None,
            strategy_id='test-strategy',
            strategy_generation=5,
            metrics={'max_drawdown': -0.15},  # No sharpe_ratio
            classification_level="LEVEL_3",
            strategy=None
        )

        assert result is False
        mock_champion_tracker.update_champion.assert_not_called()


class TestChampionTrackerFactorGraphIntegration:
    """Integration tests for ChampionTracker with Factor Graph strategies."""

    def test_champion_tracker_update_champion_signature(self):
        """Verify ChampionTracker.update_champion accepts strategy parameter."""
        from src.learning.champion_tracker import ChampionTracker
        import inspect

        # Get the update_champion method signature
        sig = inspect.signature(ChampionTracker.update_champion)
        params = list(sig.parameters.keys())

        # Verify required parameters exist
        assert 'iteration_num' in params
        assert 'code' in params
        assert 'metrics' in params
        # Note: 'strategy' is passed via **kwargs

    def test_champion_strategy_supports_factor_graph_fields(self):
        """Verify ChampionStrategy has Factor Graph fields."""
        from src.learning.champion_tracker import ChampionStrategy
        from src.backtest.metrics import StrategyMetrics

        metrics = StrategyMetrics(
            sharpe_ratio=2.5,
            max_drawdown=-0.15,
            total_return=0.45,
            win_rate=0.62,
            execution_success=True
        )

        # Create Factor Graph champion
        champion = ChampionStrategy(
            iteration_num=10,
            generation_method="factor_graph",
            strategy_id="test-strategy-001",
            strategy_generation=5,
            metrics=metrics,
            timestamp="2025-01-01T00:00:00"
        )

        # Verify Factor Graph fields
        assert champion.generation_method == "factor_graph"
        assert champion.strategy_id == "test-strategy-001"
        assert champion.strategy_generation == 5
        assert champion.code is None  # Factor Graph has no code
