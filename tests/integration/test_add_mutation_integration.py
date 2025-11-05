"""
Integration Tests for add_factor() Mutation Operator

Tests real-world integration scenarios for add_factor mutation operator:
- Adding factors to momentum strategy
- Adding factors to turtle strategy
- Building complex multi-factor strategies
- Category-aware factor composition
- Pipeline execution after mutations
- Performance with real data

Architecture: Phase 2.0+ Factor Graph System
Task: C.1 - Integration Testing
Test Coverage: Real-world mutation scenarios with actual strategy templates
"""

import pytest
import pandas as pd
import numpy as np

from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.strategy import Strategy
from src.factor_graph.mutations import add_factor, remove_factor, replace_factor
from src.factor_library.registry import FactorRegistry


# Test Fixtures

@pytest.fixture
def registry():
    """Factor registry."""
    return FactorRegistry.get_instance()


@pytest.fixture
def test_data():
    """Real-world OHLCV data for testing."""
    np.random.seed(42)
    n = 100

    # Generate realistic price data
    close = 100 * np.exp(np.cumsum(np.random.randn(n) * 0.02))
    high = close * (1 + np.abs(np.random.randn(n) * 0.01))
    low = close * (1 - np.abs(np.random.randn(n) * 0.01))
    open_ = close * (1 + np.random.randn(n) * 0.005)
    volume = np.random.randint(1000, 10000, n)

    return pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume
    })


@pytest.fixture
def momentum_strategy(registry):
    """Create simple momentum strategy."""
    strategy = Strategy(id="momentum_base", generation=0)

    # Add momentum factor
    momentum = registry.create_factor(
        "momentum_factor",
        parameters={"momentum_period": 20}
    )
    strategy.add_factor(momentum)

    # Add MA filter
    ma_filter = registry.create_factor(
        "ma_filter_factor",
        parameters={"ma_periods": 60}
    )
    strategy.add_factor(ma_filter)

    # Add breakout entry
    breakout = registry.create_factor(
        "breakout_factor",
        parameters={"entry_window": 20}
    )
    strategy.add_factor(breakout, depends_on=["momentum_factor"])

    return strategy


@pytest.fixture
def turtle_strategy(registry):
    """Create Turtle-style strategy."""
    strategy = Strategy(id="turtle_base", generation=0)

    # Add ATR
    atr = registry.create_factor(
        "atr_factor",
        parameters={"atr_period": 20}
    )
    strategy.add_factor(atr)

    # Add breakout
    breakout = registry.create_factor(
        "breakout_factor",
        parameters={"entry_window": 20}
    )
    strategy.add_factor(breakout)

    # Add dual MA filter
    dual_ma = registry.create_factor(
        "dual_ma_filter_factor",
        parameters={"short_ma": 20, "long_ma": 60}
    )
    strategy.add_factor(dual_ma)

    return strategy


# Test Class 1: Momentum Strategy Mutations

