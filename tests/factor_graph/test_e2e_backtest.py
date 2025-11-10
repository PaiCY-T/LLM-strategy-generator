"""
End-to-End Tests for Factor Graph V2 (Phase 2.0 Matrix-Native)
================================================================

Tests for complete backtest workflows from data loading to position generation.
Validates the entire system with realistic data scenarios.

Test Coverage:
--------------
1. Complete Backtest Pipeline
   - Data module → Strategy → Position matrix
   - Multi-stock scenarios
   - Long time series

2. Real-World Strategy Scenarios
   - Momentum strategy complete workflow
   - Turtle trading strategy complete workflow
   - Combined strategy with multiple factor types

3. Performance Validation
   - Large dataset handling (1000+ dates, 100+ symbols)
   - Memory efficiency
   - Execution time benchmarks

4. Data Integration
   - Mock FinLab data integration
   - Multiple data sources (price, volume, fundamentals)
   - Missing data handling

Architecture: Phase 2.0 Matrix-Native Factor Graph System
"""

import pytest
import pandas as pd
import numpy as np
import time
from unittest.mock import Mock
from datetime import datetime, timedelta

from src.factor_graph.strategy import Strategy
from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.finlab_dataframe import FinLabDataFrame


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def realistic_data_module():
    """Create mock data module with realistic market data for 100 stocks over 1 year."""
    mock_data = Mock()

    # 252 trading days (1 year), 100 stocks
    dates = pd.date_range('2023-01-01', periods=252, freq='B')
    symbols = [f'{2000+i:04d}' for i in range(100)]

    # Generate realistic price data with trends and volatility
    np.random.seed(42)
    base_prices = 100
    returns = np.random.randn(252, 100) * 0.02  # 2% daily volatility
    cumulative_returns = np.exp(returns.cumsum(axis=0))
    close = pd.DataFrame(
        base_prices * cumulative_returns,
        index=dates,
        columns=symbols
    )

    # High prices (slightly above close)
    high = close * (1 + np.abs(np.random.randn(252, 100) * 0.01))

    # Low prices (slightly below close)
    low = close * (1 - np.abs(np.random.randn(252, 100) * 0.01))

    # Volume data
    volume = pd.DataFrame(
        np.random.randint(100000, 10000000, size=(252, 100)),
        index=dates,
        columns=symbols
    )

    def mock_get(key):
        data_map = {
            'price:收盤價': close,
            'price:最高價': high,
            'price:最低價': low,
            'price:成交量': volume,
        }
        if key in data_map:
            return data_map[key]
        raise KeyError(f"Mock data not found: {key}")

    mock_data.get = mock_get
    return mock_data


@pytest.fixture
def large_data_module():
    """Create large dataset for performance testing: 1000 days × 150 stocks."""
    mock_data = Mock()

    dates = pd.date_range('2020-01-01', periods=1000, freq='B')
    symbols = [f'{1000+i:04d}' for i in range(150)]

    np.random.seed(123)
    base_prices = 50
    returns = np.random.randn(1000, 150) * 0.015
    cumulative_returns = np.exp(returns.cumsum(axis=0))
    close = pd.DataFrame(
        base_prices * cumulative_returns,
        index=dates,
        columns=symbols
    )

    high = close * (1 + np.abs(np.random.randn(1000, 150) * 0.008))
    low = close * (1 - np.abs(np.random.randn(1000, 150) * 0.008))

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
# Complete Backtest Pipeline Tests
# ============================================================================

