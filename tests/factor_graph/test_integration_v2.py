"""
Integration Tests for Factor Graph V2 (Phase 2.0 Matrix-Native)
================================================================

Tests for multi-factor pipeline execution and complete strategy flows.
Validates data flow through entire pipelines with multiple factors.

Test Coverage:
--------------
1. Multi-Factor Pipelines
   - Momentum + Filter + Position pipeline
   - Turtle strategy complete pipeline
   - Exit factors composite pipeline

2. Cross-Category Integration
   - Combining momentum, entry, and exit factors
   - DAG dependency resolution
   - Matrix flow validation

3. Data Flow Validation
   - Input to output matrix propagation
   - Intermediate matrix creation
   - Final position matrix generation

4. Error Propagation
   - Errors in middle of pipeline
   - Missing dependencies
   - Invalid matrix shapes

Architecture: Phase 2.0 Matrix-Native Factor Graph System
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock

from src.factor_graph.strategy import Strategy
from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.finlab_dataframe import FinLabDataFrame


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_data_module():
    """Create mock data module with realistic market data."""
    mock_data = Mock()

    dates = pd.date_range('2023-01-01', periods=100)
    symbols = ['2330', '2317', '2454']

    # Close prices with realistic patterns
    close = pd.DataFrame(
        np.random.randn(100, 3).cumsum(axis=0) * 2 + 100,
        index=dates,
        columns=symbols
    )

    # High prices (slightly above close)
    high = close * (1 + np.abs(np.random.randn(100, 3) * 0.02))

    # Low prices (slightly below close)
    low = close * (1 - np.abs(np.random.randn(100, 3) * 0.02))

    def mock_get(key):
        data_map = {
            'price:收盤價': close,
            'price:最高價': high,
            'price:最低價': low,
        }
        if key in data_map:
            return data_map[key]
        raise KeyError(f"Mock data not found: {key}")

    mock_data.get = mock_get
    return mock_data


# ============================================================================
# Multi-Factor Pipeline Tests
# ============================================================================

class TestMomentumPipeline:
    """Test complete momentum strategy pipeline."""

    def test_momentum_filter_position_pipeline(self, mock_data_module):
        """Test: Momentum → MA Filter → Position Signal pipeline."""

        # Define momentum calculation
        def momentum_logic(container, params):
            close = container.get_matrix('close')
            period = params['period']
            momentum = (close / close.shift(period)) - 1
            container.add_matrix('momentum', momentum)

        # Define MA filter
        def ma_filter_logic(container, params):
            close = container.get_matrix('close')
            period = params['period']
            ma = close.rolling(period).mean()
            ma_filter = close > ma
            container.add_matrix('ma_filter', ma_filter)

        # Define position signal (momentum * ma_filter)
        def position_logic(container, params):
            momentum = container.get_matrix('momentum')
            ma_filter = container.get_matrix('ma_filter')
            # Convert boolean to float and multiply
            position = (momentum > 0) & ma_filter
            container.add_matrix('position', position.astype(float))

        # Create factors
        momentum_factor = Factor(
            id='momentum', name='Momentum', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['momentum'],
            logic=momentum_logic, parameters={'period': 20}
        )

        ma_filter_factor = Factor(
            id='ma_filter', name='MA Filter', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['ma_filter'],
            logic=ma_filter_logic, parameters={'period': 60}
        )

        position_factor = Factor(
            id='position', name='Position', category=FactorCategory.ENTRY,
            inputs=['momentum', 'ma_filter'], outputs=['position'],
            logic=position_logic, parameters={}
        )

        # Create strategy and execute pipeline
        strategy = Strategy(name='Momentum Strategy')
        strategy.add_factor(momentum_factor)
        strategy.add_factor(ma_filter_factor)
        strategy.add_factor(position_factor)

        # Execute full pipeline
        positions = strategy.to_pipeline(mock_data_module)

        # Validate output
        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (100, 3)
        assert positions.isin([0.0, 1.0]).all().all()

    def test_pipeline_intermediate_matrices(self, mock_data_module):
        """Test that all intermediate matrices are created in pipeline."""

        def step1(container, params):
            close = container.get_matrix('close')
            container.add_matrix('step1_output', close * 1.1)

        def step2(container, params):
            step1_out = container.get_matrix('step1_output')
            container.add_matrix('step2_output', step1_out * 1.2)

        def step3(container, params):
            step2_out = container.get_matrix('step2_output')
            container.add_matrix('position', step2_out * 0)

        factors = [
            Factor(id='s1', name='S1', category=FactorCategory.MOMENTUM,
                   inputs=['close'], outputs=['step1_output'], logic=step1, parameters={}),
            Factor(id='s2', name='S2', category=FactorCategory.MOMENTUM,
                   inputs=['step1_output'], outputs=['step2_output'], logic=step2, parameters={}),
            Factor(id='s3', name='S3', category=FactorCategory.ENTRY,
                   inputs=['step2_output'], outputs=['position'], logic=step3, parameters={})
        ]

        strategy = Strategy(name='Test')
        for f in factors:
            strategy.add_factor(f)

        # Create container and execute manually to inspect
        container = FinLabDataFrame(data_module=mock_data_module)
        for f in factors:
            container = f.execute(container)

        # Verify all intermediate outputs exist
        assert container.has_matrix('close')
        assert container.has_matrix('step1_output')
        assert container.has_matrix('step2_output')
        assert container.has_matrix('position')


class TestTurtlePipeline:
    """Test complete turtle trading strategy pipeline."""

    def test_turtle_complete_pipeline(self, mock_data_module):
        """Test: ATR → Breakout → Filter → Stop → Position pipeline."""

        # ATR calculation
        def atr_logic(container, params):
            high = container.get_matrix('high')
            low = container.get_matrix('low')
            close = container.get_matrix('close')

            tr1 = high - low
            tr2 = (high - close.shift(1)).abs()
            tr3 = (low - close.shift(1)).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            atr = tr.rolling(params['period']).mean()
            container.add_matrix('atr', atr)

        # Breakout signal
        def breakout_logic(container, params):
            close = container.get_matrix('close')
            period = params['period']

            high_breakout = close > close.shift(1).rolling(period).max()
            container.add_matrix('breakout', high_breakout.astype(float))

        # Position with stop loss
        def position_logic(container, params):
            breakout = container.get_matrix('breakout')
            atr = container.get_matrix('atr')
            close = container.get_matrix('close')

            # Simple position: breakout signal only
            position = breakout
            container.add_matrix('position', position)

        # Create factors
        atr_factor = Factor(
            id='atr', name='ATR', category=FactorCategory.MOMENTUM,
            inputs=['high', 'low', 'close'], outputs=['atr'],
            logic=atr_logic, parameters={'period': 14}
        )

        breakout_factor = Factor(
            id='breakout', name='Breakout', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['breakout'],
            logic=breakout_logic, parameters={'period': 20}
        )

        position_factor = Factor(
            id='position', name='Position', category=FactorCategory.ENTRY,
            inputs=['breakout', 'atr', 'close'], outputs=['position'],
            logic=position_logic, parameters={}
        )

        # Build strategy
        strategy = Strategy(name='Turtle Strategy')
        strategy.add_factor(atr_factor)
        strategy.add_factor(breakout_factor)
        strategy.add_factor(position_factor)

        # Execute pipeline
        positions = strategy.to_pipeline(mock_data_module)

        # Validate
        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (100, 3)
        assert positions.isin([0.0, 1.0]).all().all()


class TestExitPipeline:
    """Test exit factors pipeline with composite signals."""

    def test_composite_exit_pipeline(self, mock_data_module):
        """Test: Trailing Stop + Profit Target → Composite Exit pipeline."""

        # Trailing stop
        def trailing_stop_logic(container, params):
            close = container.get_matrix('close')
            threshold = params['threshold']

            highest = close.rolling(20, min_periods=1).max()
            drawdown = (close - highest) / highest
            stop_signal = drawdown < -threshold

            container.add_matrix('trailing_stop', stop_signal.astype(float))

        # Profit target
        def profit_target_logic(container, params):
            close = container.get_matrix('close')
            target = params['target']

            entry_price = close.shift(10)  # Assume entry 10 days ago
            profit = (close - entry_price) / entry_price
            target_signal = profit > target

            container.add_matrix('profit_target', target_signal.astype(float))

        # Composite exit (OR of signals)
        def composite_exit_logic(container, params):
            trailing = container.get_matrix('trailing_stop')
            profit = container.get_matrix('profit_target')

            composite = (trailing > 0) | (profit > 0)
            container.add_matrix('position', composite.astype(float))

        # Create factors
        trailing_factor = Factor(
            id='trailing', name='Trailing Stop', category=FactorCategory.EXIT,
            inputs=['close'], outputs=['trailing_stop'],
            logic=trailing_stop_logic, parameters={'threshold': 0.1}
        )

        profit_factor = Factor(
            id='profit', name='Profit Target', category=FactorCategory.EXIT,
            inputs=['close'], outputs=['profit_target'],
            logic=profit_target_logic, parameters={'target': 0.2}
        )

        composite_factor = Factor(
            id='composite', name='Composite Exit', category=FactorCategory.EXIT,
            inputs=['trailing_stop', 'profit_target'], outputs=['position'],
            logic=composite_exit_logic, parameters={}
        )

        # Build strategy
        strategy = Strategy(name='Exit Strategy')
        strategy.add_factor(trailing_factor)
        strategy.add_factor(profit_factor)
        strategy.add_factor(composite_factor)

        # Execute
        positions = strategy.to_pipeline(mock_data_module)

        # Validate
        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (100, 3)


# ============================================================================
# Cross-Category Integration Tests
# ============================================================================

class TestCrossCategoryIntegration:
    """Test integration across different factor categories."""

    def test_momentum_entry_exit_pipeline(self, mock_data_module):
        """Test pipeline combining MOMENTUM → ENTRY → EXIT factors."""

        # Momentum
        def momentum_logic(container, params):
            close = container.get_matrix('close')
            momentum = (close / close.shift(20)) - 1
            container.add_matrix('momentum', momentum)

        # Entry (based on momentum)
        def entry_logic(container, params):
            momentum = container.get_matrix('momentum')
            entry = momentum > 0.05  # 5% momentum threshold
            container.add_matrix('entry', entry.astype(float))

        # Exit (time-based)
        def exit_logic(container, params):
            entry = container.get_matrix('entry')
            # Simple: exit after entry (simplified)
            exit_signal = entry.shift(5) > 0
            container.add_matrix('exit', exit_signal.astype(float))

        # Position (entry AND NOT exit)
        def position_logic(container, params):
            entry = container.get_matrix('entry')
            exit_sig = container.get_matrix('exit')
            position = (entry > 0) & (exit_sig == 0)
            container.add_matrix('position', position.astype(float))

        factors = [
            Factor(id='mom', name='Momentum', category=FactorCategory.MOMENTUM,
                   inputs=['close'], outputs=['momentum'], logic=momentum_logic, parameters={}),
            Factor(id='entry', name='Entry', category=FactorCategory.ENTRY,
                   inputs=['momentum'], outputs=['entry'], logic=entry_logic, parameters={}),
            Factor(id='exit', name='Exit', category=FactorCategory.EXIT,
                   inputs=['entry'], outputs=['exit'], logic=exit_logic, parameters={}),
            Factor(id='pos', name='Position', category=FactorCategory.ENTRY,
                   inputs=['entry', 'exit'], outputs=['position'], logic=position_logic, parameters={})
        ]

        strategy = Strategy(name='Complete Strategy')
        for f in factors:
            strategy.add_factor(f)

        positions = strategy.to_pipeline(mock_data_module)

        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (100, 3)
        assert positions.isin([0.0, 1.0]).all().all()

    def test_dag_resolves_complex_dependencies(self, mock_data_module):
        """Test DAG resolution with complex dependencies."""

        # Create factors with complex dependency graph:
        # A ──┐
        #     ├──> C ──> E
        # B ──┘         ↗
        # D ───────────┘

        def logic_a(c, p): c.add_matrix('A', c.get_matrix('close') * 1)
        def logic_b(c, p): c.add_matrix('B', c.get_matrix('close') * 2)
        def logic_c(c, p):
            a = c.get_matrix('A')
            b = c.get_matrix('B')
            c.add_matrix('C', a + b)
        def logic_d(c, p): c.add_matrix('D', c.get_matrix('close') * 3)
        def logic_e(c, p):
            cc = c.get_matrix('C')
            d = c.get_matrix('D')
            c.add_matrix('position', (cc + d) * 0)

        factors = [
            Factor(id='E', name='E', category=FactorCategory.ENTRY,
                   inputs=['C', 'D'], outputs=['position'], logic=logic_e, parameters={}),
            Factor(id='C', name='C', category=FactorCategory.MOMENTUM,
                   inputs=['A', 'B'], outputs=['C'], logic=logic_c, parameters={}),
            Factor(id='A', name='A', category=FactorCategory.MOMENTUM,
                   inputs=['close'], outputs=['A'], logic=logic_a, parameters={}),
            Factor(id='D', name='D', category=FactorCategory.MOMENTUM,
                   inputs=['close'], outputs=['D'], logic=logic_d, parameters={}),
            Factor(id='B', name='B', category=FactorCategory.MOMENTUM,
                   inputs=['close'], outputs=['B'], logic=logic_b, parameters={}),
        ]

        strategy = Strategy(name='Complex DAG')
        # Add in random order
        for f in factors:
            strategy.add_factor(f)

        # Should execute in correct order: A,B,D → C → E
        positions = strategy.to_pipeline(mock_data_module)

        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (100, 3)


# ============================================================================
# Error Propagation Tests
# ============================================================================

class TestErrorPropagation:
    """Test error handling in multi-factor pipelines."""

    def test_error_in_middle_factor(self, mock_data_module):
        """Test that error in middle factor stops pipeline."""

        def good_logic(container, params):
            close = container.get_matrix('close')
            container.add_matrix('step1', close)

        def bad_logic(container, params):
            raise ValueError("Intentional error in middle factor")

        def final_logic(container, params):
            container.add_matrix('position', container.get_matrix('step2'))

        factors = [
            Factor(id='f1', name='F1', category=FactorCategory.MOMENTUM,
                   inputs=['close'], outputs=['step1'], logic=good_logic, parameters={}),
            Factor(id='f2', name='F2', category=FactorCategory.MOMENTUM,
                   inputs=['step1'], outputs=['step2'], logic=bad_logic, parameters={}),
            Factor(id='f3', name='F3', category=FactorCategory.ENTRY,
                   inputs=['step2'], outputs=['position'], logic=final_logic, parameters={})
        ]

        strategy = Strategy(name='Error Test')
        for f in factors:
            strategy.add_factor(f)

        with pytest.raises(ValueError, match="Intentional error"):
            strategy.to_pipeline(mock_data_module)

    def test_missing_dependency_error(self, mock_data_module):
        """Test that missing dependency is caught."""

        def logic(container, params):
            # Try to access non-existent matrix
            container.get_matrix('nonexistent')
            container.add_matrix('position', container.get_matrix('close') * 0)

        factor = Factor(
            id='bad', name='Bad', category=FactorCategory.ENTRY,
            inputs=['nonexistent'], outputs=['position'],
            logic=logic, parameters={}
        )

        strategy = Strategy(name='Missing Dep')
        strategy.add_factor(factor)

        with pytest.raises(KeyError, match="Missing matrices"):
            strategy.to_pipeline(mock_data_module)


# ============================================================================
# Performance and Scale Tests
# ============================================================================

class TestPerformanceScale:
    """Test pipeline performance with larger data."""

    def test_large_pipeline_execution(self, mock_data_module):
        """Test pipeline with 10 factors executes correctly."""

        factors = []
        for i in range(9):
            def make_logic(i):
                def logic(container, params):
                    if i == 0:
                        inp = container.get_matrix('close')
                    else:
                        inp = container.get_matrix(f'step{i}')
                    container.add_matrix(f'step{i+1}', inp * 1.01)
                return logic

            factors.append(Factor(
                id=f'f{i}',
                name=f'Factor {i}',
                category=FactorCategory.MOMENTUM,
                inputs=['close'] if i == 0 else [f'step{i}'],
                outputs=[f'step{i+1}'],
                logic=make_logic(i),
                parameters={}
            ))

        # Final factor creates position
        def final_logic(container, params):
            container.add_matrix('position', container.get_matrix('step9') * 0)

        factors.append(Factor(
            id='final',
            name='Final',
            category=FactorCategory.ENTRY,
            inputs=['step9'],
            outputs=['position'],
            logic=final_logic,
            parameters={}
        ))

        strategy = Strategy(name='Large Pipeline')
        for f in factors:
            strategy.add_factor(f)

        positions = strategy.to_pipeline(mock_data_module)

        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (100, 3)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
