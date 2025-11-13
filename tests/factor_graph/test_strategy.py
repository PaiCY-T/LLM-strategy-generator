"""
Unit Tests for Strategy DAG Structure

Tests Strategy class with DAG structure implementation including:
- Strategy initialization and validation
- Factor addition with dependency tracking
- Factor removal with orphan detection
- Topological sorting and execution order
- Cycle detection and prevention
- Strategy cloning and independence

Architecture: Phase 2.0+ Factor Graph System
Test Coverage: Task A.2 acceptance criteria
"""

import pytest
import pandas as pd
import networkx as nx
from typing import Dict, Any

from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.strategy import Strategy


# Test fixtures - reusable factor definitions


@pytest.fixture
def simple_logic():
    """Simple logic function for testing."""
    def logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        data = data.copy()
        data["output"] = data["input"] * params.get("multiplier", 1.0)
        return data
    return logic


@pytest.fixture
def rsi_factor(simple_logic):
    """RSI momentum factor (no dependencies)."""
    return Factor(
        id="rsi_14",
        name="RSI Momentum",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["rsi", "rsi_signal"],
        logic=simple_logic,
        parameters={"period": 14}
    )


@pytest.fixture
def ma_factor(simple_logic):
    """Moving average factor (no dependencies)."""
    return Factor(
        id="ma_20",
        name="MA 20",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["ma"],
        logic=simple_logic,
        parameters={"period": 20}
    )


@pytest.fixture
def signal_factor(simple_logic):
    """Signal factor (depends on rsi and ma)."""
    return Factor(
        id="signal",
        name="Entry Signal",
        category=FactorCategory.SIGNAL,
        inputs=["rsi", "ma"],
        outputs=["entry_signal"],
        logic=simple_logic,
        parameters={}
    )


@pytest.fixture
def exit_factor(simple_logic):
    """Exit factor (depends on entry_signal)."""
    return Factor(
        id="exit",
        name="Exit Signal",
        category=FactorCategory.EXIT,
        inputs=["entry_signal"],
        outputs=["exit_signal"],
        logic=simple_logic,
        parameters={}
    )


# Test Class 1: Strategy Initialization


class TestStrategyInitialization:
    """Test Strategy initialization and validation."""

    def test_create_empty_strategy(self):
        """TC1: Create empty Strategy → success."""
        strategy = Strategy(id="test_strategy", generation=0)

        assert strategy.id == "test_strategy"
        assert strategy.generation == 0
        assert strategy.parent_ids == []
        assert len(strategy.factors) == 0
        assert strategy.dag.number_of_nodes() == 0
        assert strategy.dag.number_of_edges() == 0

    def test_create_strategy_with_lineage(self):
        """Test creating strategy with parent lineage."""
        strategy = Strategy(
            id="child_strategy",
            generation=5,
            parent_ids=["parent1", "parent2"]
        )

        assert strategy.id == "child_strategy"
        assert strategy.generation == 5
        assert strategy.parent_ids == ["parent1", "parent2"]

    def test_invalid_id_raises_error(self):
        """Test that empty or invalid ID raises ValueError."""
        with pytest.raises(ValueError, match="id cannot be empty"):
            Strategy(id="", generation=0)

        with pytest.raises(TypeError):
            Strategy(id=123, generation=0)

    def test_invalid_generation_raises_error(self):
        """Test that invalid generation raises TypeError or ValueError."""
        with pytest.raises(TypeError):
            Strategy(id="test", generation="not_int")

        with pytest.raises(ValueError, match="non-negative"):
            Strategy(id="test", generation=-1)

    def test_invalid_parent_ids_raises_error(self):
        """Test that invalid parent_ids raises TypeError."""
        with pytest.raises(TypeError, match="must be list"):
            Strategy(id="test", generation=0, parent_ids="not_list")

        with pytest.raises(TypeError, match="list of strings"):
            Strategy(id="test", generation=0, parent_ids=[1, 2, 3])


# Test Class 2: Adding Factors