class TestCompleteBacktestPipeline:
    """Test complete backtest workflow from data to positions."""

    def test_momentum_strategy_complete_workflow(self, realistic_data_module):
        """Test complete momentum strategy workflow: Data → Strategy → Positions."""

        # Define complete momentum strategy
        def momentum_logic(container, params):
            close = container.get_matrix('close')
            period = params['period']
            momentum = (close / close.shift(period)) - 1
            container.add_matrix('momentum', momentum)

        def ma_filter_logic(container, params):
            close = container.get_matrix('close')
            period = params['period']
            ma = close.rolling(period).mean()
            ma_filter = close > ma
            container.add_matrix('ma_filter', ma_filter)

        def position_logic(container, params):
            momentum = container.get_matrix('momentum')
            ma_filter = container.get_matrix('ma_filter')
            threshold = params['threshold']

            # Position = positive momentum above threshold AND above MA
            position = (momentum > threshold) & ma_filter
            container.add_matrix('position', position.astype(float))

        # Build strategy
        strategy = Strategy(name='Momentum Strategy')
        strategy.add_factor(Factor(
            id='momentum', name='Momentum', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['momentum'],
            logic=momentum_logic, parameters={'period': 20}
        ))
        strategy.add_factor(Factor(
            id='ma_filter', name='MA Filter', category=FactorCategory.MOMENTUM,
            inputs=['close'], outputs=['ma_filter'],
            logic=ma_filter_logic, parameters={'period': 60}
        ))
        strategy.add_factor(Factor(
            id='position', name='Position', category=FactorCategory.ENTRY,
            inputs=['momentum', 'ma_filter'], outputs=['position'],
            logic=position_logic, parameters={'threshold': 0.05}
        ))

        # Execute complete pipeline
        positions = strategy.to_pipeline(realistic_data_module)

        # Validate output
        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (252, 100)  # 1 year × 100 stocks
        assert positions.isin([0.0, 1.0]).all().all()  # Binary positions
        assert positions.sum().sum() > 0  # Some positions generated
        assert positions.sum().sum() < positions.size * 0.5  # Not all positions

    def test_turtle_strategy_complete_workflow(self, realistic_data_module):
        """Test complete turtle trading strategy workflow."""

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

        # Breakout detection
        def breakout_logic(container, params):
            close = container.get_matrix('close')
            period = params['period']

            highest = close.shift(1).rolling(period).max()
            lowest = close.shift(1).rolling(period).min()

            long_breakout = close > highest
            short_breakout = close < lowest

            # 1 for long, -1 for short, 0 for neutral
            signal = long_breakout.astype(int) - short_breakout.astype(int)
            container.add_matrix('breakout', signal.astype(float))

        # Position with volume filter
        def position_logic(container, params):
            breakout = container.get_matrix('breakout')
            volume = container.get_matrix('volume')

            # Volume filter: above 20-day average
            volume_ma = volume.rolling(20).mean()
            volume_filter = volume > volume_ma

            # Position = breakout signal AND volume confirmation
            # For simplicity, only take long positions
            position = (breakout > 0) & volume_filter
            container.add_matrix('position', position.astype(float))

        # Build strategy
        strategy = Strategy(name='Turtle Strategy')
        strategy.add_factor(Factor(
            id='atr', name='ATR', category=FactorCategory.MOMENTUM,
            inputs=['high', 'low', 'close'], outputs=['atr'],
            logic=atr_logic, parameters={'period': 14}
        ))
        strategy.add_factor(Factor(
            id='breakout', name='Breakout', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['breakout'],
            logic=breakout_logic, parameters={'period': 20}
        ))
        strategy.add_factor(Factor(
            id='position', name='Position', category=FactorCategory.ENTRY,
            inputs=['breakout', 'volume'], outputs=['position'],
            logic=position_logic, parameters={}
        ))

        # Execute
        positions = strategy.to_pipeline(realistic_data_module)

        # Validate
        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (252, 100)
        assert positions.isin([0.0, 1.0]).all().all()
        assert positions.sum().sum() > 0  # Some trades generated

    def test_combined_strategy_workflow(self, realistic_data_module):
        """Test combined strategy with momentum + entry + exit factors."""

        # Momentum
        def momentum_logic(container, params):
            close = container.get_matrix('close')
            momentum = (close / close.shift(20)) - 1
            container.add_matrix('momentum', momentum)

        # Entry signal
        def entry_logic(container, params):
            momentum = container.get_matrix('momentum')
            volume = container.get_matrix('volume')

            # Entry: strong momentum + volume spike
            volume_ma = volume.rolling(20).mean()
            volume_spike = volume > volume_ma * 1.5

            entry = (momentum > 0.1) & volume_spike
            container.add_matrix('entry', entry.astype(float))

        # Trailing stop exit
        def exit_logic(container, params):
            close = container.get_matrix('close')
            threshold = params['threshold']

            highest = close.rolling(20, min_periods=1).max()
            drawdown = (close - highest) / highest
            exit_signal = drawdown < -threshold

            container.add_matrix('exit', exit_signal.astype(float))

        # Position (entry AND NOT exit)
        def position_logic(container, params):
            entry = container.get_matrix('entry')
            exit_sig = container.get_matrix('exit')

            # Simplified position logic
            position = (entry > 0) & (exit_sig == 0)
            container.add_matrix('position', position.astype(float))

        # Build strategy
        strategy = Strategy(name='Combined Strategy')
        factors = [
            Factor(id='mom', name='Momentum', category=FactorCategory.MOMENTUM,
                   inputs=['close'], outputs=['momentum'], logic=momentum_logic, parameters={}),
            Factor(id='entry', name='Entry', category=FactorCategory.ENTRY,
                   inputs=['momentum', 'volume'], outputs=['entry'], logic=entry_logic, parameters={}),
            Factor(id='exit', name='Exit', category=FactorCategory.EXIT,
                   inputs=['close'], outputs=['exit'], logic=exit_logic, parameters={'threshold': 0.15}),
            Factor(id='pos', name='Position', category=FactorCategory.ENTRY,
                   inputs=['entry', 'exit'], outputs=['position'], logic=position_logic, parameters={})
        ]

        for f in factors:
            strategy.add_factor(f)

        # Execute
        positions = strategy.to_pipeline(realistic_data_module)

        # Validate
        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (252, 100)
        assert positions.isin([0.0, 1.0]).all().all()


