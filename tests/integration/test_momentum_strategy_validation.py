"""
Integration Test: Momentum Strategy Validation

Tests that Strategy DAG replicates MomentumTemplate behavior.

Test Coverage:
1. Strategy DAG creation and validation
2. Factor execution order
3. DAG dependency structure
4. Metrics comparison with baseline (when full pipeline is implemented)

Task A.5: Foundation Validation
"""

import pytest
import sys
from typing import Dict

# Add project root to path
sys.path.insert(0, '/mnt/c/Users/jnpi/Documents/finlab')

from src.factor_graph.strategy import Strategy
from src.factor_graph.factor_category import FactorCategory
from examples.momentum_strategy_composition import create_momentum_strategy
from src.templates.momentum_template import MomentumTemplate


class TestMomentumStrategyValidation:
    """Integration tests for momentum strategy validation."""

    @pytest.fixture
    def test_params(self) -> Dict:
        """Standard test parameters for validation."""
        return {
            'momentum_period': 10,
            'ma_period': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10
        }

    @pytest.fixture
    def baseline_params(self) -> Dict:
        """Baseline parameters for MomentumTemplate."""
        return {
            'momentum_period': 10,
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'resample_offset': 0
        }

    def test_strategy_creation(self, test_params):
        """Test that strategy can be created from parameters."""
        strategy = create_momentum_strategy(test_params)

        assert isinstance(strategy, Strategy)
        assert strategy.id == f"momentum_dag_{test_params['momentum_period']}_{test_params['ma_period']}"
        assert strategy.generation == 0
        assert len(strategy.factors) == 5

    def test_strategy_validation(self, test_params):
        """Test that strategy passes validation checks."""
        strategy = create_momentum_strategy(test_params)

        # Should not raise ValueError
        is_valid = strategy.validate()
        assert is_valid is True

    def test_factor_count(self, test_params):
        """Test that strategy has correct number of factors."""
        strategy = create_momentum_strategy(test_params)

        # Should have 5 factors:
        # 1. momentum_factor
        # 2. ma_filter_factor
        # 3. catalyst_factor
        # 4. selection_factor
        # 5. position_signal_factor
        assert len(strategy.factors) == 5

        expected_factor_ids = [
            'momentum_factor',
            'ma_filter_factor',
            'catalyst_factor',
            'selection_factor',
            'position_signal_factor'
        ]

        for factor_id in expected_factor_ids:
            assert factor_id in strategy.factors

    def test_factor_categories(self, test_params):
        """Test that factors have correct categories."""
        strategy = create_momentum_strategy(test_params)

        # Check factor categories
        assert strategy.factors['momentum_factor'].category == FactorCategory.MOMENTUM
        assert strategy.factors['ma_filter_factor'].category == FactorCategory.MOMENTUM
        assert strategy.factors['catalyst_factor'].category == FactorCategory.QUALITY
        assert strategy.factors['selection_factor'].category == FactorCategory.SIGNAL
        assert strategy.factors['position_signal_factor'].category == FactorCategory.ENTRY

    def test_factor_execution_order(self, test_params):
        """Test that factors are in correct topological order."""
        strategy = create_momentum_strategy(test_params)

        factors = strategy.get_factors()
        factor_ids = [f.id for f in factors]

        # Root factors (no dependencies) should come first
        root_factors = ['momentum_factor', 'ma_filter_factor', 'catalyst_factor']
        for root_factor in root_factors:
            root_index = factor_ids.index(root_factor)
            # Root factors should come before selection_factor
            selection_index = factor_ids.index('selection_factor')
            assert root_index < selection_index

        # selection_factor should come before position_signal_factor
        selection_index = factor_ids.index('selection_factor')
        position_index = factor_ids.index('position_signal_factor')
        assert selection_index < position_index

    def test_factor_dependencies(self, test_params):
        """Test that DAG dependencies are correct."""
        strategy = create_momentum_strategy(test_params)

        # Root factors should have no dependencies
        root_factors = ['momentum_factor', 'ma_filter_factor', 'catalyst_factor']
        for factor_id in root_factors:
            predecessors = list(strategy.dag.predecessors(factor_id))
            assert len(predecessors) == 0, f"{factor_id} should have no dependencies"

        # selection_factor should depend on all root factors
        selection_predecessors = list(strategy.dag.predecessors('selection_factor'))
        assert set(selection_predecessors) == set(root_factors)

        # position_signal_factor should depend on selection_factor
        position_predecessors = list(strategy.dag.predecessors('position_signal_factor'))
        assert position_predecessors == ['selection_factor']

    def test_factor_inputs_outputs(self, test_params):
        """Test that factor inputs/outputs are correct."""
        strategy = create_momentum_strategy(test_params)

        # momentum_factor
        momentum = strategy.factors['momentum_factor']
        assert momentum.inputs == ['close']
        assert momentum.outputs == ['momentum']

        # ma_filter_factor
        ma_filter = strategy.factors['ma_filter_factor']
        assert ma_filter.inputs == ['close']
        assert ma_filter.outputs == ['ma_filter']

        # catalyst_factor
        catalyst = strategy.factors['catalyst_factor']
        assert catalyst.inputs == ['close']
        assert catalyst.outputs == ['catalyst_filter']

        # selection_factor
        selection = strategy.factors['selection_factor']
        assert set(selection.inputs) == {'momentum', 'ma_filter', 'catalyst_filter'}
        assert selection.outputs == ['selected']

        # position_signal_factor
        position = strategy.factors['position_signal_factor']
        assert position.inputs == ['selected']
        assert position.outputs == ['positions']

    def test_factor_parameters(self, test_params):
        """Test that factor parameters are correctly set."""
        strategy = create_momentum_strategy(test_params)

        # Check parameters
        assert strategy.factors['momentum_factor'].parameters['momentum_period'] == test_params['momentum_period']
        assert strategy.factors['ma_filter_factor'].parameters['ma_period'] == test_params['ma_period']
        assert strategy.factors['catalyst_factor'].parameters['catalyst_type'] == test_params['catalyst_type']
        assert strategy.factors['catalyst_factor'].parameters['catalyst_lookback'] == test_params['catalyst_lookback']
        assert strategy.factors['selection_factor'].parameters['n_stocks'] == test_params['n_stocks']

    def test_dag_acyclic(self, test_params):
        """Test that DAG is acyclic (no cycles)."""
        strategy = create_momentum_strategy(test_params)

        import networkx as nx
        assert nx.is_directed_acyclic_graph(strategy.dag)

    def test_dag_connected(self, test_params):
        """Test that all factors are connected (no orphans)."""
        strategy = create_momentum_strategy(test_params)

        import networkx as nx
        assert nx.is_weakly_connected(strategy.dag)

    def test_baseline_template_params_valid(self, baseline_params):
        """Test that baseline parameters are valid for MomentumTemplate."""
        template = MomentumTemplate()
        is_valid, errors = template.validate_params(baseline_params)

        assert is_valid, f"Baseline params invalid: {errors}"

    def test_strategy_produces_position_signal(self, test_params):
        """Test that strategy produces position signals."""
        strategy = create_momentum_strategy(test_params)

        # Check that at least one factor produces position signals
        position_columns = {'positions', 'position', 'signal', 'signals'}

        has_position_signal = False
        for factor in strategy.factors.values():
            if any(output in position_columns for output in factor.outputs):
                has_position_signal = True
                break

        assert has_position_signal, "Strategy must produce position signals"

    def test_strategy_copy(self, test_params):
        """Test that strategy can be copied for mutation."""
        original = create_momentum_strategy(test_params)
        copied = original.copy()

        # Should be independent instances
        assert copied is not original
        assert copied.id != original.id  # Copy has "_copy" suffix
        assert len(copied.factors) == len(original.factors)

        # Modifying copy should not affect original
        copied.remove_factor('position_signal_factor')
        assert 'position_signal_factor' not in copied.factors
        assert 'position_signal_factor' in original.factors

    @pytest.mark.parametrize("catalyst_type", ['revenue', 'earnings'])
    def test_different_catalyst_types(self, test_params, catalyst_type):
        """Test strategy creation with different catalyst types."""
        test_params['catalyst_type'] = catalyst_type
        strategy = create_momentum_strategy(test_params)

        assert strategy.validate() is True
        assert strategy.factors['catalyst_factor'].parameters['catalyst_type'] == catalyst_type

    @pytest.mark.parametrize("n_stocks", [5, 10, 15, 20])
    def test_different_portfolio_sizes(self, test_params, n_stocks):
        """Test strategy creation with different portfolio sizes."""
        test_params['n_stocks'] = n_stocks
        strategy = create_momentum_strategy(test_params)

        assert strategy.validate() is True
        assert strategy.factors['selection_factor'].parameters['n_stocks'] == n_stocks


