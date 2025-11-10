"""
Test Suite for Strategy (Phase 2.0 Matrix-Native)
=================================================

Comprehensive tests for Strategy.to_pipeline() with FinLabDataFrame container.
Tests cover DAG execution, factor chaining, and position matrix extraction.

Test Coverage:
--------------
1. Basic Pipeline Execution
   - Single factor execution
   - Multi-factor pipeline
   - Factor DAG topological sort

2. Container Integration
   - FinLabDataFrame creation
   - Matrix flow through factors
   - Position matrix extraction

3. Error Handling
   - Missing position matrix
   - Invalid DAG (cycles)
   - Missing input matrices
   - Factor validation errors

Architecture: Phase 2.0 Matrix-Native Factor Graph System
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock

from src.factor_graph.strategy import Strategy
from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.finlab_dataframe import FinLabDataFrame


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_data_module():
    """Create mock finlab data module."""
    mock_data = Mock()

    # Create sample price matrices
    dates = pd.date_range('2023-01-01', periods=100)
    symbols = ['2330', '2317', '2454']

    close = pd.DataFrame(
        np.random.randn(100, 3) * 10 + 100,
        index=dates,
        columns=symbols
    )

    high = close * 1.02
    low = close * 0.98

    # Mock get() method
    def get_side_effect(key):
        mapping = {
            'price:收盤價': close,
            'price:最高價': high,
            'price:最低價': low,
        }
        return mapping.get(key)

    mock_data.get = Mock(side_effect=get_side_effect)
    return mock_data


@pytest.fixture
def simple_factor():
    """Create a simple factor for testing."""
    def logic(container, parameters):
        close = container.get_matrix('close')
        momentum = (close / close.shift(10)) - 1
        container.add_matrix('momentum', momentum)

    return Factor(
        id='momentum_10',
        name='Momentum 10',
        category=FactorCategory.MOMENTUM,
        inputs=['close'],
        outputs=['momentum'],
        logic=logic,
        parameters={'period': 10}
    )


@pytest.fixture
def position_factor():
    """Create a factor that produces position matrix."""
    def logic(container, parameters):
        momentum = container.get_matrix('momentum')
        position = (momentum > 0).astype(float)
        container.add_matrix('position', position)

    return Factor(
        id='position_from_momentum',
        name='Position from Momentum',
        category=FactorCategory.ENTRY,
        inputs=['momentum'],
        outputs=['position'],
        logic=logic,
        parameters={}
    )


# ============================================================================
# Basic Pipeline Execution Tests
# ============================================================================

class TestBasicPipelineExecution:
    """Test basic pipeline execution with to_pipeline()."""

    def test_single_factor_pipeline(self, mock_data_module, simple_factor, position_factor):
        """Test pipeline with single factor chain."""
        strategy = Strategy(id='test_strategy')
        strategy.add_factor(simple_factor)
        strategy.add_factor(position_factor, depends_on=['momentum_10'])

        # Execute pipeline
        positions = strategy.to_pipeline(mock_data_module)

        # Verify output
        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (100, 3)  # Same shape as input
        assert not positions.isna().all().all()  # Has non-NaN values

    def test_multi_factor_pipeline_execution(self, mock_data_module):
        """Test pipeline with multiple factors in sequence."""
        # Create multi-factor strategy
        def momentum_logic(container, params):
            close = container.get_matrix('close')
            momentum = (close / close.shift(params['period'])) - 1
            container.add_matrix('momentum', momentum)

        def filter_logic(container, params):
            close = container.get_matrix('close')
            ma = close.rolling(window=params['ma_period']).mean()
            trend_filter = close > ma
            container.add_matrix('trend_filter', trend_filter)

        def position_logic(container, params):
            momentum = container.get_matrix('momentum')
            trend_filter = container.get_matrix('trend_filter')
            position = ((momentum > 0) & trend_filter).astype(float)
            container.add_matrix('position', position)

        # Create factors
        momentum_factor = Factor(
            id='momentum', name='Momentum', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['momentum'], logic=momentum_logic,
            parameters={'period': 10}
        )

        filter_factor = Factor(
            id='filter', name='Filter', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['trend_filter'], logic=filter_logic,
            parameters={'ma_period': 20}
        )

        position_factor = Factor(
            id='position', name='Position', category=FactorCategory.ENTRY,
            inputs=['momentum', 'trend_filter'], outputs=['position'],
            logic=position_logic, parameters={}
        )

        # Create strategy
        strategy = Strategy(id='multi_factor')
        strategy.add_factor(momentum_factor)
        strategy.add_factor(filter_factor)
        strategy.add_factor(position_factor, depends_on=['momentum', 'filter'])

        # Execute
        positions = strategy.to_pipeline(mock_data_module)

        assert positions.shape == (100, 3)
        assert positions.dtypes.apply(lambda x: x in [float, 'float64']).all()

    def test_empty_strategy_raises_error(self, mock_data_module):
        """Test that empty strategy raises validation error."""
        strategy = Strategy(id='empty')

        with pytest.raises(ValueError, match="must contain at least one factor"):
            strategy.to_pipeline(mock_data_module)


# ============================================================================
# Container Integration Tests
# ============================================================================

class TestContainerIntegration:
    """Test FinLabDataFrame container integration."""

    def test_container_creation_from_data_module(self, mock_data_module, simple_factor, position_factor):
        """Test that container is created correctly from data module."""
        strategy = Strategy(id='test')
        strategy.add_factor(simple_factor)
        strategy.add_factor(position_factor, depends_on=['momentum_10'])

        # Mock the logic to capture container
        captured_container = None

        def capture_logic(container, parameters):
            nonlocal captured_container
            captured_container = container
            close = container.get_matrix('close')
            momentum = (close / close.shift(10)) - 1
            container.add_matrix('momentum', momentum)

        simple_factor.logic = capture_logic

        strategy.to_pipeline(mock_data_module)

        # Verify container was created
        assert captured_container is not None
        assert isinstance(captured_container, FinLabDataFrame)
        assert captured_container.has_matrix('close')

    def test_matrix_flow_through_pipeline(self, mock_data_module):
        """Test that matrices flow correctly through factor pipeline."""
        matrix_history = []

        def tracking_logic(name):
            def logic(container, parameters):
                matrix_history.append((name, container.list_matrices()))

                if name == 'factor1':
                    close = container.get_matrix('close')
                    container.add_matrix('output1', close * 1.1)
                elif name == 'factor2':
                    output1 = container.get_matrix('output1')
                    container.add_matrix('output2', output1 * 1.1)
                elif name == 'factor3':
                    output2 = container.get_matrix('output2')
                    container.add_matrix('position', output2 > 100)

            return logic

        # Create factors with tracking
        factors = [
            Factor(
                id=f'factor{i}', name=f'Factor {i}',
                category=FactorCategory.MOMENTUM,
                inputs=['close'] if i == 1 else [f'output{i-1}'],
                outputs=[f'output{i}'] if i < 3 else ['position'],
                logic=tracking_logic(f'factor{i}'),
                parameters={}
            )
            for i in range(1, 4)
        ]

        strategy = Strategy(id='tracking')
        strategy.add_factor(factors[0])  # factor1
        strategy.add_factor(factors[1], depends_on=['factor1'])  # factor2
        strategy.add_factor(factors[2], depends_on=['factor2'])  # factor3

        strategy.to_pipeline(mock_data_module)

        # Verify matrix accumulation
        assert len(matrix_history) == 3
        assert 'close' in matrix_history[0][1]
        assert 'output1' in matrix_history[1][1]
        assert 'output2' in matrix_history[2][1]

    def test_position_matrix_extraction(self, mock_data_module, simple_factor, position_factor):
        """Test that position matrix is correctly extracted."""
        strategy = Strategy(id='test')
        strategy.add_factor(simple_factor)
        strategy.add_factor(position_factor, depends_on=['momentum_10'])

        positions = strategy.to_pipeline(mock_data_module)

        # Verify it's the position matrix
        assert isinstance(positions, pd.DataFrame)
        assert positions.shape[0] == 100  # Same number of dates
        assert positions.shape[1] == 3    # Same number of symbols


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in pipeline execution."""

    def test_missing_position_matrix_raises_error(self, mock_data_module, simple_factor):
        """Test that missing position matrix raises KeyError."""
        strategy = Strategy(id='no_position')
        strategy.add_factor(simple_factor)  # Doesn't produce 'position'

        with pytest.raises(KeyError, match="did not produce 'position' matrix"):
            strategy.to_pipeline(mock_data_module, skip_validation=True)

    def test_missing_input_matrix_raises_error(self, mock_data_module):
        """Test that missing input matrix raises clear error."""
        def bad_logic(container, parameters):
            # Try to access non-existent matrix
            nonexistent = container.get_matrix('nonexistent')
            container.add_matrix('position', nonexistent)

        bad_factor = Factor(
            id='bad', name='Bad', category=FactorCategory.MOMENTUM,
            inputs=['nonexistent'], outputs=['position'],
            logic=bad_logic, parameters={}
        )

        strategy = Strategy(id='bad')
        strategy.add_factor(bad_factor)

        with pytest.raises((KeyError, RuntimeError)):
            strategy.to_pipeline(mock_data_module, skip_validation=True)

    def test_factor_validation_error_propagates(self, mock_data_module):
        """Test that factor validation errors propagate correctly."""
        def error_logic(container, parameters):
            raise ValueError("Intentional error in factor logic")

        error_factor = Factor(
            id='error', name='Error', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['position'],
            logic=error_logic, parameters={}
        )

        strategy = Strategy(id='error')
        strategy.add_factor(error_factor)

        with pytest.raises(ValueError, match="Intentional error"):
            strategy.to_pipeline(mock_data_module)

    def test_invalid_data_module_raises_error(self, simple_factor, position_factor):
        """Test that invalid data module raises error."""
        strategy = Strategy(id='test')
        strategy.add_factor(simple_factor)
        strategy.add_factor(position_factor, depends_on=['momentum_10'])

        # Pass None as data module
        with pytest.raises((AttributeError, TypeError)):
            strategy.to_pipeline(None)