# ============================================================================
# Performance and Scale Tests
# ============================================================================

class TestPerformanceScale:
    """Test system performance with large datasets."""

    def test_large_dataset_execution(self, large_data_module):
        """Test execution with 1000 days × 150 stocks (~150k data points)."""

        def simple_momentum_logic(container, params):
            close = container.get_matrix('close')
            momentum = (close / close.shift(20)) - 1
            position = momentum > 0.05
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='Simple Momentum')
        strategy.add_factor(Factor(
            id='momentum', name='Momentum', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=simple_momentum_logic, parameters={}
        ))

        # Measure execution time
        start_time = time.time()
        positions = strategy.to_pipeline(large_data_module)
        execution_time = time.time() - start_time

        # Validate output
        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (1000, 150)
        assert positions.isin([0.0, 1.0]).all().all()

        # Performance check: should complete in reasonable time
        assert execution_time < 10.0, f"Execution too slow: {execution_time:.2f}s"

    def test_complex_strategy_performance(self, large_data_module):
        """Test complex multi-factor strategy performance on large dataset."""

        # Create 5-factor strategy
        def factor1(c, p): c.add_matrix('f1', c.get_matrix('close') * 1.1)
        def factor2(c, p): c.add_matrix('f2', c.get_matrix('f1') / c.get_matrix('f1').shift(10))
        def factor3(c, p): c.add_matrix('f3', c.get_matrix('f2').rolling(20).mean())
        def factor4(c, p): c.add_matrix('f4', c.get_matrix('f3') > 1.0)
        def factor5(c, p): c.add_matrix('position', c.get_matrix('f4').astype(float))

        strategy = Strategy(name='Complex Strategy')
        factors = [
            Factor(id='f1', name='F1', category=FactorCategory.MOMENTUM,
                   inputs=['close'], outputs=['f1'], logic=factor1, parameters={}),
            Factor(id='f2', name='F2', category=FactorCategory.MOMENTUM,
                   inputs=['f1'], outputs=['f2'], logic=factor2, parameters={}),
            Factor(id='f3', name='F3', category=FactorCategory.MOMENTUM,
                   inputs=['f2'], outputs=['f3'], logic=factor3, parameters={}),
            Factor(id='f4', name='F4', category=FactorCategory.MOMENTUM,
                   inputs=['f3'], outputs=['f4'], logic=factor4, parameters={}),
            Factor(id='f5', name='F5', category=FactorCategory.ENTRY,
                   inputs=['f4'], outputs=['position'], logic=factor5, parameters={})
        ]

        for f in factors:
            strategy.add_factor(f)

        # Execute
        start_time = time.time()
        positions = strategy.to_pipeline(large_data_module)
        execution_time = time.time() - start_time

        # Validate
        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (1000, 150)
        assert execution_time < 15.0, f"Complex strategy too slow: {execution_time:.2f}s"

    def test_memory_efficiency(self, large_data_module):
        """Test that container doesn't accumulate excessive matrices."""

        def logic_with_temp(container, params):
            close = container.get_matrix('close')
            # Create intermediate calculations
            temp1 = close.rolling(10).mean()
            temp2 = close.rolling(20).mean()
            temp3 = close.rolling(30).mean()

            # Only add final result
            signal = (temp1 > temp2) & (temp2 > temp3)
            container.add_matrix('position', signal.astype(float))

        strategy = Strategy(name='Memory Test')
        strategy.add_factor(Factor(
            id='test', name='Test', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=logic_with_temp, parameters={}
        ))

        # Create container manually to inspect
        container = FinLabDataFrame(data_module=large_data_module)
        for factor in [strategy.factors['test']]:
            container = factor.execute(container)

        # Should only have close + position, not temp variables
        matrices = container.list_matrices()
        assert 'close' in matrices
        assert 'position' in matrices
        assert 'temp1' not in matrices
        assert 'temp2' not in matrices
        assert 'temp3' not in matrices


