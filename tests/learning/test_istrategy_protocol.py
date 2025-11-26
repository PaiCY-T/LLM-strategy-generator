"""
Unit tests for IStrategy Protocol (Spec A Task 4.1).

Tests IStrategy Protocol compliance for Factor Graph Strategy class.
Verifies protocol contract: id, generation, metrics, dominates(),
get_parameters(), get_metrics().

Test Coverage:
- Runtime isinstance() check with @runtime_checkable
- Property access (id, generation, metrics)
- Method calls (dominates, get_parameters, get_metrics)
- Edge cases (None metrics, empty parameters)
"""

import pytest
from typing import Dict, Any

from src.learning.interfaces import IStrategy
from src.evolution.types import Strategy, MultiObjectiveMetrics


class TestIStrategyProtocol:
    """Test IStrategy Protocol compliance."""

    @pytest.fixture
    def sample_metrics(self) -> MultiObjectiveMetrics:
        """Create sample metrics for testing."""
        return MultiObjectiveMetrics(
            sharpe_ratio=2.5,
            calmar_ratio=1.8,
            max_drawdown=-0.15,
            total_return=0.45,
            win_rate=0.62,
            annual_return=0.28,
            success=True
        )

    @pytest.fixture
    def sample_strategy(self, sample_metrics) -> Strategy:
        """Create sample Strategy for testing."""
        return Strategy(
            id='test-strategy-001',
            generation=5,
            parent_ids=['parent-001', 'parent-002'],
            code='def strategy(): pass',
            parameters={'n_stocks': 20, 'lookback': 60},
            metrics=sample_metrics,
            novelty_score=0.85,
            pareto_rank=1,
            crowding_distance=0.75,
            timestamp='2025-01-19T10:30:00',
            template_type='FactorGraph',
            metadata={'author': 'test'}
        )

    def test_strategy_implements_istrategy(self, sample_strategy):
        """Test Strategy class implements IStrategy via duck typing."""
        # Runtime check with @runtime_checkable
        assert isinstance(sample_strategy, IStrategy), \
            "Strategy should implement IStrategy Protocol"

    def test_strategy_id_property(self, sample_strategy):
        """Test IStrategy.id property contract."""
        strategy_id = sample_strategy.id

        # Contract: non-empty string
        assert isinstance(strategy_id, str)
        assert len(strategy_id) > 0

        # Contract: stable (same value across calls)
        assert sample_strategy.id == strategy_id

    def test_strategy_generation_property(self, sample_strategy):
        """Test IStrategy.generation property contract."""
        generation = sample_strategy.generation

        # Contract: non-negative integer
        assert isinstance(generation, int)
        assert generation >= 0

        # Contract: stable
        assert sample_strategy.generation == generation

    def test_strategy_metrics_property(self, sample_strategy):
        """Test IStrategy.metrics property contract."""
        metrics = sample_strategy.metrics

        # Contract: not None (for evaluated strategy)
        assert metrics is not None

        # Contract: has sharpe_ratio attribute
        assert hasattr(metrics, 'sharpe_ratio')
        assert isinstance(metrics.sharpe_ratio, (int, float))

    def test_strategy_metrics_none_when_unevaluated(self):
        """Test IStrategy.metrics is None for unevaluated strategy."""
        strategy = Strategy(
            id='unevaluated-001',
            generation=0,
            parent_ids=[],
            code='def strategy(): pass',
            parameters={},
            metrics=None  # Not evaluated
        )

        assert isinstance(strategy, IStrategy)
        assert strategy.metrics is None

    def test_strategy_dominates_method(self, sample_metrics):
        """Test IStrategy.dominates() method contract."""
        # Create dominant strategy
        strategy_a = Strategy(
            id='strategy-a',
            generation=1,
            metrics=MultiObjectiveMetrics(
                sharpe_ratio=3.0,
                calmar_ratio=2.5,
                max_drawdown=-0.10,
                total_return=0.60,
                win_rate=0.70,
                annual_return=0.35,
                success=True
            )
        )

        # Create dominated strategy
        strategy_b = Strategy(
            id='strategy-b',
            generation=1,
            metrics=MultiObjectiveMetrics(
                sharpe_ratio=1.5,
                calmar_ratio=1.2,
                max_drawdown=-0.20,
                total_return=0.30,
                win_rate=0.50,
                annual_return=0.20,
                success=True
            )
        )

        # Contract: A dominates B
        assert strategy_a.dominates(strategy_b) is True

        # Contract: B does not dominate A
        assert strategy_b.dominates(strategy_a) is False

    def test_strategy_dominates_with_none_metrics(self, sample_strategy):
        """Test IStrategy.dominates() returns False with None metrics."""
        unevaluated = Strategy(
            id='unevaluated',
            generation=0,
            metrics=None
        )

        # Contract: None metrics -> False
        assert sample_strategy.dominates(unevaluated) is False
        assert unevaluated.dominates(sample_strategy) is False

    def test_strategy_get_parameters_method(self, sample_strategy):
        """Test IStrategy.get_parameters() method contract."""
        params = sample_strategy.get_parameters()

        # Contract: returns dict
        assert isinstance(params, dict)

        # Contract: contains expected parameters
        assert 'n_stocks' in params
        assert 'lookback' in params
        assert params['n_stocks'] == 20
        assert params['lookback'] == 60

    def test_strategy_get_parameters_empty(self):
        """Test IStrategy.get_parameters() with empty parameters."""
        strategy = Strategy(
            id='empty-params',
            generation=0,
            parameters={}
        )

        params = strategy.get_parameters()

        # Contract: returns empty dict (not None)
        assert isinstance(params, dict)
        assert len(params) == 0

    def test_strategy_get_metrics_method(self, sample_strategy):
        """Test IStrategy.get_metrics() method contract."""
        metrics_dict = sample_strategy.get_metrics()

        # Contract: returns dict
        assert isinstance(metrics_dict, dict)

        # Contract: contains sharpe_ratio
        assert 'sharpe_ratio' in metrics_dict
        assert metrics_dict['sharpe_ratio'] == 2.5

        # Contract: contains other metrics
        assert 'calmar_ratio' in metrics_dict
        assert 'max_drawdown' in metrics_dict
        assert 'total_return' in metrics_dict
        assert 'win_rate' in metrics_dict
        assert 'annual_return' in metrics_dict

    def test_strategy_get_metrics_empty_when_unevaluated(self):
        """Test IStrategy.get_metrics() returns empty dict when unevaluated."""
        strategy = Strategy(
            id='unevaluated',
            generation=0,
            metrics=None
        )

        metrics_dict = strategy.get_metrics()

        # Contract: returns empty dict (not None)
        assert isinstance(metrics_dict, dict)
        assert len(metrics_dict) == 0

    def test_strategy_auto_generates_id(self):
        """Test Strategy auto-generates ID if not provided."""
        strategy = Strategy(
            generation=0,
            code='def strategy(): pass'
        )

        # Should implement IStrategy
        assert isinstance(strategy, IStrategy)

        # ID should be auto-generated (UUID format)
        assert len(strategy.id) > 0
        assert '-' in strategy.id  # UUID has dashes

    def test_strategy_auto_generates_timestamp(self):
        """Test Strategy auto-generates timestamp if not provided."""
        strategy = Strategy(
            generation=0,
            code='def strategy(): pass'
        )

        # Timestamp should be auto-generated (ISO format)
        assert len(strategy.timestamp) > 0
        assert 'T' in strategy.timestamp  # ISO format has T separator