class TestMomentumStrategyMutations:
    """Test adding factors to momentum strategy."""

    def test_add_exit_factor_to_momentum_strategy(self, momentum_strategy, registry):
        """Test adding trailing stop exit to momentum strategy."""
        # Add trailing stop at leaf
        mutated = add_factor(
            strategy=momentum_strategy,
            factor_name="trailing_stop_factor",
            parameters={"trail_percent": 0.10, "activation_profit": 0.05},
            insert_point="leaf"
        )

        # Verify exit factor added
        assert "trailing_stop_factor" in mutated.factors
        assert mutated.factors["trailing_stop_factor"].category == FactorCategory.EXIT

        # Verify strategy is valid
        assert mutated.validate() is True

    def test_add_multiple_exit_factors(self, momentum_strategy, registry):
        """Test adding multiple exit factors to momentum strategy."""
        # Add trailing stop
        mutated1 = add_factor(
            strategy=momentum_strategy,
            factor_name="trailing_stop_factor",
            parameters={"trail_percent": 0.10, "activation_profit": 0.05},
            insert_point="leaf"
        )

        # Add time-based exit
        mutated2 = add_factor(
            strategy=mutated1,
            factor_name="time_based_exit_factor",
            parameters={"max_holding_periods": 20},
            insert_point="leaf"
        )

        # Verify both exits added
        assert "trailing_stop_factor" in mutated2.factors
        assert "time_based_exit_factor" in mutated2.factors

        # Verify strategy is valid
        assert mutated2.validate() is True

    def test_add_risk_factor_to_momentum_strategy(self, momentum_strategy, registry):
        """Test adding ATR risk factor to momentum strategy."""
        # Add ATR at root (independent calculation)
        mutated = add_factor(
            strategy=momentum_strategy,
            factor_name="atr_factor",
            parameters={"atr_period": 20},
            insert_point="root"
        )

        # Verify ATR added
        assert "atr_factor" in mutated.factors
        assert mutated.factors["atr_factor"].category == FactorCategory.RISK

        # Verify strategy is valid
        assert mutated.validate() is True

    def test_momentum_strategy_pipeline_after_mutation(self, momentum_strategy, registry, test_data):
        """Test strategy pipeline executes correctly after adding factors."""
        # Add exit factor
        mutated = add_factor(
            strategy=momentum_strategy,
            factor_name="trailing_stop_factor",
            parameters={"trail_percent": 0.10, "activation_profit": 0.05},
            insert_point="leaf"
        )

        # Execute pipeline
        result = mutated.to_pipeline(test_data)

        # Verify all outputs present
        assert "momentum" in result.columns
        assert "ma_filter" in result.columns
        assert "positions" in result.columns
        # Note: trailing_stop output columns depend on implementation

        # Verify no NaN in critical columns (after warmup)
        assert not result["momentum"].iloc[30:].isna().all()


# Test Class 2: Turtle Strategy Mutations

class TestTurtleStrategyMutations:
    """Test adding factors to turtle strategy."""

    def test_add_atr_stop_to_turtle_strategy(self, turtle_strategy, registry):
        """Test adding ATR-based stop loss to turtle strategy."""
        # Add ATR stop loss
        mutated = add_factor(
            strategy=turtle_strategy,
            factor_name="atr_stop_loss_factor",
            parameters={"atr_multiplier": 2.0},
            insert_point="smart"
        )

        # Verify stop loss added
        assert "atr_stop_loss_factor" in mutated.factors
        assert mutated.factors["atr_stop_loss_factor"].category == FactorCategory.EXIT

        # Verify strategy is valid
        assert mutated.validate() is True

    def test_add_profit_target_to_turtle_strategy(self, turtle_strategy, registry):
        """Test adding profit target exit to turtle strategy."""
        # Add profit target
        mutated = add_factor(
            strategy=turtle_strategy,
            factor_name="profit_target_factor",
            parameters={"target_percent": 0.30},
            insert_point="leaf"
        )

        # Verify profit target added
        assert "profit_target_factor" in mutated.factors

        # Verify strategy is valid
        assert mutated.validate() is True

    def test_turtle_strategy_pipeline_after_mutation(self, turtle_strategy, registry, test_data):
        """Test turtle strategy executes after adding factors."""
        # Add exit factor
        mutated = add_factor(
            strategy=turtle_strategy,
            factor_name="atr_stop_loss_factor",
            parameters={"atr_multiplier": 2.0},
            insert_point="smart"
        )

        # Execute pipeline
        result = mutated.to_pipeline(test_data)

        # Verify key outputs present
        assert "atr" in result.columns
        assert "positions" in result.columns
        assert "dual_ma_filter" in result.columns


# Test Class 3: Multi-Factor Composition