# ============================================================================
# DAG Execution Tests
# ============================================================================

class TestDAGExecution:
    """Test DAG topological sort and execution order."""

    def test_factor_execution_order(self, mock_data_module):
        """Test that factors execute in correct topological order."""
        execution_order = []

        def tracking_logic(factor_id):
            def logic(container, parameters):
                execution_order.append(factor_id)

                # Simple logic to produce output
                if factor_id == 'A':
                    close = container.get_matrix('close')
                    container.add_matrix('output_A', close * 1.1)
                elif factor_id == 'B':
                    output_A = container.get_matrix('output_A')
                    container.add_matrix('output_B', output_A * 1.1)
                elif factor_id == 'C':
                    output_B = container.get_matrix('output_B')
                    container.add_matrix('position', output_B > 100)

            return logic

        # Create factors with dependencies: A → B → C
        factor_A = Factor(
            id='A', name='Factor A', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['output_A'],
            logic=tracking_logic('A'), parameters={}
        )

        factor_B = Factor(
            id='B', name='Factor B', category=FactorCategory.MOMENTUM,
            inputs=['output_A'], outputs=['output_B'],
            logic=tracking_logic('B'), parameters={}
        )

        factor_C = Factor(
            id='C', name='Factor C', category=FactorCategory.ENTRY,
            inputs=['output_B'], outputs=['position'],
            logic=tracking_logic('C'), parameters={}
        )

        strategy = Strategy(id='dag_test')
        # Add in random order with explicit dependencies
        strategy.add_factor(factor_C, depends_on=['B'])
        strategy.add_factor(factor_A)  # Root factor
        strategy.add_factor(factor_B, depends_on=['A'])

        strategy.to_pipeline(mock_data_module)

        # Verify execution order: A → B → C
        assert execution_order == ['A', 'B', 'C']

    def test_parallel_factors_can_execute_any_order(self, mock_data_module):
        """Test that independent factors can execute in any order."""
        execution_order = []

        def parallel_logic(factor_id, output_name):
            def logic(container, parameters):
                execution_order.append(factor_id)
                close = container.get_matrix('close')
                container.add_matrix(output_name, close * (1.0 + factor_id * 0.1))
            return logic

        # Create parallel factors (no dependencies between them)
        parallel_factors = [
            Factor(
                id=f'{i}', name=f'Factor {i}', category=FactorCategory.MOMENTUM,
                inputs=['close'], outputs=[f'output_{i}'],
                logic=parallel_logic(i, f'output_{i}'), parameters={}
            )
            for i in range(1, 4)
        ]

        # Position factor depends on all parallel factors
        def position_logic(container, parameters):
            execution_order.append('position')
            avg = (container.get_matrix('output_1') +
                   container.get_matrix('output_2') +
                   container.get_matrix('output_3')) / 3
            container.add_matrix('position', avg > 100)

        position_factor = Factor(
            id='position', name='Position', category=FactorCategory.ENTRY,
            inputs=['output_1', 'output_2', 'output_3'], outputs=['position'],
            logic=position_logic, parameters={}
        )

        strategy = Strategy(id='parallel')
        for factor in parallel_factors:
            strategy.add_factor(factor)  # Root factors (no dependencies)
        # Position factor depends on all parallel factors
        strategy.add_factor(position_factor, depends_on=['1', '2', '3'])

        strategy.to_pipeline(mock_data_module)

        # Position should be last
        assert execution_order[-1] == 'position'
        # Parallel factors should all execute before position
        assert set(execution_order[:3]) == {1, 2, 3}


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases in pipeline execution."""

    def test_factor_with_no_inputs(self, mock_data_module):
        """Test factor that produces constant signal (minimal inputs)."""
        def constant_logic(container, parameters):
            # Create constant position (all ones)
            close = container.get_matrix('close')
            ones = pd.DataFrame(1.0, index=close.index, columns=close.columns)
            container.add_matrix('position', ones)

        constant_factor = Factor(
            id='constant', name='Constant', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],  # Needs close for shape
            logic=constant_logic, parameters={}
        )

        strategy = Strategy(id='constant')
        strategy.add_factor(constant_factor)

        positions = strategy.to_pipeline(mock_data_module)

        assert (positions == 1.0).all().all()

    def test_factor_with_multiple_outputs(self, mock_data_module):
        """Test factor that produces multiple output matrices."""
        def multi_output_logic(container, parameters):
            close = container.get_matrix('close')
            container.add_matrix('momentum', (close / close.shift(10)) - 1)
            container.add_matrix('ma', close.rolling(20).mean())
            container.add_matrix('position', (close > close.rolling(20).mean()).astype(float))

        multi_factor = Factor(
            id='multi', name='Multi', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['momentum', 'ma', 'position'],
            logic=multi_output_logic, parameters={}
        )

        strategy = Strategy(id='multi_output')
        strategy.add_factor(multi_factor)

        positions = strategy.to_pipeline(mock_data_module)

        assert positions.shape == (100, 3)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