class TestAddFactor:
    """Test adding factors to strategy with dependency validation."""

    def test_add_factor_without_dependencies(self, rsi_factor):
        """TC2: Add Factor without dependencies → added to DAG."""
        strategy = Strategy(id="test")
        strategy.add_factor(rsi_factor)

        assert "rsi_14" in strategy.factors
        assert strategy.factors["rsi_14"] == rsi_factor
        assert "rsi_14" in strategy.dag.nodes()
        assert strategy.dag.number_of_nodes() == 1
        assert strategy.dag.number_of_edges() == 0

    def test_add_factor_with_dependencies(self, rsi_factor, signal_factor):
        """TC3: Add Factor with dependencies → edges created."""
        strategy = Strategy(id="test")
        strategy.add_factor(rsi_factor)
        strategy.add_factor(signal_factor, depends_on=["rsi_14"])

        assert "signal" in strategy.factors
        assert strategy.dag.number_of_nodes() == 2
        assert strategy.dag.number_of_edges() == 1
        assert strategy.dag.has_edge("rsi_14", "signal")

    def test_add_multiple_factors_with_dependencies(
        self, rsi_factor, ma_factor, signal_factor
    ):
        """Test adding factor with multiple dependencies."""
        strategy = Strategy(id="test")
        strategy.add_factor(rsi_factor)
        strategy.add_factor(ma_factor)
        strategy.add_factor(signal_factor, depends_on=["rsi_14", "ma_20"])

        assert strategy.dag.number_of_nodes() == 3
        assert strategy.dag.number_of_edges() == 2
        assert strategy.dag.has_edge("rsi_14", "signal")
        assert strategy.dag.has_edge("ma_20", "signal")

    def test_add_factor_creating_cycle_raises_error(self, simple_logic):
        """TC4: Add Factor creating cycle → raises ValueError, rollback."""
        # The way to test cycle creation is to manually corrupt the DAG
        # and then verify that add_factor detects it
        # In normal usage, it's impossible to create a cycle through add_factor
        # because we build incrementally and check after each addition

        strategy = Strategy(id="test")

        factor_a = Factor(
            id="a", name="A", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["a_out"],
            logic=simple_logic, parameters={}
        )
        factor_b = Factor(
            id="b", name="B", category=FactorCategory.MOMENTUM,
            inputs=["a_out"], outputs=["b_out"],
            logic=simple_logic, parameters={}
        )

        strategy.add_factor(factor_a)
        strategy.add_factor(factor_b, depends_on=["a"])

        # Manually corrupt DAG by adding a cycle: b → a (creates cycle a → b → a)
        strategy.dag.add_edge("b", "a")

        # Verify DAG now has a cycle
        assert not nx.is_directed_acyclic_graph(strategy.dag)

        # Now try to add a new factor - should detect the existing cycle
        factor_c = Factor(
            id="c", name="C", category=FactorCategory.SIGNAL,
            inputs=["b_out"], outputs=["c_out"],
            logic=simple_logic, parameters={}
        )

        with pytest.raises(ValueError, match="cycle"):
            strategy.add_factor(factor_c, depends_on=["b"])

        # Verify rollback: factor c should not be added
        assert "c" not in strategy.factors
        assert "c" not in strategy.dag.nodes()

    def test_add_factor_self_dependency_raises_error(self, simple_logic):
        """Test that self-dependency creates cycle and raises error."""
        # Similar to previous test - manually create a cycle and verify detection
        strategy = Strategy(id="test")

        factor_a = Factor(
            id="a", name="A", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["a_out"],
            logic=simple_logic, parameters={}
        )

        strategy.add_factor(factor_a)

        # Manually create self-loop: a → a
        strategy.dag.add_edge("a", "a")

        # Verify cycle exists
        assert not nx.is_directed_acyclic_graph(strategy.dag)

        # Try to add another factor - should detect cycle
        factor_b = Factor(
            id="b", name="B", category=FactorCategory.SIGNAL,
            inputs=["a_out"], outputs=["b_out"],
            logic=simple_logic, parameters={}
        )

        with pytest.raises(ValueError, match="cycle"):
            strategy.add_factor(factor_b, depends_on=["a"])

    def test_add_factor_with_nonexistent_dependency_raises_error(self, signal_factor):
        """Test adding factor with non-existent dependency raises ValueError."""
        strategy = Strategy(id="test")

        with pytest.raises(ValueError, match="not found in strategy"):
            strategy.add_factor(signal_factor, depends_on=["nonexistent_factor"])

    def test_add_duplicate_factor_id_raises_error(self, rsi_factor, simple_logic):
        """Test adding factor with duplicate ID raises ValueError."""
        strategy = Strategy(id="test")
        strategy.add_factor(rsi_factor)

        duplicate_factor = Factor(
            id="rsi_14",  # Duplicate ID
            name="Duplicate RSI",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["rsi_duplicate"],
            logic=simple_logic,
            parameters={}
        )

        with pytest.raises(ValueError, match="already exists"):
            strategy.add_factor(duplicate_factor)

    def test_add_non_factor_raises_error(self):
        """Test adding non-Factor object raises TypeError."""
        strategy = Strategy(id="test")

        with pytest.raises(TypeError, match="Expected Factor"):
            strategy.add_factor("not a factor")


# Test Class 3: Removing Factors


class TestRemoveFactor:
    """Test removing factors from strategy with orphan detection."""

    def test_remove_factor_with_dependents_raises_error(
        self, rsi_factor, signal_factor
    ):
        """TC5: Remove Factor with dependents → raises ValueError."""
        strategy = Strategy(id="test")
        strategy.add_factor(rsi_factor)
        strategy.add_factor(signal_factor, depends_on=["rsi_14"])

        with pytest.raises(ValueError, match="depend on its outputs"):
            strategy.remove_factor("rsi_14")

        # Verify factor still exists
        assert "rsi_14" in strategy.factors

    def test_remove_leaf_factor(self, rsi_factor, signal_factor):
        """TC6: Remove leaf Factor → success."""
        strategy = Strategy(id="test")
        strategy.add_factor(rsi_factor)
        strategy.add_factor(signal_factor, depends_on=["rsi_14"])

        # Remove leaf factor (no dependents)
        strategy.remove_factor("signal")

        assert "signal" not in strategy.factors
        assert "signal" not in strategy.dag.nodes()
        assert strategy.dag.number_of_nodes() == 1
        assert strategy.dag.number_of_edges() == 0

    def test_remove_nonexistent_factor_raises_error(self):
        """Test removing non-existent factor raises ValueError."""
        strategy = Strategy(id="test")

        with pytest.raises(ValueError, match="not found"):
            strategy.remove_factor("nonexistent")

    def test_remove_all_factors_sequentially(
        self, rsi_factor, signal_factor, exit_factor
    ):
        """Test removing all factors in correct order."""
        strategy = Strategy(id="test")
        strategy.add_factor(rsi_factor)
        strategy.add_factor(signal_factor, depends_on=["rsi_14"])
        strategy.add_factor(exit_factor, depends_on=["signal"])

        # Remove in reverse dependency order (leaf to root)
        strategy.remove_factor("exit")
        assert len(strategy.factors) == 2

        strategy.remove_factor("signal")
        assert len(strategy.factors) == 1

        strategy.remove_factor("rsi_14")
        assert len(strategy.factors) == 0
        assert strategy.dag.number_of_nodes() == 0