class TestIStrategyProtocolEdgeCases:
    """Test edge cases for IStrategy Protocol."""

    def test_strategy_with_complex_parameters(self):
        """Test get_parameters() with nested dict parameters."""
        strategy = Strategy(
            id='complex-params',
            generation=1,
            parameters={
                'dag_nodes': ['Selection', 'Filter', 'Strategy'],
                'dag_edges': [('Selection', 'Filter'), ('Filter', 'Strategy')],
                'node_params': {
                    'Selection': {'top_n': 50, 'method': 'momentum'},
                    'Filter': {'threshold': 0.05}
                }
            }
        )

        params = strategy.get_parameters()

        assert 'dag_nodes' in params
        assert 'dag_edges' in params
        assert 'node_params' in params

    def test_dominates_reflexive(self):
        """Test strategy does not dominate itself."""
        strategy = Strategy(
            id='self-test',
            generation=1,
            metrics=MultiObjectiveMetrics(
                sharpe_ratio=2.0,
                calmar_ratio=1.5,
                max_drawdown=-0.15,
                total_return=0.40,
                win_rate=0.60,
                annual_return=0.25,
                success=True
            )
        )

        # A strategy should not dominate itself (equal metrics)
        assert strategy.dominates(strategy) is False

    def test_dominates_symmetric_incomparable(self):
        """Test two strategies that don't dominate each other."""
        # Strategy A: high sharpe, low calmar
        strategy_a = Strategy(
            id='high-sharpe',
            generation=1,
            metrics=MultiObjectiveMetrics(
                sharpe_ratio=3.0,
                calmar_ratio=1.0,
                max_drawdown=-0.20,
                total_return=0.50,
                win_rate=0.65,
                annual_return=0.30,
                success=True
            )
        )

        # Strategy B: low sharpe, high calmar
        strategy_b = Strategy(
            id='high-calmar',
            generation=1,
            metrics=MultiObjectiveMetrics(
                sharpe_ratio=1.5,
                calmar_ratio=2.5,
                max_drawdown=-0.10,
                total_return=0.40,
                win_rate=0.55,
                annual_return=0.25,
                success=True
            )
        )

        # Neither should dominate the other (trade-off)
        assert strategy_a.dominates(strategy_b) is False
        assert strategy_b.dominates(strategy_a) is False

    def test_failed_backtest_metrics(self):
        """Test get_metrics() with failed backtest."""
        strategy = Strategy(
            id='failed-backtest',
            generation=1,
            metrics=MultiObjectiveMetrics(
                sharpe_ratio=0.0,
                calmar_ratio=0.0,
                max_drawdown=-0.50,
                total_return=-0.30,
                win_rate=0.30,
                annual_return=-0.20,
                success=False
            )
        )

        metrics_dict = strategy.get_metrics()

        # Should still return metrics dict
        assert isinstance(metrics_dict, dict)
        assert 'sharpe_ratio' in metrics_dict
        assert metrics_dict['success'] == 0.0  # False -> 0.0