class TestMomentumStrategyMetrics:
    """Tests for metrics comparison (requires full pipeline implementation)."""

    @pytest.fixture
    def baseline_params(self) -> Dict:
        """Baseline parameters for comparison."""
        return {
            'momentum_period': 10,
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'resample_offset': 0
        }

    @pytest.mark.skip(reason="Requires full pipeline implementation with backtest integration")
    def test_metrics_match_baseline(self, baseline_params):
        """Test that Strategy DAG metrics match MomentumTemplate within tolerance."""
        # This test will be implemented when full pipeline is ready
        # It should:
        # 1. Execute MomentumTemplate.generate_strategy(baseline_params)
        # 2. Execute Strategy DAG with equivalent params
        # 3. Compare metrics with ±5% tolerance
        pass

    @pytest.mark.skip(reason="Requires full pipeline implementation with backtest integration")
    def test_annual_return_match(self, baseline_params):
        """Test that annual return matches within ±5%."""
        pass

    @pytest.mark.skip(reason="Requires full pipeline implementation with backtest integration")
    def test_sharpe_ratio_match(self, baseline_params):
        """Test that Sharpe ratio matches within ±5%."""
        pass

    @pytest.mark.skip(reason="Requires full pipeline implementation with backtest integration")
    def test_max_drawdown_match(self, baseline_params):
        """Test that max drawdown matches within ±5%."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