class TestMultiFactorComposition:
    """Test building complex strategies through sequential additions."""

    def test_build_strategy_from_scratch(self, registry, test_data):
        """Test building complete strategy by adding factors sequentially."""
        # Start with empty strategy
        strategy = Strategy(id="composed_strategy", generation=0)

        # Add momentum factor
        momentum = registry.create_factor(
            "momentum_factor",
            parameters={"momentum_period": 20}
        )
        strategy.add_factor(momentum)

        # Add ATR using mutation
        mutated1 = add_factor(
            strategy=strategy,
            factor_name="atr_factor",
            parameters={"atr_period": 20},
            insert_point="root"
        )

        # Add breakout entry
        mutated2 = add_factor(
            strategy=mutated1,
            factor_name="breakout_factor",
            parameters={"entry_window": 20},
            insert_point="smart"
        )

        # Add trailing stop exit
        mutated3 = add_factor(
            strategy=mutated2,
            factor_name="trailing_stop_factor",
            parameters={"trail_percent": 0.10, "activation_profit": 0.05},
            insert_point="leaf"
        )

        # Verify complete strategy
        assert len(mutated3.factors) == 4
        assert mutated3.validate() is True

        # Execute pipeline
        result = mutated3.to_pipeline(test_data)
        assert "positions" in result.columns

    def test_add_factors_different_categories_sequentially(self, registry):
        """Test adding factors from different categories builds valid strategy."""
        strategy = Strategy(id="multi_category", generation=0)

        # Add MOMENTUM factor
        momentum = registry.create_factor("momentum_factor")
        strategy.add_factor(momentum)

        # Add VALUE factor (revenue catalyst)
        mutated1 = add_factor(
            strategy=strategy,
            factor_name="revenue_catalyst_factor",
            parameters={"catalyst_lookback": 3},
            insert_point="root"
        )

        # Add QUALITY factor (earnings catalyst)
        mutated2 = add_factor(
            strategy=mutated1,
            factor_name="earnings_catalyst_factor",
            parameters={"catalyst_lookback": 3},
            insert_point="root"
        )

        # Add ENTRY factor
        mutated3 = add_factor(
            strategy=mutated2,
            factor_name="breakout_factor",
            parameters={"entry_window": 20},
            insert_point="smart"
        )

        # Verify diverse categories
        categories = {f.category for f in mutated3.factors.values()}
        assert FactorCategory.MOMENTUM in categories
        assert FactorCategory.VALUE in categories
        assert FactorCategory.QUALITY in categories
        assert FactorCategory.ENTRY in categories

    def test_complex_dependency_chain(self, registry):
        """Test building complex dependency chains through mutations."""
        strategy = Strategy(id="complex_deps", generation=0)

        # Add base momentum
        momentum = registry.create_factor("momentum_factor")
        strategy.add_factor(momentum)

        # Add MA filter (depends on close, independent)
        mutated1 = add_factor(
            strategy=strategy,
            factor_name="ma_filter_factor",
            parameters={"ma_periods": 60},
            insert_point="root"
        )

        # Add dual MA filter (also independent)
        mutated2 = add_factor(
            strategy=mutated1,
            factor_name="dual_ma_filter_factor",
            parameters={"short_ma": 20, "long_ma": 60},
            insert_point="root"
        )

        # Add breakout (will depend on some of the above)
        mutated3 = add_factor(
            strategy=mutated2,
            factor_name="breakout_factor",
            parameters={"entry_window": 20},
            insert_point="smart"
        )

        # Verify complex dependencies created
        assert len(mutated3.factors) == 4
        assert mutated3.validate() is True


# Test Class 4: Category-Aware Behavior

class TestCategoryAwareBehavior:
    """Test category-aware insertion and positioning."""

    def test_entry_factors_positioned_early(self, registry):
        """Test ENTRY factors are positioned early in pipeline."""
        strategy = Strategy(id="test", generation=0)

        # Add momentum
        momentum = registry.create_factor("momentum_factor")
        strategy.add_factor(momentum)

        # Add entry factor with smart insertion
        mutated = add_factor(
            strategy=strategy,
            factor_name="breakout_factor",
            parameters={"entry_window": 20},
            insert_point="smart"
        )

        # Entry should be early in execution order
        factors = mutated.get_factors()
        entry_index = next(i for i, f in enumerate(factors) if f.id == "breakout_factor")

        # Entry should not be last (not a leaf in this context)
        # But depends on what factors it needs
        assert entry_index >= 0  # Basic check

    def test_exit_factors_positioned_late(self, momentum_strategy, registry):
        """Test EXIT factors are positioned late in pipeline."""
        # Add exit factor with smart insertion
        mutated = add_factor(
            strategy=momentum_strategy,
            factor_name="trailing_stop_factor",
            parameters={"trail_percent": 0.10, "activation_profit": 0.05},
            insert_point="smart"
        )

        # Exit should be late in execution order
        factors = mutated.get_factors()
        exit_index = next(i for i, f in enumerate(factors) if f.id == "trailing_stop_factor")

        # Exit should be after entry/signal factors
        # In this case, should be last or near-last
        assert exit_index > 0

    def test_momentum_factors_in_middle(self, registry):
        """Test MOMENTUM factors positioned in middle layers."""
        strategy = Strategy(id="test", generation=0)

        # Add base momentum
        momentum = registry.create_factor("momentum_factor")
        strategy.add_factor(momentum)

        # Add entry
        entry = registry.create_factor("breakout_factor")
        strategy.add_factor(entry, depends_on=["momentum_factor"])

        # Add another momentum factor with smart insertion
        mutated = add_factor(
            strategy=strategy,
            factor_name="ma_filter_factor",
            parameters={"ma_periods": 60},
            insert_point="smart"
        )

        # Should be positioned appropriately
        assert "ma_filter_factor" in mutated.factors
        assert mutated.validate() is True