class TestIStrategyTypeHints:
    """Test IStrategy can be used as type hint."""

    def test_function_with_istrategy_parameter(self):
        """Test function accepting IStrategy parameter."""
        def process_strategy(strategy: IStrategy) -> Dict[str, Any]:
            return {
                'id': strategy.id,
                'generation': strategy.generation,
                'metrics': strategy.get_metrics()
            }

        strategy = Strategy(
            id='type-hint-test',
            generation=3,
            metrics=MultiObjectiveMetrics(
                sharpe_ratio=2.0,
                calmar_ratio=1.5,
                max_drawdown=-0.15,
                total_return=0.40,
                win_rate=0.60,
                annual_return=0.25,
                success=True
            )
        )

        result = process_strategy(strategy)

        assert result['id'] == 'type-hint-test'
        assert result['generation'] == 3
        assert result['metrics']['sharpe_ratio'] == 2.0

    def test_function_comparing_strategies(self):
        """Test function comparing two IStrategy instances."""
        def find_dominant(s1: IStrategy, s2: IStrategy) -> IStrategy:
            if s1.dominates(s2):
                return s1
            elif s2.dominates(s1):
                return s2
            else:
                # Return the one with higher Sharpe if incomparable
                m1 = s1.get_metrics()
                m2 = s2.get_metrics()
                sharpe1 = m1.get('sharpe_ratio', 0)
                sharpe2 = m2.get('sharpe_ratio', 0)
                return s1 if sharpe1 >= sharpe2 else s2

        strategy_a = Strategy(
            id='strategy-a',
            generation=1,
            metrics=MultiObjectiveMetrics(
                sharpe_ratio=3.0,
                calmar_ratio=2.0,
                max_drawdown=-0.10,
                total_return=0.50,
                win_rate=0.65,
                annual_return=0.30,
                success=True
            )
        )

        strategy_b = Strategy(
            id='strategy-b',
            generation=2,
            metrics=MultiObjectiveMetrics(
                sharpe_ratio=1.5,
                calmar_ratio=1.0,
                max_drawdown=-0.20,
                total_return=0.30,
                win_rate=0.50,
                annual_return=0.20,
                success=True
            )
        )

        dominant = find_dominant(strategy_a, strategy_b)

        assert dominant.id == 'strategy-a'