# Test Class 4: Getting Factors in Order


class TestGetFactors:
    """Test getting factors in topologically sorted order."""

    def test_get_factors_empty_strategy(self):
        """Test getting factors from empty strategy returns empty list."""
        strategy = Strategy(id="test")
        factors = strategy.get_factors()

        assert factors == []

    def test_get_factors_single_factor(self, rsi_factor):
        """Test getting single factor."""
        strategy = Strategy(id="test")
        strategy.add_factor(rsi_factor)

        factors = strategy.get_factors()

        assert len(factors) == 1
        assert factors[0] == rsi_factor

    def test_get_factors_topologically_sorted(
        self, rsi_factor, ma_factor, signal_factor
    ):
        """TC7: get_factors() → topologically sorted list."""
        strategy = Strategy(id="test")
        strategy.add_factor(rsi_factor)
        strategy.add_factor(ma_factor)
        strategy.add_factor(signal_factor, depends_on=["rsi_14", "ma_20"])

        factors = strategy.get_factors()

        assert len(factors) == 3

        # Extract IDs
        factor_ids = [f.id for f in factors]

        # Verify topological order: dependencies come before dependents
        rsi_idx = factor_ids.index("rsi_14")
        ma_idx = factor_ids.index("ma_20")
        signal_idx = factor_ids.index("signal")

        assert signal_idx > rsi_idx, "signal should come after rsi_14"
        assert signal_idx > ma_idx, "signal should come after ma_20"

    def test_get_factors_complex_dag(
        self, rsi_factor, ma_factor, signal_factor, exit_factor
    ):
        """Test topological sort with complex dependency chain."""
        strategy = Strategy(id="test")
        strategy.add_factor(rsi_factor)
        strategy.add_factor(ma_factor)
        strategy.add_factor(signal_factor, depends_on=["rsi_14", "ma_20"])
        strategy.add_factor(exit_factor, depends_on=["signal"])

        factors = strategy.get_factors()

        assert len(factors) == 4

        factor_ids = [f.id for f in factors]

        # Verify order constraints
        rsi_idx = factor_ids.index("rsi_14")
        ma_idx = factor_ids.index("ma_20")
        signal_idx = factor_ids.index("signal")
        exit_idx = factor_ids.index("exit")

        assert signal_idx > rsi_idx
        assert signal_idx > ma_idx
        assert exit_idx > signal_idx


# Test Class 5: Strategy Cloning


class TestStrategyCopy:
    """Test strategy cloning and independence."""

    def test_copy_empty_strategy(self):
        """Test copying empty strategy."""
        original = Strategy(id="original", generation=5, parent_ids=["p1", "p2"])
        copy = original.copy()

        assert copy.id == "original_copy"
        assert copy.generation == 5
        assert copy.parent_ids == ["p1", "p2"]
        assert len(copy.factors) == 0

        # Verify independence
        copy.parent_ids.append("p3")
        assert len(original.parent_ids) == 2

    def test_copy_strategy_with_factors(
        self, rsi_factor, signal_factor
    ):
        """TC8: copy() → independent clone created."""
        original = Strategy(id="original", generation=0)
        original.add_factor(rsi_factor)
        original.add_factor(signal_factor, depends_on=["rsi_14"])

        copy = original.copy()

        # Verify structure is copied
        assert len(copy.factors) == 2
        assert "rsi_14" in copy.factors
        assert "signal" in copy.factors
        assert copy.dag.number_of_nodes() == 2
        assert copy.dag.number_of_edges() == 1

        # Verify independence: modify copy
        copy.remove_factor("signal")

        assert len(copy.factors) == 1
        assert len(original.factors) == 2  # Original unchanged

    def test_copy_creates_independent_factors(self, rsi_factor):
        """Test that copied factors are independent."""
        original = Strategy(id="original")
        original.add_factor(rsi_factor)

        copy = original.copy()

        # Modify copy's factor parameters
        copy.factors["rsi_14"].parameters["period"] = 50

        # Verify original unchanged
        assert original.factors["rsi_14"].parameters["period"] == 14

    def test_copy_preserves_dag_structure(
        self, rsi_factor, ma_factor, signal_factor, exit_factor
    ):
        """Test that DAG structure is preserved in copy."""
        original = Strategy(id="original")
        original.add_factor(rsi_factor)
        original.add_factor(ma_factor)
        original.add_factor(signal_factor, depends_on=["rsi_14", "ma_20"])
        original.add_factor(exit_factor, depends_on=["signal"])

        copy = original.copy()

        # Verify DAG structure
        assert copy.dag.number_of_nodes() == 4
        assert copy.dag.number_of_edges() == 3
        assert copy.dag.has_edge("rsi_14", "signal")
        assert copy.dag.has_edge("ma_20", "signal")
        assert copy.dag.has_edge("signal", "exit")

        # Verify topological order matches
        original_order = [f.id for f in original.get_factors()]
        copy_order = [f.id for f in copy.get_factors()]

        # Order should be equivalent (may differ if multiple valid orders exist)
        # Just verify dependencies are satisfied in both
        for factors, dag in [(original.factors, original.dag), (copy.factors, copy.dag)]:
            topo_order = list(factors.keys())
            for factor_id in topo_order:
                for predecessor in dag.predecessors(factor_id):
                    assert topo_order.index(predecessor) < topo_order.index(factor_id)


# Test Class 6: String Representations