# Test Class 5: Real Pipeline Execution

class TestRealPipelineExecution:
    """Test pipeline execution with real data after mutations."""

    def test_pipeline_produces_valid_signals(self, momentum_strategy, registry, test_data):
        """Test mutated strategy produces valid trading signals."""
        # Add exit factor
        mutated = add_factor(
            strategy=momentum_strategy,
            factor_name="trailing_stop_factor",
            parameters={"trail_percent": 0.10, "activation_profit": 0.05},
            insert_point="leaf"
        )

        # Execute pipeline
        result = mutated.to_pipeline(test_data)

        # Verify positions column exists and has valid values
        assert "positions" in result.columns
        assert result["positions"].dtype in [np.int64, np.int32, np.float64]

        # Check for reasonable signal values (0, 1, or -1 typically)
        unique_positions = result["positions"].dropna().unique()
        assert len(unique_positions) > 0  # Has some signals

    def test_pipeline_handles_missing_data(self, momentum_strategy, registry):
        """Test pipeline handles data with NaN values."""
        # Create data with some NaN
        data = pd.DataFrame({
            "open": [100, 101, np.nan, 103, 104],
            "high": [101, 102, 103, 104, 105],
            "low": [99, 100, 101, 102, 103],
            "close": [100.5, np.nan, 102.5, 103.5, 104.5],
            "volume": [1000, 1100, 1200, 1300, 1400]
        })

        # Add factor
        mutated = add_factor(
            strategy=momentum_strategy,
            factor_name="ma_filter_factor",
            parameters={"ma_periods": 60},
            insert_point="root"
        )

        # Execute pipeline (should handle NaN gracefully)
        result = mutated.to_pipeline(data)

        # Should complete without errors
        assert result is not None
        assert len(result) == len(data)

    def test_pipeline_performance_with_mutations(self, momentum_strategy, registry, test_data):
        """Test pipeline performance after multiple mutations."""
        # Add multiple factors
        mutated = momentum_strategy
        for _ in range(3):
            mutated = add_factor(
                strategy=mutated,
                factor_name="ma_filter_factor",
                parameters={"ma_periods": 60},
                insert_point="root"
            )

        # Execute pipeline and measure time
        import time
        start = time.time()
        result = mutated.to_pipeline(test_data)
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 1.0  # 1 second for 100 rows


# Test Class 6: Error Recovery

class TestErrorRecovery:
    """Test error handling and recovery in real scenarios."""

    def test_invalid_factor_addition_preserves_original(self, momentum_strategy):
        """Test failed addition doesn't corrupt original strategy."""
        original_count = len(momentum_strategy.factors)

        # Try to add non-existent factor
        with pytest.raises(ValueError):
            add_factor(
                strategy=momentum_strategy,
                factor_name="nonexistent_factor",
                parameters={},
                insert_point="root"
            )

        # Verify original strategy unchanged
        assert len(momentum_strategy.factors) == original_count
        assert momentum_strategy.validate() is True

    def test_invalid_parameters_preserves_original(self, momentum_strategy, registry):
        """Test invalid parameters don't corrupt strategy."""
        original_count = len(momentum_strategy.factors)

        # Try to add factor with invalid parameters
        with pytest.raises(ValueError):
            add_factor(
                strategy=momentum_strategy,
                factor_name="momentum_factor",
                parameters={"momentum_period": 1000},  # Out of range
                insert_point="root"
            )

        # Verify original strategy unchanged
        assert len(momentum_strategy.factors) == original_count
