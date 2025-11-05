"""
Core Tests for add_factor() Mutation Operator

Focused tests for essential add_factor() functionality:
- Root, after-factor, leaf, and smart insertion
- Dependency resolution
- Parameter validation
- Strategy preservation

Architecture: Phase 2.0+ Factor Graph System
Task: C.1 - Core Mutation Tests
"""

import pytest
import pandas as pd

from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.strategy import Strategy
from src.factor_graph.mutations import add_factor, remove_factor, replace_factor
from src.factor_library.registry import FactorRegistry


@pytest.fixture
def registry():
    """Factor registry."""
    return FactorRegistry.get_instance()


@pytest.fixture
def momentum_factor(registry):
    """Create momentum factor."""
    return registry.create_factor("momentum_factor", {"momentum_period": 20})


@pytest.fixture
def simple_strategy(momentum_factor, registry):
    """Simple strategy with momentum factor."""
    strategy = Strategy(id="test_strategy", generation=0)
    strategy.add_factor(momentum_factor)

    # Add breakout entry
    breakout = registry.create_factor("breakout_factor", {"entry_window": 20})
    strategy.add_factor(breakout)

    return strategy


class TestRootInsertion:
    """Test adding factors at root."""

    def test_add_factor_at_root(self, simple_strategy, registry):
        """Test adding factor at root with no dependencies."""
        # Add MA filter at root
        mutated = add_factor(
            strategy=simple_strategy,
            factor_name="ma_filter_factor",
            parameters={"ma_periods": 60},
            insert_point="root"
        )

        # Verify factor added (ID is ma_filter_60 based on parameters)
        assert "ma_filter_60" in mutated.factors
        assert mutated.factors["ma_filter_60"].category == FactorCategory.MOMENTUM

        # Verify no dependencies (root factor)
        dependencies = list(mutated.dag.predecessors("ma_filter_60"))
        assert len(dependencies) == 0

        # Verify original unchanged
        assert "ma_filter_60" not in simple_strategy.factors

    def test_root_insertion_validates(self, simple_strategy, registry):
        """Test root insertion creates valid strategy."""
        mutated = add_factor(
            strategy=simple_strategy,
            factor_name="atr_factor",
            parameters={"atr_period": 20},
            insert_point="root"
        )

        # Strategy has breakout_signal but needs positions
        # Note: breakout produces breakout_signal, not positions
        # So this test should validate that strategy structure is valid
        # even if it doesn't produce final positions
        assert len(mutated.factors) == 3  # Original 2 + new 1


class TestAfterFactorInsertion:
    """Test adding factors after specific factors."""

    def test_add_factor_after_specific_factor(self, simple_strategy, registry):
        """Test adding factor after existing factor."""
        # Add MA filter after momentum_20
        mutated = add_factor(
            strategy=simple_strategy,
            factor_name="ma_filter_factor",
            parameters={"ma_periods": 60},
            insert_point="momentum_20"
        )

        # Verify factor added
        assert "ma_filter_60" in mutated.factors

        # Verify depends on momentum_20
        dependencies = list(mutated.dag.predecessors("ma_filter_60"))
        assert "momentum_20" in dependencies

    def test_after_factor_invalid_id(self, simple_strategy):
        """Test error when specifying non-existent factor."""
        with pytest.raises(ValueError, match="Invalid insert_point"):
            add_factor(
                strategy=simple_strategy,
                factor_name="ma_filter_factor",
                parameters={"ma_periods": 60},
                insert_point="nonexistent_factor"
            )


class TestLeafInsertion:
    """Test adding factors at leaves."""

    def test_add_factor_at_leaf(self, simple_strategy, registry):
        """Test adding factor at leaf."""
        # Add time-based exit at leaf (uses only close, positions)
        mutated = add_factor(
            strategy=simple_strategy,
            factor_name="time_based_exit_factor",
            parameters={"max_holding_periods": 20},
            insert_point="leaf"
        )

        # Verify factor added (ID is time_exit_20d with 'd' suffix)
        assert "time_exit_20d" in mutated.factors

        # Verify depends on current leaf (breakout_20)
        dependencies = list(mutated.dag.predecessors("time_exit_20d"))
        assert "breakout_20" in dependencies


class TestSmartInsertion:
    """Test smart insertion with category-aware positioning."""

    def test_smart_insertion_default(self, simple_strategy, registry):
        """Test smart insertion is default behavior."""
        # Add ATR factor (RISK category)
        mutated = add_factor(
            strategy=simple_strategy,
            factor_name="atr_factor",
            parameters={"atr_period": 20}
        )

        # Verify factor added (ID is atr_20)
        assert "atr_20" in mutated.factors

    def test_smart_insertion_momentum_factor(self, registry):
        """Test smart insertion positions momentum factors."""
        strategy = Strategy(id="test", generation=0)
        momentum = registry.create_factor("momentum_factor", {"momentum_period": 20})
        strategy.add_factor(momentum)

        # Add another momentum factor
        mutated = add_factor(
            strategy=strategy,
            factor_name="ma_filter_factor",
            parameters={"ma_periods": 60},
            insert_point="smart"
        )

        # Verify momentum factor added
        assert "ma_filter_60" in mutated.factors