class TestStrategyRepresentations:
    """Test string representations of Strategy."""

    def test_repr_empty_strategy(self):
        """Test __repr__ for empty strategy."""
        strategy = Strategy(id="test", generation=5, parent_ids=["p1"])
        repr_str = repr(strategy)

        assert "Strategy" in repr_str
        assert "id='test'" in repr_str
        assert "generation=5" in repr_str
        assert "parent_ids=['p1']" in repr_str
        assert "factors=0" in repr_str

    def test_str_empty_strategy(self):
        """Test __str__ for empty strategy."""
        strategy = Strategy(id="test", generation=5)
        str_repr = str(strategy)

        assert "test" in str_repr
        assert "gen 5" in str_repr
        assert "0 factors" in str_repr
        assert "empty" in str_repr

    def test_str_strategy_with_factors(self, rsi_factor, signal_factor):
        """Test __str__ for strategy with factors."""
        strategy = Strategy(id="momentum", generation=2)
        strategy.add_factor(rsi_factor)
        strategy.add_factor(signal_factor, depends_on=["rsi_14"])

        str_repr = str(strategy)

        assert "momentum" in str_repr
        assert "gen 2" in str_repr
        assert "2 factors" in str_repr
        assert "rsi_14" in str_repr
        assert "signal" in str_repr


# Test Class 7: Edge Cases and Validation


class TestEdgeCases:
    """Test edge cases and validation scenarios."""

    def test_strategy_with_many_factors(self, simple_logic):
        """Test strategy with many factors (scalability)."""
        strategy = Strategy(id="large")

        # Add 20 factors in chain
        for i in range(20):
            factor = Factor(
                id=f"factor_{i}",
                name=f"Factor {i}",
                category=FactorCategory.MOMENTUM,
                inputs=["close"] if i == 0 else [f"output_{i-1}"],
                outputs=[f"output_{i}"],
                logic=simple_logic,
                parameters={}
            )
            depends_on = [f"factor_{i-1}"] if i > 0 else None
            strategy.add_factor(factor, depends_on=depends_on)

        assert len(strategy.factors) == 20
        assert strategy.dag.number_of_edges() == 19

        # Verify topological order
        factors = strategy.get_factors()
        assert len(factors) == 20
        assert factors[0].id == "factor_0"
        assert factors[-1].id == "factor_19"

    def test_strategy_with_diamond_dependency(self, simple_logic):
        """Test strategy with diamond-shaped dependency graph."""
        strategy = Strategy(id="diamond")

        # Create diamond: A → B, A → C, B → D, C → D
        factor_a = Factor(
            id="a", name="A", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["a_out"],
            logic=simple_logic, parameters={}
        )
        factor_b = Factor(
            id="b", name="B", category=FactorCategory.MOMENTUM,
            inputs=["a_out"], outputs=["b_out"],
            logic=simple_logic, parameters={}
        )
        factor_c = Factor(
            id="c", name="C", category=FactorCategory.MOMENTUM,
            inputs=["a_out"], outputs=["c_out"],
            logic=simple_logic, parameters={}
        )
        factor_d = Factor(
            id="d", name="D", category=FactorCategory.SIGNAL,
            inputs=["b_out", "c_out"], outputs=["d_out"],
            logic=simple_logic, parameters={}
        )

        strategy.add_factor(factor_a)
        strategy.add_factor(factor_b, depends_on=["a"])
        strategy.add_factor(factor_c, depends_on=["a"])
        strategy.add_factor(factor_d, depends_on=["b", "c"])

        # Verify structure
        assert strategy.dag.number_of_nodes() == 4
        assert strategy.dag.number_of_edges() == 4

        # Verify topological order respects all dependencies
        factors = strategy.get_factors()
        factor_ids = [f.id for f in factors]

        a_idx = factor_ids.index("a")
        b_idx = factor_ids.index("b")
        c_idx = factor_ids.index("c")
        d_idx = factor_ids.index("d")

        assert a_idx < b_idx
        assert a_idx < c_idx
        assert b_idx < d_idx
        assert c_idx < d_idx


# Test Class 8: Strategy Validation Framework


