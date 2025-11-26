"""
Performance and Regression Tests (Spec A Task 5.2).

Tests to ensure no regressions from Spec A changes:
- Existing Strategy serialization still works
- HallOfFameRepository still functions correctly
- IStrategy Protocol doesn't break existing code
- Factor Graph Champion update works end-to-end

These tests verify backward compatibility and system integrity.
"""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

from src.evolution.types import Strategy, MultiObjectiveMetrics
from src.repository.hall_of_fame import HallOfFameRepository
from src.learning.interfaces import IStrategy


class TestStrategyBackwardCompatibility:
    """Test Strategy class backward compatibility."""

    def test_strategy_serialization_roundtrip(self):
        """Test Strategy to_dict → from_dict roundtrip."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=2.5,
            calmar_ratio=1.8,
            max_drawdown=-0.15,
            total_return=0.45,
            win_rate=0.62,
            annual_return=0.28,
            success=True
        )

        original = Strategy(
            id='test-001',
            generation=5,
            parent_ids=['parent-001', 'parent-002'],
            code='def strategy(): pass',
            parameters={'n_stocks': 20, 'lookback': 60},
            metrics=metrics,
            novelty_score=0.85,
            pareto_rank=1,
            crowding_distance=0.75,
            timestamp='2025-01-19T10:30:00',
            template_type='FactorGraph',
            metadata={'author': 'test'}
        )

        # Serialize to dict
        data = original.to_dict()

        # Deserialize back
        restored = Strategy.from_dict(data)

        # Verify all fields match
        assert restored.id == original.id
        assert restored.generation == original.generation
        assert restored.parent_ids == original.parent_ids
        assert restored.code == original.code
        assert restored.parameters == original.parameters
        assert restored.novelty_score == original.novelty_score
        assert restored.pareto_rank == original.pareto_rank
        assert restored.crowding_distance == original.crowding_distance
        assert restored.timestamp == original.timestamp
        assert restored.template_type == original.template_type
        assert restored.metadata == original.metadata

        # Verify metrics
        assert restored.metrics is not None
        assert restored.metrics.sharpe_ratio == original.metrics.sharpe_ratio

    def test_strategy_json_serialization(self):
        """Test Strategy can be JSON serialized."""
        strategy = Strategy(
            id='json-test',
            generation=3,
            parameters={'test': 123}
        )

        data = strategy.to_dict()

        # Should be JSON serializable
        json_str = json.dumps(data)
        assert isinstance(json_str, str)

        # Should be deserializable
        parsed = json.loads(json_str)
        restored = Strategy.from_dict(parsed)
        assert restored.id == 'json-test'

    def test_strategy_dominates_still_works(self):
        """Test Strategy.dominates() still works correctly."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=3.0,
            calmar_ratio=2.5,
            max_drawdown=-0.10,
            total_return=0.60,
            win_rate=0.70,
            annual_return=0.35,
            success=True
        )

        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=1.2,
            max_drawdown=-0.20,
            total_return=0.30,
            win_rate=0.50,
            annual_return=0.20,
            success=True
        )

        strategy_a = Strategy(id='a', generation=1, metrics=metrics_a)
        strategy_b = Strategy(id='b', generation=1, metrics=metrics_b)

        # A should dominate B
        assert strategy_a.dominates(strategy_b) is True
        assert strategy_b.dominates(strategy_a) is False


class TestIStrategyProtocolCompatibility:
    """Test IStrategy Protocol doesn't break existing code."""

    def test_existing_strategy_is_istrategy(self):
        """Test existing Strategy class implements IStrategy."""
        strategy = Strategy(
            id='protocol-test',
            generation=5,
            parameters={'n_stocks': 20}
        )

        # Should pass isinstance check
        assert isinstance(strategy, IStrategy)

    def test_istrategy_methods_work(self):
        """Test IStrategy methods work on Strategy."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=2.0,
            calmar_ratio=1.5,
            max_drawdown=-0.15,
            total_return=0.40,
            win_rate=0.60,
            annual_return=0.25,
            success=True
        )

        strategy = Strategy(
            id='method-test',
            generation=3,
            parameters={'key': 'value'},
            metrics=metrics
        )

        # Test IStrategy methods
        assert strategy.id == 'method-test'
        assert strategy.generation == 3
        assert strategy.metrics is not None

        params = strategy.get_parameters()
        assert params == {'key': 'value'}

        metrics_dict = strategy.get_metrics()
        assert 'sharpe_ratio' in metrics_dict
        assert metrics_dict['sharpe_ratio'] == 2.0

    def test_istrategy_dominates_with_protocol(self):
        """Test dominates() works through IStrategy interface."""
        def compare_strategies(s1: IStrategy, s2: IStrategy) -> bool:
            """Function using IStrategy type hints."""
            return s1.dominates(s2)

        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=3.0, calmar_ratio=2.0, max_drawdown=-0.10,
            total_return=0.50, win_rate=0.65, annual_return=0.30, success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.5, calmar_ratio=1.0, max_drawdown=-0.20,
            total_return=0.30, win_rate=0.50, annual_return=0.20, success=True
        )

        strategy_a = Strategy(id='a', generation=1, metrics=metrics_a)
        strategy_b = Strategy(id='b', generation=1, metrics=metrics_b)

        # Should work through IStrategy interface
        result = compare_strategies(strategy_a, strategy_b)
        assert result is True


class TestHallOfFameRepositoryCompatibility:
    """Test HallOfFameRepository backward compatibility."""

    @pytest.fixture
    def temp_repo(self):
        """Create temporary HallOfFameRepository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = HallOfFameRepository(base_path=tmpdir, test_mode=True)
            yield repo

    def test_save_and_load_strategy(self, temp_repo):
        """Test HallOfFameRepository save/load still works."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=2.5,
            calmar_ratio=1.8,
            max_drawdown=-0.15,
            total_return=0.45,
            win_rate=0.62,
            annual_return=0.28,
            success=True
        )

        strategy = Strategy(
            id='repo-test-001',
            generation=5,
            parent_ids=['parent-001'],
            code='def strategy(): pass',
            parameters={'n_stocks': 20},
            metrics=metrics,
            template_type='FactorGraph'
        )

        # Save
        temp_repo.save_strategy(strategy, tier='champions')

        # Load
        loaded = temp_repo.load_strategy(tier='champions')

        # Verify
        assert loaded is not None
        assert loaded.id == strategy.id
        assert loaded.generation == strategy.generation
        assert loaded.parameters == strategy.parameters

    def test_tier_based_storage(self, temp_repo):
        """Test tier-based storage still works."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=2.0, calmar_ratio=1.5, max_drawdown=-0.15,
            total_return=0.40, win_rate=0.60, annual_return=0.25, success=True
        )

        # Save to different tiers
        for tier in ['champions', 'contenders', 'archive']:
            strategy = Strategy(
                id=f'{tier}-test',
                generation=1,
                parameters={'tier': tier},
                metrics=metrics
            )
            temp_repo.save_strategy(strategy, tier=tier)

        # Verify each tier
        for tier in ['champions', 'contenders', 'archive']:
            loaded = temp_repo.load_strategy(tier=tier)
            assert loaded is not None
            assert loaded.id == f'{tier}-test'


