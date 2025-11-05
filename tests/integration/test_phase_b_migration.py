"""
Phase B Migration Integration Tests
====================================

Comprehensive integration tests for Phase B migration validation.

Test Coverage:
1. Registry Integration (5 tests)
2. Strategy Composition (6 tests)
3. Factor Interoperability (4 tests)
4. Backward Compatibility (3 tests)

Total: 18+ tests validating Phase B migration success

Run with: pytest tests/integration/test_phase_b_migration.py -v
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict

from src.factor_library.registry import FactorRegistry
from src.factor_graph.factor import Factor
from src.factor_graph.strategy import Strategy
from src.factor_graph.factor_category import FactorCategory


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def registry():
    """Fixture providing fresh FactorRegistry instance."""
    FactorRegistry.reset()  # Reset singleton for clean state
    return FactorRegistry.get_instance()


@pytest.fixture
def sample_data():
    """Fixture providing sample OHLCV data."""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    base_price = 100
    returns = np.random.randn(100) * 0.02 + 0.001
    close_prices = base_price * np.exp(np.cumsum(returns))

    data = pd.DataFrame({
        'open': close_prices * (1 + np.random.randn(100) * 0.005),
        'high': close_prices * (1 + np.abs(np.random.randn(100) * 0.01)),
        'low': close_prices * (1 - np.abs(np.random.randn(100) * 0.01)),
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)

    # Ensure OHLC constraints
    data['high'] = data[['high', 'open', 'close']].max(axis=1)
    data['low'] = data[['low', 'open', 'close']].min(axis=1)

    return data


# ============================================================================
# Registry Integration Tests (5 tests)
# ============================================================================

class TestRegistryIntegration:
    """Test Factor Registry integration and core functionality."""

    def test_all_factors_registered(self, registry):
        """Test that all 13 factors are registered."""
        all_factors = registry.list_factors()
        assert len(all_factors) == 13, f"Expected 13 factors, got {len(all_factors)}"

    def test_category_filtering(self, registry):
        """Test that category filtering returns correct factors."""
        # Momentum factors (momentum, ma_filter, dual_ma_filter)
        momentum_factors = registry.list_by_category(FactorCategory.MOMENTUM)
        assert len(momentum_factors) == 3, f"Expected 3 momentum factors, got {len(momentum_factors)}"

        # Exit factors (atr_stop_loss, trailing_stop, time_exit, volatility_stop, profit_target, composite_exit)
        exit_factors = registry.list_by_category(FactorCategory.EXIT)
        assert len(exit_factors) == 6, f"Expected 6 exit factors, got {len(exit_factors)}"

        # Entry factors (breakout)
        entry_factors = registry.list_by_category(FactorCategory.ENTRY)
        assert len(entry_factors) == 1, f"Expected 1 entry factor, got {len(entry_factors)}"

        # Risk factors (atr)
        risk_factors = registry.list_by_category(FactorCategory.RISK)
        assert len(risk_factors) == 1, f"Expected 1 risk factor, got {len(risk_factors)}"

    def test_parameter_validation(self, registry):
        """Test that parameter validation works correctly."""
        # Valid parameters
        is_valid, msg = registry.validate_parameters("momentum_factor", {"momentum_period": 20})
        assert is_valid, f"Valid parameters rejected: {msg}"

        # Invalid parameters (below min)
        is_valid, msg = registry.validate_parameters("momentum_factor", {"momentum_period": 1})
        assert not is_valid, "Invalid parameters (below min) accepted"

        # Invalid parameters (above max)
        is_valid, msg = registry.validate_parameters("momentum_factor", {"momentum_period": 150})
        assert not is_valid, "Invalid parameters (above max) accepted"

        # Unknown parameters
        is_valid, msg = registry.validate_parameters("momentum_factor", {"unknown_param": 10})
        assert not is_valid, "Unknown parameters accepted"

    def test_factor_creation_via_registry(self, registry):
        """Test factor creation via registry works correctly."""
        # Create factor with default parameters
        momentum = registry.create_factor("momentum_factor")
        assert momentum.id == "momentum_20"
        assert momentum.parameters["momentum_period"] == 20

        # Create factor with custom parameters
        custom_momentum = registry.create_factor("momentum_factor", {"momentum_period": 30})
        assert custom_momentum.id == "momentum_30"
        assert custom_momentum.parameters["momentum_period"] == 30

        # Verify factor is functional
        data = pd.DataFrame({"close": [100, 102, 101, 103, 105]})
        result = custom_momentum.execute(data)
        assert "momentum" in result.columns

    def test_metadata_accuracy(self, registry):
        """Test that factor metadata is accurate."""
        # Test momentum factor metadata
        metadata = registry.get_metadata("momentum_factor")
        assert metadata is not None
        assert metadata["category"] == FactorCategory.MOMENTUM
        assert "momentum_period" in metadata["parameters"]
        assert "momentum_period" in metadata["parameter_ranges"]
        assert metadata["parameter_ranges"]["momentum_period"] == (5, 100)

        # Test exit factor metadata
        exit_metadata = registry.get_metadata("trailing_stop_factor")
        assert exit_metadata is not None
        assert exit_metadata["category"] == FactorCategory.EXIT
        assert "trail_percent" in exit_metadata["parameters"]
        assert "activation_profit" in exit_metadata["parameters"]


# ============================================================================
# Strategy Composition Tests (6 tests)
# ============================================================================

class TestStrategyComposition:
    """Test full strategy composition via Factor Registry."""

    def test_momentum_strategy_composition(self, registry, sample_data):
        """Test momentum strategy composition and execution."""
        # Create strategy
        strategy = Strategy(id="momentum_test", generation=0)

        # Add factors
        momentum = registry.create_factor("momentum_factor", {"momentum_period": 20})
        ma_filter = registry.create_factor("ma_filter_factor", {"ma_periods": 60})

        strategy.add_factor(momentum)
        strategy.add_factor(ma_filter)

        # Add signal factor
        def signal_logic(data: pd.DataFrame, params: Dict) -> pd.DataFrame:
            data['positions'] = (data['momentum'] > 0) & data['ma_filter']
            data['entry_price'] = data['close'].where(data['positions'], np.nan).ffill()
            data['entry_date'] = data.index.to_series().where(data['positions'], pd.NaT).ffill()
            return data

        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["close", "momentum", "ma_filter"],
            outputs=["positions", "entry_price", "entry_date"],
            logic=signal_logic, parameters={}
        )
        strategy.add_factor(signal_factor, depends_on=["momentum_20", "ma_filter_60"])

        # Validate and execute
        assert strategy.validate() == True
        result = strategy.to_pipeline(sample_data)
        assert "positions" in result.columns
        assert "momentum" in result.columns
        assert "ma_filter" in result.columns

    def test_turtle_strategy_composition(self, registry, sample_data):
        """Test turtle strategy composition and execution."""
        # Create strategy
        strategy = Strategy(id="turtle_test", generation=0)

        # Add factors
        atr = registry.create_factor("atr_factor", {"atr_period": 20})
        breakout = registry.create_factor("breakout_factor", {"entry_window": 20})
        dual_ma = registry.create_factor("dual_ma_filter_factor", {"short_ma": 20, "long_ma": 60})

        strategy.add_factor(atr)
        strategy.add_factor(breakout)
        strategy.add_factor(dual_ma)

        # Add signal factor - connect all factors to avoid orphans
        def signal_logic(data: pd.DataFrame, params: Dict) -> pd.DataFrame:
            data['positions'] = (data['breakout_signal'] == 1) & data['dual_ma_filter']
            data['entry_price'] = data['close'].where(data['positions'], np.nan).ffill()
            data['entry_date'] = data.index.to_series().where(data['positions'], pd.NaT).ffill()
            return data

        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["close", "atr", "breakout_signal", "dual_ma_filter"],
            outputs=["positions", "entry_price", "entry_date"],
            logic=signal_logic, parameters={}
        )
        strategy.add_factor(signal_factor, depends_on=["atr_20", "breakout_20", "dual_ma_filter_20_60"])

        # Validate and execute
        assert strategy.validate() == True
        result = strategy.to_pipeline(sample_data)
        assert "positions" in result.columns
        assert "atr" in result.columns
        assert "breakout_signal" in result.columns

    def test_hybrid_strategy_composition(self, registry, sample_data):
        """Test hybrid strategy mixing momentum and turtle factors."""
        # Create strategy
        strategy = Strategy(id="hybrid_test", generation=0)

        # Mix momentum and turtle factors
        momentum = registry.create_factor("momentum_factor", {"momentum_period": 10})
        atr = registry.create_factor("atr_factor", {"atr_period": 14})
        breakout = registry.create_factor("breakout_factor", {"entry_window": 20})

        strategy.add_factor(momentum)
        strategy.add_factor(atr)
        strategy.add_factor(breakout)

        # Add signal factor combining both - connect all factors
        def signal_logic(data: pd.DataFrame, params: Dict) -> pd.DataFrame:
            data['positions'] = (data['momentum'] > 0) | (data['breakout_signal'] == 1)
            data['entry_price'] = data['close'].where(data['positions'], np.nan).ffill()
            data['entry_date'] = data.index.to_series().where(data['positions'], pd.NaT).ffill()
            return data

        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["close", "atr", "momentum", "breakout_signal"],
            outputs=["positions", "entry_price", "entry_date"],
            logic=signal_logic, parameters={}
        )
        strategy.add_factor(signal_factor, depends_on=["momentum_10", "atr_14", "breakout_20"])

        # Validate and execute
        assert strategy.validate() == True
        result = strategy.to_pipeline(sample_data)
        assert "positions" in result.columns
        assert "momentum" in result.columns
        assert "atr" in result.columns
        assert "breakout_signal" in result.columns

    def test_exit_factor_integration(self, registry, sample_data):
        """Test exit factors integrate correctly with entry factors."""
        # Create strategy with entry and multiple exits
        strategy = Strategy(id="exit_test", generation=0)

        # Add entry
        momentum = registry.create_factor("momentum_factor", {"momentum_period": 20})
        strategy.add_factor(momentum)

        # Add signal
        def signal_logic(data: pd.DataFrame, params: Dict) -> pd.DataFrame:
            data['positions'] = data['momentum'] > 0
            data['entry_price'] = data['close'].where(data['positions'], np.nan).ffill()
            data['entry_date'] = data.index.to_series().where(data['positions'], pd.NaT).ffill()
            return data

        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["close", "momentum"],
            outputs=["positions", "entry_price", "entry_date"],
            logic=signal_logic, parameters={}
        )
        strategy.add_factor(signal_factor, depends_on=["momentum_20"])

        # Add multiple exit factors
        profit_target = registry.create_factor("profit_target_factor", {"target_percent": 0.30})
        trailing_stop = registry.create_factor("trailing_stop_factor", {"trail_percent": 0.10, "activation_profit": 0.05})

        strategy.add_factor(profit_target, depends_on=["signal"])
        strategy.add_factor(trailing_stop, depends_on=["signal"])

        # Add composite exit
        composite = registry.create_factor("composite_exit_factor", {
            "exit_signals": ["profit_target_signal", "trailing_stop_signal"]
        })
        strategy.add_factor(composite, depends_on=["profit_target_30pct", "trailing_stop_10pct"])

        # Validate and execute
        assert strategy.validate() == True
        result = strategy.to_pipeline(sample_data)
        assert "final_exit_signal" in result.columns

    def test_dag_validation_passes(self, registry):
        """Test that DAG validation passes for composed strategies."""
        # Create valid strategy
        strategy = Strategy(id="dag_test", generation=0)

        momentum = registry.create_factor("momentum_factor")
        strategy.add_factor(momentum)

        def signal_logic(data: pd.DataFrame, params: Dict) -> pd.DataFrame:
            data['positions'] = data['momentum'] > 0
            return data

        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["momentum"],
            outputs=["positions"],
            logic=signal_logic, parameters={}
        )
        strategy.add_factor(signal_factor, depends_on=["momentum_20"])

        # Validate should pass
        assert strategy.validate() == True

    def test_pipeline_execution_succeeds(self, registry, sample_data):
        """Test that pipeline execution succeeds for composed strategies."""
        # Create and execute strategy
        strategy = Strategy(id="pipeline_test", generation=0)

        momentum = registry.create_factor("momentum_factor", {"momentum_period": 10})
        atr = registry.create_factor("atr_factor", {"atr_period": 14})

        strategy.add_factor(momentum)
        strategy.add_factor(atr)

        def signal_logic(data: pd.DataFrame, params: Dict) -> pd.DataFrame:
            data['positions'] = data['momentum'] > 0
            return data

        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["atr", "momentum"],
            outputs=["positions"],
            logic=signal_logic, parameters={}
        )
        strategy.add_factor(signal_factor, depends_on=["momentum_10", "atr_14"])

        # Execute pipeline
        result = strategy.to_pipeline(sample_data)

        # Verify results
        assert len(result) == len(sample_data)
        assert "momentum" in result.columns
        assert "atr" in result.columns
        assert "positions" in result.columns


# ============================================================================
# Factor Interoperability Tests (4 tests)
# ============================================================================

class TestFactorInteroperability:
    """Test that factors from different modules work together."""

    def test_factors_from_different_modules_work_together(self, registry, sample_data):
        """Test momentum factors work with turtle factors."""
        strategy = Strategy(id="interop_test", generation=0)

        # Mix momentum and turtle factors
        momentum = registry.create_factor("momentum_factor")  # From momentum_factors.py
        atr = registry.create_factor("atr_factor")  # From turtle_factors.py
        trailing_stop = registry.create_factor("trailing_stop_factor")  # From exit_factors.py

        strategy.add_factor(momentum)
        strategy.add_factor(atr)

        def signal_logic(data: pd.DataFrame, params: Dict) -> pd.DataFrame:
            data['positions'] = data['momentum'] > 0
            data['entry_price'] = data['close'].where(data['positions'], np.nan).ffill()
            data['entry_date'] = data.index.to_series().where(data['positions'], pd.NaT).ffill()
            return data

        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["close", "atr", "momentum"],
            outputs=["positions", "entry_price", "entry_date"],
            logic=signal_logic, parameters={}
        )
        strategy.add_factor(signal_factor, depends_on=["momentum_20", "atr_20"])
        strategy.add_factor(trailing_stop, depends_on=["signal"])

        # Should execute without errors
        result = strategy.to_pipeline(sample_data)
        assert "momentum" in result.columns
        assert "atr" in result.columns
        assert "trailing_stop_signal" in result.columns

    def test_exit_factors_integrate_with_entry_factors(self, registry, sample_data):
        """Test exit factors work with entry/momentum factors."""
        strategy = Strategy(id="exit_interop_test", generation=0)

        # Entry factor
        breakout = registry.create_factor("breakout_factor")
        strategy.add_factor(breakout)

        def signal_logic(data: pd.DataFrame, params: Dict) -> pd.DataFrame:
            data['positions'] = data['breakout_signal'] == 1
            data['entry_price'] = data['close'].where(data['positions'], np.nan).ffill()
            data['entry_date'] = data.index.to_series().where(data['positions'], pd.NaT).ffill()
            return data

        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["close", "breakout_signal"],
            outputs=["positions", "entry_price", "entry_date"],
            logic=signal_logic, parameters={}
        )
        strategy.add_factor(signal_factor, depends_on=["breakout_20"])

        # Exit factors
        profit_target = registry.create_factor("profit_target_factor")
        time_exit = registry.create_factor("time_based_exit_factor")

        strategy.add_factor(profit_target, depends_on=["signal"])
        strategy.add_factor(time_exit, depends_on=["signal"])

        # Should execute without errors
        result = strategy.to_pipeline(sample_data)
        assert "profit_target_signal" in result.columns
        assert "time_exit_signal" in result.columns

    def test_composite_exits_combine_multiple_signals(self, registry, sample_data):
        """Test composite exit factor combines multiple exit signals."""
        strategy = Strategy(id="composite_test", generation=0)

        # Simple entry
        momentum = registry.create_factor("momentum_factor")
        strategy.add_factor(momentum)

        def signal_logic(data: pd.DataFrame, params: Dict) -> pd.DataFrame:
            data['positions'] = data['momentum'] > 0
            data['entry_price'] = data['close'].where(data['positions'], np.nan).ffill()
            data['entry_date'] = data.index.to_series().where(data['positions'], pd.NaT).ffill()
            return data

        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["close", "momentum"],
            outputs=["positions", "entry_price", "entry_date"],
            logic=signal_logic, parameters={}
        )
        strategy.add_factor(signal_factor, depends_on=["momentum_20"])

        # Multiple exits
        profit = registry.create_factor("profit_target_factor")
        trailing = registry.create_factor("trailing_stop_factor")
        volatility = registry.create_factor("volatility_stop_factor")

        strategy.add_factor(profit, depends_on=["signal"])
        strategy.add_factor(trailing, depends_on=["signal"])
        strategy.add_factor(volatility, depends_on=["signal"])

        # Composite exit
        composite = registry.create_factor("composite_exit_factor", {
            "exit_signals": ["profit_target_signal", "trailing_stop_signal", "volatility_stop_signal"]
        })
        strategy.add_factor(composite, depends_on=["profit_target_30pct", "trailing_stop_10pct", "volatility_stop_20_2_0std"])

        # Execute and verify
        result = strategy.to_pipeline(sample_data)
        assert "final_exit_signal" in result.columns

        # Verify composite logic (any exit should trigger final exit)
        exit_signals = result[["profit_target_signal", "trailing_stop_signal", "volatility_stop_signal"]].any(axis=1)
        pd.testing.assert_series_equal(exit_signals, result["final_exit_signal"], check_names=False)

    def test_factor_outputs_compatible_across_categories(self, registry, sample_data):
        """Test that factor outputs are compatible across different categories."""
        strategy = Strategy(id="compat_test", generation=0)

        # Risk factor (ATR)
        atr = registry.create_factor("atr_factor")
        strategy.add_factor(atr)

        # Entry factor (Breakout)
        breakout = registry.create_factor("breakout_factor")
        strategy.add_factor(breakout)

        # Signal from different categories
        def signal_logic(data: pd.DataFrame, params: Dict) -> pd.DataFrame:
            data['positions'] = data['breakout_signal'] == 1
            data['entry_price'] = data['close'].where(data['positions'], np.nan).ffill()
            data['entry_date'] = data.index.to_series().where(data['positions'], pd.NaT).ffill()
            return data

        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["close", "breakout_signal"],
            outputs=["positions", "entry_price", "entry_date"],
            logic=signal_logic, parameters={}
        )
        strategy.add_factor(signal_factor, depends_on=["breakout_20"])

        # Exit using ATR from Risk category
        atr_stop = registry.create_factor("atr_stop_loss_factor")
        strategy.add_factor(atr_stop, depends_on=["atr_20", "signal"])

        # Should execute without errors
        result = strategy.to_pipeline(sample_data)
        assert "stop_loss_level" in result.columns


# ============================================================================
# Backward Compatibility Tests (3 tests)
# ============================================================================

class TestBackwardCompatibility:
    """Test backward compatibility with existing APIs."""

    def test_original_factory_functions_still_work(self):
        """Test that original factory functions still work."""
        from src.factor_library.momentum_factors import create_momentum_factor
        from src.factor_library.turtle_factors import create_atr_factor
        from src.factor_library.exit_factors import create_profit_target_factor

        # Create factors using factory functions
        momentum = create_momentum_factor(momentum_period=20)
        atr = create_atr_factor(atr_period=20)
        profit = create_profit_target_factor(target_percent=0.30)

        # Verify factors are functional
        assert momentum.id == "momentum_20"
        assert atr.id == "atr_20"
        assert profit.id == "profit_target_30pct"

    def test_direct_factor_creation_without_registry(self, sample_data):
        """Test direct factor creation (without registry) still works."""
        from src.factor_library.momentum_factors import MomentumFactor
        from src.factor_library.turtle_factors import ATRFactor

        # Create factors directly
        momentum = MomentumFactor(momentum_period=20)
        atr = ATRFactor(atr_period=20)

        # Execute factors
        result = sample_data.copy()
        result = momentum.execute(result)
        result = atr.execute(result)

        # Verify outputs
        assert "momentum" in result.columns
        assert "atr" in result.columns

    def test_no_breaking_changes_to_existing_apis(self, registry):
        """Test that no breaking changes to existing APIs."""
        # Registry API
        assert hasattr(registry, 'register_factor')
        assert hasattr(registry, 'get_factor')
        assert hasattr(registry, 'list_factors')
        assert hasattr(registry, 'list_by_category')
        assert hasattr(registry, 'create_factor')
        assert hasattr(registry, 'validate_parameters')

        # Factor API
        from src.factor_library.momentum_factors import MomentumFactor
        momentum = MomentumFactor(momentum_period=20)

        assert hasattr(momentum, 'id')
        assert hasattr(momentum, 'name')
        assert hasattr(momentum, 'category')
        assert hasattr(momentum, 'inputs')
        assert hasattr(momentum, 'outputs')
        assert hasattr(momentum, 'logic')
        assert hasattr(momentum, 'parameters')
        assert hasattr(momentum, 'execute')
        assert hasattr(momentum, 'validate_inputs')

        # Strategy API
        strategy = Strategy(id="test", generation=0)
        assert hasattr(strategy, 'add_factor')
        assert hasattr(strategy, 'remove_factor')
        assert hasattr(strategy, 'get_factors')
        assert hasattr(strategy, 'validate')
        assert hasattr(strategy, 'to_pipeline')
        assert hasattr(strategy, 'copy')


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