class TestStrategyValidation:
    """Test strategy validation framework (Task A.3)."""

    def test_valid_strategy_passes_validation(self, rsi_factor, simple_logic):
        """TC1: Valid strategy passes all checks → True."""
        strategy = Strategy(id="valid")

        # Create a signal factor that produces "positions"
        signal_factor = Factor(
            id="signal",
            name="Position Signal",
            category=FactorCategory.SIGNAL,
            inputs=["rsi"],
            outputs=["positions"],
            logic=simple_logic,
            parameters={}
        )

        strategy.add_factor(rsi_factor)
        strategy.add_factor(signal_factor, depends_on=["rsi_14"])

        # Should pass all validation checks
        assert strategy.validate() is True

    def test_cyclic_dag_raises_error(self, simple_logic):
        """TC2: Cyclic DAG → raises ValueError."""
        strategy = Strategy(id="cyclic")

        factor_a = Factor(
            id="a", name="A", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["a_out"],
            logic=simple_logic, parameters={}
        )
        factor_b = Factor(
            id="b", name="B", category=FactorCategory.SIGNAL,
            inputs=["a_out"], outputs=["positions"],
            logic=simple_logic, parameters={}
        )

        strategy.add_factor(factor_a)
        strategy.add_factor(factor_b, depends_on=["a"])

        # Manually corrupt DAG to create cycle
        strategy.dag.add_edge("b", "a")

        # Validation should detect cycle
        with pytest.raises(ValueError, match="cycle"):
            strategy.validate()

    def test_missing_input_dependencies_raises_error(self, simple_logic):
        """TC3: Missing input dependencies → raises ValueError with details."""
        strategy = Strategy(id="missing_deps")

        # Factor that requires "volume" but it's not produced by any factor
        factor_a = Factor(
            id="vol_factor", name="Volume Factor", category=FactorCategory.MOMENTUM,
            inputs=["close", "volume"], outputs=["vol_signal"],
            logic=simple_logic, parameters={}
        )

        # Factor that requires non-existent column
        factor_b = Factor(
            id="bad_factor", name="Bad Factor", category=FactorCategory.SIGNAL,
            inputs=["vol_signal", "nonexistent_column"], outputs=["positions"],
            logic=simple_logic, parameters={}
        )

        strategy.add_factor(factor_a)
        strategy.add_factor(factor_b, depends_on=["vol_factor"])

        # Validation should detect missing input
        with pytest.raises(ValueError, match="nonexistent_column.*not available"):
            strategy.validate()

    def test_no_position_signals_raises_error(self, rsi_factor):
        """TC4: No position signals → raises ValueError."""
        strategy = Strategy(id="no_signals")
        strategy.add_factor(rsi_factor)  # Only produces "rsi", "rsi_signal" (not "positions")

        # Validation should detect lack of position signals
        with pytest.raises(ValueError, match="position signals"):
            strategy.validate()

    def test_orphaned_factors_raises_error(self, simple_logic):
        """TC5: Orphaned factors → raises ValueError."""
        strategy = Strategy(id="orphans")

        # Main chain
        factor_a = Factor(
            id="a", name="A", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["a_out"],
            logic=simple_logic, parameters={}
        )
        factor_b = Factor(
            id="b", name="B", category=FactorCategory.SIGNAL,
            inputs=["a_out"], outputs=["positions"],
            logic=simple_logic, parameters={}
        )

        # Orphaned factor (not connected to main chain)
        orphan_factor = Factor(
            id="orphan", name="Orphan", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["orphan_out"],
            logic=simple_logic, parameters={}
        )

        strategy.add_factor(factor_a)
        strategy.add_factor(factor_b, depends_on=["a"])

        # Manually add orphan without dependencies (bypassing add_factor validation)
        strategy.factors["orphan"] = orphan_factor
        strategy.dag.add_node("orphan", factor=orphan_factor)

        # Validation should detect orphan
        with pytest.raises(ValueError, match="orphaned factors"):
            strategy.validate()

    def test_duplicate_outputs_raises_error(self, simple_logic):
        """TC6: Duplicate outputs → raises ValueError."""
        strategy = Strategy(id="duplicates")

        # Both factors use base data, so they're not orphaned
        # Both produce "signal" which is a duplicate
        factor_a = Factor(
            id="a", name="A", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["signal", "other"],
            logic=simple_logic, parameters={}
        )
        factor_b = Factor(
            id="b", name="B", category=FactorCategory.SIGNAL,
            inputs=["other"],  # Depends on factor_a's output to avoid orphaning
            outputs=["signal", "positions"],  # Duplicate "signal"
            logic=simple_logic, parameters={}
        )

        strategy.add_factor(factor_a)
        strategy.add_factor(factor_b, depends_on=["a"])  # Create dependency to avoid orphaning

        # Validation should detect duplicate output
        with pytest.raises(ValueError, match="Duplicate output column 'signal'"):
            strategy.validate()

    def test_empty_strategy_raises_error(self):
        """TC7: Empty strategy → raises ValueError."""
        strategy = Strategy(id="empty")

        # Empty strategy should fail validation
        with pytest.raises(ValueError, match="at least one factor"):
            strategy.validate()

    def test_single_factor_with_positions_passes(self, simple_logic):
        """TC8: Single-factor strategy producing positions → True."""
        strategy = Strategy(id="single")

        # Single factor that produces positions directly from base data
        factor = Factor(
            id="simple_signal", name="Simple Signal", category=FactorCategory.SIGNAL,
            inputs=["close"], outputs=["positions"],
            logic=simple_logic, parameters={}
        )

        strategy.add_factor(factor)

        # Should pass validation
        assert strategy.validate() is True

    def test_validation_with_all_position_column_variants(self, simple_logic):
        """Test that all position signal column variants are recognized."""
        position_variants = ["positions", "position", "signal", "signals"]

        for variant in position_variants:
            strategy = Strategy(id=f"test_{variant}")

            factor = Factor(
                id="sig", name="Signal", category=FactorCategory.SIGNAL,
                inputs=["close"], outputs=[variant],
                logic=simple_logic, parameters={}
            )

            strategy.add_factor(factor)

            # Should pass validation with each variant
            assert strategy.validate() is True, f"Failed for variant: {variant}"

    def test_validation_error_messages_are_detailed(self, simple_logic):
        """Test that validation error messages provide helpful details."""
        # Test missing input details
        strategy = Strategy(id="test")

        factor_a = Factor(
            id="a", name="A", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["a_out"],
            logic=simple_logic, parameters={}
        )
        factor_b = Factor(
            id="b", name="B", category=FactorCategory.SIGNAL,
            inputs=["missing_col"], outputs=["positions"],
            logic=simple_logic, parameters={}
        )

        strategy.add_factor(factor_a)
        strategy.add_factor(factor_b, depends_on=["a"])

        try:
            strategy.validate()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            error_msg = str(e)
            # Check that error message includes helpful details
            assert "missing_col" in error_msg
            assert "Factor 'b'" in error_msg
            assert "Available columns" in error_msg

    def test_validation_with_complex_valid_dag(self, simple_logic):
        """Test validation with complex but valid DAG structure."""
        strategy = Strategy(id="complex")

        # Create a complex DAG: diamond + chain
        factor_a = Factor(
            id="a", name="A", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["a_out"],
            logic=simple_logic, parameters={}
        )
        factor_b = Factor(
            id="b", name="B", category=FactorCategory.MOMENTUM,
            inputs=["a_out"], outputs=["b_out"],
            logic=simple_logic, parameters={}
        )
        factor_c = Factor(
            id="c", name="C", category=FactorCategory.MOMENTUM,
            inputs=["a_out"], outputs=["c_out"],
            logic=simple_logic, parameters={}
        )
        factor_d = Factor(
            id="d", name="D", category=FactorCategory.SIGNAL,
            inputs=["b_out", "c_out"], outputs=["positions"],
            logic=simple_logic, parameters={}
        )

        strategy.add_factor(factor_a)
        strategy.add_factor(factor_b, depends_on=["a"])
        strategy.add_factor(factor_c, depends_on=["a"])
        strategy.add_factor(factor_d, depends_on=["b", "c"])

        # Should pass validation
        assert strategy.validate() is True

    def test_validation_checks_base_ohlcv_availability(self, simple_logic):
        """Test that validation assumes base OHLCV data is available."""
        strategy = Strategy(id="ohlcv")

        # Factors using all base OHLCV columns
        factor = Factor(
            id="ohlcv_factor", name="OHLCV Factor", category=FactorCategory.MOMENTUM,
            inputs=["open", "high", "low", "close", "volume"],
            outputs=["positions"],
            logic=simple_logic, parameters={}
        )

        strategy.add_factor(factor)

        # Should pass validation (base OHLCV assumed available)
        assert strategy.validate() is True

    def test_validation_multiple_factors_producing_different_signals(self, simple_logic):
        """Test that multiple factors can produce different position-related outputs."""
        strategy = Strategy(id="multi_signal")

        factor_a = Factor(
            id="entry", name="Entry", category=FactorCategory.SIGNAL,
            inputs=["close"], outputs=["signal"],  # "signal" is a position column
            logic=simple_logic, parameters={}
        )
        factor_b = Factor(
            id="exit", name="Exit", category=FactorCategory.EXIT,
            inputs=["signal"], outputs=["positions"],  # "positions" is also a position column
            logic=simple_logic, parameters={}
        )

        strategy.add_factor(factor_a)
        strategy.add_factor(factor_b, depends_on=["entry"])

        # Should pass validation (has position signals)
        assert strategy.validate() is True