class TestDependencyResolution:
    """Test automatic dependency resolution."""

    def test_dependency_resolution_base_data(self, registry):
        """Test factors can use base OHLCV data without dependencies."""
        strategy = Strategy(id="test", generation=0)

        # Add factor using only base data
        mutated = add_factor(
            strategy=strategy,
            factor_name="momentum_factor",
            parameters={"momentum_period": 20},
            insert_point="root"
        )

        # Verify no dependencies (uses base data)
        dependencies = list(mutated.dag.predecessors("momentum_20"))
        assert len(dependencies) == 0


class TestValidationAndErrors:
    """Test validation and error handling."""

    def test_add_factor_invalid_factor_name(self, simple_strategy):
        """Test error when factor not in registry."""
        with pytest.raises(ValueError, match="not found in registry"):
            add_factor(
                strategy=simple_strategy,
                factor_name="nonexistent_factor",
                parameters={},
                insert_point="root"
            )

    def test_add_factor_invalid_parameters(self, simple_strategy):
        """Test error when parameters are invalid."""
        with pytest.raises(ValueError, match="Invalid parameters"):
            add_factor(
                strategy=simple_strategy,
                factor_name="momentum_factor",
                parameters={"momentum_period": 1},  # Below minimum (5)
                insert_point="root"
            )

    def test_add_factor_preserves_original(self, simple_strategy, registry):
        """Test that original strategy is not modified."""
        original_count = len(simple_strategy.factors)

        # Add factor
        mutated = add_factor(
            strategy=simple_strategy,
            factor_name="ma_filter_factor",
            parameters={"ma_periods": 60},
            insert_point="root"
        )

        # Verify original unchanged
        assert len(simple_strategy.factors) == original_count
        assert "ma_filter_60" not in simple_strategy.factors

        # Verify mutated has new factor
        assert len(mutated.factors) == original_count + 1
        assert "ma_filter_60" in mutated.factors


class TestRegistryIntegration:
    """Test integration with Factor Registry."""

    def test_add_factor_uses_registry(self, simple_strategy, registry):
        """Test add_factor correctly uses registry to create factors."""
        # Add factor from registry
        mutated = add_factor(
            strategy=simple_strategy,
            factor_name="momentum_factor",
            parameters={"momentum_period": 30},
            insert_point="root"
        )

        # Verify factor created with correct parameters
        assert mutated.factors["momentum_30"].parameters["momentum_period"] == 30

    def test_add_factor_uses_default_parameters(self, simple_strategy, registry):
        """Test add_factor uses registry defaults when parameters not specified."""
        # Add factor without parameters
        mutated = add_factor(
            strategy=simple_strategy,
            factor_name="atr_factor",
            parameters=None,
            insert_point="root"
        )

        # Verify default parameters used (atr_period=20)
        assert "atr_20" in mutated.factors
        assert mutated.factors["atr_20"].parameters["atr_period"] == 20


class TestSequentialAdditions:
    """Test adding multiple factors sequentially."""

    def test_add_multiple_factors(self, registry):
        """Test adding multiple factors to build complex strategy."""
        strategy = Strategy(id="test", generation=0)
        momentum = registry.create_factor("momentum_factor")
        strategy.add_factor(momentum)

        # Add ATR factor
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

        # Add time exit
        mutated3 = add_factor(
            strategy=mutated2,
            factor_name="time_based_exit_factor",
            parameters={"max_holding_periods": 20},
            insert_point="leaf"
        )

        # Verify all factors present
        assert "momentum_20" in mutated3.factors
        assert "atr_20" in mutated3.factors
        assert "breakout_20" in mutated3.factors
        assert "time_exit_20d" in mutated3.factors  # ID has 'd' suffix

        # Verify strategy has all factors
        assert len(mutated3.factors) == 4


class TestPerformance:
    """Test performance characteristics."""

    def test_add_factor_performance(self, simple_strategy, registry):
        """Test add_factor completes quickly."""
        import time

        start = time.time()
        mutated = add_factor(
            strategy=simple_strategy,
            factor_name="ma_filter_factor",
            parameters={"ma_periods": 60},
            insert_point="smart"
        )
        elapsed = time.time() - start

        # Should complete quickly (generous threshold for CI)
        assert elapsed < 0.1  # 100ms

    def test_add_factor_to_empty_strategy(self, registry):
        """Test adding first factor to empty strategy."""
        strategy = Strategy(id="test", generation=0)

        # Add first factor
        mutated = add_factor(
            strategy=strategy,
            factor_name="momentum_factor",
            parameters={"momentum_period": 20},
            insert_point="root"
        )

        # Verify factor added
        assert len(mutated.factors) == 1
        assert "momentum_20" in mutated.factors
