"""
Unit tests for evolutionary optimization data types.

Tests MultiObjectiveMetrics, Strategy, and Population dataclasses including:
- Pareto dominance logic
- Serialization/deserialization
- Property calculations
- Edge cases
"""

import pytest
from datetime import datetime

from src.evolution.types import (
    MultiObjectiveMetrics,
    Strategy,
    Population
)


class TestMultiObjectiveMetrics:
    """Test suite for MultiObjectiveMetrics dataclass."""

    def test_dominates_clear_dominance(self):
        """Test A dominates B when A is strictly better in all objectives."""
        # A is better in all metrics
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.10,  # Less negative is better
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.2,
            calmar_ratio=1.8,
            max_drawdown=-0.15,  # More negative is worse
            total_return=0.40,
            win_rate=0.55,
            annual_return=0.18,
            success=True
        )

        # A should dominate B
        assert metrics_a.dominates(metrics_b) is True
        # B should not dominate A
        assert metrics_b.dominates(metrics_a) is False

    def test_dominates_no_dominance_mixed_performance(self):
        """Test no dominance when A is better in some, worse in others."""
        # A is better in sharpe/calmar, worse in drawdown/return
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.20,  # Worse (more negative)
            total_return=0.40,   # Worse
            win_rate=0.60,
            annual_return=0.18,
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.2,
            calmar_ratio=1.8,
            max_drawdown=-0.10,  # Better (less negative)
            total_return=0.50,   # Better
            win_rate=0.55,
            annual_return=0.20,
            success=True
        )

        # Neither should dominate
        assert metrics_a.dominates(metrics_b) is False
        assert metrics_b.dominates(metrics_a) is False

    def test_dominates_equal_metrics_no_dominance(self):
        """Test no dominance when all metrics are equal."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.15,
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.15,
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )

        # Equal metrics should not dominate
        assert metrics_a.dominates(metrics_b) is False
        assert metrics_b.dominates(metrics_a) is False

    def test_dominates_better_in_one_dominance(self):
        """Test dominance when strictly better in one objective, equal in others."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=1.5,  # Better
            calmar_ratio=2.0,
            max_drawdown=-0.15,
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.2,  # Worse
            calmar_ratio=2.0,
            max_drawdown=-0.15,
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )

        # A should dominate B (better in one, equal in rest)
        assert metrics_a.dominates(metrics_b) is True
        assert metrics_b.dominates(metrics_a) is False

    def test_dominates_failed_backtest_cannot_dominate(self):
        """Test that failed backtests cannot dominate, even with better metrics."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=2.0,
            calmar_ratio=3.0,
            max_drawdown=-0.05,
            total_return=0.60,
            win_rate=0.70,
            annual_return=0.25,
            success=False  # Failed
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.0,
            calmar_ratio=1.5,
            max_drawdown=-0.20,
            total_return=0.30,
            win_rate=0.50,
            annual_return=0.15,
            success=True
        )

        # Failed backtest cannot dominate
        assert metrics_a.dominates(metrics_b) is False
        # Successful backtest cannot be dominated by failed one
        assert metrics_b.dominates(metrics_a) is False

    def test_dominates_max_drawdown_less_negative_is_better(self):
        """Test that less negative max_drawdown is correctly treated as better."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.10,  # Better (less negative)
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.25,  # Worse (more negative)
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )

        # A should dominate B (better drawdown)
        assert metrics_a.dominates(metrics_b) is True
        assert metrics_b.dominates(metrics_a) is False

    def test_repr(self):
        """Test string representation for debugging."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.15,
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )
        repr_str = repr(metrics)

        assert 'MultiObjectiveMetrics' in repr_str
        assert '1.5000' in repr_str  # sharpe
        assert '2.0000' in repr_str  # calmar
        assert '-0.1500' in repr_str  # drawdown
        assert '0.5000' in repr_str  # return


class TestStrategy:
    """Test suite for Strategy dataclass."""

    def test_auto_generate_id(self):
        """Test that Strategy auto-generates UUID if not provided."""
        strategy = Strategy(
            code='def strategy(): pass',
            parameters={'n_stocks': 10}
        )

        # ID should be generated and non-empty
        assert strategy.id != ""
        assert len(strategy.id) > 0
        # Should be a valid UUID format (36 chars with hyphens)
        assert len(strategy.id) == 36
        assert strategy.id.count('-') == 4

    def test_auto_generate_timestamp(self):
        """Test that Strategy auto-generates ISO 8601 timestamp if not provided."""
        strategy = Strategy(
            code='def strategy(): pass',
            parameters={'n_stocks': 10}
        )

        # Timestamp should be generated and non-empty
        assert strategy.timestamp != ""
        # Should be parseable as datetime
        parsed_time = datetime.fromisoformat(strategy.timestamp)
        assert isinstance(parsed_time, datetime)

    def test_preserve_provided_id_and_timestamp(self):
        """Test that provided ID and timestamp are preserved."""
        strategy = Strategy(
            id='custom-uuid-1234',
            timestamp='2025-10-19T12:00:00',
            code='def strategy(): pass',
            parameters={'n_stocks': 10}
        )

        assert strategy.id == 'custom-uuid-1234'
        assert strategy.timestamp == '2025-10-19T12:00:00'

    def test_to_dict_complete_serialization(self):
        """Test Strategy serialization to dictionary with all fields."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.15,
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )
        strategy = Strategy(
            id='test-id-1234',
            generation=5,
            parent_ids=['parent-1', 'parent-2'],
            code='def strategy(): pass',
            parameters={'n_stocks': 10, 'holding_period': 20},
            metrics=metrics,
            novelty_score=0.75,
            pareto_rank=1,
            crowding_distance=0.85,
            timestamp='2025-10-19T12:00:00',
            template_type='Momentum',
            metadata={'source': 'crossover'}
        )

        data = strategy.to_dict()

        # Check all fields present
        assert data['id'] == 'test-id-1234'
        assert data['generation'] == 5
        assert data['parent_ids'] == ['parent-1', 'parent-2']
        assert data['code'] == 'def strategy(): pass'
        assert data['parameters'] == {'n_stocks': 10, 'holding_period': 20}
        assert data['novelty_score'] == 0.75
        assert data['pareto_rank'] == 1
        assert data['crowding_distance'] == 0.85
        assert data['timestamp'] == '2025-10-19T12:00:00'
        assert data['template_type'] == 'Momentum'
        assert data['metadata'] == {'source': 'crossover'}

        # Check metrics nested dictionary
        assert data['metrics']['sharpe_ratio'] == 1.5
        assert data['metrics']['calmar_ratio'] == 2.0
        assert data['metrics']['max_drawdown'] == -0.15
        assert data['metrics']['total_return'] == 0.50
        assert data['metrics']['win_rate'] == 0.60
        assert data['metrics']['annual_return'] == 0.20
        assert data['metrics']['success'] is True

    def test_to_dict_none_metrics(self):
        """Test Strategy serialization when metrics is None."""
        strategy = Strategy(
            id='test-id-1234',
            generation=1,
            code='def strategy(): pass',
            parameters={'n_stocks': 10}
        )

        data = strategy.to_dict()

        # Metrics should be None
        assert data['metrics'] is None

    def test_from_dict_complete_deserialization(self):
        """Test Strategy deserialization from dictionary with all fields."""
        data = {
            'id': 'test-id-1234',
            'generation': 5,
            'parent_ids': ['parent-1', 'parent-2'],
            'code': 'def strategy(): pass',
            'parameters': {'n_stocks': 10, 'holding_period': 20},
            'metrics': {
                'sharpe_ratio': 1.5,
                'calmar_ratio': 2.0,
                'max_drawdown': -0.15,
                'total_return': 0.50,
                'win_rate': 0.60,
                'annual_return': 0.20,
                'success': True
            },
            'novelty_score': 0.75,
            'pareto_rank': 1,
            'crowding_distance': 0.85,
            'timestamp': '2025-10-19T12:00:00',
            'template_type': 'Momentum',
            'metadata': {'source': 'crossover'}
        }

        strategy = Strategy.from_dict(data)

        # Check all fields
        assert strategy.id == 'test-id-1234'
        assert strategy.generation == 5
        assert strategy.parent_ids == ['parent-1', 'parent-2']
        assert strategy.code == 'def strategy(): pass'
        assert strategy.parameters == {'n_stocks': 10, 'holding_period': 20}
        assert strategy.novelty_score == 0.75
        assert strategy.pareto_rank == 1
        assert strategy.crowding_distance == 0.85
        assert strategy.timestamp == '2025-10-19T12:00:00'
        assert strategy.template_type == 'Momentum'
        assert strategy.metadata == {'source': 'crossover'}

        # Check metrics
        assert strategy.metrics.sharpe_ratio == 1.5
        assert strategy.metrics.calmar_ratio == 2.0
        assert strategy.metrics.max_drawdown == -0.15
        assert strategy.metrics.total_return == 0.50
        assert strategy.metrics.win_rate == 0.60
        assert strategy.metrics.annual_return == 0.20
        assert strategy.metrics.success is True

    def test_from_dict_none_metrics(self):
        """Test Strategy deserialization when metrics is None."""
        data = {
            'id': 'test-id-1234',
            'generation': 1,
            'parent_ids': [],
            'code': 'def strategy(): pass',
            'parameters': {'n_stocks': 10},
            'metrics': None,
            'novelty_score': 0.0,
            'pareto_rank': 0,
            'crowding_distance': 0.0,
            'timestamp': '2025-10-19T12:00:00',
            'template_type': 'Momentum',
            'metadata': {}
        }

        strategy = Strategy.from_dict(data)

        assert strategy.metrics is None

    def test_from_dict_missing_fields_use_defaults(self):
        """Test Strategy deserialization with missing fields uses defaults."""
        data = {
            'code': 'def strategy(): pass'
        }

        strategy = Strategy.from_dict(data)

        # Should use default values
        # ID will be auto-generated in __post_init__ when empty string is provided
        assert strategy.id != ''  # Auto-generated UUID
        assert len(strategy.id) == 36  # Valid UUID format
        assert strategy.generation == 0
        assert strategy.parent_ids == []
        assert strategy.parameters == {}
        assert strategy.metrics is None
        assert strategy.novelty_score == 0.0
        assert strategy.pareto_rank == 0
        assert strategy.crowding_distance == 0.0
        assert strategy.template_type == 'Momentum'
        assert strategy.metadata == {}

    def test_serialization_roundtrip(self):
        """Test that Strategy survives serialization roundtrip."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.15,
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )
        original = Strategy(
            id='test-id-1234',
            generation=5,
            parent_ids=['parent-1', 'parent-2'],
            code='def strategy(): pass',
            parameters={'n_stocks': 10, 'holding_period': 20},
            metrics=metrics,
            novelty_score=0.75,
            pareto_rank=1,
            crowding_distance=0.85,
            timestamp='2025-10-19T12:00:00',
            template_type='Momentum',
            metadata={'source': 'crossover'}
        )

        # Serialize and deserialize
        data = original.to_dict()
        reconstructed = Strategy.from_dict(data)

        # All fields should match
        assert reconstructed.id == original.id
        assert reconstructed.generation == original.generation
        assert reconstructed.parent_ids == original.parent_ids
        assert reconstructed.code == original.code
        assert reconstructed.parameters == original.parameters
        assert reconstructed.novelty_score == original.novelty_score
        assert reconstructed.pareto_rank == original.pareto_rank
        assert reconstructed.crowding_distance == original.crowding_distance
        assert reconstructed.timestamp == original.timestamp
        assert reconstructed.template_type == original.template_type
        assert reconstructed.metadata == original.metadata

        # Metrics should match
        assert reconstructed.metrics.sharpe_ratio == original.metrics.sharpe_ratio
        assert reconstructed.metrics.calmar_ratio == original.metrics.calmar_ratio
        assert reconstructed.metrics.max_drawdown == original.metrics.max_drawdown
        assert reconstructed.metrics.total_return == original.metrics.total_return
        assert reconstructed.metrics.win_rate == original.metrics.win_rate
        assert reconstructed.metrics.annual_return == original.metrics.annual_return
        assert reconstructed.metrics.success == original.metrics.success

    def test_dominates_with_metrics(self):
        """Test Strategy.dominates() delegates to metrics.dominates()."""
        strategy_a = Strategy(
            code='def strategy_a(): pass',
            metrics=MultiObjectiveMetrics(
                sharpe_ratio=1.5,
                calmar_ratio=2.0,
                max_drawdown=-0.10,
                total_return=0.50,
                win_rate=0.60,
                annual_return=0.20,
                success=True
            )
        )
        strategy_b = Strategy(
            code='def strategy_b(): pass',
            metrics=MultiObjectiveMetrics(
                sharpe_ratio=1.2,
                calmar_ratio=1.8,
                max_drawdown=-0.15,
                total_return=0.40,
                win_rate=0.55,
                annual_return=0.18,
                success=True
            )
        )

        # Should delegate to metrics
        assert strategy_a.dominates(strategy_b) is True
        assert strategy_b.dominates(strategy_a) is False

    def test_dominates_missing_metrics(self):
        """Test Strategy.dominates() returns False when metrics missing."""
        strategy_a = Strategy(
            code='def strategy_a(): pass',
            metrics=None
        )
        strategy_b = Strategy(
            code='def strategy_b(): pass',
            metrics=MultiObjectiveMetrics(
                sharpe_ratio=1.2,
                calmar_ratio=1.8,
                max_drawdown=-0.15,
                total_return=0.40,
                win_rate=0.55,
                annual_return=0.18,
                success=True
            )
        )

        # Cannot dominate without metrics
        assert strategy_a.dominates(strategy_b) is False
        assert strategy_b.dominates(strategy_a) is False

    def test_repr(self):
        """Test string representation for debugging."""
        strategy = Strategy(
            id='test-id-1234567890',
            generation=5,
            template_type='Momentum',
            pareto_rank=1
        )
        repr_str = repr(strategy)

        assert 'Strategy' in repr_str
        assert 'test-id-' in repr_str  # First 8 chars
        assert 'gen=5' in repr_str
        assert 'template=Momentum' in repr_str
        assert 'rank=1' in repr_str


class TestPopulation:
    """Test suite for Population dataclass."""

    def test_auto_generate_timestamp(self):
        """Test that Population auto-generates ISO 8601 timestamp if not provided."""
        population = Population(
            generation=1,
            strategies=[]
        )

        # Timestamp should be generated and non-empty
        assert population.timestamp != ""
        # Should be parseable as datetime
        parsed_time = datetime.fromisoformat(population.timestamp)
        assert isinstance(parsed_time, datetime)

    def test_preserve_provided_timestamp(self):
        """Test that provided timestamp is preserved."""
        population = Population(
            generation=1,
            strategies=[],
            timestamp='2025-10-19T12:00:00'
        )

        assert population.timestamp == '2025-10-19T12:00:00'

    def test_size_property(self):
        """Test Population.size returns number of strategies."""
        strategies = [
            Strategy(code='def s1(): pass'),
            Strategy(code='def s2(): pass'),
            Strategy(code='def s3(): pass')
        ]
        population = Population(
            generation=1,
            strategies=strategies
        )

        assert population.size == 3

    def test_size_empty_population(self):
        """Test Population.size returns 0 for empty population."""
        population = Population(
            generation=1,
            strategies=[]
        )

        assert population.size == 0

    def test_best_sharpe_finds_maximum(self):
        """Test Population.best_sharpe returns strategy with highest Sharpe ratio."""
        strategies = [
            Strategy(
                code='def s1(): pass',
                metrics=MultiObjectiveMetrics(1.2, 1.8, -0.15, 0.40, 0.55, 0.18, True)
            ),
            Strategy(
                code='def s2(): pass',
                metrics=MultiObjectiveMetrics(1.5, 2.0, -0.10, 0.50, 0.60, 0.20, True)
            ),
            Strategy(
                code='def s3(): pass',
                metrics=MultiObjectiveMetrics(1.0, 1.5, -0.20, 0.30, 0.50, 0.15, True)
            )
        ]
        population = Population(
            generation=1,
            strategies=strategies
        )

        best = population.best_sharpe
        assert best is not None
        assert best.metrics.sharpe_ratio == 1.5

    def test_best_sharpe_unevaluated_strategies(self):
        """Test Population.best_sharpe returns None when no strategies evaluated."""
        strategies = [
            Strategy(code='def s1(): pass', metrics=None),
            Strategy(code='def s2(): pass', metrics=None),
            Strategy(code='def s3(): pass', metrics=None)
        ]
        population = Population(
            generation=1,
            strategies=strategies
        )

        assert population.best_sharpe is None

    def test_best_sharpe_empty_population(self):
        """Test Population.best_sharpe returns None for empty population."""
        population = Population(
            generation=1,
            strategies=[]
        )

        assert population.best_sharpe is None

    def test_best_sharpe_ignores_failed_backtests(self):
        """Test Population.best_sharpe ignores strategies with failed backtests."""
        strategies = [
            Strategy(
                code='def s1(): pass',
                metrics=MultiObjectiveMetrics(1.2, 1.8, -0.15, 0.40, 0.55, 0.18, True)
            ),
            Strategy(
                code='def s2(): pass',
                metrics=MultiObjectiveMetrics(2.0, 3.0, -0.05, 0.60, 0.70, 0.25, False)  # Failed
            ),
            Strategy(
                code='def s3(): pass',
                metrics=MultiObjectiveMetrics(1.0, 1.5, -0.20, 0.30, 0.50, 0.15, True)
            )
        ]
        population = Population(
            generation=1,
            strategies=strategies
        )

        best = population.best_sharpe
        # Should be s1 (1.2), not s2 (2.0 but failed)
        assert best.metrics.sharpe_ratio == 1.2

    def test_avg_sharpe_calculates_mean(self):
        """Test Population.avg_sharpe calculates average Sharpe ratio."""
        strategies = [
            Strategy(
                code='def s1(): pass',
                metrics=MultiObjectiveMetrics(1.0, 1.5, -0.20, 0.30, 0.50, 0.15, True)
            ),
            Strategy(
                code='def s2(): pass',
                metrics=MultiObjectiveMetrics(1.5, 2.0, -0.10, 0.50, 0.60, 0.20, True)
            ),
            Strategy(
                code='def s3(): pass',
                metrics=MultiObjectiveMetrics(2.0, 2.5, -0.05, 0.60, 0.70, 0.25, True)
            )
        ]
        population = Population(
            generation=1,
            strategies=strategies
        )

        # Average: (1.0 + 1.5 + 2.0) / 3 = 1.5
        assert population.avg_sharpe == pytest.approx(1.5, rel=1e-9)

    def test_avg_sharpe_unevaluated_strategies(self):
        """Test Population.avg_sharpe returns 0.0 when no strategies evaluated."""
        strategies = [
            Strategy(code='def s1(): pass', metrics=None),
            Strategy(code='def s2(): pass', metrics=None),
            Strategy(code='def s3(): pass', metrics=None)
        ]
        population = Population(
            generation=1,
            strategies=strategies
        )

        assert population.avg_sharpe == 0.0

    def test_avg_sharpe_empty_population(self):
        """Test Population.avg_sharpe returns 0.0 for empty population."""
        population = Population(
            generation=1,
            strategies=[]
        )

        assert population.avg_sharpe == 0.0

    def test_avg_sharpe_ignores_failed_backtests(self):
        """Test Population.avg_sharpe ignores strategies with failed backtests."""
        strategies = [
            Strategy(
                code='def s1(): pass',
                metrics=MultiObjectiveMetrics(1.0, 1.5, -0.20, 0.30, 0.50, 0.15, True)
            ),
            Strategy(
                code='def s2(): pass',
                metrics=MultiObjectiveMetrics(5.0, 6.0, -0.02, 0.80, 0.90, 0.35, False)  # Failed
            ),
            Strategy(
                code='def s3(): pass',
                metrics=MultiObjectiveMetrics(2.0, 2.5, -0.05, 0.60, 0.70, 0.25, True)
            )
        ]
        population = Population(
            generation=1,
            strategies=strategies
        )

        # Average: (1.0 + 2.0) / 2 = 1.5 (excludes failed s2)
        assert population.avg_sharpe == pytest.approx(1.5, rel=1e-9)

    def test_avg_sharpe_mixed_evaluated_and_unevaluated(self):
        """Test Population.avg_sharpe handles mix of evaluated and unevaluated."""
        strategies = [
            Strategy(
                code='def s1(): pass',
                metrics=MultiObjectiveMetrics(1.0, 1.5, -0.20, 0.30, 0.50, 0.15, True)
            ),
            Strategy(code='def s2(): pass', metrics=None),
            Strategy(
                code='def s3(): pass',
                metrics=MultiObjectiveMetrics(2.0, 2.5, -0.05, 0.60, 0.70, 0.25, True)
            )
        ]
        population = Population(
            generation=1,
            strategies=strategies
        )

        # Average: (1.0 + 2.0) / 2 = 1.5 (excludes unevaluated s2)
        assert population.avg_sharpe == pytest.approx(1.5, rel=1e-9)

    def test_to_dict_serialization(self):
        """Test Population serialization to dictionary."""
        strategies = [
            Strategy(
                id='strategy-1',
                code='def s1(): pass',
                metrics=MultiObjectiveMetrics(1.5, 2.0, -0.10, 0.50, 0.60, 0.20, True)
            ),
            Strategy(
                id='strategy-2',
                code='def s2(): pass',
                metrics=None
            )
        ]
        population = Population(
            generation=5,
            strategies=strategies,
            pareto_front=[strategies[0]],
            diversity_metrics={'avg_distance': 0.75},
            timestamp='2025-10-19T12:00:00'
        )

        data = population.to_dict()

        assert data['generation'] == 5
        assert len(data['strategies']) == 2
        assert data['pareto_front'] == ['strategy-1']
        assert data['diversity_metrics'] == {'avg_distance': 0.75}
        assert data['timestamp'] == '2025-10-19T12:00:00'

    def test_repr(self):
        """Test string representation for debugging."""
        strategies = [
            Strategy(code='def s1(): pass'),
            Strategy(code='def s2(): pass')
        ]
        population = Population(
            generation=5,
            strategies=strategies,
            pareto_front=[strategies[0]]
        )
        repr_str = repr(population)

        assert 'Population' in repr_str
        assert 'gen=5' in repr_str
        assert 'size=2' in repr_str
        assert 'pareto=1' in repr_str


class TestEdgeCases:
    """Test suite for edge cases across all data types."""

    def test_empty_population_all_properties(self):
        """Test empty population handles all property calculations safely."""
        population = Population(
            generation=1,
            strategies=[]
        )

        # All properties should handle empty population gracefully
        assert population.size == 0
        assert population.best_sharpe is None
        assert population.avg_sharpe == 0.0

    def test_population_only_failed_strategies(self):
        """Test population with only failed strategies."""
        strategies = [
            Strategy(
                code='def s1(): pass',
                metrics=MultiObjectiveMetrics(1.5, 2.0, -0.10, 0.50, 0.60, 0.20, False)
            ),
            Strategy(
                code='def s2(): pass',
                metrics=MultiObjectiveMetrics(1.2, 1.8, -0.15, 0.40, 0.55, 0.18, False)
            )
        ]
        population = Population(
            generation=1,
            strategies=strategies
        )

        # Should handle all-failed population
        assert population.size == 2
        assert population.best_sharpe is None
        assert population.avg_sharpe == 0.0

    def test_metrics_extreme_values(self):
        """Test MultiObjectiveMetrics with extreme values."""
        # Very high performance
        metrics_high = MultiObjectiveMetrics(
            sharpe_ratio=10.0,
            calmar_ratio=20.0,
            max_drawdown=-0.01,
            total_return=5.0,
            win_rate=0.99,
            annual_return=2.0,
            success=True
        )

        # Very poor performance
        metrics_low = MultiObjectiveMetrics(
            sharpe_ratio=-2.0,
            calmar_ratio=-5.0,
            max_drawdown=-0.95,
            total_return=-0.80,
            win_rate=0.01,
            annual_return=-0.50,
            success=True
        )

        # Should handle extreme values correctly
        assert metrics_high.dominates(metrics_low) is True
        assert metrics_low.dominates(metrics_high) is False

    def test_strategy_empty_code(self):
        """Test Strategy with empty code string."""
        strategy = Strategy(
            code='',
            parameters={}
        )

        # Should create successfully
        assert strategy.code == ''
        assert strategy.id != ''
        assert strategy.timestamp != ''

    def test_strategy_large_parameters_dict(self):
        """Test Strategy with large parameters dictionary."""
        large_params = {f'param_{i}': i * 0.1 for i in range(100)}
        strategy = Strategy(
            code='def strategy(): pass',
            parameters=large_params
        )

        # Should handle large parameter sets
        assert len(strategy.parameters) == 100

        # Test serialization roundtrip
        data = strategy.to_dict()
        reconstructed = Strategy.from_dict(data)
        assert reconstructed.parameters == large_params

    def test_population_large_strategy_list(self):
        """Test Population with large number of strategies."""
        strategies = [
            Strategy(
                code=f'def strategy_{i}(): pass',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0 + i * 0.1,
                    calmar_ratio=1.5 + i * 0.1,
                    max_drawdown=-0.20 + i * 0.01,
                    total_return=0.30 + i * 0.05,
                    win_rate=0.50 + i * 0.01,
                    annual_return=0.15 + i * 0.02,
                    success=True
                )
            )
            for i in range(100)
        ]
        population = Population(
            generation=1,
            strategies=strategies
        )

        # Should handle large populations
        assert population.size == 100
        assert population.best_sharpe is not None
        assert population.avg_sharpe > 0