# Test Class 9: Pipeline Compilation (Task A.4)


class TestPipelineCompilation:
    """Test strategy pipeline compilation and execution."""

    @pytest.fixture
    def simple_rsi_logic(self):
        """Simple RSI-like logic for testing."""
        def logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
            result = data.copy()
            # Simple RSI calculation (not accurate, just for testing)
            period = params.get("period", 14)
            delta = result["close"].diff()
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / (loss + 1e-10)  # Avoid division by zero
            result["rsi"] = 100 - (100 / (1 + rs))
            return result
        return logic

    @pytest.fixture
    def simple_signal_logic(self):
        """Simple signal logic for testing."""
        def logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
            result = data.copy()
            threshold = params.get("threshold", 50)
            result["positions"] = (result["rsi"] > threshold).astype(int)
            return result
        return logic

    @pytest.fixture
    def sample_ohlcv_data(self):
        """Sample OHLCV data for testing."""
        return pd.DataFrame({
            "open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "high": [101.0, 102.0, 103.0, 104.0, 105.0],
            "low": [99.0, 100.0, 101.0, 102.0, 103.0],
            "close": [100.5, 101.5, 102.5, 103.5, 104.5],
            "volume": [1000, 1100, 1200, 1300, 1400]
        })

    def test_simple_pipeline_two_factors(
        self, simple_rsi_logic, simple_signal_logic, sample_ohlcv_data
    ):
        """TC1: Simple pipeline (2 factors) → executes in order, produces outputs."""
        strategy = Strategy(id="simple_pipeline")

        # Create RSI factor
        rsi_factor = Factor(
            id="rsi_14", name="RSI 14", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["rsi"],
            logic=simple_rsi_logic, parameters={"period": 14}
        )

        # Create signal factor (depends on RSI)
        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["rsi"], outputs=["positions"],
            logic=simple_signal_logic, parameters={"threshold": 50}
        )

        strategy.add_factor(rsi_factor)
        strategy.add_factor(signal_factor, depends_on=["rsi_14"])

        # Execute pipeline
        result = strategy.to_pipeline(sample_ohlcv_data)

        # Verify outputs
        assert "rsi" in result.columns, "RSI column should be present"
        assert "positions" in result.columns, "Positions column should be present"
        assert len(result) == len(sample_ohlcv_data), "Row count should match input"

        # Verify original data is preserved
        assert all(col in result.columns for col in sample_ohlcv_data.columns)

    def test_complex_pipeline_five_factors(self):
        """TC2: Complex pipeline (5+ factors) → correct execution order."""
        strategy = Strategy(id="complex_pipeline")

        # Create 5 factors with dependencies
        factors = []
        for i in range(5):
            if i == 0:
                # Root factor
                logic = lambda d, p, idx=i: d.assign(**{f"output_{idx}": d["close"] * (idx + 1)})
                factor = Factor(
                    id=f"factor_{i}", name=f"Factor {i}",
                    category=FactorCategory.MOMENTUM,
                    inputs=["close"], outputs=[f"output_{i}"],
                    logic=logic, parameters={}
                )
                strategy.add_factor(factor)
            elif i == 4:
                # Final factor (signal)
                logic = lambda d, p: d.assign(positions=(d["output_3"] > d["output_2"]).astype(int))
                factor = Factor(
                    id=f"factor_{i}", name=f"Factor {i}",
                    category=FactorCategory.SIGNAL,
                    inputs=["output_2", "output_3"], outputs=["positions"],
                    logic=logic, parameters={}
                )
                strategy.add_factor(factor, depends_on=[f"factor_2", f"factor_3"])
            else:
                # Intermediate factors
                logic = lambda d, p, idx=i: d.assign(**{f"output_{idx}": d[f"output_{idx-1}"] * 1.1})
                factor = Factor(
                    id=f"factor_{i}", name=f"Factor {i}",
                    category=FactorCategory.MOMENTUM,
                    inputs=[f"output_{i-1}"], outputs=[f"output_{i}"],
                    logic=logic, parameters={}
                )
                strategy.add_factor(factor, depends_on=[f"factor_{i-1}"])
            factors.append(factor)

        # Execute pipeline
        data = pd.DataFrame({"close": [100.0, 101.0, 102.0, 103.0, 104.0]})
        result = strategy.to_pipeline(data)

        # Verify all outputs are present
        assert "output_0" in result.columns
        assert "output_1" in result.columns
        assert "output_2" in result.columns
        assert "output_3" in result.columns
        assert "positions" in result.columns

    def test_pipeline_with_branching(self):
        """TC3: Pipeline with branching (parallel factors) → both branches execute."""
        strategy = Strategy(id="branching_pipeline")

        # Create root factor
        root_logic = lambda d, p: d.assign(base_signal=d["close"].rolling(5).mean())
        root_factor = Factor(
            id="root", name="Root", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["base_signal"],
            logic=root_logic, parameters={}
        )

        # Create two parallel branches
        branch_a_logic = lambda d, p: d.assign(branch_a=d["base_signal"] * 1.1)
        branch_a = Factor(
            id="branch_a", name="Branch A", category=FactorCategory.MOMENTUM,
            inputs=["base_signal"], outputs=["branch_a"],
            logic=branch_a_logic, parameters={}
        )

        branch_b_logic = lambda d, p: d.assign(branch_b=d["base_signal"] * 0.9)
        branch_b = Factor(
            id="branch_b", name="Branch B", category=FactorCategory.MOMENTUM,
            inputs=["base_signal"], outputs=["branch_b"],
            logic=branch_b_logic, parameters={}
        )

        # Create merge factor
        merge_logic = lambda d, p: d.assign(positions=(d["branch_a"] > d["branch_b"]).astype(int))
        merge_factor = Factor(
            id="merge", name="Merge", category=FactorCategory.SIGNAL,
            inputs=["branch_a", "branch_b"], outputs=["positions"],
            logic=merge_logic, parameters={}
        )

        strategy.add_factor(root_factor)
        strategy.add_factor(branch_a, depends_on=["root"])
        strategy.add_factor(branch_b, depends_on=["root"])
        strategy.add_factor(merge_factor, depends_on=["branch_a", "branch_b"])

        # Execute pipeline
        data = pd.DataFrame({"close": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0]})
        result = strategy.to_pipeline(data)

        # Verify both branches executed
        assert "branch_a" in result.columns
        assert "branch_b" in result.columns
        assert "positions" in result.columns

    def test_invalid_strategy_raises_error(self, simple_rsi_logic):
        """TC4: Invalid strategy → raises ValueError before execution."""
        strategy = Strategy(id="invalid")

        # Create factor without position signals
        rsi_factor = Factor(
            id="rsi_14", name="RSI 14", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["rsi"],
            logic=simple_rsi_logic, parameters={"period": 14}
        )

        strategy.add_factor(rsi_factor)

        # Should raise ValueError during validation
        data = pd.DataFrame({"close": [100.0, 101.0, 102.0]})
        with pytest.raises(ValueError, match="position signals"):
            strategy.to_pipeline(data)

    def test_factor_execution_error_propagates(self):
        """TC5: Factor execution error → propagates with context."""
        strategy = Strategy(id="error_pipeline")

        # Create factor that will raise error
        error_logic = lambda d, p: (_ for _ in ()).throw(RuntimeError("Test error"))
        error_factor = Factor(
            id="error_factor", name="Error Factor", category=FactorCategory.SIGNAL,
            inputs=["close"], outputs=["positions"],
            logic=error_logic, parameters={}
        )

        strategy.add_factor(error_factor)

        # Should propagate error with context
        data = pd.DataFrame({"close": [100.0, 101.0, 102.0]})
        with pytest.raises(RuntimeError, match="error_factor"):
            strategy.to_pipeline(data)

    def test_empty_dataframe_handled_gracefully(self, simple_rsi_logic, simple_signal_logic):
        """TC6: Empty DataFrame → handles gracefully."""
        strategy = Strategy(id="empty_data")

        rsi_factor = Factor(
            id="rsi_14", name="RSI 14", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["rsi"],
            logic=simple_rsi_logic, parameters={"period": 14}
        )

        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["rsi"], outputs=["positions"],
            logic=simple_signal_logic, parameters={"threshold": 50}
        )

        strategy.add_factor(rsi_factor)
        strategy.add_factor(signal_factor, depends_on=["rsi_14"])

        # Execute with empty DataFrame
        empty_data = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        result = strategy.to_pipeline(empty_data)

        # Should return empty DataFrame with all columns
        assert len(result) == 0
        assert "rsi" in result.columns
        assert "positions" in result.columns

    def test_missing_required_columns_raises_error(self, simple_signal_logic):
        """TC7: Missing required columns → clear error message."""
        strategy = Strategy(id="missing_cols")

        # Create factor that requires "rsi" column (which won't be available)
        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["rsi"], outputs=["positions"],
            logic=simple_signal_logic, parameters={"threshold": 50}
        )

        strategy.add_factor(signal_factor)

        # Execute with data missing "rsi" column
        data = pd.DataFrame({"close": [100.0, 101.0, 102.0]})

        # Should raise ValueError during validation (missing inputs)
        with pytest.raises(ValueError, match="signal.*requires inputs.*rsi"):
            strategy.to_pipeline(data)

    def test_performance_benchmark(self):
        """TC8: Performance: <1s for 10-factor pipeline on 1000 rows."""
        import time

        strategy = Strategy(id="performance_test")

        # Create 10-factor chain
        for i in range(10):
            if i == 0:
                logic = lambda d, p, idx=i: d.assign(**{f"col_{idx}": d["close"] + idx})
                factor = Factor(
                    id=f"factor_{i}", name=f"Factor {i}",
                    category=FactorCategory.MOMENTUM,
                    inputs=["close"], outputs=[f"col_{i}"],
                    logic=logic, parameters={}
                )
                strategy.add_factor(factor)
            elif i == 9:
                # Final factor produces positions
                logic = lambda d, p: d.assign(positions=(d["col_8"] > d["close"]).astype(int))
                factor = Factor(
                    id=f"factor_{i}", name=f"Factor {i}",
                    category=FactorCategory.SIGNAL,
                    inputs=["col_8", "close"], outputs=["positions"],
                    logic=logic, parameters={}
                )
                strategy.add_factor(factor, depends_on=[f"factor_8"])
            else:
                logic = lambda d, p, idx=i: d.assign(**{f"col_{idx}": d[f"col_{idx-1}"] + 1})
                factor = Factor(
                    id=f"factor_{i}", name=f"Factor {i}",
                    category=FactorCategory.MOMENTUM,
                    inputs=[f"col_{i-1}"], outputs=[f"col_{i}"],
                    logic=logic, parameters={}
                )
                strategy.add_factor(factor, depends_on=[f"factor_{i-1}"])

        # Create 1000-row dataset
        import numpy as np
        data = pd.DataFrame({
            "close": np.random.randn(1000).cumsum() + 100
        })

        # Measure execution time
        start_time = time.time()
        result = strategy.to_pipeline(data)
        end_time = time.time()

        execution_time = end_time - start_time

        # Verify performance requirement
        assert execution_time < 1.0, f"Pipeline took {execution_time:.2f}s, expected <1s"
        assert len(result) == 1000
        assert "positions" in result.columns

    def test_pipeline_preserves_input_data(self, simple_rsi_logic, simple_signal_logic, sample_ohlcv_data):
        """Test that pipeline does not modify input DataFrame."""
        strategy = Strategy(id="preserve_input")

        rsi_factor = Factor(
            id="rsi_14", name="RSI 14", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["rsi"],
            logic=simple_rsi_logic, parameters={"period": 14}
        )

        signal_factor = Factor(
            id="signal", name="Signal", category=FactorCategory.SIGNAL,
            inputs=["rsi"], outputs=["positions"],
            logic=simple_signal_logic, parameters={"threshold": 50}
        )

        strategy.add_factor(rsi_factor)
        strategy.add_factor(signal_factor, depends_on=["rsi_14"])

        # Save original data
        original_data = sample_ohlcv_data.copy()
        original_columns = set(sample_ohlcv_data.columns)

        # Execute pipeline
        result = strategy.to_pipeline(sample_ohlcv_data)

        # Verify input data unchanged
        assert set(sample_ohlcv_data.columns) == original_columns
        assert len(sample_ohlcv_data) == len(original_data)
        pd.testing.assert_frame_equal(sample_ohlcv_data, original_data)

        # Verify result has new columns
        assert "rsi" in result.columns
        assert "positions" in result.columns

    def test_pipeline_execution_order_complex_dag(self):
        """Test that pipeline respects complex DAG dependencies."""
        strategy = Strategy(id="complex_dag")

        # Create diamond DAG: A → B, A → C, B → D, C → D
        factor_a = Factor(
            id="a", name="A", category=FactorCategory.MOMENTUM,
            inputs=["close"], outputs=["a_out"],
            logic=lambda d, p: d.assign(a_out=d["close"] * 2),
            parameters={}
        )

        factor_b = Factor(
            id="b", name="B", category=FactorCategory.MOMENTUM,
            inputs=["a_out"], outputs=["b_out"],
            logic=lambda d, p: d.assign(b_out=d["a_out"] + 10),
            parameters={}
        )

        factor_c = Factor(
            id="c", name="C", category=FactorCategory.MOMENTUM,
            inputs=["a_out"], outputs=["c_out"],
            logic=lambda d, p: d.assign(c_out=d["a_out"] - 5),
            parameters={}
        )

        factor_d = Factor(
            id="d", name="D", category=FactorCategory.SIGNAL,
            inputs=["b_out", "c_out"], outputs=["positions"],
            logic=lambda d, p: d.assign(positions=(d["b_out"] > d["c_out"]).astype(int)),
            parameters={}
        )

        strategy.add_factor(factor_a)
        strategy.add_factor(factor_b, depends_on=["a"])
        strategy.add_factor(factor_c, depends_on=["a"])
        strategy.add_factor(factor_d, depends_on=["b", "c"])

        # Execute pipeline
        data = pd.DataFrame({"close": [100.0, 101.0, 102.0]})
        result = strategy.to_pipeline(data)

        # Verify all outputs present and computed correctly
        assert "a_out" in result.columns
        assert "b_out" in result.columns
        assert "c_out" in result.columns
        assert "positions" in result.columns

        # Verify computation correctness
        assert all(result["a_out"] == data["close"] * 2)
        assert all(result["b_out"] == result["a_out"] + 10)
        assert all(result["c_out"] == result["a_out"] - 5)