class TestFactorGraphChampionUpdateRegression:
    """Test Factor Graph champion update doesn't regress."""

    def test_factor_graph_strategy_fields(self):
        """Test Factor Graph strategy has required fields."""
        strategy = Strategy(
            id='fg-test-001',
            generation=5,
            parent_ids=['parent-001'],
            code='# Factor Graph DAG representation',
            parameters={
                'dag_nodes': ['Selection', 'Filter'],
                'dag_edges': [('Selection', 'Filter')],
                'node_params': {'Selection': {'top_n': 50}}
            },
            template_type='FactorGraph'
        )

        # Verify Factor Graph fields
        assert strategy.template_type == 'FactorGraph'
        assert 'dag_nodes' in strategy.parameters
        assert 'dag_edges' in strategy.parameters

    def test_factor_graph_implements_istrategy(self):
        """Test Factor Graph Strategy implements IStrategy."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=2.5, calmar_ratio=1.8, max_drawdown=-0.15,
            total_return=0.45, win_rate=0.62, annual_return=0.28, success=True
        )

        strategy = Strategy(
            id='fg-istrategy-test',
            generation=5,
            parameters={'dag_nodes': ['A', 'B']},
            metrics=metrics,
            template_type='FactorGraph'
        )

        # Should implement IStrategy
        assert isinstance(strategy, IStrategy)

        # IStrategy methods should work
        assert strategy.id == 'fg-istrategy-test'
        assert strategy.generation == 5

        params = strategy.get_parameters()
        assert 'dag_nodes' in params

        metrics_dict = strategy.get_metrics()
        assert metrics_dict['sharpe_ratio'] == 2.5


class TestPerformanceMetrics:
    """Test performance characteristics haven't degraded."""

    def test_strategy_creation_is_fast(self):
        """Test Strategy creation performance."""
        import time

        start = time.time()

        # Create 1000 strategies
        for i in range(1000):
            Strategy(
                id=f'perf-test-{i}',
                generation=i % 10,
                parameters={'n_stocks': 20}
            )

        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0, f"Strategy creation too slow: {elapsed:.2f}s for 1000 strategies"

    def test_strategy_serialization_is_fast(self):
        """Test Strategy serialization performance."""
        import time

        metrics = MultiObjectiveMetrics(
            sharpe_ratio=2.0, calmar_ratio=1.5, max_drawdown=-0.15,
            total_return=0.40, win_rate=0.60, annual_return=0.25, success=True
        )

        strategy = Strategy(
            id='perf-serial-test',
            generation=5,
            parameters={'n_stocks': 20, 'lookback': 60, 'threshold': 0.05},
            metrics=metrics,
            metadata={'tags': ['momentum', 'volume']}
        )

        start = time.time()

        # Serialize 1000 times
        for _ in range(1000):
            data = strategy.to_dict()
            _ = Strategy.from_dict(data)

        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0, f"Strategy serialization too slow: {elapsed:.2f}s for 1000 roundtrips"

    def test_istrategy_isinstance_is_fast(self):
        """Test isinstance(strategy, IStrategy) performance."""
        import time

        strategy = Strategy(
            id='isinstance-test',
            generation=5,
            parameters={'n_stocks': 20}
        )

        start = time.time()

        # Check isinstance 10000 times
        for _ in range(10000):
            _ = isinstance(strategy, IStrategy)

        elapsed = time.time() - start

        # Should complete in under 0.5 seconds
        assert elapsed < 0.5, f"isinstance check too slow: {elapsed:.2f}s for 10000 checks"