# ============================================================================
# Data Integration Tests
# ============================================================================

class TestDataIntegration:
    """Test integration with data sources and missing data handling."""

    def test_multiple_data_sources(self, realistic_data_module):
        """Test strategy using multiple data sources (price + volume)."""

        def multi_source_logic(container, params):
            close = container.get_matrix('close')
            volume = container.get_matrix('volume')

            # Price momentum
            price_signal = (close / close.shift(20)) > 1.05

            # Volume confirmation
            volume_ma = volume.rolling(20).mean()
            volume_signal = volume > volume_ma * 1.2

            # Combined signal
            position = price_signal & volume_signal
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='Multi Source')
        strategy.add_factor(Factor(
            id='multi', name='Multi Source', category=FactorCategory.ENTRY,
            inputs=['close', 'volume'], outputs=['position'],
            logic=multi_source_logic, parameters={}
        ))

        positions = strategy.to_pipeline(realistic_data_module)

        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (252, 100)

    def test_missing_data_handling(self):
        """Test handling of missing data in matrices."""
        mock_data = Mock()

        # Create data with NaN values
        dates = pd.date_range('2023-01-01', periods=100)
        symbols = ['A', 'B', 'C']

        close = pd.DataFrame(
            np.random.randn(100, 3) * 10 + 100,
            index=dates,
            columns=symbols
        )
        # Introduce missing data
        close.iloc[10:15, 0] = np.nan  # Symbol A has missing data
        close.iloc[20:25, 1] = np.nan  # Symbol B has missing data

        def mock_get(key):
            if key == 'price:收盤價':
                return close
            raise KeyError(f"Mock data not found: {key}")

        mock_data.get = mock_get

        # Strategy should handle NaN gracefully
        def nan_handling_logic(container, params):
            close = container.get_matrix('close')
            # fillna or other handling
            momentum = (close / close.shift(10)).fillna(0) - 1
            position = momentum > 0.05
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='NaN Handling')
        strategy.add_factor(Factor(
            id='nan', name='NaN Handler', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=nan_handling_logic, parameters={}
        ))

        positions = strategy.to_pipeline(mock_data)

        assert isinstance(positions, pd.DataFrame)
        assert positions.shape == (100, 3)
        # No NaN in output positions
        assert not positions.isna().any().any()


# ============================================================================
# Validation Tests
# ============================================================================

class TestOutputValidation:
    """Test validation of position matrix output."""

    def test_position_matrix_properties(self, realistic_data_module):
        """Test that position matrix has correct properties."""

        def valid_position_logic(container, params):
            close = container.get_matrix('close')
            momentum = (close / close.shift(20)) - 1
            position = momentum > 0.05
            container.add_matrix('position', position.astype(float))

        strategy = Strategy(name='Valid Position')
        strategy.add_factor(Factor(
            id='pos', name='Position', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=valid_position_logic, parameters={}
        ))

        positions = strategy.to_pipeline(realistic_data_module)

        # Validate properties
        assert isinstance(positions, pd.DataFrame)
        assert isinstance(positions.index, pd.DatetimeIndex)
        assert positions.dtypes.apply(lambda x: x in [np.float64, np.int64]).all()
        assert positions.values.min() >= 0.0
        assert positions.values.max() <= 1.0

    def test_position_matrix_consistency(self, realistic_data_module):
        """Test that running same strategy twice gives same result."""

        def deterministic_logic(container, params):
            close = container.get_matrix('close')
            signal = close > close.rolling(20).mean()
            container.add_matrix('position', signal.astype(float))

        strategy = Strategy(name='Deterministic')
        strategy.add_factor(Factor(
            id='det', name='Deterministic', category=FactorCategory.ENTRY,
            inputs=['close'], outputs=['position'],
            logic=deterministic_logic, parameters={}
        ))

        # Run twice
        positions1 = strategy.to_pipeline(realistic_data_module)
        positions2 = strategy.to_pipeline(realistic_data_module)

        # Should be identical
        pd.testing.assert_frame_equal(positions1, positions2)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
